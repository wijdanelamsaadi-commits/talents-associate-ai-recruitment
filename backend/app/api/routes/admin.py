from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.database import get_db
from app.models import User
from app.schemas.admin import (
    AdminDashboardStats,
    AdminSettingsRead,
    AdminSettingsUpdate,
    AdminUserCreate,
    AdminUserRead,
    AdminUserUpdate,
)
from app.services import admin_service
from app.services.admin_service import AdminServiceError


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_user_or_404(user_id: UUID, db: Session) -> User:
    user = admin_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user


@router.get("", response_model=AdminDashboardStats)
def read_admin_dashboard(db: Session = Depends(get_db)) -> AdminDashboardStats:
    return AdminDashboardStats(**admin_service.dashboard_stats(db))


@router.get("/users", response_model=list[AdminUserRead])
def list_users(db: Session = Depends(get_db)) -> list[AdminUserRead]:
    return admin_service.list_users(db)


@router.post("/users", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: AdminUserCreate, db: Session = Depends(get_db)) -> AdminUserRead:
    try:
        return admin_service.create_user(db, payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà.") from exc


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(user_id: UUID, payload: AdminUserUpdate, db: Session = Depends(get_db)) -> AdminUserRead:
    user = _get_user_or_404(user_id, db)
    try:
        return admin_service.update_user(db, user, payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà.") from exc


@router.patch("/users/{user_id}/disable", response_model=AdminUserRead)
def disable_user(user_id: UUID, db: Session = Depends(get_db)) -> AdminUserRead:
    user = _get_user_or_404(user_id, db)
    return admin_service.disable_user(db, user)


@router.patch("/users/{user_id}/enable", response_model=AdminUserRead)
def enable_user(user_id: UUID, db: Session = Depends(get_db)) -> AdminUserRead:
    user = _get_user_or_404(user_id, db)
    return admin_service.enable_user(db, user)


@router.delete("/users/{user_id}", response_model=AdminUserRead)
def delete_user(user_id: UUID, db: Session = Depends(get_db)) -> AdminUserRead:
    user = _get_user_or_404(user_id, db)
    return admin_service.soft_delete_user(db, user)


@router.get("/settings", response_model=AdminSettingsRead)
def read_settings(db: Session = Depends(get_db)) -> AdminSettingsRead:
    return AdminSettingsRead(settings=admin_service.get_settings(db))


@router.patch("/settings", response_model=AdminSettingsRead)
def update_settings(payload: AdminSettingsUpdate, db: Session = Depends(get_db)) -> AdminSettingsRead:
    try:
        return AdminSettingsRead(settings=admin_service.update_settings(db, payload))
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
