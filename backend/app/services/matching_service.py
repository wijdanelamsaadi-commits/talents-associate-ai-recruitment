import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIMatchingResult, Candidate, ExtractedCVData, JobOffer
from app.schemas import MatchingOutput
from app.services.timeline_service import create_timeline_event


class MatchingError(ValueError):
    pass


def match_candidate_to_job(db: Session, candidate_id: UUID, job_id: UUID, application_id: UUID | None = None) -> AIMatchingResult:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise MatchingError("Candidate not found.")

    job = db.get(JobOffer, job_id)
    if job is None:
        raise MatchingError("Job offer not found.")

    extracted_data = _get_latest_parsed_cv(db, candidate_id)
    if extracted_data is None or not extracted_data.ai_output:
        raise MatchingError("Candidate must have parsed CV data before matching.")

    output = calculate_match(extracted_data.ai_output, job)
    existing_result = _get_existing_generated_result(db, candidate_id, job_id)

    result = existing_result or AIMatchingResult(
        candidate_id=candidate_id,
        job_offer_id=job_id,
        model_name="heuristic-v1",
    )
    if application_id is not None:
        result.application_id = application_id
    result.score = Decimal(output.score) / Decimal(100)
    result.detailed_scores = {
        "skill_score": output.skill_score,
        "experience_score": output.experience_score,
        "education_score": output.education_score,
        "language_score": output.language_score,
    }
    result.matched_skills = output.matched_skills
    result.missing_skills = output.missing_skills
    result.explanation = output.explanation
    result.recommendation = output.recommendation
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


def calculate_match(parsed_candidate: dict, job: JobOffer) -> MatchingOutput:
    candidate_skills = _normalize_set(parsed_candidate.get("skills", []))
    required_skills = _normalize_set(job.required_skills or [])
    preferred_skills = _normalize_set(job.preferred_skills or [])

    matched_required = sorted(required_skills & candidate_skills)
    matched_preferred = sorted(preferred_skills & candidate_skills)
    missing_required = sorted(required_skills - candidate_skills)

    required_score = _ratio_score(len(matched_required), len(required_skills))
    preferred_score = _ratio_score(len(matched_preferred), len(preferred_skills)) if preferred_skills else 100
    skill_score = round((required_score * 0.75) + (preferred_score * 0.25))

    experience_score = _experience_score(parsed_candidate.get("experience", []), job.required_experience_years)
    education_score = _education_score(parsed_candidate.get("education", []), job.education_level)
    language_score = _language_score(parsed_candidate.get("languages", []), job.description)

    total_score = round(
        (skill_score * 0.40)
        + (experience_score * 0.30)
        + (education_score * 0.25)
        + (language_score * 0.05)
    )
    recommendation = _recommendation(total_score)

    explanation = (
        f"Matched {len(matched_required)} of {len(required_skills)} required skills"
        f" and {len(matched_preferred)} preferred skills. "
        f"Experience score is {experience_score}/100, diploma/education score is {education_score}/100, "
        f"and language score is {language_score}/100. Weights prioritize competences, experience, "
        f"and diplome: skills 40%, experience 30%, diploma 25%, languages 5%. Recommendation: {recommendation}."
    )

    return MatchingOutput(
        score=total_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        language_score=language_score,
        matched_skills=sorted(_display_items(matched_required + matched_preferred)),
        missing_skills=sorted(_display_items(missing_required)),
        explanation=explanation,
        recommendation=recommendation,
    )


def list_matching_results(db: Session, skip: int = 0, limit: int = 100) -> list[AIMatchingResult]:
    statement = select(AIMatchingResult).order_by(AIMatchingResult.created_at.desc()).offset(skip).limit(limit)
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


def _experience_score(experience_items: list[str], required_years: int | None) -> int:
    if required_years is None or required_years == 0:
        return 100
    text = " ".join(experience_items).lower()
    explicit_years = [int(value) for value in re.findall(r"(\d+)\+?\s*(?:years|year|ans|an)", text)]
    estimated_years = max(explicit_years) if explicit_years else max(len(experience_items), 0)
    return min(round((estimated_years / required_years) * 100), 100)


def _education_score(education_items: list[str], education_level: str | None) -> int:
    if not education_level:
        return 100
    education_text = " ".join(education_items).lower()
    required = education_level.lower()
    keywords = {
        "phd": {"phd", "doctorate", "doctor"},
        "master": {"master", "msc", "ma"},
        "bachelor": {"bachelor", "licence", "bs", "ba"},
        "degree": {"degree", "diploma", "master", "bachelor", "licence"},
    }
    expected_terms = keywords.get(required, {required})
    return 100 if any(term in education_text for term in expected_terms) else 40 if education_items else 0


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
