from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.main import app
from app.models import Candidate, ExtractedCVData
from app.schemas import CandidateCreate, CandidateUpdate, VivierSearchResult
from app.services import matching_service

client = TestClient(app)


class FakeDb:
    def __init__(self, items=None):
        self.items = items or []
        self.added = []
        self.committed = False
        self.refreshed = None

    def add(self, item):
        if getattr(item, "id", None) is None:
            item.id = uuid4()
        self.added.append(item)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def refresh(self, item):
        self.refreshed = item

    def get(self, model, identifier):
        for item in self.items:
            if getattr(item, "id", None) == identifier and isinstance(item, model):
                return item
        return None

    def scalar(self, statement):
        # Simplistic parser for _get_latest_parsed_cv
        # statement is typically a select(ExtractedCVData).where(...)
        # We find CVs matching the candidate
        candidate_id = None
        for clause in getattr(statement, "_where_criteria", []):
            if "candidate_id" in str(clause):
                # Try to extract UUID
                for word in str(clause).split():
                    if "-" in word:
                        candidate_id = word.strip("'")
        
        cvs = [item for item in self.items if isinstance(item, ExtractedCVData)]
        if cvs:
            return cvs[0]
        return None

    def scalars(self, statement):
        # Returns all candidates
        candidates = [item for item in self.items if isinstance(item, Candidate)]
        return SimpleNamespace(all=lambda: candidates)


def test_candidate_sector_schema():
    # Verify candidate schemas include sector
    data = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "sector": "Aéronautique",
    }
    schema = CandidateCreate(**data)
    assert schema.sector == "Aéronautique"

    update_schema = CandidateUpdate(sector="Banque")
    assert update_schema.sector == "Banque"


def test_vivier_search_service_logic():
    # Setup mock candidates
    c1 = Candidate(
        id=uuid4(),
        first_name="Alice",
        last_name="Martin",
        email="alice@example.com",
        sector="Banque",
        current_title="Python Developer",
        status="active",
        source="manual",
        is_talent_pool=False,
        consent_given=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    c2 = Candidate(
        id=uuid4(),
        first_name="Bob",
        last_name="Dupond",
        email="bob@example.com",
        sector="Assurance",
        current_title="React Dev",
        status="active",
        source="manual",
        is_talent_pool=False,
        consent_given=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db = FakeDb(items=[c1, c2])

    # Search sector="Banque"
    results = matching_service.search_candidates_vivier(db, secteur="Banque")
    assert len(results) == 1
    assert results[0][0].first_name == "Alice"

    # Search title="React"
    results_title = matching_service.search_candidates_vivier(db, poste="React")
    assert len(results_title) == 1
    assert results_title[0][0].first_name == "Bob"

    # Search skill="n8n" should not return unrelated profiles with no skill match
    c3 = Candidate(
        id=uuid4(),
        first_name="Karim",
        last_name="Agence",
        email="karim@example.com",
        sector=None,
        current_title="Responsable agence",
        status="active",
        source="manual",
        is_talent_pool=False,
        consent_given=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    c4 = Candidate(
        id=uuid4(),
        first_name="Nora",
        last_name="Automation",
        email="nora@example.com",
        sector=None,
        current_title="n8n Automation Developer",
        status="active",
        source="manual",
        is_talent_pool=False,
        consent_given=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db = FakeDb(items=[c3, c4])
    skill_results = matching_service.search_candidates_vivier(db, secteur="Informatique", technical_skills="n8n")
    assert len(skill_results) == 1
    assert skill_results[0][0].first_name == "Nora"
    assert skill_results[0][1] > 0


def test_vivier_search_route():
    recruiter = SimpleNamespace(id=uuid4(), role="recruiter", status="active")
    c1 = Candidate(
        id=uuid4(),
        first_name="Charlie",
        last_name="Gomez",
        email="charlie@example.com",
        sector="Telecom",
        current_title="Network Engineer",
        status="active",
        source="manual",
        is_talent_pool=False,
        consent_given=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    fake_db = FakeDb(items=[c1])

    app.dependency_overrides[get_current_user] = lambda: recruiter
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.get("/api/matching/search?secteur=Telecom")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["candidate"]["first_name"] == "Charlie"
        assert data[0]["candidate"]["sector"] == "Telecom"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
