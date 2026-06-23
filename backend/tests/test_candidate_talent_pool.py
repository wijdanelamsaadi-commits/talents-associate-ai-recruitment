from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services import candidate_service


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class FakeDb:
    def __init__(self, latest_application=None):
        self.now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
        self.latest_application = latest_application
        self.committed = False
        self.refreshed = None

    def execute(self, _statement):
        return FakeScalarResult(self.now)

    def scalar(self, _statement):
        return self.latest_application

    def get(self, _model, _identifier):
        return None

    def commit(self):
        self.committed = True

    def refresh(self, instance):
        self.refreshed = instance


def make_candidate(status="active"):
    return SimpleNamespace(
        id=uuid4(),
        status=status,
        is_talent_pool=False,
        archived_at=None,
        rejected_at=None,
        reactivated_at=None,
        last_decision_at=None,
    )


def test_archive_candidate_keeps_candidate_and_marks_soft_archive(monkeypatch):
    events = []
    monkeypatch.setattr(candidate_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    candidate = make_candidate()
    db = FakeDb()

    result = candidate_service.archive_candidate(db, candidate)

    assert result is candidate
    assert candidate.status == "archived"
    assert candidate.archived_at == db.now
    assert candidate.last_decision_at == db.now
    assert db.committed is True
    assert db.refreshed is candidate
    assert events[0]["event_type"] == "candidate_archived"
    assert events[0]["metadata"]["soft_delete"] is True


def test_reject_candidate_marks_latest_application_and_talent_pool(monkeypatch):
    events = []
    monkeypatch.setattr(candidate_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    candidate = make_candidate()
    application = SimpleNamespace(candidate_id=candidate.id, status="submitted", current_stage="submitted")
    db = FakeDb(latest_application=application)

    result = candidate_service.reject_candidate(db, candidate)

    assert result is candidate
    assert candidate.status == "rejected"
    assert candidate.is_talent_pool is True
    assert candidate.rejected_at == db.now
    assert candidate.last_decision_at == db.now
    assert application.status == "rejected"
    assert application.current_stage == "rejected"
    assert events[0]["event_type"] == "candidate_rejected"


def test_reactivate_candidate_restores_active_status(monkeypatch):
    events = []
    monkeypatch.setattr(candidate_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    candidate = make_candidate(status="rejected")
    candidate.is_talent_pool = True
    db = FakeDb()

    result = candidate_service.reactivate_candidate(db, candidate)

    assert result is candidate
    assert candidate.status == "active"
    assert candidate.is_talent_pool is False
    assert candidate.reactivated_at == db.now
    assert candidate.last_decision_at == db.now
    assert events[0]["event_type"] == "candidate_reactivated"
    assert events[0]["metadata"]["previous_status"] == "rejected"
