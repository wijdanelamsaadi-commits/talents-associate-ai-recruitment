from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class InterviewBase(BaseModel):
    candidate_id: UUID
    job_offer_id: UUID
    interview_type: str = Field(default="screening", pattern="^(screening|technical|hr|manager|final)$")
    status: str = Field(default="scheduled", pattern="^(scheduled|completed|cancelled|rescheduled|no_show)$")
    scheduled_start_at: datetime
    scheduled_end_at: datetime | None = None
    meeting_url: str | None = None
    location: str | None = Field(default=None, max_length=180)
    notes: str | None = None
    scheduled_by_user_id: UUID | None = None
    interviewer_user_id: UUID | None = None

    @model_validator(mode="after")
    def validate_schedule(self) -> "InterviewBase":
        if self.scheduled_end_at is not None and self.scheduled_end_at <= self.scheduled_start_at:
            raise ValueError("Interview end time must be after start time.")
        return self


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    candidate_id: UUID | None = None
    job_offer_id: UUID | None = None
    interview_type: str | None = Field(default=None, pattern="^(screening|technical|hr|manager|final)$")
    status: str | None = Field(default=None, pattern="^(scheduled|completed|cancelled|rescheduled|no_show)$")
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    meeting_url: str | None = None
    location: str | None = Field(default=None, max_length=180)
    notes: str | None = None
    scheduled_by_user_id: UUID | None = None
    interviewer_user_id: UUID | None = None


class InterviewStatusUpdate(BaseModel):
    status: str = Field(pattern="^(scheduled|completed|cancelled|rescheduled|no_show)$")


class InterviewRead(InterviewBase):
    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime
