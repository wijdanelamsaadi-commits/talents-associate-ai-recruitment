from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Evaluation, Interview
from app.schemas import EvaluationCreate, EvaluationUpdate
from app.services.pipeline_service import apply_pipeline_stage
from app.services.timeline_service import create_timeline_event


class EvaluationError(ValueError):
    pass


SCORE_FIELDS = ("technical_score", "soft_skills_score", "motivation_score")


def create_evaluation(db: Session, evaluation_in: EvaluationCreate) -> Evaluation:
    interview = _get_interview_or_raise(db, evaluation_in.interview_id)
    candidate_id = evaluation_in.candidate_id or interview.candidate_id
    if candidate_id != interview.candidate_id:
        raise EvaluationError("Le candidat ne correspond pas au candidat de l'entretien.")

    data = evaluation_in.model_dump()
    data["candidate_id"] = candidate_id
    data["application_id"] = interview.application_id
    data["communication_score"] = evaluation_in.rating
    data["culture_fit_score"] = evaluation_in.rating
    data["global_score"] = calculate_global_score(data, rating=evaluation_in.rating)
    data["notes"] = data.get("comments")
    data["submitted_at"] = datetime.now(timezone.utc)

    evaluation = Evaluation(
        interview_id=data["interview_id"],
        application_id=data["application_id"],
        candidate_id=data["candidate_id"],
        evaluator_name=data["evaluator_name"],
        rating=data["rating"],
        technical_score=data["technical_score"],
        soft_skills_score=data["soft_skills_score"],
        motivation_score=data["motivation_score"],
        communication_score=data["communication_score"],
        culture_fit_score=data["culture_fit_score"],
        global_score=data["global_score"],
        recommendation=data["recommendation"],
        comments=data.get("comments"),
        notes=data.get("notes"),
        submitted_at=data["submitted_at"],
    )
    db.add(evaluation)
    db.flush()

    job_offer_id = _interview_job_offer_id(db, interview)
    apply_pipeline_stage(db, candidate_id, evaluation_in.recommendation, job_offer_id=job_offer_id)
    interview.status = evaluation_in.recommendation

    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="evaluation_added",
        title="Évaluation d'entretien",
        description=f"{evaluation_in.evaluator_name} a enregistré une évaluation.",
        metadata={
            "evaluation_id": str(evaluation.id),
            "interview_id": str(evaluation.interview_id),
            "global_score": float(evaluation.global_score),
            "recommendation": evaluation.recommendation,
            "pipeline_stage": evaluation_in.recommendation,
        },
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation


def list_evaluations(db: Session, skip: int = 0, limit: int = 100) -> list[Evaluation]:
    statement = select(Evaluation).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def list_interview_evaluations(db: Session, interview_id: UUID) -> list[Evaluation]:
    statement = select(Evaluation).where(Evaluation.interview_id == interview_id).order_by(Evaluation.created_at.desc())
    return list(db.scalars(statement).all())


def get_evaluation(db: Session, evaluation_id: UUID) -> Evaluation | None:
    return db.get(Evaluation, evaluation_id)


def update_evaluation(db: Session, evaluation: Evaluation, evaluation_in: EvaluationUpdate) -> Evaluation:
    data = evaluation_in.model_dump(exclude_unset=True)

    if "interview_id" in data:
        interview = _get_interview_or_raise(db, data["interview_id"])
        evaluation.interview_id = interview.id
        evaluation.application_id = interview.application_id
        evaluation.candidate_id = interview.candidate_id

    if "candidate_id" in data and data["candidate_id"] is not None:
        interview = _get_interview_or_raise(db, evaluation.interview_id)
        if data["candidate_id"] != interview.candidate_id:
            raise EvaluationError("Le candidat ne correspond pas au candidat de l'entretien.")
        evaluation.candidate_id = data.pop("candidate_id")

    for field, value in data.items():
        if field == "interview_id":
            continue
        setattr(evaluation, field, value)

    if "rating" in data:
        evaluation.communication_score = data["rating"]
        evaluation.culture_fit_score = data["rating"]

    evaluation.global_score = calculate_global_score(
        {field: getattr(evaluation, field) for field in SCORE_FIELDS},
        rating=evaluation.rating,
    )
    evaluation.notes = evaluation.comments

    interview = _get_interview_or_raise(db, evaluation.interview_id)
    job_offer_id = _interview_job_offer_id(db, interview)
    apply_pipeline_stage(db, evaluation.candidate_id, evaluation.recommendation, job_offer_id=job_offer_id)
    interview.status = evaluation.recommendation

    db.commit()
    db.refresh(evaluation)
    return evaluation


def delete_evaluation(db: Session, evaluation: Evaluation) -> None:
    db.delete(evaluation)
    db.commit()


def calculate_global_score(score_data: dict, rating: int | None = None) -> Decimal:
    if rating is not None:
        return Decimal(rating)
    scores = [Decimal(score_data[field]) for field in SCORE_FIELDS if score_data.get(field) is not None]
    if not scores:
        return Decimal("3")
    return (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"))


def _get_interview_or_raise(db: Session, interview_id: UUID) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise EvaluationError("Entretien introuvable.")
    return interview


def _interview_job_offer_id(db: Session, interview: Interview) -> UUID | None:
    application = db.get(Application, interview.application_id)
    return application.job_offer_id if application is not None else None
