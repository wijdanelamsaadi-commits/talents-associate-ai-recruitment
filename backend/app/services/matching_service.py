import re
import unicodedata
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import AIMatchingResult, Candidate, ExtractedCVData, JobOffer
from app.schemas import MatchingOutput
from app.services.embedding_service import cosine_similarity
from app.services.timeline_service import create_timeline_event


class MatchingError(ValueError):
    pass


SEMANTIC_SCORE_WEIGHT = 0.3
MATCHING_MODEL_NAME = "hybrid-heuristic-embedding-v1"
LIGHTWEIGHT_MODEL_NAME = "lightweight-title-match-v1"


def match_candidate_to_job(db: Session, candidate_id: UUID, job_id: UUID, application_id: UUID | None = None) -> AIMatchingResult:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise MatchingError("Candidate not found.")

    job = db.get(JobOffer, job_id)
    if job is None:
        raise MatchingError("Job offer not found.")

    extracted_data = _get_latest_parsed_cv(db, candidate_id)
    has_parsed_cv = extracted_data is not None and extracted_data.ai_output

    if has_parsed_cv:
        output = calculate_match(extracted_data.ai_output, job, extracted_data.embedding)
        model_name = MATCHING_MODEL_NAME
        used_embedding = output.used_semantic_embedding
    elif candidate.current_title:
        output = calculate_lightweight_match(candidate, job)
        model_name = LIGHTWEIGHT_MODEL_NAME
        used_embedding = False
    else:
        raise MatchingError("Candidate must have parsed CV data or a current job title before matching.")

    existing_result = _get_existing_generated_result(db, candidate_id, job_id)

    result = existing_result or AIMatchingResult(
        candidate_id=candidate_id,
        job_offer_id=job_id,
        model_name=model_name,
    )
    result.model_name = model_name
    if application_id is not None:
        result.application_id = application_id
    result.score = Decimal(output.score) / Decimal(100)
    result.detailed_scores = {
        "skill_score": output.skill_score,
        "experience_score": output.experience_score,
        "education_score": output.education_score,
        "language_score": output.language_score,
        "semantic_score": output.semantic_score,
    }
    result.matched_skills = output.matched_skills
    result.missing_skills = output.missing_skills
    result.explanation = output.explanation
    result.recommendation = output.recommendation
    result.embedding_version = settings.EMBEDDING_MODEL_NAME if used_embedding else None
    result.status = "generated"

    db.add(result)
    db.flush()
    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="ai_match_generated",
        title="AI matching generated",
        description=f"Generated a {output.score}/100 match score for {job.title}.",
        metadata={
            "matching_result_id": str(result.id),
            "job_offer_id": str(job_id),
            "score": output.score,
            "recommendation": output.recommendation,
        },
    )
    db.commit()
    db.refresh(result)
    return result


