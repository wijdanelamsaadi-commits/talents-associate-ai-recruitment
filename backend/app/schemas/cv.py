from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CVFileRead(BaseModel):
    id: UUID
    candidate_id: UUID
    original_filename: str
    storage_path: str
    mime_type: str | None
    file_size_bytes: int | None
    checksum_sha256: str | None
    parsing_status: str
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CVUploadProcessedRead(CVFileRead):
    processing_status: str
    confidence_score: float | None
    parser_model: str | None
    structured_json: dict | None
    matching_result_ids: list[UUID]


class ExtractedCVTextRead(BaseModel):
    cv_file_id: UUID
    candidate_id: UUID
    raw_text: str
    parsing_status: str
    confidence_score: float | None
    parser_model: str | None
    ai_output: dict | None

    model_config = ConfigDict(from_attributes=True)


class ParsedCVRead(BaseModel):
    cv_file_id: UUID
    parsing_status: str
    confidence_score: float | None
    parser_model: str | None
    structured_json: dict | None

    model_config = ConfigDict(from_attributes=True)


class CVBatchResultItem(BaseModel):
    filename: str
    status: str
    candidate_id: UUID | None = None
    error_message: str | None = None


class CVBatchUploadSummary(BaseModel):
    total: int
    success_count: int
    error_count: int
    results: list[CVBatchResultItem]
