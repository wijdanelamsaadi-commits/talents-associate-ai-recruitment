from fastapi import APIRouter


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
def jobs_placeholder() -> dict[str, str]:
    return {"message": "Jobs module placeholder"}
