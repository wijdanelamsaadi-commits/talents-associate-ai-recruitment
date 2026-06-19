from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_candidate_access_token, hash_password, verify_password
from app.models import AIMatchingResult, Application, CVFile, Candidate, JobOffer
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
)
from app.services.cv_service import parse_and_auto_match_cv, upload_cv
from app.services.timeline_service import create_timeline_event


class PortalApplicationError(ValueError):
    pass


class CandidateAuthError(ValueError):
    pass


def register_candidate(db: Session, payload: CandidateRegister) -> CandidateTokenResponse:
    _ensure_candidate_account_columns(db)
    normalized_email = payload.email.lower().strip()
    candidate = db.scalar(select(Candidate).where(Candidate.email == normalized_email))
    if candidate and candidate.password_hash:
        raise CandidateAuthError("A candidate account already exists with this email.")

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
        title = "Candidate account created"
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
        title = "Candidate account activated"

    candidate.password_hash = hash_password(payload.password)
    candidate.account_status = "active"
    create_timeline_event(
        db,
        candidate_id=candidate.id,
        event_type=event_type,
        title=title,
        description="Candidate created or activated a secure portal account.",
        metadata={"source": "candidate_portal"},
    )
    db.commit()
    db.refresh(candidate)
    return _candidate_token_response(db, candidate)


def login_candidate(db: Session, payload: CandidateLogin) -> CandidateTokenResponse:
    _ensure_candidate_account_columns(db)
    candidate = db.scalar(select(Candidate).where(Candidate.email == payload.email.lower().strip()))
    if candidate is None or not candidate.password_hash or not verify_password(payload.password, candidate.password_hash):
        raise CandidateAuthError("Invalid email or password.")
    if candidate.account_status != "active":
        raise CandidateAuthError("Candidate account is not active.")

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
            title="Candidate profile updated",
            description="Candidate updated profile information from the portal.",
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
        raise PortalApplicationError("Job offer is not available for public applications.")

    latest_cv = _get_latest_cv_file(db, candidate.id)
    if latest_cv is None:
        raise PortalApplicationError("Upload a CV before applying to this job.")

    application = _get_or_create_application(db, candidate.id, job.id)
    application.cv_file_id = latest_cv.id
    db.commit()
    db.refresh(application)

    extracted_data, matching_results = parse_and_auto_match_cv(
        db,
        cv_file_id=latest_cv.id,
        selected_job_id=job.id,
        application_id=application.id,
    )
    return PortalApplicationResponse(
        candidate_id=candidate.id,
        application_id=application.id,
        cv_file_id=latest_cv.id,
        parsing_status=extracted_data.parsing_status,
        confidence_score=float(extracted_data.confidence_score) if extracted_data.confidence_score is not None else None,
        matching_result_ids=[result.id for result in matching_results],
        message="Application submitted from your candidate portal.",
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
        matches = _get_application_matches(db, application.id)
        best_match = matches[0] if matches else None
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
                best_matching_score=_score_percent(best_match.score) if best_match else None,
                recommendation=best_match.recommendation if best_match else None,
                matching_result_ids=[match.id for match in matches],
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
        best_match = _get_best_application_match(db, application.id)
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
                best_matching_score=_score_percent(best_match.score) if best_match else None,
                recommendation=best_match.recommendation if best_match else None,
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
        raise PortalApplicationError("Job offer is not available for public applications.")

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

    extracted_data, matching_results = parse_and_auto_match_cv(
        db,
        cv_file_id=cv_file.id,
        selected_job_id=job.id,
        application_id=application.id,
    )

    return PortalApplicationResponse(
        candidate_id=candidate.id,
        application_id=application.id,
        cv_file_id=cv_file.id,
        parsing_status=extracted_data.parsing_status,
        confidence_score=float(extracted_data.confidence_score) if extracted_data.confidence_score is not None else None,
        matching_result_ids=[result.id for result in matching_results],
        message="Application submitted. CV extracted, parsed, and matched against the selected job.",
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
            title="Candidate created from portal",
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
            title="Candidate updated from portal",
            description="Candidate profile was updated from a public application form.",
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
        title="Candidate applied through portal",
        description="Candidate submitted an application through the public portal.",
        metadata={"source": "candidate_portal", "application_id": str(application.id), "job_offer_id": str(job_id)},
    )
    db.commit()
    db.refresh(application)
    return application


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
