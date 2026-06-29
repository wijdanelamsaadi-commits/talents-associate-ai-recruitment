import io
import zipfile
from uuid import uuid4
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.services import cv_service

client = TestClient(app)

class FakeDb:
    def __init__(self):
        self.committed = False
    def commit(self):
        self.committed = True
    def rollback(self):
        pass

def test_batch_upload_zip(monkeypatch):
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    fake_db = FakeDb()

    # Create a dummy zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        z.writestr("John_Doe_CV.pdf", b"%PDF-1.4 dummy content")
        z.writestr("Jane_Smith_CV.docx", b"dummy word content")
        z.writestr("unsupported.txt", b"txt files should be ignored")

    zip_buffer.seek(0)

    # Track calls to cv_service.upload_cv
    mock_cv_files = []
    def fake_upload_cv(db, candidate_id, upload_file, **kwargs):
        candidate_id = uuid4()  # simulate auto-created candidate
        cv = SimpleNamespace(
            id=uuid4(),
            candidate_id=candidate_id,
            original_filename=upload_file.filename,
        )
        mock_cv_files.append(cv)
        return cv

    # Mock cv_service.parse_and_auto_match_cv
    parsed_calls = []
    def fake_parse_and_auto_match_cv(db, cv_file_id, **kwargs):
        parsed_calls.append(cv_file_id)
        return SimpleNamespace(confidence_score=0.9, parser_model="mock", ai_output={}), []

    monkeypatch.setattr(cv_service, "upload_cv", fake_upload_cv)
    monkeypatch.setattr(cv_service, "parse_and_auto_match_cv", fake_parse_and_auto_match_cv)

    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.post(
            "/api/cv/upload-batch",
            files={"file": ("cvs.zip", zip_buffer, "application/zip")},
        )
        assert response.status_code == 201
        data = response.json()

        # We expect 2 processed successfully (txt is ignored)
        assert data["total"] == 2
        assert data["success_count"] == 2
        assert data["error_count"] == 0
        assert len(data["results"]) == 2

        filenames = {item["filename"] for item in data["results"]}
        assert "John_Doe_CV.pdf" in filenames
        assert "Jane_Smith_CV.docx" in filenames

        # Verify cv_service.upload_cv was called twice (once per valid file)
        assert len(mock_cv_files) == 2
        processed_names = {cv.original_filename for cv in mock_cv_files}
        assert "John_Doe_CV.pdf" in processed_names
        assert "Jane_Smith_CV.docx" in processed_names
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
