from datetime import datetime, timezone
from email.message import EmailMessage
import smtplib
import ssl
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


def _send_smtp_message(message: EmailMessage) -> None:
    context = ssl.create_default_context()
    timeout = settings.SMTP_TIMEOUT_SECONDS
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout, context=context) as smtp:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as smtp:
        smtp.starttls(context=context)
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


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

        _send_smtp_message(message)

        log.status = "sent"
        log.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)

    return log


def send_user_activation_email(
    db: Session,
    *,
    to_email: str,
    full_name: str,
    activation_link: str,
    expires_in_hours: int = 48,
) -> EmailLog:
    subject = "Activez votre compte Talents Associate"
    html_body = user_activation_email_template(
        full_name=full_name,
        activation_link=activation_link,
        expires_in_hours=expires_in_hours,
    )
    text_body = (
        f"Bonjour {full_name},\n\n"
        "Un compte recruteur Talents Associate vient d'etre cree ou reactive pour vous.\n"
        "Definissez votre mot de passe avec ce lien securise :\n"
        f"{activation_link}\n\n"
        f"Ce lien expire dans {expires_in_hours} heures.\n\n"
        "Talents Associate"
    )
    log = EmailLog(to_email=to_email, subject=subject, body=html_body, status="pending")
    db.add(log)
    db.flush()

    if not settings.EMAIL_ENABLED or not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        log.status = "skipped"
        log.error_message = "Email delivery is disabled or SMTP is not configured."
        print("=" * 70)
        print("EMAIL D'ACTIVATION TALENTS ASSOCIATE")
        print("A      :", to_email)
        print("Lien   :", activation_link)
        print("=" * 70)
        return log

    try:
        message = EmailMessage()
        message["From"] = _sender()
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        _send_smtp_message(message)

        log.status = "sent"
        log.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)

    return log


def send_password_reset_email(
    db: Session,
    *,
    to_email: str,
    full_name: str,
    reset_link: str,
    expires_in_hours: int = 24,
) -> EmailLog:
    subject = "Réinitialisation de votre mot de passe Talents Associate"
    html_body = user_password_reset_email_template(
        full_name=full_name,
        reset_link=reset_link,
        expires_in_hours=expires_in_hours,
    )
    text_body = (
        f"Bonjour {full_name},\n\n"
        "Vous avez demandé la réinitialisation de votre mot de passe Talents Associate.\n"
        "Définissez un nouveau mot de passe avec ce lien sécurisé :\n"
        f"{reset_link}\n\n"
        f"Ce lien expire dans {expires_in_hours} heures.\n\n"
        "Talents Associate"
    )
    log = EmailLog(to_email=to_email, subject=subject, body=html_body, status="pending")
    db.add(log)
    db.flush()

    if not settings.EMAIL_ENABLED or not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        log.status = "skipped"
        log.error_message = "Email delivery is disabled or SMTP is not configured."
        print("=" * 70)
        print("EMAIL RESET PASSWORD TALENTS ASSOCIATE")
        print("A      :", to_email)
        print("Lien   :", reset_link)
        print("=" * 70)
        return log

    try:
        message = EmailMessage()
        message["From"] = _sender()
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        _send_smtp_message(message)

        log.status = "sent"
        log.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)

    return log


def user_activation_email_template(*, full_name: str, activation_link: str, expires_in_hours: int = 48) -> str:
    logo_url = f"{settings.FRONTEND_URL.rstrip('/')}/talents-associate-logo-official.png"
    return f"""
    <html>
      <body style="margin:0;background:#f7f3f0;color:#27313f;font-family:Inter,Segoe UI,Arial,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f3f0;padding:32px 16px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border:1px solid #eadfd8;border-radius:18px;overflow:hidden;">
                <tr>
                  <td style="padding:30px 34px 18px;text-align:center;">
                    <img src="{logo_url}" alt="Talents Associate" width="132" style="display:block;margin:0 auto 14px;max-width:132px;height:auto;" />
                    <div style="font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#EE6C2F;">Talents Associate</div>
                    <div style="margin:12px auto 0;width:92px;height:3px;background:#EE6C2F;border-radius:999px;"></div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 34px 34px;">
                    <h1 style="margin:0;color:#1f2933;font-size:26px;line-height:1.25;font-weight:800;">Definissez votre mot de passe</h1>
                    <p style="margin:18px 0 0;color:#4b5563;font-size:15px;line-height:1.7;">Bonjour {full_name},</p>
                    <p style="margin:10px 0 0;color:#4b5563;font-size:15px;line-height:1.7;">
                      Un compte recruteur Talents Associate vient d'etre cree ou reactive pour vous. Pour securiser votre acces,
                      vous devez choisir vous-meme votre mot de passe via le lien ci-dessous.
                    </p>
                    <div style="text-align:center;margin:30px 0;">
                      <a href="{activation_link}" style="display:inline-block;background:#EE6C2F;color:#ffffff;text-decoration:none;font-weight:800;font-size:15px;padding:14px 26px;border-radius:10px;">
                        Definir mon mot de passe
                      </a>
                    </div>
                    <p style="margin:0;color:#6b7280;font-size:13px;line-height:1.6;">
                      Ce lien est unique et expire dans {expires_in_hours} heures. Si le bouton ne fonctionne pas, copiez-collez ce lien dans votre navigateur :
                    </p>
                    <p style="word-break:break-all;margin:10px 0 0;font-size:13px;line-height:1.6;">
                      <a href="{activation_link}" style="color:#EE6C2F;">{activation_link}</a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def user_password_reset_email_template(*, full_name: str, reset_link: str, expires_in_hours: int = 24) -> str:
    logo_url = f"{settings.FRONTEND_URL.rstrip('/')}/talents-associate-logo-official.png"
    return f"""
    <html>
      <body style="margin:0;background:#f7f3f0;color:#27313f;font-family:Inter,Segoe UI,Arial,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f3f0;padding:32px 16px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border:1px solid #eadfd8;border-radius:18px;overflow:hidden;">
                <tr>
                  <td style="padding:30px 34px 18px;text-align:center;">
                    <img src="{logo_url}" alt="Talents Associate" width="132" style="display:block;margin:0 auto 14px;max-width:132px;height:auto;" />
                    <div style="font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#EE6C2F;">Talents Associate</div>
                    <div style="margin:12px auto 0;width:92px;height:3px;background:#EE6C2F;border-radius:999px;"></div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 34px 34px;">
                    <h1 style="margin:0;color:#1f2933;font-size:26px;line-height:1.25;font-weight:800;">Réinitialisez votre mot de passe</h1>
                    <p style="margin:18px 0 0;color:#4b5563;font-size:15px;line-height:1.7;">Bonjour {full_name},</p>
                    <p style="margin:10px 0 0;color:#4b5563;font-size:15px;line-height:1.7;">
                      Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le bouton ci-dessous
                      pour choisir un nouveau mot de passe.
                    </p>
                    <div style="text-align:center;margin:30px 0;">
                      <a href="{reset_link}" style="display:inline-block;background:#EE6C2F;color:#ffffff;text-decoration:none;font-weight:800;font-size:15px;padding:14px 26px;border-radius:10px;">
                        Réinitialiser mon mot de passe
                      </a>
                    </div>
                    <p style="margin:0;color:#6b7280;font-size:13px;line-height:1.6;">
                      Ce lien est unique et expire dans {expires_in_hours} heures. Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.
                    </p>
                    <p style="word-break:break-all;margin:10px 0 0;font-size:13px;line-height:1.6;">
                      <a href="{reset_link}" style="color:#EE6C2F;">{reset_link}</a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


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
