from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.routes import auth, candidates, cv_upload, dashboard, evaluations, health, imports, interviews, jobs, matching, portal, timeline


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(portal.router)
protected_dependencies = [Depends(get_current_user)]
api_router.include_router(candidates.router, dependencies=protected_dependencies)
api_router.include_router(cv_upload.router, dependencies=protected_dependencies)
api_router.include_router(dashboard.router, dependencies=protected_dependencies)
api_router.include_router(imports.router, dependencies=protected_dependencies)
api_router.include_router(jobs.router, dependencies=protected_dependencies)
api_router.include_router(matching.router, dependencies=protected_dependencies)
api_router.include_router(interviews.router, dependencies=protected_dependencies)
api_router.include_router(evaluations.router, dependencies=protected_dependencies)
api_router.include_router(timeline.router, dependencies=protected_dependencies)
