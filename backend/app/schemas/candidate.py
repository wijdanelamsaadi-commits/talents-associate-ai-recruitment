from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class CandidateBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    current_title: str | None = Field(default=None, max_length=150)
    source: str = Field(default="manual", pattern="^(manual|cv_upload|linkedin_csv|candidate_portal|referral|other)$")
    status: str = Field(
        default="new",
        pattern="^(new|active|shortlisted|interviewing|offered|hired|rejected|archived)$",
    )
    consent_given: bool = False
    owner_user_id: UUID | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateRead(CandidateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
