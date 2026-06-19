import csv
import hashlib
import uuid
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import CVFile, Candidate, ExtractedCVData, LinkedInCSVImport, OutlookCVImport
from app.services.cv_service import MAX_CV_FILE_SIZE_BYTES, UPLOAD_DIRECTORY
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
LOCATION_COLUMNS = ("location", "city", "address")
PHONE_COLUMNS = ("phone", "phone number", "mobile")
OUTLOOK_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


async def import_linkedin_csv(db: Session, upload_file: UploadFile) -> LinkedInCSVImport:
    filename = upload_file.filename or "linkedin-export.csv"
    if not filename.lower().endswith(".csv"):
        raise ImportError("Only CSV files are supported.")

    content = await upload_file.read()
    if not content:
        raise ImportError("Uploaded CSV file is empty.")

    reader = csv.DictReader(StringIO(_decode_csv(content)))
    if not reader.fieldnames:
        raise ImportError("CSV file has no header row.")

    imported = 0
    updated = 0
    skipped = 0
    rows_report: list[dict[str, Any]] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {_normalize_key(key): (value or "").strip() for key, value in row.items() if key is not None}
        email = _get_first(normalized_row, EMAIL_COLUMNS).lower()
        linkedin_url = _get_first(normalized_row, LINKEDIN_COLUMNS)
        first_name = _get_first(normalized_row, FIRST_NAME_COLUMNS)
        last_name = _get_first(normalized_row, LAST_NAME_COLUMNS)

        if not email and not linkedin_url:
            skipped += 1
            rows_report.append({"row": row_number, "status": "skipped", "reason": "Missing email and LinkedIn URL."})
            continue

        candidate = _find_candidate(db, email=email, linkedin_url=linkedin_url)
        if candidate is None and (not first_name or not last_name):
            skipped += 1
            rows_report.append({"row": row_number, "status": "skipped", "reason": "Missing candidate name for new record."})
            continue

        if candidate is None:
            candidate = Candidate(
                first_name=first_name,
                last_name=last_name,
                email=email or None,
                linkedin_url=linkedin_url or None,
                phone=_get_first(normalized_row, PHONE_COLUMNS) or None,
                location=_get_first(normalized_row, LOCATION_COLUMNS) or None,
                current_title=_get_first(normalized_row, TITLE_COLUMNS) or None,
                source="linkedin_csv",
                status="active",
            )
            db.add(candidate)
            db.flush()
            create_timeline_event(
                db,
                candidate_id=candidate.id,
                event_type="linkedin_csv_imported",
                title="Candidate imported from LinkedIn CSV",
                description=f"{candidate.first_name} {candidate.last_name} was imported from a LinkedIn CSV file.",
                metadata={"source": "linkedin_csv", "filename": filename, "row": row_number},
            )
            imported += 1
            rows_report.append({"row": row_number, "status": "imported", "candidate_id": str(candidate.id)})
            continue

        changed_fields = _update_candidate_from_row(candidate, normalized_row)
        candidate.source = "linkedin_csv"
        if changed_fields:
            create_timeline_event(
                db,
                candidate_id=candidate.id,
                event_type="linkedin_csv_imported",
                title="Candidate updated from LinkedIn CSV",
                description="Candidate profile was updated during LinkedIn CSV import.",
                metadata={"source": "linkedin_csv", "filename": filename, "row": row_number, "updated_fields": changed_fields},
            )
        updated += 1
        rows_report.append({"row": row_number, "status": "updated", "candidate_id": str(candidate.id), "updated_fields": changed_fields})

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
        raise ImportError("Upload a ZIP archive or at least one PDF/DOCX CV file.")

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
        raise ImportError("No CV files were found in the Outlook import upload.")

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
            files_report.append({"file": filename, "status": "failed", "reason": "Invalid file content."})
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
    raise ImportError("CSV encoding is not supported.")


def _find_candidate(db: Session, email: str, linkedin_url: str) -> Candidate | None:
    conditions = []
    if email:
        conditions.append(Candidate.email == email)
    if linkedin_url:
        conditions.append(Candidate.linkedin_url == linkedin_url)
    if not conditions:
        return None
    return db.scalar(select(Candidate).where(or_(*conditions)))


