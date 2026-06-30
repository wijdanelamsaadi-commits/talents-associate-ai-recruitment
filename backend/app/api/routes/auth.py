from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_recruiter_or_admin
from app.core.database import get_db
from app.models import User
from app.schemas import RecruiterLogin, RecruiterRegister, TokenResponse, UserRead
from app.schemas.auth import ActivationInfo, ActivationSetPassword
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_recruiter(_recruiter_in: RecruiterRegister) -> TokenResponse:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="La création d'un compte recruteur est réservée aux administrateurs.",
    )


@router.post("/login", response_model=TokenResponse)
def login_recruiter(login_in: RecruiterLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate_recruiter(db, login_in.email, login_in.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_token_response(user)


@router.get("/activate/{token}", response_model=ActivationInfo)
def verify_activation_token(token: str, db: Session = Depends(get_db)) -> ActivationInfo:
    user = auth_service.get_user_by_activation_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien d'activation invalide ou expiré.",
        )
    return ActivationInfo(email=user.email, full_name=user.full_name)


@router.post("/activate/{token}", response_model=TokenResponse)
def set_password_with_token(
    token: str, payload: ActivationSetPassword, db: Session = Depends(get_db)
) -> TokenResponse:
    user = auth_service.activate_user(db, token, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien d'activation invalide ou expiré.",
        )
    return auth_service.create_token_response(user)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(require_recruiter_or_admin)) -> User:
    return current_user
