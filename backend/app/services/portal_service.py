import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_candidate_access_token, hash_password, verify_password
from app.models import AIMatchingResult, Application, CVFile, Candidate, CandidateTimelineEvent, JobOffer
from app.schemas.portal import (
    CandidateApplicationRead,
    CandidateLogin,
    CandidateProfileRead,
    CandidateProfileUpdate,
    CandidateRegister,
    CandidateTokenResponse,
    PortalApplicationResponse,
    PortalApplicationStatusItem,
    PortalApplicationStatusResponse,
    PortalCandidateData,
    PublicPortalApplicationResponse,
)
from app.services import cv_service
from app.services.cv_service import DuplicateCVError, parse_and_auto_match_cv, upload_cv
from app.services.embedding_service import build_job_embedding_text, generate_embedding
from app.services.matching_service import match_candidate_to_job
from app.services.timeline_service import create_timeline_event


class PortalApplicationError(ValueError):
    pass


class CandidateAuthError(ValueError):
    pass


class PortalPublicApplicationError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def register_candidate(db: Session, payload: CandidateRegister) -> CandidateTokenResponse:
    _ensure_candidate_account_columns(db)
    normalized_email = payload.email.lower().strip()
    candidate = db.scalar(select(Candidate).where(Candidate.email == normalized_email))
    if candidate and candidate.password_hash:
        raise CandidateAuthError("Un compte candidat existe déjà avec cet email.")

    if candidate is None:
        candidate = Candidate(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=normalized_email,
            phone=payload.phone,
            location=payload.location,
            current_title=payload.current_title,
            source="candidate_portal",
            status="active",
            consent_given=True,
        )
        db.add(candidate)
        db.flush()
        event_type = "candidate_created"
        title = "Compte candidat créé"
    else:
        candidate.first_name = payload.first_name
        candidate.last_name = payload.last_name
        candidate.phone = payload.phone or candidate.phone
        candidate.location = payload.location or candidate.location
        candidate.current_title = payload.current_title or candidate.current_title
        candidate.source = "candidate_portal"
        candidate.status = "active"
        candidate.consent_given = True
        event_type = "portal_update"
        title = "Compte candidat activé"

    candidate.password_hash = hash_password(payload.password)
    candidate.account_status = "active"
    create_timeline_event(
        db,
        candidate_id=candidate.id,
        event_type=event_type,
        title=title,
        description="Le candidat a créé ou activé un compte portail sécurisé.",
        metadata={"source": "candidate_portal"},
    )
    db.commit()
    db.refresh(candidate)
    return _candidate_token_response(db, candidate)


def login_candidate(db: Session, payload: CandidateLogin) -> CandidateTokenResponse:
    _ensure_candidate_account_columns(db)
    candidate = db.scalar(select(Candidate).where(Candidate.email == payload.email.lower().strip()))
    if candidate is None or not candidate.password_hash or not verify_password(payload.password, candidate.password_hash):
        raise CandidateAuthError("Email ou mot de passe invalide.")
    if candidate.account_status != "active":
        raise CandidateAuthError("Le compte candidat n'est pas actif.")

    candidate.last_login_at = db.execute(select(func.now())).scalar_one()
    db.commit()
    db.refresh(candidate)
    return _candidate_token_response(db, candidate)


def get_candidate_profile(db: Session, candidate: Candidate) -> CandidateProfileRead:
    latest_cv = _get_latest_cv_file(db, candidate.id)
    return CandidateProfileRead(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        linkedin_url=candidate.linkedin_url,
        portfolio_url=candidate.portfolio_url,
        current_title=candidate.current_title,
        source=candidate.source,
        status=candidate.status,
        account_status=candidate.account_status,
        latest_cv_file_id=latest_cv.id if latest_cv else None,
        latest_cv_filename=latest_cv.original_filename if latest_cv else None,
        latest_cv_uploaded_at=latest_cv.uploaded_at if latest_cv else None,
    )