def calculate_match(parsed_candidate: dict, job: JobOffer, candidate_embedding: list[float] | None = None) -> MatchingOutput:
    candidate_skills = _normalize_set(parsed_candidate.get("skills", []))
    required_skills = _normalize_set(job.required_skills or [])
    preferred_skills = _normalize_set(job.preferred_skills or [])

    matched_required = sorted(required_skills & candidate_skills)
    matched_preferred = sorted(preferred_skills & candidate_skills)
    missing_required = sorted(required_skills - candidate_skills)

    required_score = _ratio_score(len(matched_required), len(required_skills))
    preferred_score = _ratio_score(len(matched_preferred), len(preferred_skills)) if preferred_skills else 100
    skill_score = round((required_score * 0.75) + (preferred_score * 0.25))

    experience_score = _experience_score(
        parsed_candidate.get("experience", []),
        parsed_candidate.get("total_experience_years") or parsed_candidate.get("experience_totale"),
        job.required_experience_years,
        getattr(job, "contract_type", None),
    )
    education_score = _education_score(
        parsed_candidate.get("education", []),
        parsed_candidate.get("highest_degree"),
        job.education_level,
    )
    language_score = _language_score(parsed_candidate.get("languages", []), job.description)

    heuristic_score = round(
        (skill_score * 0.40)
        + (experience_score * 0.30)
        + (education_score * 0.25)
        + (language_score * 0.05)
    )
    used_semantic_embedding = bool(candidate_embedding and job.embedding)
    if used_semantic_embedding:
        semantic_score = round(_clamp(cosine_similarity(candidate_embedding or [], job.embedding or []), 0.0, 1.0) * 100)
    else:
        semantic_score = heuristic_score

    total_score = round((heuristic_score * (1 - SEMANTIC_SCORE_WEIGHT)) + (semantic_score * SEMANTIC_SCORE_WEIGHT))
    recommendation = _recommendation(total_score)

    explanation = (
        f"Matched {len(matched_required)} of {len(required_skills)} required skills"
        f" and {len(matched_preferred)} preferred skills. "
        f"Experience score is {experience_score}/100, diploma/education score is {education_score}/100, "
        f"and language score is {language_score}/100. Weights prioritize competences, experience, "
        f"and diplome: skills 40%, experience 30%, diploma 25%, languages 5%. "
        f"Semantic similarity contributes {semantic_score}/100 with a {round(SEMANTIC_SCORE_WEIGHT * 100)}% blend weight. "
        f"Recommendation: {recommendation}."
    )

    return MatchingOutput(
        score=total_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        language_score=language_score,
        semantic_score=semantic_score,
        used_semantic_embedding=used_semantic_embedding,
        matched_skills=sorted(_display_items(matched_required + matched_preferred)),
        missing_skills=sorted(_display_items(missing_required)),
        explanation=explanation,
        recommendation=recommendation,
    )


def calculate_lightweight_match(candidate: Candidate, job: JobOffer) -> MatchingOutput:
    title_score = _title_keyword_score(candidate.current_title or "", job.title, job.required_skills or [])
    company_score = _company_match_score(candidate.current_company, getattr(job, "company_name", None))
    experience_score = 100 if _is_internship_contract(getattr(job, "contract_type", None)) else 50
    total_score = round((title_score * 0.60) + (company_score * 0.10) + (experience_score * 0.30))
    total_score = max(0, min(total_score, 100))
    recommendation = _recommendation(total_score)
    recommendation_note = "Based on job title only - no CV available."
    explanation = (
        f"Lightweight matching (no CV): title similarity is {title_score}/100, "
        f"company match is {company_score}/100, experience estimate is {experience_score}/100. "
        f"Weights: title 60%, company 10%, experience 30%. Note: {recommendation_note} "
        f"Recommendation: {recommendation}."
    )
    return MatchingOutput(
        score=total_score,
        skill_score=title_score,
        experience_score=experience_score,
        education_score=0,
        language_score=0,
        semantic_score=0,
        used_semantic_embedding=False,
        matched_skills=[],
        missing_skills=[],
        explanation=explanation,
        recommendation=f"{recommendation} - {recommendation_note}",
    )


def _title_keyword_score(candidate_title: str, job_title: str, required_skills: list[str]) -> int:
    candidate_tokens = _tokenize_title(candidate_title)
    if not candidate_tokens:
        return 0
    target_tokens = _tokenize_title(job_title)
    for skill in required_skills:
        target_tokens |= _tokenize_title(skill)
    if not target_tokens:
        return 100
    return _ratio_score(len(candidate_tokens & target_tokens), len(target_tokens))


def _company_match_score(candidate_company: str | None, job_company: str | None) -> int:
    if not candidate_company or not job_company:
        return 0
    candidate_value = _strip_accents(candidate_company.strip().lower())
    job_value = _strip_accents(job_company.strip().lower())
    if candidate_value == job_value:
        return 100
    if candidate_value in job_value or job_value in candidate_value:
        return 75
    return 0


def _tokenize_title(text: str) -> set[str]:
    noise_words = {
        "de", "du", "des", "le", "la", "les", "et", "en", "a", "au", "aux",
        "the", "and", "or", "of", "in", "at", "for", "to", "an",
    }
    normalized = _strip_accents(text.lower())
    tokens = set(re.split(r"[\s\-/|,;.()]+", normalized))
    return {token for token in tokens if token and token not in noise_words and len(token) > 1}


