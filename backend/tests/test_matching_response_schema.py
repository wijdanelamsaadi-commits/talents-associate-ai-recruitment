from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.matching import MatchingResultRead


def test_matching_response_exposes_semantic_fields():
    result = SimpleNamespace(
        id=uuid4(),
        candidate_id=uuid4(),
        job_offer_id=uuid4(),
        score=Decimal("0.82"),
        detailed_scores={"semantic_score": 91},
        matched_skills=["React"],
        missing_skills=["Docker"],
        explanation="Hybrid matching result.",
        recommendation="good_match",
        status="generated",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        candidate_name="Sara Candidate",
        job_title="Developpeur Full Stack",
        semantic_score=91,
        used_semantic_embedding=True,
    )

    payload = MatchingResultRead.model_validate(result)

    assert payload.score == 82.0
    assert payload.semantic_score == 91
    assert payload.used_semantic_embedding is True
