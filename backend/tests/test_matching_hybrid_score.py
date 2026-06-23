from types import SimpleNamespace

from app.services.matching_service import calculate_match


def test_calculate_match_blends_heuristic_and_semantic_scores():
    parsed_candidate = {
        "skills": ["Python", "SQL"],
        "experience": ["Software Engineer 3 years"],
        "total_experience_years": 3,
        "education": ["Master Computer Science"],
        "languages": ["French"],
    }
    job = SimpleNamespace(
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        required_experience_years=3,
        education_level="master",
        description="French-speaking backend role",
        contract_type="CDI",
        embedding=[1.0, 0.0],
    )

    output = calculate_match(parsed_candidate, job, candidate_embedding=[1.0, 0.0])

    assert output.semantic_score == 100
    assert output.used_semantic_embedding is True
    assert output.score >= 90


def test_calculate_match_without_embedding_keeps_heuristic_score():
    parsed_candidate = {
        "skills": ["Python", "SQL"],
        "experience": ["Software Engineer 3 years"],
        "total_experience_years": 3,
        "education": ["Master Computer Science"],
        "languages": ["French"],
    }
    job = SimpleNamespace(
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        required_experience_years=3,
        education_level="master",
        description="French-speaking backend role",
        contract_type="CDI",
        embedding=None,
    )

    output = calculate_match(parsed_candidate, job, candidate_embedding=[1.0, 0.0])

    assert output.used_semantic_embedding is False
    assert output.semantic_score == output.score


def test_stage_contract_requires_no_experience():
    parsed_candidate = {
        "skills": [],
        "experience": [],
        "total_experience_years": None,
        "education": [],
        "languages": [],
    }
    job = SimpleNamespace(
        required_skills=[],
        preferred_skills=[],
        required_experience_years=3,
        education_level=None,
        description="",
        contract_type="stage",
        embedding=None,
    )

    output = calculate_match(parsed_candidate, job)

    assert output.experience_score == 100
