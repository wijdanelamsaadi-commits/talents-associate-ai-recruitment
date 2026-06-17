from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TimelineEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=180)
    description: str | None = None
    metadata: dict | None = None


class TimelineEventRead(BaseModel):
    id: UUID
    candidate_id: UUID
    event_type: str
    title: str
    description: str | None
    metadata: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
