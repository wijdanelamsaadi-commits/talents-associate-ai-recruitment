from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Evaluation, Interview
from app.schemas import EvaluationCreate, EvaluationUpdate
from app.services.timeline_service import create_timeline_event


class EvaluationError(ValueError):
    pass


SCORE_FIELDS = (
    "technical_score",
    "soft_skills_score",
    "motivation_score",
    "communication_score",
    "culture_fit_score",
)


def create_evaluation(db: Session, evaluation_in: EvaluationCreate) -> Evaluation:
    interview = _get_interview_or_raise(db, evaluation_in.interview_id)
    candidate_id = evaluation_in.candidate_id or interview.candidate_id
    if candidate_id != interview.candidate_id:
        raise EvaluationError("Candidate does not match the interview candidate.")

    data = evaluation_in.model_dump()
    data["candidate_id"] = candidate_id
    data["application_id"] = interview.application_id
    data["global_score"] = calculate_global_score(data)
    data["notes"] = data.get("comments")

    evaluation = Evaluation(**data)
    db.add(evaluation)
    db.flush()
    create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type="evaluation_added",
        title="Evaluation added",
        description=f"{evaluation_in.evaluator_name} added an interview evaluation.",
        metadata={
            "evaluation_id": str(evaluation.id),
            "interview_id": str(evaluation.interview_id),
            "global_score": float(evaluation.global_score),
            "recommendation": evaluation.recommendation,
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
            raise EvaluationError("Candidate does not match the interview candidate.")
        evaluation.candidate_id = data.pop("candidate_id")

    for field, value in data.items():
        if field == "interview_id":
            continue
        setattr(evaluation, field, value)

    evaluation.global_score = calculate_global_score(
        {
            field: getattr(evaluation, field)
            for field in SCORE_FIELDS
        }
    )
    evaluation.notes = evaluation.comments

    db.commit()
    db.refresh(evaluation)
    return evaluation


def delete_evaluation(db: Session, evaluation: Evaluation) -> None:
    db.delete(evaluation)
    db.commit()


def calculate_global_score(score_data: dict) -> Decimal:
    scores = [Decimal(score_data[field]) for field in SCORE_FIELDS]
    return (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"))


def _get_interview_or_raise(db: Session, interview_id: UUID) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise EvaluationError("Interview not found.")
    return interview
