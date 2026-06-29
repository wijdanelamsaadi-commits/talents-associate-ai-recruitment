from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Evaluation
from app.schemas import EvaluationCreate, EvaluationRead, EvaluationUpdate
from app.services import evaluation_service
from app.services.evaluation_service import EvaluationError


router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _serialize_evaluation(evaluation: Evaluation) -> EvaluationRead:
    return EvaluationRead(
        id=evaluation.id,
        interview_id=evaluation.interview_id,
        application_id=evaluation.application_id,
        candidate_id=evaluation.candidate_id,
        evaluator_name=evaluation.evaluator_name or "Recruteur",
        rating=evaluation.rating or int(float(evaluation.global_score or 3)),
        technical_score=evaluation.technical_score or 3,
        soft_skills_score=evaluation.soft_skills_score or 3,
        motivation_score=evaluation.motivation_score or 3,
        global_score=float(evaluation.global_score or evaluation.rating or 3),
        recommendation=evaluation.recommendation,
        comments=evaluation.comments,
        submitted_at=evaluation.submitted_at,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(evaluation_in: EvaluationCreate, db: Session = Depends(get_db)) -> EvaluationRead:
    try:
        evaluation = evaluation_service.create_evaluation(db, evaluation_in)
    except EvaluationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_evaluation(evaluation)


@router.get("", response_model=list[EvaluationRead])
def list_evaluations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[EvaluationRead]:
    return [_serialize_evaluation(evaluation) for evaluation in evaluation_service.list_evaluations(db, skip, limit)]


@router.get("/interview/{interview_id}", response_model=list[EvaluationRead])
def list_interview_evaluations(interview_id: UUID, db: Session = Depends(get_db)) -> list[EvaluationRead]:
    return [
        _serialize_evaluation(evaluation)
        for evaluation in evaluation_service.list_interview_evaluations(db, interview_id)
    ]


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(evaluation_id: UUID, db: Session = Depends(get_db)) -> EvaluationRead:
    evaluation = evaluation_service.get_evaluation(db, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    return _serialize_evaluation(evaluation)


@router.put("/{evaluation_id}", response_model=EvaluationRead)
def update_evaluation(evaluation_id: UUID, evaluation_in: EvaluationUpdate, db: Session = Depends(get_db)) -> EvaluationRead:
    evaluation = evaluation_service.get_evaluation(db, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    try:
        updated = evaluation_service.update_evaluation(db, evaluation, evaluation_in)
    except EvaluationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_evaluation(updated)


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(evaluation_id: UUID, db: Session = Depends(get_db)) -> None:
    evaluation = evaluation_service.get_evaluation(db, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    evaluation_service.delete_evaluation(db, evaluation)
