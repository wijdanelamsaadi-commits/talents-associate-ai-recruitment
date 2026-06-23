from uuid import UUID

from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from app.models import Application, Candidate, CandidateNotification, Interview, JobOffer
from app.services import email_service


def create_candidate_notification(
    db: Session,
    *,
    candidate_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    application_id: UUID | None = None,
    interview_id: UUID | None = None,
) -> CandidateNotification:
    notification = CandidateNotification(
        candidate_id=candidate_id,
        application_id=application_id,
        interview_id=interview_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notification)
    db.flush()
    return notification


def list_candidate_notifications(db: Session, candidate_id: UUID) -> list[CandidateNotification]:
    return list(
        db.scalars(
            select(CandidateNotification)
            .where(CandidateNotification.candidate_id == candidate_id)
            .order_by(CandidateNotification.created_at.desc())
        ).all()
    )


def mark_candidate_notification_read(
    db: Session,
    *,
    notification_id: UUID,
    candidate_id: UUID,
) -> CandidateNotification | None:
    notification = db.get(CandidateNotification, notification_id)
    if notification is None or notification.candidate_id != candidate_id:
        return None

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = db.execute(select(sa_func.now())).scalar_one()
        db.commit()
        db.refresh(notification)
    return notification


def notify_application_accepted(db: Session, *, candidate: Candidate, application: Application, job: JobOffer | None) -> None:
    candidate_name = f"{candidate.first_name} {candidate.last_name}"
    job_title = job.title if job else "l'opportunité concernée"
    title = "Candidature acceptée"
    message = f"Votre candidature pour le poste « {job_title} » a été retenue."
    create_candidate_notification(
        db,
        candidate_id=candidate.id,
        application_id=application.id,
        notification_type="accepted",
        title=title,
        message=message,
    )
    subject, body = email_service.accepted_email(candidate_name, job_title)
    email_service.send_candidate_email(
        db,
        to_email=candidate.email,
        subject=subject,
        body=body,
        candidate_id=candidate.id,
        application_id=application.id,
    )


def notify_application_rejected(db: Session, *, candidate: Candidate, application: Application, job: JobOffer | None) -> None:
    candidate_name = f"{candidate.first_name} {candidate.last_name}"
    job_title = job.title if job else "l'opportunité concernée"
    title = "Candidature non retenue"
    message = (
        f"Votre candidature pour le poste « {job_title} » n'a pas été retenue. "
        "Votre profil reste conservé dans notre vivier candidats."
    )
    create_candidate_notification(
        db,
        candidate_id=candidate.id,
        application_id=application.id,
        notification_type="rejected",
        title=title,
        message=message,
    )
    subject, body = email_service.rejected_email(candidate_name, job_title)
    email_service.send_candidate_email(
        db,
        to_email=candidate.email,
        subject=subject,
        body=body,
        candidate_id=candidate.id,
        application_id=application.id,
    )


def notify_interview_invitation(db: Session, *, candidate: Candidate, application: Application, interview: Interview, job: JobOffer | None) -> None:
    candidate_name = f"{candidate.first_name} {candidate.last_name}"
    job_title = job.title if job else "l'opportunité concernée"
    scheduled_at = interview.scheduled_start_at.strftime("%d/%m/%Y à %H:%M")
    location = interview.meeting_url or interview.location
    title = "Convocation entretien"
    message = f"Vous êtes convié(e) à un entretien pour le poste « {job_title} » le {scheduled_at}."
    if location:
        message = f"{message} Modalités : {location}."
    create_candidate_notification(
        db,
        candidate_id=candidate.id,
        application_id=application.id,
        interview_id=interview.id,
        notification_type="interview_invitation",
        title=title,
        message=message,
    )
    subject, body = email_service.interview_invitation_email(candidate_name, job_title, scheduled_at, location)
    email_service.send_candidate_email(
        db,
        to_email=candidate.email,
        subject=subject,
        body=body,
        candidate_id=candidate.id,
        application_id=application.id,
    )