def _ensure_candidate_account_columns(db: Session) -> None:
    db.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS password_hash TEXT"))
    db.execute(
        text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS account_status VARCHAR(30) NOT NULL DEFAULT 'active'")
    )
    db.execute(text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_candidates_account_status ON candidates (account_status)"))
    db.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'ck_candidates_account_status'
                ) THEN
                    ALTER TABLE candidates
                    ADD CONSTRAINT ck_candidates_account_status
                    CHECK (account_status IN ('active', 'invited', 'suspended', 'deleted'));
                END IF;
            END$$;
            """
        )
    )
    db.commit()


def update_candidate_profile(db: Session, candidate: Candidate, payload: CandidateProfileUpdate) -> CandidateProfileRead:
    data = payload.model_dump(exclude_unset=True)
    changed_fields = []
    for field, value in data.items():
        if getattr(candidate, field) != value:
            setattr(candidate, field, value)
            changed_fields.append(field)

    if changed_fields:
        candidate.source = "candidate_portal"
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="portal_update",
            title="Profil candidat mis à jour",
            description="Le candidat a mis à jour ses informations depuis le portail.",
            metadata={"updated_fields": sorted(changed_fields)},
        )
        db.commit()
        db.refresh(candidate)

    return get_candidate_profile(db, candidate)


def replace_candidate_cv(db: Session, candidate: Candidate, upload_file: UploadFile) -> tuple[CandidateProfileRead, list[AIMatchingResult]]:
    cv_file = upload_cv(db, candidate_id=candidate.id, upload_file=upload_file, uploaded_by="candidate_portal")
    _extracted_data, matching_results = parse_and_auto_match_cv(db, cv_file_id=cv_file.id)
    return get_candidate_profile(db, candidate), matching_results


def apply_authenticated_candidate(db: Session, candidate: Candidate, job_id: UUID) -> PortalApplicationResponse:
    job = get_public_job(db, job_id)
    if job is None:
        raise PortalApplicationError("Cette offre n'est pas ouverte aux candidatures publiques.")

    latest_cv = _get_latest_cv_file(db, candidate.id)
    if latest_cv is None:
        raise PortalApplicationError("Importez un CV avant de postuler à cette offre.")

    application = _get_or_create_application(db, candidate.id, job.id)
    application.cv_file_id = latest_cv.id
    db.commit()
    db.refresh(application)

    parse_and_auto_match_cv(
        db,
        cv_file_id=latest_cv.id,
        selected_job_id=job.id,
        application_id=application.id,
    )
    return PortalApplicationResponse(
        candidate_id=candidate.id,
        application_id=application.id,
        cv_file_id=latest_cv.id,
        message="Candidature envoyée depuis votre espace candidat.",
    )


def list_authenticated_applications(db: Session, candidate: Candidate) -> list[CandidateApplicationRead]:
    statement = (
        select(Application, JobOffer)
        .join(JobOffer, Application.job_offer_id == JobOffer.id)
        .where(Application.candidate_id == candidate.id)
        .order_by(Application.applied_at.desc())
    )
    applications = []
    for application, job in db.execute(statement).all():
        applications.append(
            CandidateApplicationRead(
                application_id=application.id,
                job_offer_id=job.id,
                job_title=job.title,
                company_name=job.company_name,
                application_status=application.status,
                current_stage=application.current_stage,
                applied_at=application.applied_at,
                cv_file_id=application.cv_file_id,
            )
        )
    return applications


def list_public_jobs(db: Session) -> list[JobOffer]:
    statement = select(JobOffer).where(JobOffer.status == "open").order_by(JobOffer.created_at.desc())
    return list(db.scalars(statement).all())


def get_public_job(db: Session, job_id: UUID) -> JobOffer | None:
    statement = select(JobOffer).where(JobOffer.id == job_id).where(JobOffer.status == "open")
    return db.scalar(statement)


def get_application_status_by_email(db: Session, email: str) -> PortalApplicationStatusResponse:
    normalized_email = email.lower().strip()
    candidate = db.scalar(select(Candidate).where(Candidate.email == normalized_email))
    if candidate is None:
        return PortalApplicationStatusResponse(email=normalized_email, candidate_id=None, applications=[])

    statement = (
        select(Application, JobOffer)
        .join(JobOffer, Application.job_offer_id == JobOffer.id)
        .where(Application.candidate_id == candidate.id)
        .order_by(Application.applied_at.desc())
    )
    applications = []
    for application, job in db.execute(statement).all():
        applications.append(
            PortalApplicationStatusItem(
                application_id=application.id,
                job_offer_id=job.id,
                job_title=job.title,
                company_name=job.company_name,
                application_status=application.status,
                current_stage=application.current_stage,
                applied_at=application.applied_at,
                cv_file_id=application.cv_file_id,
            )
        )

    return PortalApplicationStatusResponse(email=normalized_email, candidate_id=candidate.id, applications=applications)


def _candidate_token_response(db: Session, candidate: Candidate) -> CandidateTokenResponse:
    return CandidateTokenResponse(
        access_token=create_candidate_access_token(candidate.id, candidate.email or ""),
        candidate=get_candidate_profile(db, candidate),
    )


def submit_application(
    db: Session,
    job_id: UUID,
    candidate_data: PortalCandidateData,
    upload_file: UploadFile,
) -> PortalApplicationResponse:
    job = get_public_job(db, job_id)
    if job is None:
        raise PortalApplicationError("Cette offre n'est pas ouverte aux candidatures publiques.")

    candidate = _get_or_create_candidate(db, candidate_data)
    application = _get_or_create_application(db, candidate.id, job.id)
    cv_file = upload_cv(
        db,
        candidate_id=candidate.id,
        upload_file=upload_file,
        uploaded_by="candidate_portal",
        application_id=application.id,
    )

    application.cv_file_id = cv_file.id
    db.commit()
    db.refresh(application)

    parse_and_auto_match_cv(
        db,
        cv_file_id=cv_file.id,
        selected_job_id=job.id,
        application_id=application.id,
    )

    return PortalApplicationResponse(
        candidate_id=candidate.id,
        application_id=application.id,
        cv_file_id=cv_file.id,
        message="Candidature envoyée.",
    )


def submit_wordpress_application(
    db: Session,
    *,
    opportunite: str,
    nom: str,
    prenom: str,
    email: str,
    telephone: str | None,
    ville: str,
    message: str | None,
    upload_file: UploadFile,
) -> PublicPortalApplicationResponse:
    job = _resolve_public_job_offer(db, opportunite)
    candidate_data = PortalCandidateData(
        first_name=prenom.strip(),
        last_name=nom.strip(),
        email=email.strip().lower(),
        phone=(telephone or "").strip() or None,
        location=ville.strip(),
    )
    checksum, _file_size = _inspect_public_cv_upload(upload_file)
    existing_cv = db.scalar(select(CVFile).where(CVFile.checksum_sha256 == checksum))

    if existing_cv is not None:
        candidate = _get_candidate_for_duplicate_cv(db, candidate_data, existing_cv)
        application, created_application = _get_or_create_wordpress_application(db, candidate.id, job.id)
        if application.cv_file_id is None:
            application.cv_file_id = existing_cv.id
            db.commit()
            db.refresh(application)
        _record_wordpress_message(
            db,
            candidate_id=candidate.id,
            application_id=application.id,
            job_id=job.id,
            message=message,
            dedupe_key=checksum,
            created_application=created_application,
            duplicate_cv=True,
        )
        processing_status = "cv_deja_present"
        if _get_existing_generated_match(db, candidate.id, job.id) is None:
            _ensure_job_embedding(job)
            db.commit()
            match_candidate_to_job(db, candidate.id, job.id, application_id=application.id)
            processing_status = "cv_deja_present_matching_genere"
        return PublicPortalApplicationResponse(
            candidate_id=candidate.id,
            application_id=application.id,
            cv_file_id=existing_cv.id,
            candidate_status="existant",
            cv_received=True,
            processing_status=processing_status,
            message="Votre candidature a bien été reçue.",
        )

    candidate = _get_or_create_candidate(db, candidate_data)
    application, _created_application = _get_or_create_wordpress_application(db, candidate.id, job.id)

    try:
        cv_file = upload_cv(
            db,
            candidate_id=candidate.id,
            upload_file=upload_file,
            uploaded_by="candidate_portal",
            application_id=application.id,
        )
    except DuplicateCVError as exc:
        cv_file = exc.cv_file
        processing_status = "cv_deja_present"
    else:
        processing_status = "analyse_effectuee"

    application.cv_file_id = cv_file.id
    db.commit()
    db.refresh(application)
    _record_wordpress_message(
        db,
        candidate_id=candidate.id,
        application_id=application.id,
        job_id=job.id,
        message=message,
        dedupe_key=checksum,
        created_application=False,
        duplicate_cv=False,
    )

    _ensure_job_embedding(job)
    db.commit()
    parse_and_auto_match_cv(
        db,
        cv_file_id=cv_file.id,
        selected_job_id=job.id,
        application_id=application.id,
    )

    return PublicPortalApplicationResponse(
        candidate_id=candidate.id,
        application_id=application.id,
        cv_file_id=cv_file.id,
        candidate_status="cree_ou_mis_a_jour",
        cv_received=True,
        processing_status=processing_status,
        message="Votre candidature a bien été reçue.",
    )


def _get_or_create_candidate(db: Session, candidate_data: PortalCandidateData) -> Candidate:
    statement = select(Candidate).where(Candidate.email == candidate_data.email.lower())
    candidate = db.scalar(statement)
    if candidate is None:
        candidate = Candidate(
            first_name=candidate_data.first_name,
            last_name=candidate_data.last_name,
            email=candidate_data.email.lower(),
            phone=candidate_data.phone,
            location=candidate_data.location,
            source="candidate_portal",
            status="active",
            consent_given=True,
        )
        db.add(candidate)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="candidate_created",
            title="Candidat créé depuis le portail",
            description=f"{candidate.first_name} {candidate.last_name} applied through the candidate portal.",
            metadata={"source": "candidate_portal", "status": candidate.status},
        )
        db.commit()
        db.refresh(candidate)
        return candidate

    updates = {}
    for field in ("first_name", "last_name", "phone", "location"):
        value = getattr(candidate_data, field)
        if value and getattr(candidate, field) != value:
            updates[field] = value
    if candidate.source != "candidate_portal":
        updates["source"] = "candidate_portal"

    if updates:
        for field, value in updates.items():
            setattr(candidate, field, value)
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="candidate_updated",
            title="Candidat mis à jour depuis le portail",
            description="Le profil candidat a été mis à jour depuis le formulaire public de candidature.",
            metadata={"updated_fields": sorted(updates.keys())},
        )
        db.commit()
        db.refresh(candidate)

    return candidate


def _get_or_create_application(db: Session, candidate_id: UUID, job_id: UUID) -> Application:
    statement = select(Application).where(
        Application.candidate_id == candidate_id,
        Application.job_offer_id == job_id,
    )
    application = db.scalar(statement)
    if application is None:
        application = Application(
            candidate_id=candidate_id,
            job_offer_id=job_id,
            source="candidate_portal",
            status="submitted",
            current_stage="application_submitted",
        )
        db.add(application)
        db.flush()
    else:
        application.source = "candidate_portal"
        application.status = "submitted"
        application.current_stage = "application_submitted"

    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="candidate_application_submitted",
        title="Candidature envoyée depuis le portail",
        description="Le candidat a envoyé une candidature depuis le portail public.",
        metadata={"source": "candidate_portal", "application_id": str(application.id), "job_offer_id": str(job_id)},
    )
    db.commit()
    db.refresh(application)
    return application


def _resolve_public_job_offer(db: Session, opportunite: str) -> JobOffer:
    value = (opportunite or "").strip()
    if not value:
        raise PortalPublicApplicationError("L'opportunité est obligatoire.", status_code=400)

    try:
        job_id = UUID(value)
    except ValueError:
        job_id = None

    if job_id is not None:
        job = get_public_job(db, job_id)
        if job is None:
            raise PortalPublicApplicationError("L'offre demandée est introuvable ou inactive.", status_code=404)
        return job

    normalized_title = value.lower()
    statement = (
        select(JobOffer)
        .where(JobOffer.status == "open")
        .where(func.lower(JobOffer.title) == normalized_title)
        .order_by(JobOffer.created_at.desc())
    )
    job = db.scalar(statement)
    if job is None:
        statement = (
            select(JobOffer)
            .where(JobOffer.status == "open")
            .where(JobOffer.title.ilike(f"%{value}%"))
            .order_by(JobOffer.created_at.desc())
        )
        job = db.scalar(statement)
    if job is None:
        raise PortalPublicApplicationError("Aucune offre active ne correspond à l'opportunité demandée.", status_code=404)
    return job


def _inspect_public_cv_upload(upload_file: UploadFile) -> tuple[str, int]:
    original_filename = upload_file.filename or ""
    extension = Path(original_filename).suffix.lower()
    if extension not in {".pdf", ".doc", ".docx"}:
        raise PortalPublicApplicationError("Format de CV non autorisé. Importez un fichier PDF, DOC ou DOCX.", status_code=415)
    if extension == ".doc":
        raise PortalPublicApplicationError(
            "Le format DOC n'est pas encore exploitable par le parser. Importez un fichier PDF ou DOCX.",
            status_code=415,
        )
    sha256 = hashlib.sha256()
    file_size = 0
    while chunk := upload_file.file.read(1024 * 1024):
        file_size += len(chunk)
        if file_size > cv_service.MAX_CV_FILE_SIZE_BYTES:
            upload_file.file.seek(0)
            raise PortalPublicApplicationError("Le CV est trop volumineux. La taille maximale autorisée est de 5 Mo.", status_code=413)
        sha256.update(chunk)
    upload_file.file.seek(0)
    if file_size == 0:
        raise PortalPublicApplicationError("Le CV est obligatoire et ne peut pas être vide.", status_code=400)
    return sha256.hexdigest(), file_size


def _get_candidate_for_duplicate_cv(db: Session, candidate_data: PortalCandidateData, cv_file: CVFile) -> Candidate:
    candidate = db.scalar(select(Candidate).where(Candidate.email == candidate_data.email.lower()))
    if candidate is not None:
        if candidate.id != cv_file.candidate_id:
            raise PortalPublicApplicationError("Ce CV existe déjà dans la base de données.", status_code=409)
        return _get_or_create_candidate(db, candidate_data)
    if cv_file.candidate.email and cv_file.candidate.email.lower() != candidate_data.email.lower():
        raise PortalPublicApplicationError("Ce CV existe déjà dans la base de données.", status_code=409)
    return cv_file.candidate


def _get_or_create_wordpress_application(db: Session, candidate_id: UUID, job_id: UUID) -> tuple[Application, bool]:
    statement = select(Application).where(
        Application.candidate_id == candidate_id,
        Application.job_offer_id == job_id,
    )
    application = db.scalar(statement)
    if application is not None:
        return application, False

    application = Application(
        candidate_id=candidate_id,
        job_offer_id=job_id,
        source="candidate_portal",
        status="submitted",
        current_stage="application_submitted",
    )
    db.add(application)
    db.flush()
    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="candidate_application_submitted",
        title="Candidature reçue depuis WordPress",
        description="Le candidat a envoyé une candidature depuis le formulaire Talents Associate.",
        metadata={"source": "wordpress", "application_id": str(application.id), "job_offer_id": str(job_id)},
    )
    db.commit()
    db.refresh(application)
    return application, True


def _record_wordpress_message(
    db: Session,
    *,
    candidate_id: UUID,
    application_id: UUID,
    job_id: UUID,
    message: str | None,
    dedupe_key: str,
    created_application: bool,
    duplicate_cv: bool,
) -> None:
    cleaned_message = (message or "").strip()
    if not cleaned_message:
        return
    existing_event = db.scalar(
        select(CandidateTimelineEvent)
        .where(CandidateTimelineEvent.candidate_id == candidate_id)
        .where(CandidateTimelineEvent.event_type == "note")
        .where(CandidateTimelineEvent.event_metadata["application_id"].astext == str(application_id))
        .where(CandidateTimelineEvent.event_metadata["source"].astext == "wordpress")
        .where(CandidateTimelineEvent.event_metadata["message_checksum"].astext == hashlib.sha256(cleaned_message.encode("utf-8")).hexdigest())
    )
    if existing_event is not None:
        return
    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="note",
        title="Message de candidature WordPress",
        description="Message reçu avec la candidature WordPress.",
        metadata={
            "source": "wordpress",
            "application_id": str(application_id),
            "job_offer_id": str(job_id),
            "message": cleaned_message,
            "message_checksum": hashlib.sha256(cleaned_message.encode("utf-8")).hexdigest(),
            "cv_checksum": dedupe_key,
            "created_application": created_application,
            "duplicate_cv": duplicate_cv,
        },
    )
    db.commit()


def _ensure_job_embedding(job: JobOffer) -> None:
    if job.embedding:
        return
    job.embedding = generate_embedding(build_job_embedding_text(job))
    job.embedding_generated_at = datetime.now(timezone.utc)


def _get_existing_generated_match(db: Session, candidate_id: UUID, job_id: UUID) -> AIMatchingResult | None:
    statement = (
        select(AIMatchingResult)
        .where(AIMatchingResult.candidate_id == candidate_id)
        .where(AIMatchingResult.job_offer_id == job_id)
        .where(AIMatchingResult.status == "generated")
    )
    return db.scalar(statement)


def _get_best_application_match(db: Session, application_id: UUID) -> AIMatchingResult | None:
    statement = (
        select(AIMatchingResult)
        .where(AIMatchingResult.application_id == application_id)
        .order_by(AIMatchingResult.score.desc(), AIMatchingResult.created_at.desc())
    )
    return db.scalar(statement)


def _get_application_matches(db: Session, application_id: UUID) -> list[AIMatchingResult]:
    statement = (
        select(AIMatchingResult)
        .where(AIMatchingResult.application_id == application_id)
        .order_by(AIMatchingResult.score.desc(), AIMatchingResult.created_at.desc())
    )
    return list(db.scalars(statement).all())


def _get_latest_cv_file(db: Session, candidate_id: UUID) -> CVFile | None:
    statement = (
        select(CVFile)
        .where(CVFile.candidate_id == candidate_id)
        .order_by(CVFile.uploaded_at.desc(), CVFile.created_at.desc())
    )
    return db.scalar(statement)


def _score_percent(score) -> float:
    numeric_score = float(score)
    return round(numeric_score * 100, 2) if numeric_score <= 1 else round(numeric_score, 2)
