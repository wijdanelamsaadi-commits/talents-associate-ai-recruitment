import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models import Candidate, LinkedInCSVImport
from app.services import candidate_service
from app.services.import_service import _extract_linkedin_candidate_fields, import_linkedin_csv


class FakeUploadFile:
    filename = "linkedin13082026.csv"

    def __init__(self, content: str):
        self._content = content.encode("utf-8")

    async def read(self) -> bytes:
        return self._content


class FakeLinkedInImportDb:
    def __init__(self):
        self.candidates: list[Candidate] = []
        self.import_records: list[LinkedInCSVImport] = []
        self.timeline_events = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, item):
        if getattr(item, "id", None) is None:
            item.id = uuid4()
        if isinstance(item, Candidate) and item not in self.candidates:
            self.candidates.append(item)
        elif isinstance(item, LinkedInCSVImport) and item not in self.import_records:
            self.import_records.append(item)
        else:
            self.timeline_events.append(item)

    def flush(self):
        pass

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, item):
        pass

    def scalar(self, statement):
        statement_text = str(statement)
        for candidate in self.candidates:
            if "candidates.email" in statement_text and "email_1" in statement_text:
                expected = statement.compile().params.get("email_1")
                if candidate.email == expected:
                    return candidate
            if "candidates.linkedin_url" in statement_text and "linkedin_url_1" in statement_text:
                expected = statement.compile().params.get("linkedin_url_1")
                if candidate.linkedin_url == expected:
                    return candidate
            if "candidates.current_company" in statement_text:
                params = statement.compile().params
                if (
                    candidate.first_name.lower() == params.get("lower_1")
                    and candidate.last_name.lower() == params.get("lower_2")
                    and (candidate.current_company or "").lower() == params.get("lower_3")
                ):
                    return candidate
        return None


ADNANE_CSV = """First Name;Last Name;LinkedIn URL;Email;Company;Position;Connected On
Adnane;Ayoub;https://www.linkedin.com/in/adnane-ayoub-8a02bb207;;Arab Open University;Finance Officer;27-juil-25
"""

SHIFTED_URL_CSV = """First Name;Last Name;URL;Email Address;Company;Position;Connected On
OUAKOUR OUSSAMA PMI ATP Instructor; PMP; IA;;PSM, PMO-CP,MS PROJECT,ITIL 4, NLP Coach;https://www.linkedin.com/in/ouakour-oussama-pmi-atp-instructor-pmp%C2%AE-ia%C2%AE-psm%C2%AE-pmo-cp%C2%AE-ms-project%C2%AE-itil-4%C2%AE-nlp-coach%C2%AE-a1208957;02-oct-18
"""


def test_linkedin_import_persists_candidate_without_email_using_linkedin_url():
    db = FakeLinkedInImportDb()

    import_record = asyncio.run(import_linkedin_csv(db, FakeUploadFile(ADNANE_CSV)))

    assert import_record.imported_count == 1
    assert import_record.updated_count == 0
    assert import_record.skipped_count == 0
    assert len(db.candidates) == 1
    candidate = db.candidates[0]
    assert candidate.first_name == "Adnane"
    assert candidate.last_name == "Ayoub"
    assert candidate.email is None
    assert candidate.linkedin_url == "https://www.linkedin.com/in/adnane-ayoub-8a02bb207"
    assert candidate.current_company == "Arab Open University"
    assert candidate.current_title == "Finance Officer"
    assert candidate.source == "linkedin_csv"
    assert db.commits >= 2


def test_linkedin_import_second_same_url_updates_without_duplicate_candidate():
    db = FakeLinkedInImportDb()

    first_record = asyncio.run(import_linkedin_csv(db, FakeUploadFile(ADNANE_CSV)))
    second_record = asyncio.run(import_linkedin_csv(db, FakeUploadFile(ADNANE_CSV)))

    assert first_record.imported_count == 1
    assert second_record.imported_count == 0
    assert second_record.updated_count == 1
    assert len(db.candidates) == 1


def test_candidate_search_query_covers_full_name_title_company_and_linkedin_url():
    statement = candidate_service._apply_candidate_filter(select(Candidate), search_query="Adnane Ayoub")
    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "concat" in compiled
    assert "first_name" in compiled
    assert "last_name" in compiled
    assert "current_title" in compiled
    assert "current_company" in compiled
    assert "linkedin_url" in compiled

    ordered_statement = select(Candidate).order_by(candidate_service._candidate_search_order("Adnane").asc())
    ordered_compiled = str(ordered_statement.compile(dialect=postgresql.dialect()))
    assert "CASE" in ordered_compiled


def test_linkedin_import_recovers_profile_url_shifted_into_position_column():
    db = FakeLinkedInImportDb()

    import_record = asyncio.run(import_linkedin_csv(db, FakeUploadFile(SHIFTED_URL_CSV)))

    assert import_record.imported_count == 1
    assert import_record.skipped_count == 0
    assert len(db.candidates) == 1
    candidate = db.candidates[0]
    assert candidate.linkedin_url == (
        "https://www.linkedin.com/in/ouakour-oussama-pmi-atp-instructor-pmp%C2%AE-ia%C2%AE-psm%C2%AE-pmo-cp%C2%AE-ms-project%C2%AE-itil-4%C2%AE-nlp-coach%C2%AE-a1208957"
    )
    assert candidate.current_title is None
    assert candidate.current_company == "PSM, PMO-CP,MS PROJECT,ITIL 4, NLP Coach"


def test_linkedin_row_values_are_limited_to_candidate_column_lengths():
    row = {
        "first name": "A" * 120,
        "last name": "B" * 120,
        "url": "https://www.linkedin.com/in/example",
        "company": "C" * 180,
        "position": "D" * 180,
    }

    parsed = _extract_linkedin_candidate_fields(row)

    assert len(parsed["first_name"]) == 100
    assert len(parsed["last_name"]) == 100
    assert len(parsed["current_company"]) == 150
    assert len(parsed["current_title"]) == 150
