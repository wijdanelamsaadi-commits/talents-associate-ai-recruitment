from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.models import Candidate
from app.services import application_service


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeDecisionDb:
    def __init__(self, candidate):
        self.candidate = candidate
        self.now = datetime(2026, 6, 23, 11, 0, tzinfo=timezone.utc)
        self.committed = False
        self.refreshed = None

    def execute(self, _statement):
        return FakeScalarResult(self.now)

    def get(self, model, _identifier):
        if model is Candidate:
            return self.candidate
        return None

    def commit(self):
        self.committed = True

    def refresh(self, instance):
        self.refreshed = instance


def make_candidate(status="active"):
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        first_name="Sara",
        last_name="Test",
        email="sara@example.com",
        phone=None,
        location="Casablanca",
        linkedin_url=None,
        portfolio_url=None,
        current_title=None,
        current_company=None,
        gender=None,
        source="manual",
        status=status,
        is_talent_pool=False,
        archived_at=None,
        rejected_at=None,
        reactivated_at=None,
        last_decision_at=None,
        consent_given=True,
        owner_user_id=None,
        created_at=now,
        updated_at=now,
    )


def make_application(candidate_id):
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        candidate_id=candidate_id,
        job_offer_id=uuid4(),
        cv_file_id=None,
        source="candidate_portal",
        status="submitted",
        current_stage="application_submitted",
        applied_at=now,
        created_at=now,
        updated_at=now,
    )


def test_accept_application_marks_hired_and_adds_timeline(monkeypatch):
    events = []
    monkeypatch.setattr(application_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    monkeypatch.setattr(application_service, "notify_application_accepted", lambda *args, **kwargs: None)
    candidate = make_candidate()
    application = make_application(candidate.id)
    db = FakeDecisionDb(candidate)

    result = application_service.accept_application(db, application)

    assert result.status == "hired"
    assert result.current_stage == "hired"
    assert candidate.status == "hired"
    assert candidate.is_talent_pool is False
    assert candidate.last_decision_at == db.now
    assert events[0]["event_type"] == "application_accepted"
    assert db.committed is True


def test_reject_application_keeps_candidate_in_talent_pool(monkeypatch):
    events = []
    monkeypatch.setattr(application_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    monkeypatch.setattr(application_service, "notify_application_rejected", lambda *args, **kwargs: None)
    candidate = make_candidate()
    application = make_application(candidate.id)
    db = FakeDecisionDb(candidate)

    result = application_service.reject_application(db, application)

    assert result.status == "rejected"
    assert result.current_stage == "rejected"
    assert candidate.status == "rejected"
    assert candidate.is_talent_pool is True
    assert candidate.rejected_at == db.now
    assert candidate.last_decision_at == db.now
    assert events[0]["event_type"] == "application_rejected"


def test_reactivate_application_restores_candidate_active(monkeypatch):
    events = []
    monkeypatch.setattr(application_service, "create_timeline_event", lambda *args, **kwargs: events.append(kwargs))
    candidate = make_candidate(status="rejected")
    candidate.is_talent_pool = True
    application = make_application(candidate.id)
    application.status = "rejected"
    application.current_stage = "rejected"
    db = FakeDecisionDb(candidate)

    result = application_service.reactivate_application(db, application)

    assert result.status == "shortlisted"
    assert result.current_stage == "shortlisted"
    assert candidate.status == "active"
    assert candidate.is_talent_pool is False
    assert candidate.reactivated_at == db.now
    assert events[0]["event_type"] == "application_reactivated"


def test_candidate_history_contains_internal_rh_sections():
    candidate = make_candidate()
    job = SimpleNamespace(id=uuid4(), title="Développeur Full Stack", company_name="Talents Associate")
    application = make_application(candidate.id)
    application.job_offer = job
    application.job_offer_id = job.id
    application.matching_results = []
    application.interviews = []
    application.evaluations = []
    match = SimpleNamespace(
        id=uuid4(),
        application_id=application.id,
        candidate_id=candidate.id,
        job_offer_id=job.id,
        job_offer=job,
        score=Decimal("0.8200"),
        semantic_score=74,
        used_semantic_embedding=True,
        recommendation="strong_match",
        explanation="Bon alignement.",
        matched_skills=["React"],
        missing_skills=[],
        detailed_scores={"semantic_score": 74},
        created_at=datetime(2026, 6, 23, tzinfo=timezone.utc),
    )
    interview = SimpleNamespace(
        id=uuid4(),
        application_id=application.id,
        interview_type="hr",
        status="scheduled",
        scheduled_start_at=datetime(2026, 6, 24, tzinfo=timezone.utc),
        scheduled_end_at=None,
        location=None,
        meeting_url=None,
        notes=None,
    )
    evaluation = SimpleNamespace(
        id=uuid4(),
        application_id=application.id,
        interview_id=interview.id,
        evaluator_name="RH",
        rating=4,
        technical_score=80,
        soft_skills_score=90,
        motivation_score=85,
        communication_score=88,
        culture_fit_score=80,
        global_score=Decimal("84.00"),
        recommendation="yes",
        strengths="Communication",
        weaknesses=None,
        comments=None,
        notes=None,
        submitted_at=datetime(2026, 6, 24, tzinfo=timezone.utc),
    )
    application.matching_results = [match]
    application.interviews = [interview]
    application.evaluations = [evaluation]
    event = SimpleNamespace(
        id=uuid4(),
        event_type="application_reactivated",
        title="Application reactivated",
        description="History kept.",
        event_metadata={"application_id": str(application.id)},
        occurred_at=datetime(2026, 6, 25, tzinfo=timezone.utc),
        created_at=datetime(2026, 6, 25, tzinfo=timezone.utc),
    )

    class FakeHistoryDb:
        def __init__(self):
            self.scalar_sets = [
                [],
                [],
                [application],
                [match],
                [interview],
                [evaluation],
                [event],
            ]

        def get(self, _model, _identifier):
            return candidate

        def scalars(self, _statement):
            return FakeScalars(self.scalar_sets.pop(0))

    history = application_service.get_candidate_history(FakeHistoryDb(), candidate.id)

    assert history is not None
    assert history.candidate.id == candidate.id
    assert history.applications[0].matching_results[0].score == Decimal("0.8200")
    assert history.matching_results[0].semantic_score == 74
    assert history.interviews[0].interview_type == "hr"
    assert history.evaluations[0].recommendation == "yes"
    assert history.timeline_events[0].event_type == "application_reactivated"
