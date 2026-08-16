import io
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.models import CVImportJob
from app.schemas import (
    CVBatchResultItem,
    CVBatchUploadSummary,
    CVFileRead,
    CVImportJobRead,
    CVUploadProcessedRead,
    ExtractedCVTextRead,
    ParsedCVRead,
)
from app.services import cv_service
from app.services.cv_service import CVUploadError, DuplicateCVError
from app.services.text_extraction import TextExtractionError


router = APIRouter(prefix="/cv", tags=["cv"])
CV_IMPORT_JOB_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads" / "cv_import_jobs"
SUPPORTED_BATCH_EXTENSIONS = {".pdf", ".doc", ".docx"}


@router.post("/upload", response_model=CVUploadProcessedRead, status_code=status.HTTP_201_CREATED)
def upload_cv(
    response: Response,
    file: UploadFile = File(...),
    candidate_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
) -> CVUploadProcessedRead:
    try:
        cv_file = cv_service.upload_cv(db, candidate_id=candidate_id, upload_file=file)
        extracted_text, matching_results = cv_service.parse_and_auto_match_cv(db, cv_file_id=cv_file.id)
        response.status_code = status.HTTP_200_OK if cv_file.updated_at != cv_file.created_at else status.HTTP_201_CREATED
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
            message="CV mis à jour avec succès." if cv_file.updated_at != cv_file.created_at else "CV importé avec succès.",
            duplicate=False,
            updated_existing=cv_file.updated_at != cv_file.created_at,
        )
    except DuplicateCVError as exc:
        response.status_code = status.HTTP_200_OK
        cv_file = exc.cv_file
        extracted_text = cv_service.get_extracted_text(db, cv_file.id)
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
            processing_status="duplicate",
            confidence_score=float(extracted_text.confidence_score) if extracted_text and extracted_text.confidence_score is not None else None,
            parser_model=extracted_text.parser_model if extracted_text else None,
            structured_json=extracted_text.ai_output if extracted_text else None,
            matching_result_ids=[],
            message="Ce CV existe déjà dans la base de données.",
            duplicate=True,
            updated_existing=False,
        )
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'enregistrement du CV en base de données n'a pas pu être créé.",
        ) from exc


@router.post("/upload-batch", response_model=CVBatchUploadSummary, status_code=status.HTTP_201_CREATED)
def upload_cv_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CVBatchUploadSummary:
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'import par lot accepte uniquement les fichiers .zip.",
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
                except DuplicateCVError as e:
                    results.append(
                        CVBatchResultItem(
                            filename=Path(filename).name,
                            status="duplicate",
                            candidate_id=e.cv_file.candidate_id,
                            error_message="Ce CV existe déjà dans la base de données.",
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
            detail="Fichier ZIP invalide.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur est survenue pendant le traitement du fichier ZIP : {e}",
        )

    return CVBatchUploadSummary(
        total=len(results),
        success_count=success_count,
        error_count=error_count,
        results=results,
    )


@router.post("/import-jobs", response_model=CVImportJobRead, status_code=status.HTTP_202_ACCEPTED)
def start_cv_import_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CVImportJobRead:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'import asynchrone accepte uniquement les fichiers .zip.",
        )

    try:
        file_bytes = file.file.read()
        total_count = _count_supported_zip_entries(file_bytes)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier ZIP invalide.") from exc

    CV_IMPORT_JOB_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_path = CV_IMPORT_JOB_DIRECTORY / f"{uuid.uuid4()}.zip"
    stored_path.write_bytes(file_bytes)

    job = CVImportJob(
        filename=file.filename,
        storage_path=str(stored_path),
        status="pending",
        current_step="Import préparé",
        total_count=total_count,
        processed_count=0,
        success_count=0,
        duplicate_count=0,
        error_count=0,
        message="Import ZIP lancé. Vous pouvez quitter cette page, le traitement continue côté serveur.",
        result={"items": []},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_process_cv_import_job, job.id)
    return job


@router.get("/import-jobs/active", response_model=CVImportJobRead | None)
def get_latest_cv_import_job(db: Session = Depends(get_db)) -> CVImportJobRead | None:
    statement = select(CVImportJob).order_by(CVImportJob.created_at.desc()).limit(1)
    return db.scalar(statement)


