import csv
import hashlib
import logging
import uuid
import zipfile
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CVFile, Candidate, ExtractedCVData, LinkedInCSVImport, OutlookCVImport
from app.services.cv_service import MAX_CV_FILE_SIZE_BYTES, UPLOAD_DIRECTORY
from app.services.embedding_service import build_candidate_embedding_text, generate_embedding
from app.services.llm_cv_parser_service import parse_cv_text_configurable
from app.services.matching_service import auto_match_candidate
from app.services.text_extraction import TextExtractionError, extract_text_from_file
from app.services.timeline_service import create_timeline_event


class ImportError(ValueError):
    pass


EMAIL_COLUMNS = ("email address", "email", "e-mail", "primary email")
LINKEDIN_COLUMNS = ("profile url", "profile link", "linkedin url", "linkedin_url", "url", "public profile url")
FIRST_NAME_COLUMNS = ("first name", "firstname", "first_name", "given name")
LAST_NAME_COLUMNS = ("last name", "lastname", "last_name", "surname", "family name")
TITLE_COLUMNS = ("position", "title", "job title", "current position", "headline", "occupation")
COMPANY_COLUMNS = ("company", "current company", "organization", "organisation", "employer")
LOCATION_COLUMNS = ("location", "city", "address")
PHONE_COLUMNS = ("phone", "phone number", "mobile")
OUTLOOK_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
LINKEDIN_IMPORT_BATCH_SIZE = 500
LINKEDIN_FIELD_LIMITS = {
    "first_name": 100,
    "last_name": 100,
    "email": 255,
    "phone": 50,
    "location": 255,
    "current_title": 150,
    "current_company": 150,
}
logger = logging.getLogger(__name__)


async def import_linkedin_csv(db: Session, upload_file: UploadFile) -> LinkedInCSVImport:
    filename = upload_file.filename or "linkedin-export.csv"
    if not filename.lower().endswith(".csv"):
        raise ImportError("Seuls les fichiers CSV sont pris en charge.")

    content = await upload_file.read()
    if not content:
        raise ImportError("Le fichier CSV importe est vide.")

    reader = _build_csv_reader(content)
    if not reader.fieldnames:
        raise ImportError("Le fichier CSV ne contient pas de ligne d'en-tete.")

    imported = 0
    updated = 0
    skipped = 0
    rows_report: list[dict[str, Any]] = []
    pending_rows: list[dict[str, Any]] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {_normalize_key(key): (value or "").strip() for key, value in row.items() if key is not None}
        pending_rows.append({"row_number": row_number, "row": normalized_row})
        if len(pending_rows) >= LINKEDIN_IMPORT_BATCH_SIZE:
            batch_stats = _process_linkedin_csv_batch(db, pending_rows, filename)
            imported += batch_stats["imported"]
            updated += batch_stats["updated"]
            skipped += batch_stats["skipped"]
            rows_report.extend(batch_stats["rows"])
            pending_rows = []

    if pending_rows:
        batch_stats = _process_linkedin_csv_batch(db, pending_rows, filename)
        imported += batch_stats["imported"]
        updated += batch_stats["updated"]
        skipped += batch_stats["skipped"]
        rows_report.extend(batch_stats["rows"])

    import_record = LinkedInCSVImport(
        filename=filename,
        imported_count=imported,
        updated_count=updated,
        skipped_count=skipped,
        report={"rows": rows_report},
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)
    return import_record


def _process_linkedin_csv_batch(db: Session, rows: list[dict[str, Any]], filename: str) -> dict[str, Any]:
    pending_results: list[dict[str, Any]] = []
    try:
        for item in rows:
            row_number = int(item["row_number"])
            normalized_row = item["row"]
            pending_results.append(_process_linkedin_csv_row(db, normalized_row, row_number, filename))
        db.commit()
    except Exception as exc:
        db.rollback()
        first_row = rows[0]["row_number"] if rows else None
        last_row = rows[-1]["row_number"] if rows else None
        logger.exception(
            "LinkedIn CSV import batch failed stage=batch_commit exception_type=%s rows=%s-%s",
            type(exc).__name__,
            first_row,
            last_row,
        )
        raise

    return {
        "imported": sum(1 for result in pending_results if result.get("status") == "imported"),
        "updated": sum(1 for result in pending_results if result.get("status") == "updated"),
        "skipped": sum(1 for result in pending_results if result.get("status") == "skipped"),
        "rows": pending_results,
    }


