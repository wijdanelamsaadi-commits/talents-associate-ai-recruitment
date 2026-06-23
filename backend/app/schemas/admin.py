from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminUserRead(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: str
    status: str
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRecruiterCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="recruiter", pattern="^(recruiter|hiring_manager)$")


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern="^(admin|recruiter|hiring_manager)$")
    status: str | None = Field(default=None, pattern="^(active|invited|suspended|deleted)$")
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminSettingsRead(BaseModel):
    settings: dict[str, Any] = {}


class AdminSettingsUpdate(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class AdminDashboardStats(BaseModel):
    candidates_count: int
    recruiters_count: int
    jobs_count: int
    applications_count: int
    talent_pool_count: int
    email_sent_count: int
    email_skipped_count: int
    email_failed_count: int
