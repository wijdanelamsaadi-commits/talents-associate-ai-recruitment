from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.data.job_reference_titles import JOB_REFERENCE_TITLES
from app.main import app
from app.models import Candidate, ExtractedCVData, JobReferenceTitle
from app.services.cv_service import update_candidate_profile_from_parsed_cv
from app.services.job_profile_service import (
    add_job_reference_title,
    classify_candidate_profile,
    enrich_parsed_data_with_profile,
    get_job_reference_titles,
    normalize_job_title,
)


client = TestClient(app)


class FakeProfileDb:
    def __init__(self, candidate: Candidate):
        self.candidate = candidate
        self.committed = False
        self.added = []

    def get(self, model, identifier):
        if model is Candidate and self.candidate.id == identifier:
            return self.candidate
        return None

    def scalar(self, statement):
        return None

    def add(self, item):
        self.added.append(item)

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def refresh(self, item):
        pass


class FakeReferenceScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeReferenceDb:
    def __init__(self, references=None):
        self.references = references or []
        self.committed = False

    def scalars(self, statement):
        selected_keys = [getattr(column, "key", "") for column in getattr(statement, "selected_columns", [])]
        if selected_keys == ["normalized_title"]:
            return FakeReferenceScalars([reference.normalized_title for reference in self.references])
        return FakeReferenceScalars(sorted(self.references, key=lambda reference: reference.title))

    def scalar(self, statement):
        params = statement.compile().params
        expected_normalized = next(iter(params.values()), None)
        for reference in self.references:
            if reference.normalized_title == expected_normalized:
                return reference
        return None

    def add(self, item):
        self.references.append(item)

    def add_all(self, items):
        self.references.extend(items)

    def flush(self):
        pass

    def commit(self):
        self.committed = True


def test_reference_contains_expected_250_titles():
    titles = get_job_reference_titles()
    assert len(titles) == 250
    assert len({title.casefold() for title in titles}) == len(titles)
    assert "Data Analyst" in titles
    assert "DevOps Engineer" in titles
    assert "Comptable" in titles


def test_data_analyst_cv_is_classified_from_cv_content():
    result = classify_candidate_profile(
        {
            "skills": ["Power BI", "SQL", "reporting", "dashboards"],
            "experience": ["Analyse de données, tableaux de bord KPI et business intelligence"],
            "education": ["Master statistiques"],
        },
        "Création de dashboards Power BI, reporting et analyse de données pour la direction.",
    )

    assert result.title == "Data Analyst"
    assert result.title in JOB_REFERENCE_TITLES
    assert result.confidence > 0


def test_devops_cv_is_classified_from_cv_content():
    result = classify_candidate_profile(
        {
            "skills": ["Docker", "Kubernetes", "CI/CD", "Cloud"],
            "experience": ["Automatisation de déploiement avec GitHub Actions et Terraform"],
        },
        "DevOps, cloud, CI/CD, Docker, Kubernetes et automatisation déploiement.",
    )

    assert result.title == "DevOps Engineer"
    assert result.title in JOB_REFERENCE_TITLES
    assert result.confidence > 0


def test_accounting_cv_is_classified_from_cv_content():
    result = classify_candidate_profile(
        {
            "skills": ["Comptabilité", "TVA", "Sage", "rapprochement bancaire"],
            "experience": ["Saisie des écritures comptables, bilan et facturation fournisseurs"],
        },
        "Comptable chargé du bilan, de la TVA et du rapprochement bancaire.",
    )

    assert result.title in {"Comptable", "Responsable Comptable"}
    assert result.title in JOB_REFERENCE_TITLES
    assert result.confidence > 0


def test_enrich_parsed_data_keeps_current_title_and_adds_identified_profile():
    payload = {
        "current_title": "Consultant BI Senior",
        "poste_actuel": "Consultant BI Senior",
        "skills": ["Power BI", "SQL"],
        "experience": ["reporting et dashboards"],
    }

    classification = enrich_parsed_data_with_profile(payload, "analyse de données power bi")

    assert classification.title == "Data Analyst"
    assert payload["current_title"] == "Consultant BI Senior"
    assert payload["poste_actuel"] == "Consultant BI Senior"
    assert payload["identified_job_profile"] == "Data Analyst"
    assert payload["job_profile_confidence"] > 0
    assert payload["job_profile_matched_terms"]


