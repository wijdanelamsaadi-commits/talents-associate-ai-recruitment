import io
from uuid import uuid4

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.api.routes import portal as portal_routes
from app.core.database import get_db
from app.main import app
from app.schemas import PublicPortalApplicationResponse
from app.services import portal_service


client = TestClient(app)
TEST_API_KEY = "wordpress-test-key"


def _valid_form(opportunite: str | None = None) -> dict[str, str]:
    return {
        "opportunite": opportunite or str(uuid4()),
        "nom": "Candidat",
        "prenom": "Test",
        "email": "candidat.wordpress@example.com",
        "telephone": "0600000000",
        "ville": "Casablanca",
        "message": "Message de candidature.",
    }


def _valid_file(filename: str = "cv.pdf", content: bytes = b"%PDF-1.4\nCV test") -> dict:
    return {"cv": (filename, io.BytesIO(content), "application/pdf")}


def _fake_public_response() -> PublicPortalApplicationResponse:
    return PublicPortalApplicationResponse(
        candidate_id=uuid4(),
        application_id=uuid4(),
        cv_file_id=uuid4(),
        candidate_status="cree_ou_mis_a_jour",
        cv_received=True,
        processing_status="analyse_effectuee",
        message="Votre candidature a bien été reçue.",
    )


def _install_route_mocks(monkeypatch, response: PublicPortalApplicationResponse | None = None):
    monkeypatch.setattr(portal_routes.settings, "WORDPRESS_API_KEY", TEST_API_KEY)
    app.dependency_overrides[get_db] = lambda: object()
    calls = []

    def fake_submit(db, **kwargs):
        calls.append(kwargs)
        return response or _fake_public_response()

    monkeypatch.setattr(portal_routes, "submit_wordpress_application", fake_submit)
    return calls


def _clear_overrides():
    app.dependency_overrides.pop(get_db, None)


def test_wordpress_application_requires_api_key(monkeypatch):
    monkeypatch.setattr(portal_routes.settings, "WORDPRESS_API_KEY", TEST_API_KEY)
    response = client.post("/api/portal/applications", data=_valid_form(), files=_valid_file())

    assert response.status_code == 401


def test_wordpress_application_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setattr(portal_routes.settings, "WORDPRESS_API_KEY", TEST_API_KEY)
    response = client.post(
        "/api/portal/applications",
        data=_valid_form(),
        files=_valid_file(),
        headers={"X-Talents-Api-Key": "wrong"},
    )

    assert response.status_code == 403


def test_wordpress_application_accepts_valid_payload(monkeypatch):
    calls = _install_route_mocks(monkeypatch)
    try:
        response = client.post(
            "/api/portal/applications",
            data=_valid_form(),
            files=_valid_file(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    assert calls
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Votre candidature a bien été reçue."


def test_wordpress_application_supports_offer_uuid(monkeypatch):
    job_id = uuid4()
    calls = _install_route_mocks(monkeypatch)
    try:
        response = client.post(
            "/api/portal/applications",
            data=_valid_form(str(job_id)),
            files=_valid_file(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    assert calls[0]["opportunite"] == str(job_id)


def test_wordpress_application_supports_offer_title(monkeypatch):
    calls = _install_route_mocks(monkeypatch)
    try:
        response = client.post(
            "/api/portal/applications",
            data=_valid_form("Développeur Full Stack"),
            files=_valid_file(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    assert calls[0]["opportunite"] == "Développeur Full Stack"


def test_wordpress_application_rejects_invalid_email(monkeypatch):
    _install_route_mocks(monkeypatch)
    form = _valid_form()
    form["email"] = "email-invalide"
    try:
        response = client.post(
            "/api/portal/applications",
            data=form,
            files=_valid_file(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


def test_wordpress_application_requires_cv(monkeypatch):
    _install_route_mocks(monkeypatch)
    try:
        response = client.post(
            "/api/portal/applications",
            data=_valid_form(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


def test_public_cv_validation_rejects_forbidden_extension():
    upload = UploadFile(filename="cv.exe", file=io.BytesIO(b"test"))

    try:
        portal_service._inspect_public_cv_upload(upload)
    except portal_service.PortalPublicApplicationError as exc:
        assert exc.status_code == 415
    else:
        raise AssertionError("Forbidden extension should be rejected")


def test_public_cv_validation_rejects_too_large_file(monkeypatch):
    monkeypatch.setattr(portal_service.cv_service, "MAX_CV_FILE_SIZE_BYTES", 3)
    upload = UploadFile(filename="cv.pdf", file=io.BytesIO(b"1234"))

    try:
        portal_service._inspect_public_cv_upload(upload)
    except portal_service.PortalPublicApplicationError as exc:
        assert exc.status_code == 413
    else:
        raise AssertionError("Too large file should be rejected")


def test_wordpress_application_maps_missing_offer_to_404(monkeypatch):
    _install_route_mocks(monkeypatch)

    def fake_missing_offer(db, **kwargs):
        raise portal_service.PortalPublicApplicationError("Offre introuvable.", status_code=404)

    monkeypatch.setattr(portal_routes, "submit_wordpress_application", fake_missing_offer)
    try:
        response = client.post(
            "/api/portal/applications",
            data=_valid_form("Offre inconnue"),
            files=_valid_file(),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404


def test_second_identical_wordpress_application_response_has_no_sensitive_ai_fields(monkeypatch):
    reused_response = PublicPortalApplicationResponse(
        candidate_id=uuid4(),
        application_id=uuid4(),
        cv_file_id=uuid4(),
        candidate_status="existant",
        cv_received=True,
        processing_status="cv_deja_present",
        message="Votre candidature a bien été reçue.",
    )
    _install_route_mocks(monkeypatch, reused_response)
    try:
        first = client.post(
            "/api/portal/applications",
            data=_valid_form(),
            files=_valid_file(content=b"%PDF-1.4\nsame"),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
        second = client.post(
            "/api/portal/applications",
            data=_valid_form(),
            files=_valid_file(content=b"%PDF-1.4\nsame"),
            headers={"X-Talents-Api-Key": TEST_API_KEY},
        )
    finally:
        _clear_overrides()

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["candidate_id"] == second.json()["candidate_id"]
    for forbidden in ("score", "confidence_score", "matching_result_ids", "recommendation", "ai_output", "embedding"):
        assert forbidden not in second.json()


def test_portal_status_rejects_invalid_email():
    response = client.get("/api/portal/status", params={"email": "email-invalide"})

    assert response.status_code == 422
