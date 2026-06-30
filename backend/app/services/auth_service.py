from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import RecruiterRegister, TokenResponse


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def register_recruiter(db: Session, recruiter_in: RecruiterRegister) -> User:
    user = User(
        full_name=recruiter_in.full_name,
        email=recruiter_in.email.lower(),
        password_hash=hash_password(recruiter_in.password),
        role="recruiter",
        status="active",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


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
    if user.token_expires_at < datetime.now(timezone.utc):
        return None
    return user


def activate_user(db: Session, token: str, password: str) -> User | None:
    user = get_user_by_activation_token(db, token)
    if user is None:
        return None
    user.password_hash = hash_password(password)
    user.status = "active"
    user.activation_token = None  # l'token ma y3awedch yۆستعمل
    user.token_expires_at = None
    db.commit()
    db.refresh(user)
    return user
