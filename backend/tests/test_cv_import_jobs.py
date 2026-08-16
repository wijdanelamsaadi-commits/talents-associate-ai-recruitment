import io
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.routes import cv_upload
from app.core.database import get_db
from app.main import app


client = TestClient(app)


class FakeDb:
    def __init__(self, latest_job=None):
        self.latest_job = latest_job
        self.added = None

    def add(self, item):
        item.id = item.id or uuid4()
        now = datetime.now(timezone.utc)
        item.created_at = getattr(item, "created_at", None) or now
        item.updated_at = getattr(item, "updated_at", None) or now
        self.added = item
        self.latest_job = item

    def commit(self):
        if self.added is not None:
            self.added.updated_at = datetime.now(timezone.utc)

    def refresh(self, _item):
        return None

    def scalar(self, _statement):
        return self.latest_job


def _zip_bytes() -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as archive:
        archive.writestr("Adnane_Ayoub.pdf", b"%PDF-1.4 fake")
        archive.writestr("ignored.txt", b"ignored")
    zip_buffer.seek(0)
    return zip_buffer


def test_start_cv_import_job_persists_job_and_schedules_background(monkeypatch):
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    fake_db = FakeDb()
    scheduled_job_ids = []

    def fake_process(job_id):
        scheduled_job_ids.append(job_id)

    monkeypatch.setattr(cv_upload, "_process_cv_import_job", fake_process)
    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.post(
            "/api/cv/import-jobs",
            files={"file": ("cvs.zip", _zip_bytes(), "application/zip")},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 202
    data = response.json()
    assert data["filename"] == "cvs.zip"
    assert data["status"] == "pending"
    assert data["total_count"] == 1
    assert data["processed_count"] == 0
    assert data["message"].startswith("Import ZIP lancé")
    assert scheduled_job_ids == [fake_db.added.id]


def test_start_cv_import_job_rejects_invalid_zip_extension():
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: FakeDb()

    try:
        response = client.post(
            "/api/cv/import-jobs",
            files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 400
    assert "uniquement les fichiers .zip" in response.json()["detail"]


def test_latest_cv_import_job_returns_persisted_state():
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    now = datetime.now(timezone.utc)
    latest_job = SimpleNamespace(
        id=uuid4(),
        filename="lot.zip",
        status="processing",
        current_step="Analyse du CV",
        current_filename="profil.pdf",
        total_count=3,
        processed_count=1,
        success_count=1,
        duplicate_count=0,
        error_count=0,
        message="1/3 CV traité(s).",
        error_message=None,
        result={"items": []},
        started_at=now,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: FakeDb(latest_job=latest_job)

    try:
        response = client.get("/api/cv/import-jobs/active")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["current_filename"] == "profil.pdf"
    assert data["processed_count"] == 1
    assert data["total_count"] == 3
