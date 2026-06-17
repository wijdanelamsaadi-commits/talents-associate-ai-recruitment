from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas import CandidateCreate


def create_candidate(db: Session, candidate_in: CandidateCreate) -> Candidate:
    candidate_data = candidate_in.model_dump()
    for url_field in ("linkedin_url", "portfolio_url"):
        if candidate_data[url_field] is not None:
            candidate_data[url_field] = str(candidate_data[url_field])

    candidate = Candidate(**candidate_data)
    db.add(candidate)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(candidate)
    return candidate


def list_candidates(db: Session, skip: int = 0, limit: int = 100) -> list[Candidate]:
    statement = select(Candidate).order_by(Candidate.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_candidate(db: Session, candidate_id: UUID) -> Candidate | None:
    return db.get(Candidate, candidate_id)