def list_matching_results(db: Session, skip: int = 0, limit: int = 100) -> list[AIMatchingResult]:
    statement = (
        select(AIMatchingResult)
        .options(joinedload(AIMatchingResult.candidate), joinedload(AIMatchingResult.job_offer))
        .order_by(AIMatchingResult.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def list_candidate_matching_results(db: Session, candidate_id: UUID) -> list[AIMatchingResult]:
    statement = (
        select(AIMatchingResult)
        .where(AIMatchingResult.candidate_id == candidate_id)
        .order_by(AIMatchingResult.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_matching_result(db: Session, matching_result_id: UUID) -> AIMatchingResult | None:
    return db.get(AIMatchingResult, matching_result_id)


def delete_matching_result(db: Session, matching_result: AIMatchingResult) -> None:
    db.delete(matching_result)
    db.commit()


def _get_latest_parsed_cv(db: Session, candidate_id: UUID) -> ExtractedCVData | None:
    statement = (
        select(ExtractedCVData)
        .where(ExtractedCVData.candidate_id == candidate_id)
        .where(ExtractedCVData.ai_output.is_not(None))
        .order_by(ExtractedCVData.updated_at.desc())
    )
    return db.scalar(statement)


def _get_existing_generated_result(db: Session, candidate_id: UUID, job_id: UUID) -> AIMatchingResult | None:
    statement = (
        select(AIMatchingResult)
        .where(AIMatchingResult.candidate_id == candidate_id)
        .where(AIMatchingResult.job_offer_id == job_id)
        .where(AIMatchingResult.status == "generated")
    )
    return db.scalar(statement)


def list_active_job_offers(db: Session) -> list[JobOffer]:
    statement = select(JobOffer).where(JobOffer.status == "open").order_by(JobOffer.created_at.desc())
    return list(db.scalars(statement).all())


def auto_match_candidate(
    db: Session,
    candidate_id: UUID,
    selected_job_id: UUID | None = None,
    application_id: UUID | None = None,
) -> list[AIMatchingResult]:
    job_ids = [selected_job_id] if selected_job_id is not None else [job.id for job in list_active_job_offers(db)]
    results = []
    for job_id in job_ids:
        if job_id is None:
            continue
        results.append(match_candidate_to_job(db, candidate_id=candidate_id, job_id=job_id, application_id=application_id))
    return results


def _normalize_set(items: list[str]) -> set[str]:
    return {str(item).strip().lower() for item in items if str(item).strip()}


def _display_items(items: list[str]) -> set[str]:
    return {item.upper() if item in {"sql", "html", "css"} else item.title() for item in items}


def _ratio_score(matched_count: int, total_count: int) -> int:
    if total_count == 0:
        return 100
    return round((matched_count / total_count) * 100)


def _experience_score(
    experience_items: list[str],
    total_years_experience: float | int | str | None,
    required_years: int | None,
    contract_type: str | None = None,
) -> int:
    if _is_internship_contract(contract_type):
        return 100
    if required_years is None or required_years == 0:
        return 100
    candidate_years = _coerce_positive_years(total_years_experience)
    if candidate_years is None:
        candidate_years = _estimate_experience_years_from_dates(experience_items)
    if candidate_years <= 0:
        return 0
    return min(round((candidate_years / required_years) * 100), 100)


def _is_internship_contract(contract_type: str | None) -> bool:
    normalized = _strip_accents(str(contract_type or "").lower())
    return any(term in normalized for term in ("stage", "internship", "intern", "stagiaire"))


def _coerce_positive_years(value: float | int | str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        years = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return years if years > 0 else None


def _estimate_experience_years_from_dates(experience_items: list[str]) -> float:
    total_months = sum(_estimate_months_from_experience_item(str(item)) for item in experience_items or [])
    if total_months:
        return round(total_months / 12, 2)
    text = " ".join(experience_items).lower()
    explicit_years = [int(value) for value in re.findall(r"(\d+)\+?\s*(?:years|year|ans|an)", text)]
    return max(explicit_years) if explicit_years else max(len(experience_items), 0)


def _estimate_months_from_experience_item(text: str) -> float:
    date_points = _extract_experience_date_points(text)
    if len(date_points) < 2:
        return 0.0
    start = date_points[0]
    end = date_points[1]
    if end["present"]:
        today = date.today()
        end = {"year": today.year, "month": today.month, "precision": "month", "present": False}
    start_year = start["year"]
    end_year = end["year"]
    if start_year is None or end_year is None or end_year < start_year:
        return 0.0
    if start["precision"] == "year" and end["precision"] == "year":
        return max((end_year - start_year) * 12, 1)
    start_month = start["month"] or 1
    end_month = end["month"] or 12
    months = ((end_year - start_year) * 12) + (end_month - start_month) + 1
    return max(months, 1)


def _extract_experience_date_points(text: str) -> list[dict]:
    normalized = _strip_accents(text.lower()).replace("–", "-").replace("—", "-")
    month_names = "|".join(sorted(MONTHS_BY_NAME, key=len, reverse=True))
    pattern = re.compile(
        rf"(?P<month>{month_names})\.?(?:\s+|\s*-\s*)?(?P<month_year>\d{{4}})|(?P<year>\d{{4}})|(?P<present>present|current|now|en cours|aujourd hui|aujourdhui)",
        flags=re.IGNORECASE,
    )
    points = []
    for match in pattern.finditer(normalized):
        if match.group("present"):
            points.append({"year": None, "month": None, "precision": "present", "present": True})
        elif match.group("month") and match.group("month_year"):
            month_name = _strip_accents(match.group("month").lower()).rstrip(".")
            points.append({"year": int(match.group("month_year")), "month": MONTHS_BY_NAME[month_name], "precision": "month", "present": False})
        elif match.group("year"):
            points.append({"year": int(match.group("year")), "month": None, "precision": "year", "present": False})
    return points[:2]


MONTHS_BY_NAME = {
    "janvier": 1, "jan": 1, "january": 1,
    "fevrier": 2, "fev": 2, "february": 2, "feb": 2,
    "mars": 3, "mar": 3, "march": 3,
    "avril": 4, "avr": 4, "april": 4, "apr": 4,
    "mai": 5, "may": 5,
    "juin": 6, "june": 6, "jun": 6,
    "juillet": 7, "juil": 7, "july": 7, "jul": 7,
    "aout": 8, "august": 8, "aug": 8,
    "septembre": 9, "sept": 9, "september": 9, "sep": 9,
    "octobre": 10, "october": 10, "oct": 10,
    "novembre": 11, "november": 11, "nov": 11,
    "decembre": 12, "december": 12, "dec": 12,
}


def _education_score(education_items: list[str], highest_degree: str | None, education_level: str | None) -> int:
    if not education_level:
        return 100
    required_degree = _normalize_degree_level(education_level)
    candidate_degree = _normalize_degree_level(highest_degree)
    degree_rank = {"high_school": 1, "associate": 2, "bachelor": 3, "master": 4, "phd": 5}
    if required_degree and candidate_degree:
        return 100 if degree_rank[candidate_degree] >= degree_rank[required_degree] else 40
    education_text = " ".join(education_items).lower()
    required = education_level.lower().strip()
    keywords = {
        "phd": {"phd", "doctorate", "doctor", "doctorat"},
        "master": {"master", "msc", "ma", "engineer", "engineering", "ingenieur", "ingénieur", "bac+4", "bac+5"},
        "bachelor": {"bachelor", "licence", "bs", "ba", "bac+3"},
        "associate": {"associate", "bac+2", "dut", "deug", "bts"},
        "high_school": {"high school", "baccalaureate", "baccalaureat", "bac"},
        "degree": {"degree", "diploma", "master", "bachelor", "licence", "engineer", "ingenieur", "ingénieur"},
    }
    expected_terms = keywords.get(required_degree or required, {required})
    return 100 if any(term in education_text for term in expected_terms) else 40 if education_items or highest_degree else 0


def _normalize_degree_level(value: str | None) -> str | None:
    if not value:
        return None
    normalized = _strip_accents(value.lower().strip()).replace("-", "_")
    if any(term in normalized for term in ("phd", "doctor", "doctorat")):
        return "phd"
    if any(term in normalized for term in ("master", "msc", "bac+4", "bac+5", "engineer", "engineering", "ingenieur")):
        return "master"
    if any(term in normalized for term in ("bachelor", "licence", "bac+3")):
        return "bachelor"
    if any(term in normalized for term in ("associate", "bac+2", "dut", "deug", "bts")):
        return "associate"
    if any(term in normalized for term in ("high_school", "high school", "baccalaureate", "baccalaureat")) or normalized == "bac":
        return "high_school"
    return None


def _strip_accents(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


def _language_score(candidate_languages: list[str], job_description: str | None) -> int:
    job_text = (job_description or "").lower()
    required_languages = [language for language in ("english", "french", "arabic", "spanish") if language in job_text]
    if not required_languages:
        return 100
    candidate_language_set = _normalize_set(candidate_languages)
    matched = sum(1 for language in required_languages if language in candidate_language_set)
    return _ratio_score(matched, len(required_languages))


def _recommendation(score: int) -> str:
    if score >= 85:
        return "strong_match"
    if score >= 70:
        return "good_match"
    if score >= 50:
        return "average_match"
    return "weak_match"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def search_candidates_vivier(
    db: Session,
    poste: str | None = None,
    secteur: str | None = None,
    experience_level: str | None = None,
    education_level: str | None = None,
    contract_type: str | None = None,
    technical_skills: str | None = None,
    soft_skills: str | None = None,
    langues: str | None = None,
) -> list[tuple[Candidate, float, bool, UUID | None]]:
    # 1. Query candidates not archived
    statement = select(Candidate).where(Candidate.status != "archived")
    candidates = list(db.scalars(statement).all())

    # 2. Build virtual job offer if any criteria are provided
    req_skills = []
    if technical_skills:
        req_skills.extend([s.strip() for s in technical_skills.split(";") if s.strip()])
    if soft_skills:
        req_skills.extend([s.strip() for s in soft_skills.split(";") if s.strip()])

    req_exp_years = None
    if experience_level == "0–1 an":
        req_exp_years = 1
    elif experience_level == "2–5 ans":
        req_exp_years = 2
    elif experience_level == "5–10 ans":
        req_exp_years = 5
    elif experience_level == "10 ans et plus":
        req_exp_years = 10

    virtual_job = JobOffer(
        title=poste or "",
        required_skills=req_skills,
        required_experience_years=req_exp_years,
        education_level=education_level,
        contract_type=contract_type,
        description=langues or "",
    )

    results = []

    for candidate in candidates:
        cv = _get_latest_parsed_cv(db, candidate.id)
        has_cv = cv is not None and cv.ai_output is not None

        # Hard filter for Secteur if provided
        if secteur:
            secteur_matched = False
            # Check candidate model sector
            if candidate.sector and _strip_accents(candidate.sector.lower()) == _strip_accents(secteur.lower()):
                secteur_matched = True
            # Check CV parsed sector
            elif has_cv:
                cv_sector = cv.ai_output.get("sector") or cv.ai_output.get("secteur") or ""
                if cv_sector and _strip_accents(str(cv_sector).lower()) == _strip_accents(secteur.lower()):
                    secteur_matched = True
            if not secteur_matched:
                continue

        # Score candidate
        if has_cv:
            match_output = calculate_match(cv.ai_output, virtual_job, cv.embedding)
            score = float(match_output.score)
            cv_file_id = cv.cv_file_id
        else:
            # Lightweight match: poste + secteur + entreprise
            title_score = 0
            if poste:
                title_score = _title_keyword_score(candidate.current_title or "", poste, req_skills)
            elif candidate.current_title:
                title_score = 100

            sector_score = 100
            if secteur and candidate.sector:
                sector_score = (
                    100
                    if _strip_accents(candidate.sector.lower()) == _strip_accents(secteur.lower())
                    else 0
                )

            company_score = 100 if candidate.current_company else 0

            if not poste and not secteur:
                score = 100.0
            else:
                score = float(round((title_score * 0.50) + (sector_score * 0.30) + (company_score * 0.20)))
            cv_file_id = None

        results.append((candidate, score, has_cv, cv_file_id))

    # Sort results: highest score first, then by Candidate.created_at desc
    results.sort(
        key=lambda x: (
            x[1],
            x[0].created_at.timestamp() if x[0].created_at else 0.0
        ),
        reverse=True
    )
    return results

