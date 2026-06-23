from fastapi import APIRouter, Depends

from app.api.dependencies import require_recruiter_or_admin
from app.api.routes import admin, applications, auth, candidates, cv_upload, dashboard, evaluations, health, imports, interviews, jobs, matching, portal, timeline


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(portal.router)
api_router.include_router(admin.router)
protected_dependencies = [Depends(require_recruiter_or_admin)]
api_router.include_router(candidates.router, dependencies=protected_dependencies)
api_router.include_router(applications.router, dependencies=protected_dependencies)
api_router.include_router(cv_upload.router, dependencies=protected_dependencies)
api_router.include_router(dashboard.router, dependencies=protected_dependencies)
api_router.include_router(imports.router, dependencies=protected_dependencies)
api_router.include_router(jobs.router, dependencies=protected_dependencies)
api_router.include_router(matching.router, dependencies=protected_dependencies)
api_router.include_router(interviews.router, dependencies=protected_dependencies)
api_router.include_router(evaluations.router, dependencies=protected_dependencies)
api_router.include_router(timeline.router, dependencies=protected_dependencies)
