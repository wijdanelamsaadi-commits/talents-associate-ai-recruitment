from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Candidate, Interview, JobOffer
from app.schemas import InterviewCreate, InterviewUpdate
from app.services.pipeline_service import apply_pipeline_stage
from app.services.timeline_service import create_timeline_event
from app.services.notification_service import notify_interview_invitation


class InterviewError(ValueError):
    pass


def create_interview(db: Session, interview_in: InterviewCreate) -> Interview:
    application = _get_or_create_application(db, interview_in.candidate_id, interview_in.job_offer_id)
    interview = Interview(
        application_id=application.id,
        candidate_id=interview_in.candidate_id,
        scheduled_by_user_id=interview_in.scheduled_by_user_id,
        interviewer_user_id=interview_in.interviewer_user_id,
        interview_type=interview_in.interview_type,
        status=interview_in.status,
        scheduled_start_at=interview_in.scheduled_start_at,
        scheduled_end_at=interview_in.scheduled_end_at,
        meeting_url=interview_in.meeting_url,
        location=interview_in.location,
        notes=interview_in.notes,
    )

    db.add(interview)
    db.flush()
    apply_pipeline_stage(
        db,
        interview_in.candidate_id,
        interview_in.status,
        job_offer_id=interview_in.job_offer_id,
    )
    create_timeline_event(
        db,
        candidate_id=interview.candidate_id,
        event_type="interview_scheduled",
        title="Entretien planifié",
        description=f"Entretien {interview.interview_type.replace('_', ' ')} planifié.",
        metadata={
            "interview_id": str(interview.id),
            "job_offer_id": str(interview_in.job_offer_id),
            "scheduled_start_at": interview.scheduled_start_at.isoformat(),
            "pipeline_stage": interview_in.status,
        },
    )
    candidate = db.get(Candidate, interview.candidate_id)
    job = db.get(JobOffer, application.job_offer_id)
    if candidate is not None:
        notify_interview_invitation(db, candidate=candidate, application=application, interview=interview, job=job)
    db.commit()
    db.refresh(interview)
    return interview


def list_interviews(db: Session, skip: int = 0, limit: int = 100) -> list[Interview]:
    statement = select(Interview).order_by(Interview.scheduled_start_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_interview(db: Session, interview_id: UUID) -> Interview | None:
    return db.get(Interview, interview_id)


def update_interview(db: Session, interview: Interview, interview_in: InterviewUpdate) -> Interview:
    data = interview_in.model_dump(exclude_unset=True)
    next_start = data.get("scheduled_start_at", interview.scheduled_start_at)
    next_end = data.get("scheduled_end_at", interview.scheduled_end_at)
    if next_end is not None and next_end <= next_start:
        raise InterviewError("Interview end time must be after start time.")

    candidate_id = data.pop("candidate_id", None)
    job_offer_id = data.pop("job_offer_id", None)
    previous_status = interview.status

    if candidate_id is not None or job_offer_id is not None:
        current_application = db.get(Application, interview.application_id)
        next_candidate_id = candidate_id or interview.candidate_id
        next_job_offer_id = job_offer_id or current_application.job_offer_id
        application = _get_or_create_application(db, next_candidate_id, next_job_offer_id)
        interview.application_id = application.id
        interview.candidate_id = next_candidate_id

    for field, value in data.items():
        setattr(interview, field, value)

    resolved_job_offer_id = job_offer_id or get_interview_job_offer_id(db, interview)
    if interview.status != previous_status or "status" in data:
        apply_pipeline_stage(db, interview.candidate_id, interview.status, job_offer_id=resolved_job_offer_id)

    db.commit()
    db.refresh(interview)
    return interview


def update_interview_status(db: Session, interview: Interview, status: str) -> Interview:
    interview.status = status
    job_offer_id = get_interview_job_offer_id(db, interview)
    apply_pipeline_stage(db, interview.candidate_id, status, job_offer_id=job_offer_id)
    db.commit()
    db.refresh(interview)
    return interview


def delete_interview(db: Session, interview: Interview) -> None:
    db.delete(interview)
    db.commit()


def get_interview_job_offer_id(db: Session, interview: Interview) -> UUID:
    application = db.get(Application, interview.application_id)
    if application is None:
        raise InterviewError("Interview application not found.")
    return application.job_offer_id


def _get_or_create_application(db: Session, candidate_id: UUID, job_offer_id: UUID) -> Application:
    if db.get(Candidate, candidate_id) is None:
        raise InterviewError("Candidate not found.")
    if db.get(JobOffer, job_offer_id) is None:
        raise InterviewError("Job offer not found.")

    statement = select(Application).where(
        Application.candidate_id == candidate_id,
        Application.job_offer_id == job_offer_id,
    )
    application = db.scalar(statement)
    if application is not None:
        return application

    application = Application(
        candidate_id=candidate_id,
        job_offer_id=job_offer_id,
        source="recruiter",
        status="interviewing",
        current_stage="entretien_cabinet",
    )
    db.add(application)
    db.flush()
    return application
