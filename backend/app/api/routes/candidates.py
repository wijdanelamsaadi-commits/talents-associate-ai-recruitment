from fastapi import APIRouter


router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/")
def list_candidates_placeholder() -> dict[str, str]:
    return {"message": "Candidates module placeholder"}
