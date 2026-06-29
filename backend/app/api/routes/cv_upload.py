import io
import os
import zipfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    CVBatchResultItem,
    CVBatchUploadSummary,
    CVFileRead,
    CVUploadProcessedRead,
    ExtractedCVTextRead,
    ParsedCVRead,
)
from app.services import cv_service
from app.services.cv_service import CVUploadError
from app.services.text_extraction import TextExtractionError


router = APIRouter(prefix="/cv", tags=["cv"])


@router.post("/upload", response_model=CVUploadProcessedRead, status_code=status.HTTP_201_CREATED)
def upload_cv(
    file: UploadFile = File(...),
    candidate_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
) -> CVUploadProcessedRead:
    try:
        cv_file = cv_service.upload_cv(db, candidate_id=candidate_id, upload_file=file)
        extracted_text, matching_results = cv_service.parse_and_auto_match_cv(db, cv_file_id=cv_file.id)
        return CVUploadProcessedRead(
            id=cv_file.id,
            candidate_id=cv_file.candidate_id,
            original_filename=cv_file.original_filename,
            storage_path=cv_file.storage_path,
            mime_type=cv_file.mime_type,
            file_size_bytes=cv_file.file_size_bytes,
            checksum_sha256=cv_file.checksum_sha256,
            parsing_status=cv_file.parsing_status,
            uploaded_at=cv_file.uploaded_at,
            created_at=cv_file.created_at,
            updated_at=cv_file.updated_at,
            processing_status="completed",
            confidence_score=float(extracted_text.confidence_score) if extracted_text.confidence_score is not None else None,
            parser_model=extracted_text.parser_model,
            structured_json=extracted_text.ai_output,
            matching_result_ids=[result.id for result in matching_results],
        )
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A database record for this CV could not be created.",
        ) from exc


@router.post("/upload-batch", response_model=CVBatchUploadSummary, status_code=status.HTTP_201_CREATED)
def upload_cv_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CVBatchUploadSummary:
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch upload only supports .zip files.",
        )

    results = []
    success_count = 0
    error_count = 0

    try:
        file_bytes = file.file.read()
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for filename in z.namelist():
                if filename.endswith("/") or filename.startswith("__MACOSX/") or "/." in filename:
                    continue
                ext = Path(filename).suffix.lower()
                if ext not in {".pdf", ".doc", ".docx"}:
                    continue

                extracted_file_bytes = z.read(filename)
                
                try:
                    # Create a mock UploadFile
                    mock_upload_file = UploadFile(
                        file=io.BytesIO(extracted_file_bytes),
                        size=len(extracted_file_bytes),
                        filename=Path(filename).name,
                        headers=None,
                    )
                    
                    cv_file = cv_service.upload_cv(db, candidate_id=None, upload_file=mock_upload_file)
                    cv_service.parse_and_auto_match_cv(db, cv_file_id=cv_file.id)
                    
                    success_count += 1
                    results.append(
                        CVBatchResultItem(
                            filename=Path(filename).name,
                            status="success",
                            candidate_id=cv_file.candidate_id,
                        )
                    )
                except Exception as e:
                    error_count += 1
                    results.append(
                        CVBatchResultItem(
                            filename=Path(filename).name,
                            status="error",
                            candidate_id=None,
                            error_message=str(e),
                        )
                    )
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zip file.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the zip file: {e}",
        )

    return CVBatchUploadSummary(
        total=success_count + error_count,
        success_count=success_count,
        error_count=error_count,
        results=results,
    )


@router.get("/files", response_model=list[CVFileRead])
def list_cv_files(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[CVFileRead]:
    return cv_service.list_cv_files(db, skip=skip, limit=limit)


@router.get("/files/{cv_file_id}", response_model=CVFileRead)
def get_cv_file(cv_file_id: UUID, db: Session = Depends(get_db)) -> CVFileRead:
    cv_file = cv_service.get_cv_file(db, cv_file_id)
    if cv_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV file not found.")
    return cv_file


@router.delete("/files/{cv_file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv_file(cv_file_id: UUID, db: Session = Depends(get_db)) -> None:
    cv_file = cv_service.get_cv_file(db, cv_file_id)
    if cv_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV file not found.")

    cv_service.delete_cv_file(db, cv_file)


@router.get("/files/{cv_file_id}/text", response_model=ExtractedCVTextRead)
def get_cv_text(cv_file_id: UUID, db: Session = Depends(get_db)) -> ExtractedCVTextRead:
    extracted_text = cv_service.get_extracted_text(db, cv_file_id)
    if extracted_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracted CV text not found.")
    return extracted_text


@router.post("/{cv_file_id}/parse", response_model=ParsedCVRead)
def parse_cv(cv_file_id: UUID, db: Session = Depends(get_db)) -> ParsedCVRead:
    try:
        extracted_text, _matching_results = cv_service.parse_and_auto_match_cv(db, cv_file_id)
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ParsedCVRead(
        cv_file_id=extracted_text.cv_file_id,
        parsing_status=extracted_text.parsing_status,
        confidence_score=float(extracted_text.confidence_score) if extracted_text.confidence_score is not None else None,
        parser_model=extracted_text.parser_model,
        structured_json=extracted_text.ai_output,
    )


@router.get("/{cv_file_id}/parsed", response_model=ParsedCVRead)
def get_parsed_cv(cv_file_id: UUID, db: Session = Depends(get_db)) -> ParsedCVRead:
    extracted_text = cv_service.get_extracted_text(db, cv_file_id)
    if extracted_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracted CV text not found.")

    return ParsedCVRead(
        cv_file_id=extracted_text.cv_file_id,
        parsing_status=extracted_text.parsing_status,
        confidence_score=float(extracted_text.confidence_score) if extracted_text.confidence_score is not None else None,
        parser_model=extracted_text.parser_model,
        structured_json=extracted_text.ai_output,
    )


@router.get("/{cv_file_id}/download")
def download_cv_file(cv_file_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    cv_file = cv_service.get_cv_file(db, cv_file_id)
    if cv_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV file not found.")

    file_path = cv_file.storage_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File on disk not found.")

    return FileResponse(
        path=file_path,
        filename=cv_file.original_filename,
        media_type=cv_file.mime_type or "application/octet-stream",
    )