def _process_linkedin_csv_row(db: Session, normalized_row: dict[str, str], row_number: int, filename: str) -> dict[str, Any]:
    try:
        parsed_row = _extract_linkedin_candidate_fields(normalized_row)
        email = parsed_row["email"]
        linkedin_url = parsed_row["linkedin_url"]
        first_name = parsed_row["first_name"]
        last_name = parsed_row["last_name"]
        current_company = parsed_row["current_company"]

        if not email and not linkedin_url and not (first_name and last_name and current_company):
            return {
                "row": row_number,
                "status": "skipped",
                "reason": "Email, URL LinkedIn et cles nom/entreprise manquants.",
            }

        candidate = _find_linkedin_csv_candidate(
            db,
            email=email,
            linkedin_url=linkedin_url,
            first_name=first_name,
            last_name=last_name,
            current_company=current_company,
        )
        if candidate is None and (not first_name or not last_name):
            return {"row": row_number, "status": "skipped", "reason": "Nom du candidat manquant pour un nouveau profil."}

        if candidate is None:
            candidate = Candidate(
                first_name=first_name,
                last_name=last_name,
                email=email or None,
                linkedin_url=linkedin_url or None,
                phone=parsed_row["phone"] or None,
                location=parsed_row["location"] or None,
                current_title=parsed_row["current_title"] or None,
                current_company=current_company or None,
                source="linkedin_csv",
                status="active",
            )
            db.add(candidate)
            db.flush()
            create_timeline_event(
                db,
                candidate_id=candidate.id,
                event_type="linkedin_csv_imported",
                title="Candidat importe depuis un CSV LinkedIn",
                description=f"{candidate.first_name} {candidate.last_name} a ete importe depuis un fichier CSV LinkedIn.",
                metadata={"source": "linkedin_csv", "filename": filename, "row": row_number},
            )
            db.flush()
            return {"row": row_number, "status": "imported", "candidate_id": str(candidate.id)}

        changed_fields = _update_candidate_from_row(candidate, normalized_row)
        if changed_fields:
            create_timeline_event(
                db,
                candidate_id=candidate.id,
                event_type="linkedin_csv_imported",
                title="Candidat mis a jour depuis un CSV LinkedIn",
                description="Le profil candidat a ete mis a jour pendant l'import CSV LinkedIn.",
                metadata={"source": "linkedin_csv", "filename": filename, "row": row_number, "updated_fields": changed_fields},
            )
        db.flush()
        return {"row": row_number, "status": "updated", "candidate_id": str(candidate.id), "updated_fields": changed_fields}
    except Exception as exc:
        logger.exception(
            "LinkedIn CSV import row failed stage=row_processing exception_type=%s row=%s",
            type(exc).__name__,
            row_number,
        )
        raise