def test_cv_profile_update_never_overwrites_current_title_with_identified_profile():
    candidate_id = uuid4()
    candidate = Candidate(
        id=candidate_id,
        first_name="Test",
        last_name="Candidate",
        email="test.profile@example.com",
        current_title="Consultant BI Senior",
        source="cv_upload",
        status="active",
        is_talent_pool=False,
        consent_given=False,
    )
    extracted_data = ExtractedCVData(
        id=uuid4(),
        candidate_id=candidate_id,
        cv_file_id=uuid4(),
        raw_text="Consultant BI Senior Power BI SQL reporting dashboard analyse de données",
        ai_output={
            "current_title": "Consultant BI Senior",
            "poste_actuel": "Consultant BI Senior",
            "skills": ["Power BI", "SQL", "reporting"],
            "experience": ["dashboards et analyse de données"],
        },
        parsing_status="parsed",
        status="approved",
    )
    db = FakeProfileDb(candidate)

    update_candidate_profile_from_parsed_cv(db, extracted_data)

    assert candidate.current_title == "Consultant BI Senior"
    assert candidate.identified_job_profile == "Data Analyst"
    assert candidate.job_profile_confidence is not None
    assert candidate.job_profile_matched_terms
    assert extracted_data.ai_output["identified_job_profile"] == "Data Analyst"


def test_cv_reparse_recalculates_identified_profile_separately_from_current_title():
    candidate_id = uuid4()
    candidate = Candidate(
        id=candidate_id,
        first_name="Test",
        last_name="Reparse",
        email="test.reparse@example.com",
        current_title="Consultant Technique",
        source="cv_upload",
        status="active",
        is_talent_pool=False,
        consent_given=False,
    )
    extracted_data = ExtractedCVData(
        id=uuid4(),
        candidate_id=candidate_id,
        cv_file_id=uuid4(),
        raw_text="DevOps Docker Kubernetes CI/CD cloud automatisation déploiement",
        ai_output={
            "current_title": "Consultant Technique",
            "poste_actuel": "Consultant Technique",
            "skills": ["Docker", "Kubernetes", "CI/CD", "Cloud"],
            "experience": ["automatisation de déploiement"],
        },
        parsing_status="parsed",
        status="approved",
    )

    update_candidate_profile_from_parsed_cv(FakeProfileDb(candidate), extracted_data)

    assert candidate.current_title == "Consultant Technique"
    assert candidate.identified_job_profile == "DevOps Engineer"


def test_job_reference_endpoint_requires_recruiter_and_returns_titles():
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    db = FakeReferenceDb()
    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get("/api/references/job-titles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 250
        assert "Data Analyst" in data
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_custom_job_reference_is_added_without_case_duplicate():
    db = FakeReferenceDb()

    first = add_job_reference_title(db, "Ingénieur Biomédical", source="job_offer")
    second = add_job_reference_title(db, " ingénieur biomédical ", source="job_offer")
    third = add_job_reference_title(db, "INGÉNIEUR BIOMÉDICAL", source="job_offer")

    assert first is not None
    assert second is first
    assert third is first
    assert len(db.references) == 1
    assert db.references[0].title == "Ingénieur Biomédical"
    assert db.references[0].normalized_title == normalize_job_title("ingénieur biomédical")


def test_shared_job_reference_list_includes_custom_title():
    db = FakeReferenceDb(
        references=[
            JobReferenceTitle(
                title="Ingénieur Biomédical",
                normalized_title=normalize_job_title("Ingénieur Biomédical"),
                source="job_offer",
            )
        ]
    )

    titles = get_job_reference_titles(db)

    assert "Ingénieur Biomédical" in titles
