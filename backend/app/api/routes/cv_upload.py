from fastapi import APIRouter


router = APIRouter(prefix="/cv-upload", tags=["cv-upload"])


@router.get("/")
def cv_upload_placeholder() -> dict[str, str]:
    return {"message": "CV upload module placeholder"}
