from datetime import datetime, timezone
from email.message import EmailMessage
import smtplib
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import EmailLog


def _sender() -> str | None:
    if not settings.SMTP_FROM_EMAIL:
        return None
    if settings.SMTP_FROM_NAME:
        return f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    return settings.SMTP_FROM_EMAIL


def send_candidate_email(
    db: Session,
    *,
    to_email: str | None,
    subject: str,
    body: str,
    candidate_id: UUID | None = None,
    application_id: UUID | None = None,
) -> EmailLog:
    log = EmailLog(
        candidate_id=candidate_id,
        application_id=application_id,
        to_email=to_email or "",
        subject=subject,
        body=body,
        status="pending",
    )
    db.add(log)
    db.flush()

    if not to_email:
        log.status = "skipped"
        log.error_message = "Candidate email is missing."
        return log

    if not settings.EMAIL_ENABLED or not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        log.status = "skipped"
        log.error_message = "Email delivery is disabled or SMTP is not configured."
        return log

    try:
        message = EmailMessage()
        message["From"] = _sender()
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)

        log.status = "sent"
        log.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)

    return log


def accepted_email(candidate_name: str, job_title: str) -> tuple[str, str]:
    subject = f"Votre candidature a été retenue - {job_title}"
    body = (
        f"Bonjour {candidate_name},\n\n"
        f"Nous avons le plaisir de vous informer que votre candidature pour le poste « {job_title} » a été retenue.\n\n"
        "L'équipe Talents Associate reviendra vers vous avec les prochaines étapes.\n\n"
        "Cordialement,\nTalents Associate"
    )
    return subject, body


def rejected_email(candidate_name: str, job_title: str) -> tuple[str, str]:
    subject = f"Retour sur votre candidature - {job_title}"
    body = (
        f"Bonjour {candidate_name},\n\n"
        f"Nous vous remercions pour votre candidature au poste « {job_title} ».\n\n"
        "Après étude de votre dossier, nous ne poursuivrons pas le processus pour cette opportunité. "
        "Votre profil reste conservé dans notre vivier candidats afin de pouvoir vous recontacter si une opportunité adaptée se présente.\n\n"
        "Cordialement,\nTalents Associate"
    )
    return subject, body


def interview_invitation_email(candidate_name: str, job_title: str, scheduled_at: str, location: str | None) -> tuple[str, str]:
    subject = f"Convocation entretien - {job_title}"
    place = location or "Les modalités pratiques vous seront communiquées par l'équipe RH."
    body = (
        f"Bonjour {candidate_name},\n\n"
        f"Vous êtes convié(e) à un entretien pour le poste « {job_title} ».\n\n"
        f"Date et heure : {scheduled_at}\n"
        f"Lieu / lien : {place}\n\n"
        "Merci de confirmer votre disponibilité auprès de l'équipe Talents Associate.\n\n"
        "Cordialement,\nTalents Associate"
    )
    return subject, body
