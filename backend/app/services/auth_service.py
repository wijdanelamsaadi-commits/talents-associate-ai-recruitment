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
    if user is None or user.role not in {"admin", "recruiter", "hiring_manager"}:
        return None
    if user.status != "active" or not verify_password(password, user.password_hash):
        return None
    return user


def create_token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.email), user=user)
