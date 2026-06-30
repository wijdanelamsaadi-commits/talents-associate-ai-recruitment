import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CVFile, Candidate, ExtractedCVData
from app.services.embedding_service import build_candidate_embedding_text, generate_embedding
from app.services.llm_cv_parser_service import parse_cv_text_configurable
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
logger = logging.getLogger(__name__)


class CVUploadError(ValueError):
    pass


class DuplicateCVError(CVUploadError):
    def __init__(self, cv_file: CVFile):
        super().__init__("Ce CV existe déjà dans la base de données.")
        self.cv_file = cv_file


def upload_cv(
    db: Session,
    candidate_id: UUID | None,
    upload_file: UploadFile,
    uploaded_by: str = "recruiter",
    application_id: UUID | None = None,
) -> CVFile:
    original_filename = upload_file.filename or ""
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise CVUploadError("Format non pris en charge. Seuls les fichiers PDF, DOC et DOCX sont autorisés.")

    if upload_file.content_type and upload_file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise CVUploadError("Type de fichier non pris en charge. Importez un fichier PDF, DOC ou DOCX.")

    if extension == ".doc":
        raise CVUploadError("L'extraction de texte DOC n'est pas encore prise en charge. Importez un fichier PDF ou DOCX.")

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}{extension}"
    stored_path = UPLOAD_DIRECTORY / stored_filename

    file_size, checksum = _save_upload_file(upload_file, stored_path)
    if file_size == 0:
        stored_path.unlink(missing_ok=True)
        raise CVUploadError("Le fichier importé est vide.")

    try:
        existing_same_file = db.scalar(select(CVFile).where(CVFile.checksum_sha256 == checksum))
        if existing_same_file is not None:
            stored_path.unlink(missing_ok=True)
            raise DuplicateCVError(existing_same_file)

        raw_text = extract_text_from_file(stored_path, extension)
        if not raw_text:
            raise CVUploadError("Aucun texte n'a pu être extrait de ce CV.")

        parsed_cv = parse_cv_text_configurable(raw_text)
        parsed_data = parsed_cv.data or {}

        if candidate_id is None:
            email = parsed_data.get("email")

            candidate = None
            if email:
                candidate = db.scalar(select(Candidate).where(Candidate.email == email))

            if candidate is None:
                first_name = parsed_data.get("first_name")
                last_name = parsed_data.get("last_name")
                if not first_name or not last_name:
                    base_name = Path(original_filename).stem
                    name_parts = base_name.replace("_", " ").replace("-", " ").split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = " ".join(name_parts[1:])
                    else:
                        first_name = base_name or "Prénom"
                        last_name = "Candidat"
                
                from app.schemas.candidate import CandidateCreate
                from app.services import candidate_service
                candidate_in = CandidateCreate(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    source="cv_upload",
                )
                candidate = candidate_service.create_candidate(db, candidate_in)
            else:
                if uploaded_by == "recruiter":
                    candidate.source = "cv_upload"
            
            candidate_id = candidate.id
            is_new_parsed = True
        else:
            candidate = db.get(Candidate, candidate_id)
            if candidate is None:
                raise CVUploadError("Candidat introuvable.")
            if uploaded_by == "recruiter":
                candidate.source = "cv_upload"
            is_new_parsed = False

        cv_file = _get_latest_cv_file_for_candidate(db, candidate_id)
        replaces_existing_cv = cv_file is not None
        if cv_file is None:
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
        else:
            cv_file.original_filename = original_filename
            cv_file.storage_path = str(stored_path)
            cv_file.mime_type = upload_file.content_type
            cv_file.file_size_bytes = file_size
            cv_file.checksum_sha256 = checksum
            cv_file.parsing_status = "parsed"
            cv_file.uploaded_at = datetime.now(timezone.utc)
            db.flush()

        extracted_data = get_extracted_text(db, cv_file.id)
        if extracted_data is None:
            extracted_data = ExtractedCVData(
                cv_file_id=cv_file.id,
                candidate_id=candidate_id,
                raw_text=raw_text,
                parsed_json=None,
                ai_output=parsed_data,
                confidence_score=parsed_cv.confidence_score,
                parser_model=_parser_model(parsed_data),
                parsing_status="parsed",
                status="approved",
            )
            db.add(extracted_data)
        else:
            extracted_data.candidate_id = candidate_id
            extracted_data.raw_text = raw_text
            extracted_data.parsed_json = None
            extracted_data.ai_output = parsed_data
            extracted_data.confidence_score = parsed_cv.confidence_score
            extracted_data.parser_model = _parser_model(parsed_data)
            extracted_data.parsing_status = "parsed"
            extracted_data.status = "approved"

        _generate_candidate_embedding(db, extracted_data, commit=False)
        update_candidate_profile_from_parsed_cv(db, extracted_data)

        create_timeline_event(
            db,
            candidate_id=candidate_id,
            event_type="manual_cv_uploaded" if uploaded_by == "recruiter" else "cv_uploaded",
            title="CV remplacé" if replaces_existing_cv else ("CV importé par le candidat" if uploaded_by == "candidate_portal" else "CV importé"),
            description=(
                f"Le CV existant a été remplacé par {original_filename}."
                if replaces_existing_cv
                else (
                f"Le candidat a importé {original_filename} et le texte a été extrait."
                if uploaded_by == "candidate_portal"
                else f"{original_filename} a été importé et le texte a été extrait."
                )
            ),
            metadata={
                "cv_file_id": str(cv_file.id),
                "filename": original_filename,
                "file_size_bytes": file_size,
                "source": uploaded_by,
                "candidate_source": "cv_upload" if uploaded_by == "recruiter" else uploaded_by,
                "application_id": str(application_id) if application_id else None,
                "replaced_existing_cv": replaces_existing_cv,
            },
        )

        create_timeline_event(
            db,
            candidate_id=candidate_id,
            event_type="cv_parsed",
            title="CV analysé",
            description="Le texte extrait du CV a été converti en données candidat structurées.",
            metadata={
                "cv_file_id": str(cv_file.id),
                "confidence_score": float(parsed_cv.confidence_score) if parsed_cv.confidence_score is not None else None,
                "parser_used": parsed_data.get("parser_used", "llm"),
                "parser_model": extracted_data.parser_model,
                "replaced_existing_cv": replaces_existing_cv,
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


def _get_latest_cv_file_for_candidate(db: Session, candidate_id: UUID) -> CVFile | None:
    statement = (
        select(CVFile)
        .where(CVFile.candidate_id == candidate_id)
        .order_by(CVFile.uploaded_at.desc(), CVFile.created_at.desc())
        .limit(1)
    )
    return db.scalar(statement)


def parse_extracted_cv(db: Session, cv_file_id: UUID) -> ExtractedCVData:
    extracted_data = get_extracted_text(db, cv_file_id)
    if extracted_data is None:
        raise CVUploadError("Texte extrait du CV introuvable.")

    if extracted_data.parsing_status == "parsed" and extracted_data.ai_output and _has_minimum_parsing_signal(
        extracted_data.ai_output
    ):
        return extracted_data

    if not extracted_data.raw_text or not extracted_data.raw_text.strip():
        raise CVUploadError("Impossible d'analyser le CV car le texte extrait est vide.")

    parsed_cv = parse_cv_text_configurable(extracted_data.raw_text)
    extracted_data.ai_output = parsed_cv.data
    extracted_data.summary = _optional_string(parsed_cv.data.get("summary"))
    extracted_data.total_years_experience = _optional_non_negative_number(
        parsed_cv.data.get("total_experience_years") or parsed_cv.data.get("experience_totale")
    )
    extracted_data.highest_degree = _optional_string(parsed_cv.data.get("highest_degree"))
    extracted_data.parser_model = _parser_model(parsed_cv.data)
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
        title="CV analysé",
        description="Le texte extrait du CV a été converti en données candidat structurées.",
        metadata={
            "cv_file_id": str(cv_file_id),
            "confidence_score": float(parsed_cv.confidence_score),
            "parser_used": parsed_cv.data.get("parser_used"),
            "parser_model": extracted_data.parser_model,
        },
    )

    db.commit()
    db.refresh(extracted_data)
    _generate_candidate_embedding(db, extracted_data, commit=True)
    update_candidate_profile_from_parsed_cv(db, extracted_data)
    return extracted_data


def update_candidate_profile_from_parsed_cv(db: Session, extracted_data: ExtractedCVData) -> Candidate:
    candidate = db.get(Candidate, extracted_data.candidate_id)
    if candidate is None:
        raise CVUploadError("Candidat introuvable.")

    parsed_data = extracted_data.ai_output or {}
    updates: dict[str, str] = {}
    for candidate_field, parsed_field in (
        ("first_name", "first_name"),
        ("last_name", "last_name"),
        ("email", "email"),
        ("phone", "phone"),
        ("location", "location"),
        ("linkedin_url", "linkedin_url"),
        ("current_title", "current_title"),
        ("current_company", "current_company"),
        ("sector", "sector"),
        ("gender", "gender"),
    ):
        parsed_value = str(parsed_data.get(parsed_field) or "").strip()
        if parsed_field == "sector" and not parsed_value:
            parsed_value = str(parsed_data.get("secteur") or "").strip()
        if parsed_field == "location" and not parsed_value:
            parsed_value = str(parsed_data.get("ville") or "").strip()
        current_value = str(getattr(candidate, candidate_field) or "").strip()
        is_placeholder_name = candidate_field in {"first_name", "last_name"} and candidate.last_name in {"Candidate", "Candidat"}
        if candidate_field == "email" and parsed_value:
            existing_candidate = db.scalar(select(Candidate).where(Candidate.email == parsed_value))
            if existing_candidate is not None and existing_candidate.id != candidate.id:
                continue
        if parsed_value and (not current_value or is_placeholder_name):
            updates[candidate_field] = parsed_value

    for field, value in updates.items():
        setattr(candidate, field, value)

    if updates:
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="candidate_updated",
            title="Candidat mis à jour depuis le CV analysé",
            description="Les champs du profil candidat ont été complétés à partir des données du CV analysé.",
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
                raise CVUploadError("Le fichier est trop volumineux. La taille maximale autorisée est de 5 Mo.")

            sha256.update(chunk)
            buffer.write(chunk)

    return file_size, sha256.hexdigest()


def _parser_model(parsed_data: dict) -> str:
    if parsed_data.get("parser_used") == "llm":
        model = settings.LLM_MODEL or "gpt-4o-mini"
        return f"openai:{model}"
    return "heuristic-v1"


def _has_minimum_parsing_signal(parsed_data: dict) -> bool:
    list_fields = (
        "skills",
        "competences",
        "technical_skills",
        "competences_techniques",
        "education",
        "diplomes",
        "experience",
        "detailed_experience",
        "experiences_detaillees",
    )
    scalar_fields = ("email", "phone", "telephone", "first_name", "last_name", "prenom", "nom")
    has_list_signal = any(parsed_data.get(field) for field in list_fields)
    has_scalar_signal = any(parsed_data.get(field) for field in scalar_fields)
    confidence = parsed_data.get("parser_confidence")
    try:
        confidence_value = float(confidence) if confidence is not None else 0.0
    except (TypeError, ValueError):
        confidence_value = 0.0
    return has_list_signal or has_scalar_signal or confidence_value > 0


def _generate_candidate_embedding(db: Session, extracted_data: ExtractedCVData, *, commit: bool = False) -> None:
    try:
        embedding_text = build_candidate_embedding_text(extracted_data)
        extracted_data.embedding = generate_embedding(embedding_text)
        extracted_data.embedding_generated_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit()
            db.refresh(extracted_data)
    except Exception as exc:
        logger.warning("Candidate embedding generation failed; continuing without embedding: %s", exc)


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