def list_linkedin_imports(db: Session, skip: int = 0, limit: int = 50) -> list[LinkedInCSVImport]:
    statement = select(LinkedInCSVImport).order_by(LinkedInCSVImport.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_linkedin_import_summary(db: Session) -> dict[str, int]:
    statement = select(
        func.count(LinkedInCSVImport.id),
        func.coalesce(func.sum(LinkedInCSVImport.imported_count), 0),
        func.coalesce(func.sum(LinkedInCSVImport.updated_count), 0),
        func.coalesce(func.sum(LinkedInCSVImport.skipped_count), 0),
    )
    total_imports, total_imported, total_updated, total_skipped = db.execute(statement).one()
    return {
        "total_imports": int(total_imports),
        "total_imported": int(total_imported),
        "total_updated": int(total_updated),
        "total_skipped": int(total_skipped),
    }


async def import_outlook_cvs(db: Session, upload_files: list[UploadFile]) -> OutlookCVImport:
    if not upload_files:
        raise ImportError("Importez une archive ZIP ou au moins un fichier CV PDF/DOCX.")

    batches: list[dict[str, bytes | str | None]] = []
    source_names: list[str] = []
    for upload_file in upload_files:
        filename = upload_file.filename or "outlook-cv"
        source_names.append(filename)
        content = await upload_file.read()
        if not content:
            continue
        extension = Path(filename).suffix.lower()
        if extension == ".zip":
            batches.extend(_extract_zip_cv_files(filename, content))
        else:
            batches.append({"filename": filename, "content": content, "content_type": upload_file.content_type})

    if not batches:
        raise ImportError("Aucun fichier CV n'a été trouvé dans l'import.")

    imported = 0
    updated = 0
    skipped = 0
    failed = 0
    files_report: list[dict[str, Any]] = []

    for item in batches:
        filename = str(item["filename"])
        if item.get("status") == "skipped":
            skipped += 1
            files_report.append({"file": filename, "status": "skipped", "reason": item.get("reason")})
            continue
        content = item["content"]
        content_type = item.get("content_type")
        if not isinstance(content, bytes):
            failed += 1
            files_report.append({"file": filename, "status": "failed", "reason": "Contenu du fichier invalide."})
            continue

        result = _process_outlook_cv_file(db, filename=filename, content=content, content_type=str(content_type) if content_type else None)
        files_report.append(result)
        if result["status"] == "imported":
            imported += 1
        elif result["status"] == "updated":
            updated += 1
        elif result["status"] == "skipped":
            skipped += 1
        else:
            failed += 1

    import_record = OutlookCVImport(
        filename=", ".join(source_names[:3]) + ("..." if len(source_names) > 3 else ""),
        imported_count=imported,
        updated_count=updated,
        skipped_count=skipped,
        failed_count=failed,
        report={"files": files_report},
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)
    return import_record


def list_outlook_imports(db: Session, skip: int = 0, limit: int = 50) -> list[OutlookCVImport]:
    statement = select(OutlookCVImport).order_by(OutlookCVImport.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_outlook_import_summary(db: Session) -> dict[str, int]:
    statement = select(
        func.count(OutlookCVImport.id),
        func.coalesce(func.sum(OutlookCVImport.imported_count), 0),
        func.coalesce(func.sum(OutlookCVImport.updated_count), 0),
        func.coalesce(func.sum(OutlookCVImport.skipped_count), 0),
        func.coalesce(func.sum(OutlookCVImport.failed_count), 0),
    )
    total_imports, total_imported, total_updated, total_skipped, total_failed = db.execute(statement).one()
    return {
        "total_imports": int(total_imports),
        "total_imported": int(total_imported),
        "total_updated": int(total_updated),
        "total_skipped": int(total_skipped),
        "total_failed": int(total_failed),
    }


def _decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ImportError("L'encodage du fichier CSV n'est pas pris en charge.")


def _build_csv_reader(content: bytes) -> csv.DictReader:
    text = _decode_csv(content)
    return csv.DictReader(StringIO(text), delimiter=_detect_csv_delimiter(text))


def _detect_csv_delimiter(text: str) -> str:
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        header = sample.splitlines()[0] if sample else ""
        return ";" if header.count(";") > header.count(",") else ","


def _find_linkedin_csv_candidate(
    db: Session,
    *,
    email: str,
    linkedin_url: str,
    first_name: str,
    last_name: str,
    current_company: str,
) -> Candidate | None:
    linkedin_url = _normalize_linkedin_url(linkedin_url)
    if email:
        candidate = db.scalar(select(Candidate).where(Candidate.email == email))
        if candidate is not None:
            return candidate
    if linkedin_url:
        candidate = db.scalar(select(Candidate).where(Candidate.linkedin_url == linkedin_url))
        if candidate is not None:
            return candidate
    if first_name and last_name and current_company:
        candidate = db.scalar(
            select(Candidate).where(
                func.lower(Candidate.first_name) == first_name.lower(),
                func.lower(Candidate.last_name) == last_name.lower(),
                func.lower(Candidate.current_company) == current_company.lower(),
            )
        )
        if candidate is not None:
            return candidate
    return None


def _find_candidate_for_cv(db: Session, parsed_data: dict[str, Any]) -> Candidate | None:
    email = str(parsed_data.get("email") or "").strip().lower()
    if email:
        return db.scalar(select(Candidate).where(Candidate.email == email))
    return None


def _process_outlook_cv_file(db: Session, filename: str, content: bytes, content_type: str | None) -> dict[str, Any]:
    extension = Path(filename).suffix.lower()
    if extension not in OUTLOOK_SUPPORTED_EXTENSIONS:
        return {"file": filename, "status": "skipped", "reason": "Seuls les fichiers CV PDF et DOCX sont pris en charge."}
    if len(content) > MAX_CV_FILE_SIZE_BYTES:
        return {"file": filename, "status": "skipped", "reason": "Le fichier dépasse 5 Mo."}

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIRECTORY / f"{uuid.uuid4()}{extension}"
    stored_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()

    try:
        raw_text = extract_text_from_file(stored_path, extension)
        if not raw_text.strip():
            stored_path.unlink(missing_ok=True)
            return {"file": filename, "status": "failed", "reason": "Aucun texte n'a pu être extrait de ce CV."}

        parsed_cv = parse_cv_text_configurable(raw_text)
        parsed_data = parsed_cv.data
        candidate = _find_candidate_for_cv(db, parsed_data)
        status = "updated" if candidate is not None else "imported"

        if candidate is None:
            first_name = str(parsed_data.get("first_name") or "").strip() or "Prénom"
            last_name = str(parsed_data.get("last_name") or "").strip() or Path(filename).stem[:100] or "Candidat"
            candidate = Candidate(
                first_name=first_name,
                last_name=last_name,
            email=str(parsed_data.get("email") or "").strip().lower() or None,
            phone=str(parsed_data.get("phone") or "").strip() or None,
            linkedin_url=str(parsed_data.get("linkedin_url") or "").strip() or None,
            current_title=str(parsed_data.get("current_title") or "").strip() or None,
            current_company=str(parsed_data.get("current_company") or "").strip() or None,
            gender=str(parsed_data.get("gender") or "").strip() or None,
            source="outlook_import",
            status="active",
            )
            db.add(candidate)
            db.flush()
        else:
            _update_candidate_from_parsed_cv(candidate, parsed_data)
            candidate.source = "outlook_import"
            candidate.status = "active"
            db.flush()

        cv_file = CVFile(
            candidate_id=candidate.id,
            original_filename=filename,
            storage_path=str(stored_path),
            mime_type=content_type or _guess_mime_type(extension),
            file_size_bytes=len(content),
            checksum_sha256=checksum,
            parsing_status="parsed",
        )
        db.add(cv_file)
        db.flush()

        extracted_data = ExtractedCVData(
            cv_file_id=cv_file.id,
            candidate_id=candidate.id,
            raw_text=raw_text,
            parsed_json=parsed_data,
            ai_output=parsed_data,
            summary=_optional_string(parsed_data.get("summary")),
            total_years_experience=_optional_non_negative_number(parsed_data.get("total_experience_years") or parsed_data.get("experience_totale")),
            highest_degree=_optional_string(parsed_data.get("highest_degree")),
            parser_model=_parser_model(parsed_data),
            confidence_score=parsed_cv.confidence_score,
            parsing_status="parsed",
            status="approved",
        )
        db.add(extracted_data)
        db.flush()
        _generate_candidate_embedding(db, extracted_data)

        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="outlook_imported",
            title="Candidat importé depuis un fichier CV",
            description=f"{candidate.first_name} {candidate.last_name} a été traité depuis un fichier CV importé.",
            metadata={"source": "outlook_import", "filename": filename, "cv_file_id": str(cv_file.id), "status": status},
        )
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="cv_parsed",
            title="CV analysé",
            description="Le fichier CV importé a été extrait et analysé automatiquement.",
            metadata={
                "source": "outlook_import",
                "cv_file_id": str(cv_file.id),
                "confidence_score": float(parsed_cv.confidence_score),
                "parser_used": parsed_data.get("parser_used"),
                "parser_model": extracted_data.parser_model,
            },
        )
        db.commit()

        matching_results = auto_match_candidate(db, candidate_id=candidate.id)
        return {
            "file": filename,
            "status": status,
            "candidate_id": str(candidate.id),
            "cv_file_id": str(cv_file.id),
            "confidence_score": float(parsed_cv.confidence_score),
            "matching_results": len(matching_results),
        }
    except TextExtractionError as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        return {"file": filename, "status": "failed", "reason": str(exc)}
    except Exception as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        return {"file": filename, "status": "failed", "reason": "L'import du CV a échoué.", "detail": str(exc)}


