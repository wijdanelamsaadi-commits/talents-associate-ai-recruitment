from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import CVFileRead, ExtractedCVTextRead, ParsedCVRead
from app.services import cv_service
from app.services.cv_service import CVUploadError
from app.services.text_extraction import TextExtractionError


router = APIRouter(prefix="/cv", tags=["cv"])


@router.post("/upload", response_model=CVFileRead, status_code=status.HTTP_201_CREATED)
def upload_cv(
    candidate_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CVFileRead:
    try:
        return cv_service.upload_cv(db, candidate_id=candidate_id, upload_file=file)
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A database record for this CV could not be created.",
        ) from exc


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
        extracted_text = cv_service.parse_extracted_cv(db, cv_file_id)
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ParsedCVRead(
        cv_file_id=extracted_text.cv_file_id,
        parsing_status=extracted_text.parsing_status,
        confidence_score=float(extracted_text.confidence_score) if extracted_text.confidence_score is not None else None,
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
        structured_json=extracted_text.ai_output,
    )
