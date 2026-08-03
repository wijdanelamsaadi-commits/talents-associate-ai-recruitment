from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import create_candidate_access_token, hash_password
from app.main import app
from app.models import User
from app.services import admin_service, auth_service


client = TestClient(app)


class FakeDb:
    def __init__(self, user=None):
        self.user = user
        self.added = []
        self.deleted = []
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

    def delete(self, item):
        self.deleted.append(item)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def flush(self):
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
        activation_token=None,
        token_expires_at=None,
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
            "/api/admin/users",
            json={
                "full_name": "New Recruiter",
                "email": "new.recruiter@example.com",
                "role": "recruiter",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 201
    assert response.json()["email"] == "new.recruiter@example.com"
    assert response.json()["role"] == "recruiter"
    assert response.json()["status"] == "invited"
    created_user = next(item for item in fake_db.added if getattr(item, "email", None) == "new.recruiter@example.com")
    assert created_user.password_hash is None
    assert created_user.activation_token


def test_admin_can_reuse_email_from_deleted_user():
    deleted_user = make_user(role="recruiter", status="deleted")
    deleted_user.email = "reused@example.com"
    fake_db = FakeDb(user=deleted_user)

    created = admin_service.create_user(
        fake_db,
        SimpleNamespace(full_name="Reused Recruiter", email="reused@example.com", role="recruiter"),
    )

    assert deleted_user in fake_db.deleted
    assert created.email == "reused@example.com"
    assert created.status == "invited"
    assert created.password_hash is None
    assert created.activation_token


def test_admin_cannot_reuse_email_from_non_deleted_user():
    active_user = make_user(role="recruiter", status="active")
    active_user.email = "active@example.com"
    fake_db = FakeDb(user=active_user)

    try:
        admin_service.create_user(
            fake_db,
            SimpleNamespace(full_name="Blocked Recruiter", email="active@example.com", role="recruiter"),
        )
    except admin_service.AdminServiceError as exc:
        assert "existe déjà" in str(exc)
    else:
        raise AssertionError("Expected AdminServiceError")


def test_recruiter_cannot_create_recruiter():
    recruiter = make_user(role="recruiter")
    app.dependency_overrides[get_current_user] = lambda: recruiter
    try:
        response = client.post(
            "/api/admin/users",
            json={
                "full_name": "Blocked Recruiter",
                "email": "blocked.recruiter@example.com",
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
    assert enabled.json()["status"] == "invited"
    assert recruiter.password_hash is None
    assert recruiter.activation_token


def test_disabled_recruiter_cannot_login():
    suspended = make_user(role="recruiter", status="suspended")
    fake_db = FakeDb(user=suspended)

    user = auth_service.authenticate_recruiter(fake_db, suspended.email, "Password123!")

    assert user is None


def test_invited_recruiter_cannot_login_before_password_setup():
    invited = make_user(role="recruiter", status="invited")
    invited.password_hash = None
    fake_db = FakeDb(user=invited)

    user = auth_service.authenticate_recruiter(fake_db, invited.email, "Password123!")

    assert user is None


def test_activation_token_sets_password_and_activates_user():
    invited = make_user(role="recruiter", status="invited")
    invited.password_hash = None
    invited.activation_token = "valid-token"
    invited.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    fake_db = FakeDb(user=invited)

    user = auth_service.activate_user(fake_db, "valid-token", "NewPassword123!")

    assert user is invited
    assert invited.status == "active"
    assert invited.password_hash is not None
    assert invited.activation_token is None
    assert invited.token_expires_at is None
    assert auth_service.authenticate_recruiter(fake_db, invited.email, "NewPassword123!") is invited


def test_expired_activation_token_is_rejected():
    invited = make_user(role="recruiter", status="invited")
    invited.activation_token = "expired-token"
    invited.token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    fake_db = FakeDb(user=invited)

    user = auth_service.activate_user(fake_db, "expired-token", "NewPassword123!")

    assert user is None
    assert invited.status == "invited"


def test_password_reset_generates_token_for_active_user():
    active = make_user(role="recruiter", status="active")
    active.activation_token = "old-token"
    fake_db = FakeDb(user=active)

    auth_service.request_password_reset(fake_db, active.email)

    assert fake_db.committed is True
    assert active.activation_token
    assert active.activation_token != "old-token"
    assert active.token_expires_at is not None
    assert any(getattr(item, "to_email", None) == active.email for item in fake_db.added)


def test_password_reset_ignored_for_active_user_without_password():
    active = make_user(role="recruiter", status="active")
    active.password_hash = None
    fake_db = FakeDb(user=active)

    auth_service.request_password_reset(fake_db, active.email)

    assert fake_db.committed is False
    assert active.activation_token is None
    assert fake_db.added == []


def test_password_reset_token_sets_new_password():
    active = make_user(role="recruiter", status="active")
    active.activation_token = "reset-token"
    active.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    fake_db = FakeDb(user=active)

    user = auth_service.reset_password_with_token(fake_db, "reset-token", "ChangedPassword123!")

    assert user is active
    assert active.activation_token is None
    assert active.token_expires_at is None
    assert auth_service.authenticate_recruiter(fake_db, active.email, "ChangedPassword123!") is active


def test_active_user_without_password_is_repaired_to_invited_in_admin_list():
    active = make_user(role="recruiter", status="active")
    active.password_hash = None
    fake_db = FakeDb(user=active)

    users = admin_service.list_users(fake_db)

    assert users == [active]
    assert active.status == "invited"
    assert active.password_hash is None
    assert active.activation_token
    assert fake_db.committed is True


def test_admin_settings_are_protected_for_recruiter():
    recruiter = make_user(role="recruiter")
    app.dependency_overrides[get_current_user] = lambda: recruiter
    try:
        response = client.get("/api/admin/settings")
    finally:
        clear_overrides()

    assert response.status_code == 403
