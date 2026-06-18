from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import LinkedInImportRead, LinkedInImportSummary, OutlookImportRead, OutlookImportSummary
from app.services.import_service import (
    ImportError,
    get_linkedin_import_summary,
    get_outlook_import_summary,
    import_linkedin_csv,
    import_outlook_cvs,
    list_linkedin_imports,
    list_outlook_imports,
)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/linkedin-csv", response_model=LinkedInImportRead, status_code=status.HTTP_201_CREATED)
async def upload_linkedin_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> LinkedInImportRead:
    try:
        return await import_linkedin_csv(db, file)
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="LinkedIn CSV import could not be saved.") from exc


@router.get("/linkedin-csv", response_model=list[LinkedInImportRead])
def get_linkedin_imports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[LinkedInImportRead]:
    return list_linkedin_imports(db, skip=skip, limit=limit)


@router.get("/linkedin-csv/summary", response_model=LinkedInImportSummary)
def get_linkedin_imports_summary(db: Session = Depends(get_db)) -> LinkedInImportSummary:
    return LinkedInImportSummary(**get_linkedin_import_summary(db))


@router.post("/outlook", response_model=OutlookImportRead, status_code=status.HTTP_201_CREATED)
async def upload_outlook_cvs(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> OutlookImportRead:
    try:
        upload_files = [*(files or [])]
        if file is not None:
            upload_files.append(file)
        return await import_outlook_cvs(db, upload_files)
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Outlook CV import could not be saved.") from exc


@router.get("/outlook/history", response_model=list[OutlookImportRead])
def get_outlook_imports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[OutlookImportRead]:
    return list_outlook_imports(db, skip=skip, limit=limit)


@router.get("/outlook/summary", response_model=OutlookImportSummary)
def get_outlook_imports_summary(db: Session = Depends(get_db)) -> OutlookImportSummary:
    return OutlookImportSummary(**get_outlook_import_summary(db))
