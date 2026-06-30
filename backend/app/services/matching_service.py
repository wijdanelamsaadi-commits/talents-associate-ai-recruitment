import logging
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


logger = logging.getLogger(__name__)
SEMANTIC_SCORE_WEIGHT = 0.3
MATCHING_MODEL_NAME = "hybrid-heuristic-embedding-v1"
LIGHTWEIGHT_MODEL_NAME = "lightweight-title-match-v1"
MIN_VIVIER_MATCH_SCORE = 20


def match_candidate_to_job(db: Session, candidate_id: UUID, job_id: UUID, application_id: UUID | None = None) -> AIMatchingResult:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise MatchingError("Candidat introuvable.")

    job = db.get(JobOffer, job_id)
    if job is None:
        raise MatchingError("Offre d'emploi introuvable.")

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
        raise MatchingError("Le candidat doit avoir un CV analysé ou un poste actuel avant le matching IA.")

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
        title="Matching IA généré",
        description=f"Score de matching IA de {output.score}/100 généré pour {job.title}.",
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
        f"{len(matched_required)} compétence(s) obligatoire(s) correspondante(s) sur {len(required_skills)}"
        f" et {len(matched_preferred)} compétence(s) souhaitée(s). "
        f"Score expérience : {experience_score}/100, score formation/diplôme : {education_score}/100, "
        f"score langues : {language_score}/100. La pondération priorise les compétences, l'expérience "
        f"et le diplôme : compétences 40 %, expérience 30 %, diplôme 25 %, langues 5 %. "
        f"La similarité sémantique contribue à {semantic_score}/100 avec un poids de {round(SEMANTIC_SCORE_WEIGHT * 100)} %. "
        f"Recommandation : {recommendation}."
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
    recommendation_note = "Basé uniquement sur le poste actuel - aucun CV disponible."
    explanation = (
        f"Matching léger sans CV : similarité du poste {title_score}/100, "
        f"correspondance entreprise {company_score}/100, estimation expérience {experience_score}/100. "
        f"Pondération : poste 60 %, entreprise 10 %, expérience 30 %. Note : {recommendation_note} "
        f"Recommandation : {recommendation}."
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
    return {_strip_accents(str(item).strip().lower()) for item in items if str(item).strip()}


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
        return "Très bonne correspondance"
    if score >= 70:
        return "Bonne correspondance"
    if score >= 50:
        return "Correspondance moyenne"
    return "Correspondance faible"


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
    limit: int | None = 200,
) -> list[tuple[Candidate, float, bool, UUID | None, list[str], dict]]:
    statement = select(Candidate).where(Candidate.status != "archived")
    candidates = list(db.scalars(statement).all())
    parsed_cv_by_candidate_id = _get_latest_parsed_cv_map(db, [candidate.id for candidate in candidates])

    technical_skill_filters = _split_filter_values(technical_skills)
    soft_skill_filters = _split_filter_values(soft_skills)
    language_filters = _split_filter_values(langues)
    req_exp_years = _experience_level_to_years(experience_level)
    has_filters = any(
        [
            poste,
            secteur,
            technical_skill_filters,
            soft_skill_filters,
            req_exp_years is not None,
            education_level,
            contract_type,
            language_filters,
        ]
    )

    results = []
    for candidate in candidates:
        cv = parsed_cv_by_candidate_id.get(candidate.id)
        has_cv = cv is not None and cv.ai_output is not None
        parsed_payload = dict(cv.ai_output or {}) if has_cv else {}
        if has_cv:
            parsed_payload["__raw_text"] = cv.raw_text or ""
        score, debug_details = _score_vivier_candidate(
            candidate,
            parsed_payload,
            poste=poste,
            secteur=secteur,
            technical_skills=technical_skill_filters,
            soft_skills=soft_skill_filters,
            required_experience_years=req_exp_years,
            education_level=education_level,
            contract_type=contract_type,
            languages=language_filters,
        )
        matched_skills = list(debug_details.get("matched_technical_skills") or [])

        if score < MIN_VIVIER_MATCH_SCORE or (has_filters and score <= 0):
            logger.debug(
                "Vivier candidate rejected candidate_id=%s score=%s details=%s",
                candidate.id,
                score,
                debug_details,
            )
            continue

        logger.debug(
            "Vivier candidate selected candidate_id=%s score=%s details=%s",
            candidate.id,
            score,
            debug_details,
        )
        cv_file_id = cv.cv_file_id if has_cv else None
        results.append((candidate, score, has_cv, cv_file_id, matched_skills, debug_details))

    results.sort(
        key=lambda x: (
            x[1],
            x[0].created_at.timestamp() if x[0].created_at else 0.0,
        ),
        reverse=True,
    )
    if limit is None:
        return results
    return results[:limit]


