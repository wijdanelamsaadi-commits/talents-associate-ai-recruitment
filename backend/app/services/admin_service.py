import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Application, Candidate, EmailLog, JobOffer, SystemSetting, User
from app.schemas.admin import AdminSettingsUpdate, AdminUserCreate, AdminUserUpdate


class AdminServiceError(ValueError):
    pass


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc(), User.email.asc())).all())


def create_user(db: Session, payload: AdminUserCreate) -> User:
    token = secrets.token_urlsafe(32)
    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=None,  # l'user ghadi y5tar password dyalo
        role=payload.role,
        status="invited",  # machi actif 7etta y3ber l'email
        activation_token=token,
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    _send_activation_email(db, user, token)
    return user


def _send_activation_email(db: Session, user: User, token: str) -> None:
    import os

    base = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    link = f"{base}/activate/{token}"
    subject = "Activez votre compte Talents Associate"
    body = (
        f"Bonjour {user.full_name},\n\n"
        "Un compte vient d'être créé pour vous. Cliquez sur le lien ci-dessous "
        "pour définir votre mot de passe :\n\n"
        f"{link}\n\n"
        "Ce lien expire dans 48 heures."
    )

    # mode console : l'lien kيبان f l'terminal dyal backend (zéro config)
    print("=" * 70)
    print("EMAIL D'ACTIVATION")
    print("À      :", user.email)
    print("Lien   :", link)
    print("=" * 70)

    # n sجّlo f l'جدول EmailLog
    db.add(EmailLog(to_email=user.email, subject=subject, body=body, status="sent"))
    db.commit()


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def update_user(db: Session, user: User, payload: AdminUserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        user.email = str(data.pop("email")).lower()
    if "password" in data and data["password"] is not None:
        user.password_hash = hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def disable_user(db: Session, user: User) -> User:
    user.status = "suspended"
    db.commit()
    db.refresh(user)
    return user


def enable_user(db: Session, user: User) -> User:
    user.status = "active"
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user: User) -> User:
    user.status = "deleted"
    db.commit()
    db.refresh(user)
    return user


def get_settings(db: Session) -> dict:
    rows = db.scalars(select(SystemSetting).order_by(SystemSetting.key.asc())).all()
    return {row.key: row.value for row in rows}


def update_settings(db: Session, payload: AdminSettingsUpdate) -> dict:
    for key, value in payload.settings.items():
        clean_key = str(key).strip()
        if not clean_key:
            raise AdminServiceError("Setting key cannot be empty.")
        setting = db.scalar(select(SystemSetting).where(SystemSetting.key == clean_key))
        if setting is None:
            setting = SystemSetting(key=clean_key, value=value)
            db.add(setting)
        else:
            setting.value = value
    db.commit()
    return get_settings(db)


def dashboard_stats(db: Session) -> dict[str, int]:
    return {
        "candidates_count": db.scalar(select(func.count()).select_from(Candidate)) or 0,
        "recruiters_count": db.scalar(
            select(func.count()).select_from(User).where(User.role == "recruiter", User.status != "deleted")
        )
        or 0,
        "jobs_count": db.scalar(select(func.count()).select_from(JobOffer)) or 0,
        "applications_count": db.scalar(select(func.count()).select_from(Application)) or 0,
        "talent_pool_count": db.scalar(select(func.count()).select_from(Candidate).where(Candidate.is_talent_pool.is_(True))) or 0,
        "email_sent_count": db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == "sent")) or 0,
        "email_skipped_count": db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == "skipped")) or 0,
        "email_failed_count": db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == "failed")) or 0,
    }
