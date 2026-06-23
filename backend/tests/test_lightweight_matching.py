from types import SimpleNamespace

from app.services.matching_service import calculate_lightweight_match


def test_lightweight_matching_uses_title_and_company():
    candidate = SimpleNamespace(current_title="Developpeur Full Stack", current_company="HPS")
    job = SimpleNamespace(
        title="Developpeur Full Stack",
        required_skills=["Python", "React"],
        company_name="HPS",
        contract_type="CDI",
    )

    result = calculate_lightweight_match(candidate, job)

    assert result.score > 0
    assert result.used_semantic_embedding is False
    assert "no CV available" in result.recommendation


def test_lightweight_matching_no_title_overlap_is_weak():
    candidate = SimpleNamespace(current_title="Responsable agence", current_company="Attijariwafa bank")
    job = SimpleNamespace(
        title="dev full stack",
        required_skills=["Python", "React", "Node.js"],
        company_name="HPS",
        contract_type="CDI",
    )

    result = calculate_lightweight_match(candidate, job)

    assert result.score < 30
    assert result.recommendation.startswith("weak_match")