def _get_latest_parsed_cv_map(db: Session, candidate_ids: list[UUID]) -> dict[UUID, ExtractedCVData]:
    if not candidate_ids:
        return {}

    statement = (
        select(ExtractedCVData)
        .where(ExtractedCVData.candidate_id.in_(candidate_ids))
        .where(ExtractedCVData.ai_output.is_not(None))
        .order_by(ExtractedCVData.candidate_id, ExtractedCVData.updated_at.desc())
    )
    latest_by_candidate_id: dict[UUID, ExtractedCVData] = {}
    for extracted_cv in db.scalars(statement).all():
        if not isinstance(extracted_cv, ExtractedCVData):
            continue
        latest_by_candidate_id.setdefault(extracted_cv.candidate_id, extracted_cv)
    return latest_by_candidate_id


def _candidate_sector_score(candidate: Candidate, cv: ExtractedCVData | None, secteur: str | None) -> int:
    if not secteur:
        return 100

    expected_sector = _strip_accents(secteur.lower())
    candidate_sector = _strip_accents(candidate.sector.lower()) if candidate.sector else ""
    if candidate_sector:
        return 100 if candidate_sector == expected_sector else 0

    if cv is not None and cv.ai_output:
        cv_sector = cv.ai_output.get("sector") or cv.ai_output.get("secteur") or ""
        if cv_sector:
            return 100 if _strip_accents(str(cv_sector).lower()) == expected_sector else 0

    return 0


def _score_vivier_candidate(
    candidate: Candidate,
    parsed_candidate: dict,
    *,
    poste: str | None,
    secteur: str | None,
    technical_skills: list[str],
    soft_skills: list[str],
    required_experience_years: int | None,
    education_level: str | None,
    contract_type: str | None,
    languages: list[str],
) -> tuple[float, dict]:
    criteria: list[tuple[str, float, int]] = []
    debug_details: dict[str, object] = {}

    candidate_skills = _candidate_skill_set(candidate, parsed_candidate, include_title_tokens=True)
    candidate_soft_skills = _normalize_set(_extract_list_values(parsed_candidate, "soft_skills", "softSkills", "soft_skills_detected"))
    candidate_languages = _extract_list_values(parsed_candidate, "languages", "langues", "language_codes")

    if poste:
        candidate_title = _string_value(candidate.current_title or parsed_candidate.get("current_title") or parsed_candidate.get("poste_actuel")) or ""
        poste_score = _role_match_score(candidate_title, _string_value(parsed_candidate.get("__raw_text")) or "", poste)
        criteria.append(("poste", 20, poste_score))
        debug_details["poste_score"] = poste_score

    if secteur:
        sector_score = _candidate_sector_score_from_payload(candidate, parsed_candidate, secteur, candidate_skills)
        debug_details["secteur_score"] = sector_score
        if sector_score == 0:
            debug_details["rejection_reason"] = "sector does not match"
            return 0.0, debug_details
        criteria.append(("secteur", 20, sector_score))

    if technical_skills:
        required_skill_set = _normalize_set(technical_skills)
        matched_skills = sorted(required_skill_set & candidate_skills)
        skill_score = _ratio_score(len(matched_skills), len(required_skill_set))
        debug_details["technical_skill_score"] = skill_score
        debug_details["matched_technical_skills"] = matched_skills
        if skill_score == 0:
            debug_details["rejection_reason"] = "no technical skill matched"
            return 0.0, debug_details
        criteria.append(("technical_skills", 35, skill_score))

    if soft_skills:
        required_soft_set = _normalize_set(soft_skills)
        matched_soft_skills = sorted(required_soft_set & candidate_soft_skills)
        soft_score = _ratio_score(len(matched_soft_skills), len(required_soft_set))
        debug_details["soft_skill_score"] = soft_score
        debug_details["matched_soft_skills"] = matched_soft_skills
        if soft_score == 0:
            debug_details["rejection_reason"] = "no soft skill matched"
            return 0.0, debug_details
        criteria.append(("soft_skills", 10, soft_score))

    if required_experience_years is not None:
        experience_score = _experience_score(
            _extract_list_values(parsed_candidate, "experience", "experiences", "experiences_detaillees"),
            parsed_candidate.get("total_experience_years")
            or parsed_candidate.get("experience_totale")
            or parsed_candidate.get("total_years_experience"),
            required_experience_years,
            contract_type,
        )
        criteria.append(("experience", 12, experience_score))
        debug_details["experience_score"] = experience_score

    if education_level:
        education_score = _education_score(
            _extract_list_values(parsed_candidate, "education", "diplomes", "diplôme"),
            _string_value(parsed_candidate.get("highest_degree") or parsed_candidate.get("diplome")),
            education_level,
        )
        criteria.append(("education", 13, education_score))
        debug_details["education_score"] = education_score

    if languages:
        language_score = _language_match_score(candidate_languages, languages)
        debug_details["language_score"] = language_score
        if language_score == 0:
            debug_details["rejection_reason"] = "no language matched"
            return 0.0, debug_details
        criteria.append(("languages", 10, language_score))

    if not criteria:
        debug_details["rejection_reason"] = "no search criteria"
        return 0.0, debug_details

    total_weight = sum(weight for _, weight, _ in criteria)
    score = round(sum(score * weight for _, weight, score in criteria) / total_weight, 2)
    debug_details["criteria"] = [name for name, _, _ in criteria]
    debug_details["final_score"] = score
    return score, debug_details


