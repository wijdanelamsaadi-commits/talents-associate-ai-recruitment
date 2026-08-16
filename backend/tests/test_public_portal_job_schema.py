from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.portal import PublicJobRead
from app.models import JobOffer
from app.services.portal_service import get_public_job


class FakePortalJobDb:
    def __init__(self, job: JobOffer | None):
        self.job = job

    def scalar(self, _statement):
        if self.job and self.job.status == "open":
            return self.job
        return None


def test_public_job_read_exposes_soft_skills() -> None:
    job = PublicJobRead(
        id=uuid4(),
        title="Développeur Python",
        company_name="Client test",
        location="Casablanca",
        contract_type="CDI",
        required_skills=["Python", "FastAPI"],
        preferred_skills=[],
        soft_skills=["Communication", "Autonomie"],
        required_experience_years=3,
        education_level="Bac+5",
        description="Mission principale",
        status="open",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert job.required_skills == ["Python", "FastAPI"]
    assert job.soft_skills == ["Communication", "Autonomie"]
    assert job.preferred_skills == []


def test_public_job_read_splits_semicolon_soft_skills() -> None:
    job = PublicJobRead(
        id=uuid4(),
        title="Responsable Marketing",
        company_name=None,
        location="Casablanca",
        contract_type="CDI",
        required_skills="Marketing; CRM",
        preferred_skills=[],
        soft_skills="Orientation client; Orientation business; Esprit analytique; ",
        required_experience_years=None,
        education_level=None,
        description="Mission principale",
        status="open",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert job.required_skills == ["Marketing", "CRM"]
    assert job.soft_skills == ["Orientation client", "Orientation business", "Esprit analytique"]


def test_public_job_read_defaults_missing_soft_skills_to_empty_list() -> None:
    job = PublicJobRead(
        id=uuid4(),
        title="Consultant RH",
        company_name=None,
        location=None,
        contract_type=None,
        required_skills=[],
        preferred_skills=[],
        soft_skills=None,
        required_experience_years=None,
        education_level=None,
        description="Mission principale",
        status="open",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert job.soft_skills == []


def test_public_job_detail_returns_active_open_offer_by_uuid() -> None:
    job_id = uuid4()
    job = JobOffer(
        id=job_id,
        title="Ingénieur Biomédical",
        description="Missions du poste",
        status="open",
        required_skills=[],
        preferred_skills=[],
        soft_skills=[],
        languages=[],
    )

    assert get_public_job(FakePortalJobDb(job), job_id) is job


def test_public_job_detail_hides_closed_offer() -> None:
    job_id = uuid4()
    job = JobOffer(
        id=job_id,
        title="Ingénieur Biomédical",
        description="Missions du poste",
        status="closed",
        required_skills=[],
        preferred_skills=[],
        soft_skills=[],
        languages=[],
    )

    assert get_public_job(FakePortalJobDb(job), job_id) is None