def _find_candidate_for_cv(db: Session, parsed_data: dict[str, Any]) -> Candidate | None:
    email = str(parsed_data.get("email") or "").strip().lower()
    if email:
        return db.scalar(select(Candidate).where(Candidate.email == email))
    return None


def _process_outlook_cv_file(db: Session, filename: str, content: bytes, content_type: str | None) -> dict[str, Any]:
    extension = Path(filename).suffix.lower()
    if extension not in OUTLOOK_SUPPORTED_EXTENSIONS:
        return {"file": filename, "status": "skipped", "reason": "Only PDF and DOCX CV files are supported."}
    if len(content) > MAX_CV_FILE_SIZE_BYTES:
        return {"file": filename, "status": "skipped", "reason": "File is larger than 5MB."}

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIRECTORY / f"{uuid.uuid4()}{extension}"
    stored_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()

    try:
        raw_text = extract_text_from_file(stored_path, extension)
        if not raw_text.strip():
            stored_path.unlink(missing_ok=True)
            return {"file": filename, "status": "failed", "reason": "No text could be extracted from this CV."}

        parsed_cv = parse_cv_text_configurable(raw_text)
        parsed_data = parsed_cv.data
        candidate = _find_candidate_for_cv(db, parsed_data)
        status = "updated" if candidate is not None else "imported"

        if candidate is None:
            first_name = str(parsed_data.get("first_name") or "").strip() or "Unknown"
            last_name = str(parsed_data.get("last_name") or "").strip() or Path(filename).stem[:100] or "Candidate"
            candidate = Candidate(
                first_name=first_name,
                last_name=last_name,
                email=str(parsed_data.get("email") or "").strip().lower() or None,
                phone=str(parsed_data.get("phone") or "").strip() or None,
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
            confidence_score=parsed_cv.confidence_score,
            parsing_status="parsed",
            status="approved",
        )
        db.add(extracted_data)

        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="outlook_imported",
            title="Candidate imported from Outlook",
            description=f"{candidate.first_name} {candidate.last_name} was processed from an Outlook CV attachment.",
            metadata={"source": "outlook_import", "filename": filename, "cv_file_id": str(cv_file.id), "status": status},
        )
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="cv_parsed",
            title="CV parsed",
            description="Outlook CV attachment was extracted and parsed automatically.",
            metadata={
                "source": "outlook_import",
                "cv_file_id": str(cv_file.id),
                "confidence_score": float(parsed_cv.confidence_score),
                "parser_used": parsed_data.get("parser_used"),
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
        return {"file": filename, "status": "failed", "reason": "Outlook CV import failed.", "detail": str(exc)}


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
                        "reason": "Only PDF and DOCX CV files are supported.",
                    })
                    continue
                if member.file_size > MAX_CV_FILE_SIZE_BYTES:
                    files.append({
                        "filename": member_name,
                        "content": b"",
                        "content_type": None,
                        "status": "skipped",
                        "reason": "File is larger than 5MB.",
                    })
                    continue
                files.append({"filename": member_name, "content": archive.read(member), "content_type": _guess_mime_type(extension)})
        return files
    except zipfile.BadZipFile as exc:
        raise ImportError(f"{filename} is not a valid ZIP archive.") from exc


def _update_candidate_from_parsed_cv(candidate: Candidate, parsed_data: dict[str, Any]) -> None:
    for field in ("first_name", "last_name", "email", "phone"):
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
    mapping = {
        "first_name": _get_first(row, FIRST_NAME_COLUMNS),
        "last_name": _get_first(row, LAST_NAME_COLUMNS),
        "email": _get_first(row, EMAIL_COLUMNS).lower(),
        "linkedin_url": _get_first(row, LINKEDIN_COLUMNS),
        "phone": _get_first(row, PHONE_COLUMNS),
        "location": _get_first(row, LOCATION_COLUMNS),
        "current_title": _get_first(row, TITLE_COLUMNS),
    }
    changed_fields = []
    for field, value in mapping.items():
        if value and getattr(candidate, field) != value:
            setattr(candidate, field, value)
            changed_fields.append(field)
    return changed_fields


def _get_first(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        if row.get(key):
            return row[key].strip()
    return ""


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("\ufeff", "")