def _candidate_sector_score_from_payload(candidate: Candidate, parsed_candidate: dict, secteur: str, candidate_skills: set[str]) -> int:
    expected_sector = _strip_accents(secteur.lower())
    explicit_sector = _string_value(candidate.sector or parsed_candidate.get("sector") or parsed_candidate.get("secteur"))
    if explicit_sector:
        return 100 if _strip_accents(explicit_sector.lower()) == expected_sector else 0

    if expected_sector == "informatique":
        it_terms = {
            "developpeur", "developer", "dev", "software", "full", "stack", "backend", "frontend",
            "php", "python", "java", "javascript", "react", "node", "sql", "n8n", "ia", "ai",
            "data", "devops", "cloud", "informatique", "it",
        }
        title_tokens = _tokenize_title(candidate.current_title or "")
        if candidate_skills & it_terms or title_tokens & it_terms:
            return 70
    return 0


def _role_match_score(candidate_title: str, raw_text: str, requested_role: str) -> int:
    title_score = _title_keyword_score(candidate_title, requested_role, [])
    if title_score:
        return title_score

    requested_tokens = _expand_role_tokens(_tokenize_title(requested_role))
    if not requested_tokens:
        return 0

    profile_tokens = _expand_role_tokens(_tokenize_title(raw_text[:2500]))
    if not profile_tokens:
        return 0
    return _ratio_score(len(requested_tokens & profile_tokens), len(requested_tokens))


def _expand_role_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    developer_terms = {
        "developpeur",
        "developpeuse",
        "developpement",
        "developer",
        "software",
        "full",
        "stack",
        "fullstack",
        "backend",
        "frontend",
        "web",
        "engineer",
        "ingenieur",
    }
    has_developer_signal = bool(expanded & developer_terms) or any(
        "veloppeur" in token or "developp" in token for token in expanded
    )
    if has_developer_signal:
        expanded |= developer_terms
    return expanded


def _candidate_skill_set(candidate: Candidate, parsed_candidate: dict, *, include_title_tokens: bool = False) -> set[str]:
    skills = _extract_list_values(
        parsed_candidate,
        "skills",
        "competences",
        "compétences",
        "technical_skills",
        "competences_techniques",
    )
    normalized = _normalize_set(skills)
    raw_text = _string_value(parsed_candidate.get("__raw_text")) or ""
    if raw_text:
        normalized |= _extract_known_skill_tokens(raw_text)
    if include_title_tokens and candidate.current_title:
        normalized |= _tokenize_title(candidate.current_title)
    return normalized


def _extract_known_skill_tokens(text: str) -> set[str]:
    normalized_text = _strip_accents(text.lower())
    known_terms = {
        "n8n",
        "php",
        "ia",
        "ai",
        "python",
        "fastapi",
        "sql",
        "cloud",
        "devops",
        "data",
        "deep learning",
        "machine learning",
        "docker",
        "github actions",
        "laravel",
        "java",
        "javascript",
        "react",
        "node",
        "mysql",
        "oracle",
        "power bi",
    }
    found = set()
    for term in known_terms:
        if re.search(rf"\b{re.escape(term)}\b", normalized_text):
            found.add(term)
    return found


def _extract_list_values(payload: dict, *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    values.extend(str(v) for v in item.values() if v is not None)
                else:
                    values.append(str(item))
        elif isinstance(value, dict):
            values.extend(str(v) for v in value.values() if v is not None)
        else:
            values.extend(part.strip() for part in re.split(r"[;,]", str(value)) if part.strip())
    return values


def _split_filter_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[;,]", value) if part.strip()]


def _experience_level_to_years(value: str | None) -> int | None:
    normalized = _strip_accents(str(value or "").lower())
    if "0" in normalized and "1" in normalized:
        return 1
    if "2" in normalized and "5" in normalized:
        return 2
    if "5" in normalized and "10" in normalized:
        return 5
    if "10" in normalized:
        return 10
    return None


def _language_match_score(candidate_languages: list[str], required_languages: list[str]) -> int:
    candidate_set = _normalize_set(candidate_languages)
    required_set = _normalize_set(required_languages)
    if not required_set:
        return 100
    return _ratio_score(len(candidate_set & required_set), len(required_set))


def _string_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

