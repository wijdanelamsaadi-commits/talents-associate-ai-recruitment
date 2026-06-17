from fastapi import APIRouter

from app.api.routes import candidates, cv_upload, evaluations, health, interviews, jobs, matching, timeline


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(candidates.router)
api_router.include_router(cv_upload.router)
api_router.include_router(jobs.router)
api_router.include_router(matching.router)
api_router.include_router(interviews.router)
api_router.include_router(evaluations.router)
api_router.include_router(timeline.router)