@router.get("/import-jobs/{job_id}", response_model=CVImportJobRead)
def get_cv_import_job(job_id: UUID, db: Session = Depends(get_db)) -> CVImportJobRead:
    job = db.get(CVImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job d'import CV introuvable.")
    return job


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier CV introuvable.")
    return cv_file


@router.delete("/files/{cv_file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv_file(cv_file_id: UUID, db: Session = Depends(get_db)) -> None:
    cv_file = cv_service.get_cv_file(db, cv_file_id)
    if cv_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier CV introuvable.")

    cv_service.delete_cv_file(db, cv_file)


@router.get("/files/{cv_file_id}/text", response_model=ExtractedCVTextRead)
def get_cv_text(cv_file_id: UUID, db: Session = Depends(get_db)) -> ExtractedCVTextRead:
    extracted_text = cv_service.get_extracted_text(db, cv_file_id)
    if extracted_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Texte extrait du CV introuvable.")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Texte extrait du CV introuvable.")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier CV introuvable.")

    file_path = cv_file.storage_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable sur le disque.")

    return FileResponse(
        path=file_path,
        filename=cv_file.original_filename,
        media_type=cv_file.mime_type or "application/octet-stream",
    )


def _count_supported_zip_entries(file_bytes: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        return sum(1 for filename in archive.namelist() if _is_supported_zip_cv(filename))


def _is_supported_zip_cv(filename: str) -> bool:
    if filename.endswith("/") or filename.startswith("__MACOSX/") or "/." in filename:
        return False
    return Path(filename).suffix.lower() in SUPPORTED_BATCH_EXTENSIONS


def _process_cv_import_job(job_id: UUID) -> None:
    with SessionLocal() as db:
        job = db.get(CVImportJob, job_id)
        if job is None:
            return
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        job.current_step = "Ouverture du fichier ZIP"
        db.commit()

        results: list[dict] = []
        try:
            with zipfile.ZipFile(job.storage_path) as archive:
                valid_filenames = [filename for filename in archive.namelist() if _is_supported_zip_cv(filename)]
                job.total_count = len(valid_filenames)
                db.commit()

                for filename in valid_filenames:
                    display_filename = Path(filename).name
                    job.current_filename = display_filename
                    job.current_step = "Analyse du CV"
                    db.commit()

                    try:
                        extracted_file_bytes = archive.read(filename)
                        mock_upload_file = UploadFile(
                            file=io.BytesIO(extracted_file_bytes),
                            size=len(extracted_file_bytes),
                            filename=display_filename,
                            headers=None,
                        )
                        cv_file = cv_service.upload_cv(db, candidate_id=None, upload_file=mock_upload_file)
                        cv_service.parse_and_auto_match_cv(db, cv_file_id=cv_file.id)
                        job.success_count += 1
                        results.append(
                            {
                                "filename": display_filename,
                                "status": "success",
                                "candidate_id": str(cv_file.candidate_id),
                                "error_message": None,
                            }
                        )
                    except DuplicateCVError as exc:
                        job.duplicate_count += 1
                        results.append(
                            {
                                "filename": display_filename,
                                "status": "duplicate",
                                "candidate_id": str(exc.cv_file.candidate_id) if exc.cv_file.candidate_id else None,
                                "error_message": "Ce CV existe déjà dans la base de données.",
                            }
                        )
                    except Exception as exc:
                        job.error_count += 1
                        results.append(
                            {
                                "filename": display_filename,
                                "status": "error",
                                "candidate_id": None,
                                "error_message": str(exc),
                            }
                        )
                    finally:
                        job.processed_count += 1
                        job.result = {"items": results}
                        job.message = (
                            f"{job.processed_count}/{job.total_count or 0} CV traité(s). "
                            f"{job.success_count} succès, {job.duplicate_count} doublon(s), {job.error_count} erreur(s)."
                        )
                        db.commit()

            job.status = "completed"
            job.current_step = "Terminé"
            job.current_filename = None
            job.completed_at = datetime.now(timezone.utc)
            job.message = (
                f"Import ZIP terminé. {job.success_count} succès, {job.duplicate_count} doublon(s), "
                f"{job.error_count} erreur(s). Total analysé : {job.total_count or 0}."
            )
            db.commit()
        except Exception as exc:
            job.status = "failed"
            job.current_step = "Erreur"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            job.message = "Le traitement du ZIP a échoué. Consultez le détail de l'erreur."
            db.commit()