def _extract_zip_cv_files(filename: str, content: bytes) -> list[dict[str, bytes | str | None]]:
    try:
        files: list[dict[str, bytes | str | None]] = []
        with zipfile.ZipFile(BytesIO(content)) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                member_name = Path(member.filename).name
                extension = Path(member_name).suffix.lower()
                if extension not in OUTLOOK_SUPPORTED_EXTENSIONS:
                    files.append({
                        "filename": member_name,
                        "content": b"",
                        "content_type": None,
                        "status": "skipped",
                        "reason": "Seuls les fichiers CV PDF et DOCX sont pris en charge.",
                    })
                    continue
                if member.file_size > MAX_CV_FILE_SIZE_BYTES:
                    files.append({
                        "filename": member_name,
                        "content": b"",
                        "content_type": None,
                        "status": "skipped",
                        "reason": "Le fichier dépasse 5 Mo.",
                    })
                    continue
                files.append({"filename": member_name, "content": archive.read(member), "content_type": _guess_mime_type(extension)})
        return files
    except zipfile.BadZipFile as exc:
        raise ImportError(f"{filename} n'est pas une archive ZIP valide.") from exc


def _update_candidate_from_parsed_cv(candidate: Candidate, parsed_data: dict[str, Any]) -> None:
    for field in ("first_name", "last_name", "email", "phone", "linkedin_url", "current_title", "current_company", "gender"):
        value = str(parsed_data.get(field) or "").strip()
        if field == "email":
            value = value.lower()
        if value and not getattr(candidate, field):
            setattr(candidate, field, value)


