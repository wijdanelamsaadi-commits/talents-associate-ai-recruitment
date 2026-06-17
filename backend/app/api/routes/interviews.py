from fastapi import APIRouter


router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("/")
def interviews_placeholder() -> dict[str, str]:
    return {"message": "Interviews module placeholder"}
