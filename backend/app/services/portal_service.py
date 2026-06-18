from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AIMatchingResult, Application, Candidate, JobOffer
from app.schemas.portal import PortalApplicationResponse, PortalApplicationStatusItem, PortalApplicationStatusResponse, PortalCandidateData
from app.services.cv_service import parse_and_auto_match_cv, upload_cv
from app.services.timeline_service import create_timeline_event


class PortalApplicationError(ValueError):
    pass


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


def _score_percent(score) -> float:
    numeric_score = float(score)
    return round(numeric_score * 100, 2) if numeric_score <= 1 else round(numeric_score, 2)
