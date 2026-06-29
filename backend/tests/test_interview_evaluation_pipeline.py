from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.evaluation import EvaluationCreate
from app.schemas.interview import InterviewCreate, InterviewStatusUpdate
from app.services import evaluation_service, interview_service, pipeline_service


class PipelineFakeDb:
    def __init__(self):
        self.candidate_id = uuid4()
        self.job_offer_id = uuid4()
        self.application_id = uuid4()
        self.interview_id = uuid4()
        self.candidate = SimpleNamespace(
            id=self.candidate_id,
            status="new",
            is_talent_pool=False,
        )
        self.application = SimpleNamespace(
            id=self.application_id,
            candidate_id=self.candidate_id,
            job_offer_id=self.job_offer_id,
            status="submitted",
            current_stage="recu",
        )
        self.interview = SimpleNamespace(
            id=self.interview_id,
            application_id=self.application_id,
            candidate_id=self.candidate_id,
            interview_type="entretien_cabinet",
            status="entretien_cabinet",
            scheduled_start_at=datetime.now(timezone.utc),
            scheduled_end_at=None,
            meeting_url=None,
            location=None,
            notes=None,
            scheduled_by_user_id=None,
            interviewer_user_id=None,
        )
        self.job = SimpleNamespace(id=self.job_offer_id, title="Développeur")
        self.committed = False
        self.added = []

    def get(self, model, identifier):
        name = getattr(model, "__name__", str(model))
        if name == "Candidate" and identifier == self.candidate_id:
            return self.candidate
        if name == "Application" and identifier == self.application_id:
            return self.application
        if name == "Interview" and identifier == self.interview_id:
            return self.interview
        if name == "JobOffer" and identifier == self.job_offer_id:
            return self.job
        return None

    def scalar(self, statement):
        sql = str(statement)
        if "applications" in sql and "candidate_id" in sql and "job_offer_id" in sql:
            return self.application
        if "applications" in sql and "candidate_id" in sql:
            return self.application
        return None

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: [])

    def add(self, item):
        self.added.append(item)

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def refresh(self, item):
        pass


def test_apply_pipeline_stage_updates_candidate_status():
    fake_db = PipelineFakeDb()
    pipeline_service.apply_pipeline_stage(
        fake_db,
        fake_db.candidate_id,
        "profil_valide",
        job_offer_id=fake_db.job_offer_id,
    )
    assert fake_db.candidate.status == "profil_valide"
    assert fake_db.application.current_stage == "profil_valide"
    assert fake_db.application.status == "shortlisted"


def test_update_interview_status_syncs_candidate_pipeline(monkeypatch):
    fake_db = PipelineFakeDb()
    applied_stages = []

    def capture_apply(db, candidate_id, stage, job_offer_id=None):
        applied_stages.append((candidate_id, stage, job_offer_id))

    monkeypatch.setattr(interview_service, "apply_pipeline_stage", capture_apply)
    interview_service.update_interview_status(fake_db, fake_db.interview, "entretien_client")

    assert fake_db.interview.status == "entretien_client"
    assert applied_stages == [(fake_db.candidate_id, "entretien_client", fake_db.job_offer_id)]


def test_create_evaluation_syncs_candidate_pipeline(monkeypatch):
    fake_db = PipelineFakeDb()
    applied_stages = []

    def capture_apply(db, candidate_id, stage, job_offer_id=None):
        applied_stages.append((candidate_id, stage, job_offer_id))

    monkeypatch.setattr(evaluation_service, "apply_pipeline_stage", capture_apply)
    monkeypatch.setattr(evaluation_service, "create_timeline_event", lambda *args, **kwargs: None)

    evaluation_in = EvaluationCreate(
        interview_id=fake_db.interview_id,
        rating=4,
        technical_score=4,
        soft_skills_score=5,
        motivation_score=4,
        recommendation="profil_valide",
        comments="Excellent candidat",
    )
    evaluation_service.create_evaluation(fake_db, evaluation_in)

    assert applied_stages == [(fake_db.candidate_id, "profil_valide", fake_db.job_offer_id)]
    assert fake_db.interview.status == "profil_valide"


def test_interview_status_schema_accepts_pipeline_values():
    status = InterviewStatusUpdate(status="non_selectionne")
    assert status.status == "non_selectionne"
