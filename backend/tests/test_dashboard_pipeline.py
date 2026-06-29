from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.candidate import CandidateCreate
from app.schemas.dashboard import PIPELINE_STAGES
from app.services import dashboard_service


class PipelineFakeDb:
    def __init__(self, jobs, applications, candidates):
        self.jobs = jobs
        self.applications = applications
        self.candidates = candidates

    def scalars(self, statement):
        sql = str(statement)
        if "FROM job_offers" in sql:
            return SimpleNamespace(all=lambda: self.jobs)
        if "FROM applications" in sql:
            if len(self.jobs) == 1:
                job_id = self.jobs[0].id
                filtered = [application for application in self.applications if application.job_offer_id == job_id]
            else:
                filtered = self.applications
            return SimpleNamespace(all=lambda: filtered)
        if "FROM candidates" in sql:
            return SimpleNamespace(all=lambda: self.candidates)
        return SimpleNamespace(all=lambda: [])

    def scalar(self, statement):
        return 0

    def execute(self, statement):
        return SimpleNamespace(all=lambda: [])


@pytest.fixture
def sample_pipeline_data():
    job_id = uuid4()
    candidate_received = uuid4()
    candidate_preselected = uuid4()
    candidate_rejected = uuid4()

    job = SimpleNamespace(
        id=job_id,
        title="Développeur Python",
        company_name="Acme Corp",
        location="Paris",
        status="open",
        opened_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    applications = [
        SimpleNamespace(id=uuid4(), job_offer_id=job_id, candidate_id=candidate_received),
        SimpleNamespace(id=uuid4(), job_offer_id=job_id, candidate_id=candidate_preselected),
        SimpleNamespace(id=uuid4(), job_offer_id=job_id, candidate_id=candidate_rejected),
    ]
    candidates = [
        SimpleNamespace(id=candidate_received, status="new"),
        SimpleNamespace(id=candidate_preselected, status="preselectionne"),
        SimpleNamespace(id=candidate_rejected, status="refus_candidat"),
    ]
    return job, applications, candidates


def test_pipeline_stage_constants_are_french():
    labels = [label for _, label in PIPELINE_STAGES]
    assert labels == [
        "Candidatures reçues",
        "Non sélectionnées",
        "Présélectionnées",
        "Entretien cabinet",
        "Entretien client",
        "Profil validé",
        "Refus candidat",
    ]


def test_get_dashboard_pipeline_returns_job_pipeline(sample_pipeline_data):
    job, applications, candidates = sample_pipeline_data
    fake_db = PipelineFakeDb(jobs=[job], applications=applications, candidates=candidates)

    result = dashboard_service.get_dashboard_pipeline(fake_db)

    assert len(result.pipelines) == 1
    pipeline = result.pipelines[0]
    assert pipeline.title == "Développeur Python"
    stage_counts = {stage.stage: stage.count for stage in pipeline.stages}
    assert stage_counts["recu"] == 3
    assert stage_counts["preselectionne"] == 1
    assert stage_counts["refus_candidat"] == 1


def test_get_dashboard_pipeline_filters_by_client(sample_pipeline_data):
    job, applications, candidates = sample_pipeline_data
    fake_db = PipelineFakeDb(jobs=[job], applications=applications, candidates=candidates)

    result = dashboard_service.get_dashboard_pipeline(fake_db, client="Autre client")

    assert result.pipelines == []


def test_candidate_status_pattern_accepts_pipeline_statuses():
    candidate = CandidateCreate(
        first_name="Jean",
        last_name="Dupont",
        status="entretien_cabinet",
    )
    assert candidate.status == "entretien_cabinet"
