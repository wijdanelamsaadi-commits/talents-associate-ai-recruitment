import json

from app.services import llm_cv_parser_service


def _complete_llm_payload(**overrides):
    payload = {
        "prenom": "Sara",
        "nom": "Amrani",
        "first_name": "Sara",
        "last_name": "Amrani",
        "email": "sara@example.com",
        "phone": "+212600000000",
        "telephone": "+212600000000",
        "ville": "Casablanca",
        "location": "Casablanca",
        "linkedin_url": None,
        "linkedin": None,
        "current_company": "Acme",
        "entreprise_actuelle": "Acme",
        "current_title": "Developpeuse Python",
        "poste_actuel": "Developpeuse Python",
        "total_experience_years": 3,
        "experience_totale": 3,
        "experience": ["Developpeuse Python - Acme"],
        "detailed_experience": [
            {
                "company": "Acme",
                "entreprise": "Acme",
                "title": "Developpeuse Python",
                "poste": "Developpeuse Python",
                "start_date": "2021",
                "date_debut": "2021",
                "end_date": "2024",
                "date_fin": "2024",
                "location": "Casablanca",
                "description": "APIs et automatisation.",
            }
        ],
        "experiences_detaillees": [],
        "education": [
            {
                "degree": "Master",
                "diplome": "Master",
                "school": "Universite",
                "etablissement": "Universite",
                "obtained_date": "2020",
                "date_obtention": "2020",
                "description": None,
            }
        ],
        "diplomes": [],
        "skills": ["Python", "SQL", "FastAPI"],
        "competences": ["Python", "SQL", "FastAPI"],
        "technical_skills": ["Python", "SQL", "FastAPI"],
        "competences_techniques": ["Python", "SQL", "FastAPI"],
        "functional_skills": [],
        "competences_fonctionnelles": [],
        "languages": ["Francais", "Anglais"],
        "langues": ["Francais", "Anglais"],
        "certifications": [],
        "soft_skills": ["Communication"],
        "gender": None,
        "sexe": None,
        "parser_confidence": 0.91,
    }
    payload.update(overrides)
    return payload


def test_openai_parser_uses_gpt_41_mini_json_schema_and_validates_payload(monkeypatch):
    captured = {}
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_ENABLED", True)
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm_cv_parser_service.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_MODEL", None)
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_MODEL_NAME", "gpt-4.1-mini")

    def fake_open_url_with_retries(request, timeout_seconds, max_retries):
        request_payload = json.loads(request.data.decode("utf-8"))
        captured["model"] = request_payload["model"]
        captured["response_format"] = request_payload["response_format"]
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(_complete_llm_payload()),
                    }
                }
            ]
        }

    monkeypatch.setattr(llm_cv_parser_service, "_open_url_with_retries", fake_open_url_with_retries)

    parsed = llm_cv_parser_service.parse_cv_text_configurable("Sara Amrani\nPython SQL FastAPI")

    assert captured["model"] == "gpt-4.1-mini"
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["strict"] is True
    assert parsed.data["parser_used"] == "llm"
    assert parsed.data["first_name"] == "Sara"
    assert parsed.data["skills"] == ["Python", "SQL", "FastAPI"]
    assert parsed.confidence_score == 0.91


def test_openai_parser_falls_back_to_heuristic_on_validation_error(monkeypatch):
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_ENABLED", True)
    monkeypatch.setattr(llm_cv_parser_service.settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm_cv_parser_service.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        llm_cv_parser_service,
        "_open_url_with_retries",
        lambda *_args: {"choices": [{"message": {"content": json.dumps({"unexpected": "field"})}}]},
    )

    parsed = llm_cv_parser_service.parse_cv_text_configurable("Jean Dupont\njean@example.com\nPython")

    assert parsed.data["parser_used"] == "heuristic"
    assert parsed.data["email"] == "jean@example.com"
