import hashlib
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CVFile, Candidate, ExtractedCVData
from app.services.cv_parser import parse_cv_text
from app.services.matching_service import auto_match_candidate
from app.services.text_extraction import TextExtractionError, extract_text_from_file
from app.services.timeline_service import create_timeline_event


MAX_CV_FILE_SIZE_BYTES = 5 * 1024 * 1024
UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads" / "cvs"
SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class CVUploadError(ValueError):
    pass


def upload_cv(
    db: Session,
    candidate_id: UUID,
    upload_file: UploadFile,
    uploaded_by: str = "recruiter",
    application_id: UUID | None = None,
) -> CVFile:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise CVUploadError("Candidate not found.")

    original_filename = upload_file.filename or ""
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise CVUploadError("Unsupported file format. Only PDF, DOC, and DOCX files are allowed.")

    if upload_file.content_type and upload_file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise CVUploadError("Unsupported file type. Please upload a PDF, DOC, or DOCX file.")

    if extension == ".doc":
        raise CVUploadError("DOC text extraction is not supported yet. Please upload a PDF or DOCX file.")

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}{extension}"
    stored_path = UPLOAD_DIRECTORY / stored_filename

    file_size, checksum = _save_upload_file(upload_file, stored_path)
    if file_size == 0:
        stored_path.unlink(missing_ok=True)
        raise CVUploadError("Uploaded file is empty.")

    try:
        raw_text = extract_text_from_file(stored_path, extension)
        if not raw_text:
            raise CVUploadError("No text could be extracted from this CV.")

        cv_file = CVFile(
            candidate_id=candidate_id,
            original_filename=original_filename,
            storage_path=str(stored_path),
            mime_type=upload_file.content_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            parsing_status="parsed",
        )
        db.add(cv_file)
        db.flush()

        extracted_data = ExtractedCVData(
            cv_file_id=cv_file.id,
            candidate_id=candidate_id,
            raw_text=raw_text,
            parsed_json=None,
            ai_output=None,
            confidence_score=None,
            parsing_status="extracted",
            status="parsed",
        )
        db.add(extracted_data)
        create_timeline_event(
            db,
            candidate_id=candidate_id,
            event_type="cv_uploaded",
            title="CV uploaded by candidate" if uploaded_by == "candidate_portal" else "CV uploaded",
            description=(
                f"Candidate uploaded and extracted text from {original_filename}."
                if uploaded_by == "candidate_portal"
                else f"Uploaded and extracted text from {original_filename}."
            ),
            metadata={
                "cv_file_id": str(cv_file.id),
                "filename": original_filename,
                "file_size_bytes": file_size,
                "source": uploaded_by,
                "application_id": str(application_id) if application_id else None,
            },
        )
        db.commit()
        db.refresh(cv_file)
        return cv_file
    except (CVUploadError, TextExtractionError, IntegrityError):
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise


def list_cv_files(db: Session, skip: int = 0, limit: int = 100) -> list[CVFile]:
    statement = select(CVFile).order_by(CVFile.uploaded_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_cv_file(db: Session, cv_file_id: UUID) -> CVFile | None:
    return db.get(CVFile, cv_file_id)


def get_extracted_text(db: Session, cv_file_id: UUID) -> ExtractedCVData | None:
    statement = select(ExtractedCVData).where(ExtractedCVData.cv_file_id == cv_file_id)
    return db.scalar(statement)


def parse_extracted_cv(db: Session, cv_file_id: UUID) -> ExtractedCVData:
    extracted_data = get_extracted_text(db, cv_file_id)
    if extracted_data is None:
        raise CVUploadError("Extracted CV text not found.")

    if extracted_data.parsing_status == "parsed" and extracted_data.ai_output:
        return extracted_data

    if not extracted_data.raw_text or not extracted_data.raw_text.strip():
        raise CVUploadError("Cannot parse CV because extracted text is empty.")

    parsed_cv = parse_cv_text(extracted_data.raw_text)
    extracted_data.ai_output = parsed_cv.data
    extracted_data.confidence_score = parsed_cv.confidence_score
    extracted_data.parsing_status = "parsed"
    extracted_data.status = "approved"

    cv_file = db.get(CVFile, cv_file_id)
    if cv_file is not None:
        cv_file.parsing_status = "parsed"

    create_timeline_event(
        db,
        candidate_id=extracted_data.candidate_id,
        event_type="cv_parsed",
        title="CV parsed",
        description="Extracted CV text was converted into structured candidate data.",
        metadata={"cv_file_id": str(cv_file_id), "confidence_score": float(parsed_cv.confidence_score)},
    )

    db.commit()
    db.refresh(extracted_data)
    update_candidate_profile_from_parsed_cv(db, extracted_data)
    return extracted_data


def update_candidate_profile_from_parsed_cv(db: Session, extracted_data: ExtractedCVData) -> Candidate:
    candidate = db.get(Candidate, extracted_data.candidate_id)
    if candidate is None:
        raise CVUploadError("Candidate not found.")

    parsed_data = extracted_data.ai_output or {}
    updates: dict[str, str] = {}
    for candidate_field, parsed_field in (
        ("first_name", "first_name"),
        ("last_name", "last_name"),
        ("email", "email"),
        ("phone", "phone"),
    ):
        parsed_value = str(parsed_data.get(parsed_field) or "").strip()
        if parsed_value and not getattr(candidate, candidate_field):
            updates[candidate_field] = parsed_value

    for field, value in updates.items():
        setattr(candidate, field, value)

    if updates:
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="candidate_updated",
            title="Candidate updated from parsed CV",
            description="Candidate profile fields were completed from parsed CV data.",
            metadata={"updated_fields": sorted(updates.keys()), "cv_file_id": str(extracted_data.cv_file_id)},
        )
        db.commit()
        db.refresh(candidate)

    return candidate


def parse_and_auto_match_cv(
    db: Session,
    cv_file_id: UUID,
    selected_job_id: UUID | None = None,
    application_id: UUID | None = None,
) -> tuple[ExtractedCVData, list]:
    extracted_data = parse_extracted_cv(db, cv_file_id)
    matching_results = auto_match_candidate(
        db,
        candidate_id=extracted_data.candidate_id,
        selected_job_id=selected_job_id,
        application_id=application_id,
    )
    return extracted_data, matching_results


def delete_cv_file(db: Session, cv_file: CVFile) -> None:
    stored_path = Path(cv_file.storage_path)
    db.delete(cv_file)
    db.commit()
    stored_path.unlink(missing_ok=True)


def _save_upload_file(upload_file: UploadFile, stored_path: Path) -> tuple[int, str]:
    sha256 = hashlib.sha256()
    file_size = 0

    with stored_path.open("wb") as buffer:
        while chunk := upload_file.file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > MAX_CV_FILE_SIZE_BYTES:
                stored_path.unlink(missing_ok=True)
                raise CVUploadError("File is too large. Maximum allowed size is 5MB.")

            sha256.update(chunk)
            buffer.write(chunk)

    return file_size, sha256.hexdigest()
