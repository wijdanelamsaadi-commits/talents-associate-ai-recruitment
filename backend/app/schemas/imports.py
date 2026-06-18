from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LinkedInImportRead(BaseModel):
    id: UUID
    filename: str
    imported_count: int
    updated_count: int
    skipped_count: int
    report: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LinkedInImportSummary(BaseModel):
    total_imports: int
    total_imported: int
    total_updated: int
    total_skipped: int
