from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.candidate import CandidateRead



class MatchingOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    skill_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    education_score: int = Field(ge=0, le=100)
    language_score: int = Field(ge=0, le=100)
    semantic_score: int = Field(ge=0, le=100)
    used_semantic_embedding: bool = False
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str
    recommendation: str


class MatchingResultRead(BaseModel):
    id: UUID
    candidate_id: UUID
    job_offer_id: UUID
    score: float
    detailed_scores: dict | None
    matched_skills: dict | list | None
    missing_skills: dict | list | None
    explanation: str | None
    recommendation: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_name: str | None = None
    job_title: str | None = None
    semantic_score: int | None = Field(default=None, ge=0, le=100)
    used_semantic_embedding: bool = False

    model_config = ConfigDict(from_attributes=True)

    @field_validator("score", mode="before")
    @classmethod
    def convert_fraction_score_to_percent(cls, value: float) -> float:
        score = float(value)
        return round(score * 100, 2) if score <= 1 else round(score, 2)


class VivierSearchResult(BaseModel):
    candidate: CandidateRead
    score: float
    has_cv: bool
    cv_file_id: UUID | None = None
    matched_skills: list[str] = Field(default_factory=list)
    score_details: dict | None = None

