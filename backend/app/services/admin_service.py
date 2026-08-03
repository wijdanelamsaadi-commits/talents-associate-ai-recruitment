from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Application, Candidate, EmailLog, JobOffer, SystemSetting, User
from app.schemas.admin import AdminSettingsUpdate, AdminUserCreate, AdminUserUpdate
from app.services.email_service import send_user_activation_email


class AdminServiceError(ValueError):
    pass


INVITATION_EXPIRES_IN_HOURS = 48


def list_users(db: Session) -> list[User]:
    repaired = _repair_passwordless_active_users(db)
    if repaired:
        db.commit()
    statement = select(User).where(User.status != "deleted").order_by(User.created_at.desc(), User.email.asc())
    return list(db.scalars(statement).all())


def _new_activation_token() -> tuple[str, datetime]:
    return secrets.token_urlsafe(32), datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRES_IN_HOURS)


def _prepare_activation(user: User) -> str:
    token, expires_at = _new_activation_token()
    user.password_hash = None
    user.status = "invited"
    user.activation_token = token
    user.token_expires_at = expires_at
    return token


def _repair_passwordless_active_users(db: Session) -> int:
    users = db.scalars(
        select(User).where(User.status == "active", User.password_hash.is_(None), User.role.in_(["admin", "recruiter"]))
    ).all()
    for user in users:
        _prepare_activation(user)
    return len(users)


def create_user(db: Session, payload: AdminUserCreate) -> User:
    email = str(payload.email).lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        if existing.status == "deleted":
            db.delete(existing)
            db.flush()
        else:
            raise AdminServiceError("Un utilisateur actif ou en attente existe déjà avec cet email.")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=None,
        role=payload.role,
        status="invited",
    )
    token = _prepare_activation(user)
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
    activation_link = f"{settings.FRONTEND_URL.rstrip('/')}/activate/{token}"
    send_user_activation_email(
        db,
        to_email=user.email,
        full_name=user.full_name,
        activation_link=activation_link,
        expires_in_hours=INVITATION_EXPIRES_IN_HOURS,
    )
    db.commit()


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def update_user(db: Session, user: User, payload: AdminUserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        user.email = str(data.pop("email")).lower().strip()
    if "full_name" in data and data["full_name"] is not None:
        data["full_name"] = str(data["full_name"]).strip()
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
    user.activation_token = None
    user.token_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def enable_user(db: Session, user: User) -> User:
    token = _prepare_activation(user)
    db.commit()
    db.refresh(user)
    _send_activation_email(db, user, token)
    return user


def soft_delete_user(db: Session, user: User) -> User:
    user.status = "deleted"
    user.activation_token = None
    user.token_expires_at = None
    user.password_hash = None
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
