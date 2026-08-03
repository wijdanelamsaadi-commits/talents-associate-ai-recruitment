from app.services.cv_name_cleaner import (
    is_invalid_candidate_name,
    sanitize_or_fallback_name,
    extract_name_from_raw_text,
)


def test_is_invalid_candidate_name_catches_production_examples():
    # 1. first_name="berbères", last_name="Langues"
    assert is_invalid_candidate_name("berbères", "Langues") is True

    # 2. first_name="de conduire", last_name="Permis"
    assert is_invalid_candidate_name("de conduire", "Permis") is True

    # 3. first_name="baccalauréat gestion", last_name="Diplôme"
    assert is_invalid_candidate_name("baccalauréat gestion", "Diplôme") is True

    # 4. first_name="en sciences économiques", last_name="Baccalauréat"
    assert is_invalid_candidate_name("en sciences économiques", "Baccalauréat") is True

    # 5. first_name="professionnelles", last_name="Expériences"
    assert is_invalid_candidate_name("professionnelles", "Expériences") is True


def test_is_invalid_candidate_name_allows_valid_names():
    assert is_invalid_candidate_name("Wijdane", "Elamsaadi") is False
    assert is_invalid_candidate_name("Marwa", "Bouziani") is False
    assert is_invalid_candidate_name("Youssef", "Amrani") is False
    assert is_invalid_candidate_name("Jean-Pierre", "Dupont") is False


def test_sanitize_or_fallback_name_recovers_real_name():
    raw_text = """
MARWA BOUZIANI
Ingénieure Qualité et Amélioration Continue
Email: marwa.bouziani@email.com
Téléphone: 0612345678

Expériences professionnelles
- Ingénieure Qualité chez Safran (2021 - 2023)

Diplômes & Formation
- Master en Management de Qualité
"""
    fn, ln = sanitize_or_fallback_name(
        first_name="berbères",
        last_name="Langues",
        raw_text=raw_text,
        email="marwa.bouziani@email.com",
    )
    assert fn == "Marwa"
    assert ln == "Bouziani"
