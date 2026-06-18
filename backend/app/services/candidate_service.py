from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas import CandidateCreate, CandidateUpdate
from app.services.timeline_service import create_timeline_event


def create_candidate(db: Session, candidate_in: CandidateCreate) -> Candidate:
    candidate_data = candidate_in.model_dump()
    for url_field in ("linkedin_url", "portfolio_url"):
        if candidate_data[url_field] is not None:
            candidate_data[url_field] = str(candidate_data[url_field])

    candidate = Candidate(**candidate_data)
    db.add(candidate)

    try:
        db.flush()
        event_type = "outlook_imported" if candidate.source == "outlook_import" else "candidate_created"
        title = "Candidate imported from Outlook" if candidate.source == "outlook_import" else "Candidate created"
        description = (
            f"{candidate.first_name} {candidate.last_name} was imported from Outlook."
            if candidate.source == "outlook_import"
            else f"{candidate.first_name} {candidate.last_name} was added to the database."
        )
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type=event_type,
            title=title,
            description=description,
            metadata={"source": candidate.source, "status": candidate.status},
        )
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


def update_candidate(db: Session, candidate: Candidate, candidate_in: CandidateUpdate) -> Candidate:
    candidate_data = candidate_in.model_dump(exclude_unset=True)
    for url_field in ("linkedin_url", "portfolio_url"):
        if url_field in candidate_data and candidate_data[url_field] is not None:
            candidate_data[url_field] = str(candidate_data[url_field])

    for field, value in candidate_data.items():
        setattr(candidate, field, value)

    try:
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="candidate_updated",
            title="Candidate updated",
            description="Candidate profile information was updated.",
            metadata={"updated_fields": sorted(candidate_data.keys())},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(candidate)
    return candidate


def delete_candidate(db: Session, candidate: Candidate) -> None:
    db.delete(candidate)
    db.commit()