def _guess_mime_type(extension: str) -> str:
    if extension == ".pdf":
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _update_candidate_from_row(candidate: Candidate, row: dict[str, str]) -> list[str]:
    parsed_row = _extract_linkedin_candidate_fields(row)
    mapping = {
        "first_name": parsed_row["first_name"],
        "last_name": parsed_row["last_name"],
        "email": parsed_row["email"],
        "linkedin_url": parsed_row["linkedin_url"],
        "phone": parsed_row["phone"],
        "location": parsed_row["location"],
        "current_title": parsed_row["current_title"],
        "current_company": parsed_row["current_company"],
    }
    changed_fields = []
    for field, value in mapping.items():
        if value and not getattr(candidate, field):
            setattr(candidate, field, value)
            changed_fields.append(field)
    return changed_fields


def _get_first(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        if row.get(key):
            return row[key].strip()
    return ""


def _extract_linkedin_candidate_fields(row: dict[str, str]) -> dict[str, str]:
    linkedin_url = _normalize_linkedin_url(_get_first(row, LINKEDIN_COLUMNS))
    current_title = _get_first(row, TITLE_COLUMNS)

    # Some LinkedIn exports contain unquoted commas/semicolons in names or titles,
    # which can shift the real profile URL into the Position column. Recover it
    # before applying database length limits.
    title_as_url = _normalize_linkedin_url(current_title)
    if not _is_linkedin_url(linkedin_url) and _is_linkedin_url(title_as_url):
        linkedin_url = title_as_url
        current_title = ""
    elif not _is_linkedin_url(linkedin_url):
        linkedin_url = ""

    return {
        "first_name": _truncate_linkedin_field(_get_first(row, FIRST_NAME_COLUMNS), "first_name"),
        "last_name": _truncate_linkedin_field(_get_first(row, LAST_NAME_COLUMNS), "last_name"),
        "email": _truncate_linkedin_field(_get_first(row, EMAIL_COLUMNS).lower(), "email"),
        "linkedin_url": linkedin_url,
        "phone": _truncate_linkedin_field(_get_first(row, PHONE_COLUMNS), "phone"),
        "location": _truncate_linkedin_field(_get_first(row, LOCATION_COLUMNS), "location"),
        "current_title": _truncate_linkedin_field(current_title, "current_title"),
        "current_company": _truncate_linkedin_field(_get_first(row, COMPANY_COLUMNS), "current_company"),
    }


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("\ufeff", "")


def _normalize_linkedin_url(value: str) -> str:
    url = (value or "").strip()
    if not url:
        return ""
    if url.lower().startswith("linkedin.com/") or url.lower().startswith("www.linkedin.com/"):
        url = f"https://{url}"
    return url.rstrip("/")


def _is_linkedin_url(value: str) -> bool:
    return "linkedin.com/" in (value or "").lower()


def _truncate_linkedin_field(value: str, field: str) -> str:
    clean_value = (value or "").strip()
    limit = LINKEDIN_FIELD_LIMITS.get(field)
    if not limit or len(clean_value) <= limit:
        return clean_value
    return clean_value[:limit].rstrip()


def _parser_model(parsed_data: dict) -> str:
    if parsed_data.get("parser_used") == "llm":
        from app.core.config import settings

        return f"openai:{settings.effective_llm_model}"
    return "heuristic-v1"


def _generate_candidate_embedding(db: Session, extracted_data: ExtractedCVData) -> None:
    try:
        embedding_text = build_candidate_embedding_text(extracted_data)
        extracted_data.embedding = generate_embedding(embedding_text)
        extracted_data.embedding_generated_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.warning("Candidate embedding generation failed during Outlook import; continuing without embedding: %s", exc)


def _optional_string(value: object) -> str | None:
    clean_value = str(value or "").strip()
    return clean_value or None


def _optional_non_negative_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
