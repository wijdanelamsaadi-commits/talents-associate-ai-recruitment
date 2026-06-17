from fastapi import APIRouter


router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/")
def matching_placeholder() -> dict[str, str]:
    return {"message": "AI matching module placeholder"}
