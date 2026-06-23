from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import create_candidate_access_token, hash_password
from app.main import app
from app.models import User
from app.services import auth_service


client = TestClient(app)


class FakeDb:
    def __init__(self, user=None):
        self.user = user
        self.added = []
        self.committed = False
        self.refreshed = None

    def add(self, item):
        if getattr(item, "id", None) is None:
            item.id = uuid4()
        now = datetime.now(timezone.utc)
        if getattr(item, "created_at", None) is None:
            item.created_at = now
        if getattr(item, "updated_at", None) is None:
            item.updated_at = now
        self.added.append(item)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def refresh(self, item):
        self.refreshed = item

    def get(self, _model, _identifier):
        return self.user

    def scalar(self, _statement):
        return self.user

    def scalars(self, _statement):
        return SimpleNamespace(all=lambda: [self.user] if self.user else [])


def make_user(role="recruiter", status="active"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        full_name=f"{role.title()} User",
        email=f"{role}.{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("Password123!"),
        role=role,
        status=status,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )


def clear_overrides():
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_admin_can_create_recruiter():
    admin = make_user(role="admin")
    fake_db = FakeDb()
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        response = client.post(
            "/api/admin/recruiters",
            json={
                "full_name": "New Recruiter",
                "email": "new.recruiter@example.com",
                "password": "Password123!",
                "role": "recruiter",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 201
    assert response.json()["email"] == "new.recruiter@example.com"
    assert response.json()["role"] == "recruiter"


def test_recruiter_cannot_create_recruiter():
    recruiter = make_user(role="recruiter")
    app.dependency_overrides[get_current_user] = lambda: recruiter
    try:
        response = client.post(
            "/api/admin/recruiters",
            json={
                "full_name": "Blocked Recruiter",
                "email": "blocked.recruiter@example.com",
                "password": "Password123!",
                "role": "recruiter",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 403


def test_candidate_cannot_access_admin_routes():
    token = create_candidate_access_token(uuid4(), "candidate@example.com")

    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_admin_can_disable_and_enable_recruiter():
    admin = make_user(role="admin")
    recruiter = make_user(role="recruiter")
    fake_db = FakeDb(user=recruiter)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        disabled = client.patch(f"/api/admin/users/{recruiter.id}/disable")
        enabled = client.patch(f"/api/admin/users/{recruiter.id}/enable")
    finally:
        clear_overrides()

    assert disabled.status_code == 200
    assert disabled.json()["status"] == "suspended"
    assert enabled.status_code == 200
    assert enabled.json()["status"] == "active"


def test_disabled_recruiter_cannot_login():
    suspended = make_user(role="recruiter", status="suspended")
    fake_db = FakeDb(user=suspended)

    user = auth_service.authenticate_recruiter(fake_db, suspended.email, "Password123!")

    assert user is None


def test_admin_settings_are_protected_for_recruiter():
    recruiter = make_user(role="recruiter")
    app.dependency_overrides[get_current_user] = lambda: recruiter
    try:
        response = client.get("/api/admin/settings")
    finally:
        clear_overrides()

    assert response.status_code == 403
