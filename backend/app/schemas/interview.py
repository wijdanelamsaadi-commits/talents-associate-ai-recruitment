from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


INTERVIEW_TYPE_PATTERN = "^(entretien_cabinet|entretien_client)$"
PIPELINE_STATUS_PATTERN = (
    "^(preselectionne|non_selectionne|entretien_cabinet|entretien_client|profil_valide|refus_candidat)$"
)


class InterviewBase(BaseModel):
    candidate_id: UUID
    job_offer_id: UUID
    interview_type: str = Field(default="entretien_cabinet", pattern=INTERVIEW_TYPE_PATTERN)
    status: str = Field(default="entretien_cabinet", pattern=PIPELINE_STATUS_PATTERN)
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
    interview_type: str | None = Field(default=None, pattern=INTERVIEW_TYPE_PATTERN)
    status: str | None = Field(default=None, pattern=PIPELINE_STATUS_PATTERN)
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    meeting_url: str | None = None
    location: str | None = Field(default=None, max_length=180)
    notes: str | None = None
    scheduled_by_user_id: UUID | None = None
    interviewer_user_id: UUID | None = None


class InterviewStatusUpdate(BaseModel):
    status: str = Field(pattern=PIPELINE_STATUS_PATTERN)


class InterviewRead(InterviewBase):
    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime
