from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, decode_candidate_access_token
from app.models import Candidate, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'accès invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le compte recruteur n'est pas actif.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits administrateur requis.",
        )
    return current_user


def require_recruiter_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {"admin", "recruiter", "hiring_manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits recruteur ou administrateur requis.",
        )
    return current_user


def get_current_candidate(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Candidate:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification candidat requise.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_candidate_access_token(credentials.credentials)
        candidate_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'accès candidat invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    candidate = db.get(Candidate, candidate_id)
    if candidate is None or candidate.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le compte candidat n'est pas actif.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return candidate


def require_candidate(current_candidate: Candidate = Depends(get_current_candidate)) -> Candidate:
    return current_candidate
