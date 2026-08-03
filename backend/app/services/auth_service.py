from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import RecruiterRegister, TokenResponse
from app.services.email_service import send_password_reset_email


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def register_recruiter(db: Session, recruiter_in: RecruiterRegister) -> User:
    raise ValueError("La création d'un compte recruteur est réservée aux administrateurs.")


def authenticate_recruiter(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or user.role not in {"admin", "recruiter"}:
        return None
    if user.status != "active" or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.email), user=user)


def get_user_by_activation_token(db: Session, token: str) -> User | None:
    if not token:
        return None
    user = db.scalar(select(User).where(User.activation_token == token))
    if user is None or user.token_expires_at is None:
        return None
    expires_at = user.token_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if user.status != "invited" or expires_at < datetime.now(timezone.utc):
        return None
    return user


def request_password_reset(db: Session, email: str) -> None:
    user = get_user_by_email(db, email)
    if user is None or user.role not in {"admin", "recruiter"} or user.status != "active" or not user.password_hash:
        return

    token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    user.activation_token = token
    user.token_expires_at = expires_at
    db.flush()
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{token}"
    send_password_reset_email(
        db,
        to_email=user.email,
        full_name=user.full_name,
        reset_link=reset_link,
        expires_in_hours=24,
    )
    db.commit()


def get_user_by_password_reset_token(db: Session, token: str) -> User | None:
    if not token:
        return None
    user = db.scalar(select(User).where(User.activation_token == token))
    if user is None or user.token_expires_at is None:
        return None
    expires_at = user.token_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if user.status != "active" or not user.password_hash or expires_at < datetime.now(timezone.utc):
        return None
    return user


def reset_password_with_token(db: Session, token: str, password: str) -> User | None:
    user = get_user_by_password_reset_token(db, token)
    if user is None:
        return None
    user.password_hash = hash_password(password)
    user.activation_token = None
    user.token_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def activate_user(db: Session, token: str, password: str) -> User | None:
    user = get_user_by_activation_token(db, token)
    if user is None:
        return None
    user.password_hash = hash_password(password)
    user.status = "active"
    user.activation_token = None
    user.token_expires_at = None
    db.commit()
    db.refresh(user)
    return user
