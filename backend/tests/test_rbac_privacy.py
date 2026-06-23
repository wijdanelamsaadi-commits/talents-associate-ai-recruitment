from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import require_recruiter_or_admin
from app.core.security import create_candidate_access_token
from app.main import app
from app.schemas.portal import CandidateApplicationRead, PortalApplicationResponse


client = TestClient(app)


def test_public_recruiter_registration_is_blocked():
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Public Recruiter",
            "email": "public.recruiter@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 403
    assert "reserved for administrators" in response.json()["detail"]


def test_candidate_token_cannot_access_recruiter_routes():
    token = create_candidate_access_token(uuid4(), "candidate@example.com")

    response = client.get("/api/candidates", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_recruiter_guard_allows_recruiter_user_for_protected_auth_me():
    recruiter = SimpleNamespace(
        id=uuid4(),
        full_name="Recruiter User",
        email="recruiter@example.com",
        role="recruiter",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[require_recruiter_or_admin] = lambda: recruiter
    try:
        response = client.get("/api/auth/me")
    finally:
        app.dependency_overrides.pop(require_recruiter_or_admin, None)

    assert response.status_code == 200
    assert response.json()["role"] == "recruiter"


def test_candidate_portal_response_excludes_internal_ai_fields():
    payload = PortalApplicationResponse(
        candidate_id=uuid4(),
        application_id=uuid4(),
        cv_file_id=uuid4(),
        message="Application submitted.",
    ).model_dump()

    assert "matching_result_ids" not in payload
    assert "confidence_score" not in payload
    assert "parsing_status" not in payload


def test_candidate_application_status_excludes_matching_score_and_recommendation():
    payload = CandidateApplicationRead(
        application_id=uuid4(),
        job_offer_id=uuid4(),
        job_title="Developpeur Full Stack",
        company_name="Talents Associate",
        application_status="submitted",
        current_stage="application_submitted",
        applied_at=datetime.now(timezone.utc),
        cv_file_id=uuid4(),
    ).model_dump()

    assert "best_matching_score" not in payload
    assert "recommendation" not in payload
    assert "matching_result_ids" not in payload
