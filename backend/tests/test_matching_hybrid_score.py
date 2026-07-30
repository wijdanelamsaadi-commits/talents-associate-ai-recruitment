from types import SimpleNamespace

from app.services.matching_service import calculate_match
from app.services.matching_service import _education_score


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


def test_education_score_accepts_string_value():
    score = _education_score(["Master Computer Science"], None, "master")

    assert 0 <= score <= 100
    assert score == 100


def test_education_score_accepts_openai_dictionary_value():
    education = [
        {
            "degree": "Cycle Ingénieur - Cybersécurité et Confiance Numérique",
            "school": "ENSA",
            "diplome": "Cycle Ingénieur",
            "etablissement": "ENSA",
            "obtained_date": "2024 - présent",
            "date_obtention": "2024 - présent",
            "description": None,
        }
    ]

    score = _education_score(education, None, "Bac+5")

    assert 0 <= score <= 100
    assert score == 100


def test_education_score_accepts_multiple_openai_education_items():
    education = [
        {"degree": "Cycle préparatoire intégré", "school": "ENSA"},
        {"degree": "Cycle Ingénieur - Cybersécurité", "school": "ENSA", "obtained_date": "2024 - présent"},
    ]

    score = _education_score(education, None, "Bac+5")

    assert 0 <= score <= 100
    assert score == 100


def test_education_score_accepts_partial_dictionary_fields():
    education = [{"school": "Université", "date_obtention": "2025"}]

    score = _education_score(education, None, "Bac+5")

    assert 0 <= score <= 100
    assert score == 40


def test_education_score_accepts_empty_and_none_values():
    assert _education_score([], None, "Bac+5") == 0
    assert _education_score(None, None, "Bac+5") == 0


def test_calculate_match_accepts_openai_education_objects_without_exception():
    parsed_candidate = {
        "skills": ["Python", "SOC", "Wazuh"],
        "experience": [],
        "education": [
            {
                "degree": "Cycle Ingénieur - Cybersécurité et Confiance Numérique",
                "school": "ENSA",
                "obtained_date": "2024 - présent",
            }
        ],
        "languages": ["French"],
    }
    job = SimpleNamespace(
        required_skills=["Python", "SOC"],
        preferred_skills=[],
        required_experience_years=0,
        education_level="Bac+5",
        description="French-speaking SOC role",
        contract_type="Stage",
        embedding=[1.0, 0.0],
    )

    output = calculate_match(parsed_candidate, job, candidate_embedding=[1.0, 0.0])

    assert 0 <= output.score <= 100
    assert output.education_score == 100
