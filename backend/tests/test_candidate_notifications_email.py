from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models import CandidateNotification, EmailLog
from app.services import application_service, email_service, notification_service


class FakeNowResult:
    def __init__(self, now):
        self.now = now

    def scalar_one(self):
        return self.now


class FakeDb:
    def __init__(self):
        self.now = datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc)
        self.added = []
        self.committed = False
        self.refreshed = None
        self.objects = {}

    def add(self, item):
        self.added.append(item)

    def flush(self):
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()

    def execute(self, _statement):
        return FakeNowResult(self.now)

    def commit(self):
        self.committed = True

    def refresh(self, item):
        self.refreshed = item

    def get(self, model, identifier):
        return self.objects.get((model, identifier))


def make_candidate():
    return SimpleNamespace(
        id=uuid4(),
        first_name="Sara",
        last_name="Candidate",
        email="sara.candidate@example.com",
        status="active",
        is_talent_pool=False,
        rejected_at=None,
        reactivated_at=None,
        last_decision_at=None,
    )


def make_application(candidate_id):
    return SimpleNamespace(id=uuid4(), candidate_id=candidate_id, job_offer_id=uuid4(), status="submitted", current_stage="submitted")


def make_job(job_id):
    return SimpleNamespace(id=job_id, title="Développeur Full Stack")


def test_acceptation_creates_notification_and_skipped_email_log(monkeypatch):
    monkeypatch.setattr(application_service, "create_timeline_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_service.settings, "EMAIL_ENABLED", False)
    candidate = make_candidate()
    application = make_application(candidate.id)
    job = make_job(application.job_offer_id)
    db = FakeDb()
    from app.models import Candidate, JobOffer

    db.objects[(Candidate, candidate.id)] = candidate
    db.objects[(JobOffer, job.id)] = job

    application_service.accept_application(db, application)

    notifications = [item for item in db.added if isinstance(item, CandidateNotification)]
    email_logs = [item for item in db.added if isinstance(item, EmailLog)]
    assert notifications[0].type == "accepted"
    assert notifications[0].candidate_id == candidate.id
    assert email_logs[0].status == "skipped"
    assert email_logs[0].candidate_id == candidate.id
    assert application.status == "hired"


def test_refus_creates_notification_and_email_log_without_internal_details(monkeypatch):
    monkeypatch.setattr(application_service, "create_timeline_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_service.settings, "EMAIL_ENABLED", False)
    candidate = make_candidate()
    application = make_application(candidate.id)
    job = make_job(application.job_offer_id)
    db = FakeDb()
    from app.models import Candidate, JobOffer

    db.objects[(Candidate, candidate.id)] = candidate
    db.objects[(JobOffer, job.id)] = job

    application_service.reject_application(db, application)

    notifications = [item for item in db.added if isinstance(item, CandidateNotification)]
    email_logs = [item for item in db.added if isinstance(item, EmailLog)]
    assert notifications[0].type == "rejected"
    assert "score" not in notifications[0].message.lower()
    assert "matching" not in notifications[0].message.lower()
    assert "score" not in email_logs[0].body.lower()
    assert "matching" not in email_logs[0].body.lower()
    assert email_logs[0].status == "skipped"
    assert candidate.is_talent_pool is True


def test_interview_invitation_creates_notification_and_skipped_email_log(monkeypatch):
    monkeypatch.setattr(email_service.settings, "EMAIL_ENABLED", False)
    candidate = make_candidate()
    application = make_application(candidate.id)
    job = make_job(application.job_offer_id)
    interview = SimpleNamespace(
        id=uuid4(),
        scheduled_start_at=datetime(2026, 6, 24, 10, 30, tzinfo=timezone.utc),
        meeting_url="https://meet.example.com/test",
        location=None,
    )
    db = FakeDb()

    notification_service.notify_interview_invitation(db, candidate=candidate, application=application, interview=interview, job=job)

    notifications = [item for item in db.added if isinstance(item, CandidateNotification)]
    email_logs = [item for item in db.added if isinstance(item, EmailLog)]
    assert notifications[0].type == "interview_invitation"
    assert notifications[0].interview_id == interview.id
    assert email_logs[0].status == "skipped"
    assert "Convocation entretien" in email_logs[0].subject


def test_candidate_can_mark_only_own_notification_read():
    owner_id = uuid4()
    other_id = uuid4()
    notification = CandidateNotification(
        id=uuid4(),
        candidate_id=owner_id,
        type="accepted",
        title="Candidature acceptée",
        message="Votre candidature a été retenue.",
        is_read=False,
    )
    db = FakeDb()
    db.objects[(CandidateNotification, notification.id)] = notification

    assert notification_service.mark_candidate_notification_read(db, notification_id=notification.id, candidate_id=other_id) is None
    own = notification_service.mark_candidate_notification_read(db, notification_id=notification.id, candidate_id=owner_id)

    assert own is notification
    assert notification.is_read is True
    assert notification.read_at == db.now
    assert db.committed is True


def test_email_disabled_never_raises_and_creates_skipped_log(monkeypatch):
    monkeypatch.setattr(email_service.settings, "EMAIL_ENABLED", False)
    db = FakeDb()

    log = email_service.send_candidate_email(
        db,
        to_email="candidate@example.com",
        subject="Test",
        body="Bonjour",
        candidate_id=uuid4(),
        application_id=uuid4(),
    )

    assert log.status == "skipped"
    assert "disabled" in log.error_message
