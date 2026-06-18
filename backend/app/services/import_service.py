import csv
from io import StringIO
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Candidate, LinkedInCSVImport
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
                event_type="candidate_created",
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
                event_type="candidate_updated",
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
