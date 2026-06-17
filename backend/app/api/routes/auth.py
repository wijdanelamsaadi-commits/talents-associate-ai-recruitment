from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import RecruiterLogin, RecruiterRegister, TokenResponse, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_recruiter(recruiter_in: RecruiterRegister, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.register_recruiter(db, recruiter_in)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A recruiter with this email already exists.",
        ) from exc
    return auth_service.create_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login_recruiter(login_in: RecruiterLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate_recruiter(db, login_in.email, login_in.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_token_response(user)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
