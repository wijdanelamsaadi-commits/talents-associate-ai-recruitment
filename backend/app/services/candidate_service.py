from uuid import UUID

from sqlalchemy import func as sa_func, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, Candidate
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
        title = "Candidat importé depuis un fichier CV" if candidate.source == "outlook_import" else "Candidat créé"
        description = (
            f"{candidate.first_name} {candidate.last_name} a été importé depuis un fichier CV."
            if candidate.source == "outlook_import"
            else f"{candidate.first_name} {candidate.last_name} a été ajouté à la base de données."
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


CandidateFilter = str


def _apply_candidate_filter(
    statement,
    candidate_filter: CandidateFilter = "all",
    job_offer_id: UUID | None = None,
    pipeline_stage: str | None = None,
):
    if candidate_filter == "active":
        statement = statement.where(Candidate.status == "active")
    elif candidate_filter == "rejected":
        statement = statement.where(Candidate.status == "rejected")
    elif candidate_filter == "archived":
        statement = statement.where(Candidate.status == "archived")
    elif candidate_filter == "talent_pool":
        statement = statement.where(Candidate.is_talent_pool.is_(True))

    if job_offer_id is not None:
        statement = statement.where(
            Candidate.id.in_(
                select(Application.candidate_id).where(Application.job_offer_id == job_offer_id)
            )
        )

    if pipeline_stage and pipeline_stage != "recu":
        statement = statement.where(Candidate.status == pipeline_stage)

    return statement


def count_candidates(
    db: Session,
    candidate_filter: CandidateFilter = "all",
    job_offer_id: UUID | None = None,
    pipeline_stage: str | None = None,
) -> int:
    statement = _apply_candidate_filter(
        select(sa_func.count()).select_from(Candidate),
        candidate_filter,
        job_offer_id=job_offer_id,
        pipeline_stage=pipeline_stage,
    )
    return db.scalar(statement) or 0


def list_candidates(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    after_id: UUID | None = None,
    candidate_filter: CandidateFilter = "all",
    job_offer_id: UUID | None = None,
    pipeline_stage: str | None = None,
) -> list[Candidate]:
    base_statement = _apply_candidate_filter(
        select(Candidate),
        candidate_filter,
        job_offer_id=job_offer_id,
        pipeline_stage=pipeline_stage,
    )
    if after_id is not None:
        cursor_row = db.get(Candidate, after_id)
        if cursor_row is None:
            statement = base_statement.order_by(Candidate.created_at.desc(), Candidate.id.desc()).limit(limit)
        else:
            statement = (
                base_statement
                .where(tuple_(Candidate.created_at, Candidate.id) < (cursor_row.created_at, cursor_row.id))
                .order_by(Candidate.created_at.desc(), Candidate.id.desc())
                .limit(limit)
            )
    else:
        statement = base_statement.order_by(Candidate.created_at.desc(), Candidate.id.desc()).offset(skip).limit(limit)
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
            title="Candidat mis à jour",
            description="Les informations du profil candidat ont été mises à jour.",
            metadata={"updated_fields": sorted(candidate_data.keys())},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(candidate)
    return candidate


def delete_candidate(db: Session, candidate: Candidate) -> None:
    archive_candidate(db, candidate)


def archive_candidate(db: Session, candidate: Candidate) -> Candidate:
    now = db.execute(select(sa_func.now())).scalar_one()
    candidate.status = "archived"
    candidate.archived_at = now
    candidate.last_decision_at = now
    create_timeline_event(
        db,
        candidate_id=candidate.id,
        event_type="candidate_archived",
        title="Candidat archivé",
        description="Le candidat a été archivé sans supprimer son CV, ses candidatures, son analyse ou son historique.",
        metadata={"status": "archived", "soft_delete": True},
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def reject_candidate(db: Session, candidate: Candidate, application_id: UUID | None = None) -> Candidate:
    now = db.execute(select(sa_func.now())).scalar_one()
    candidate.status = "rejected"
    candidate.is_talent_pool = True
    candidate.rejected_at = now
    candidate.last_decision_at = now

    if application_id is not None:
        application = db.get(Application, application_id)
        if application is not None and application.candidate_id == candidate.id:
            application.status = "rejected"
            application.current_stage = "rejected"
    else:
        latest_application = db.scalar(
            select(Application)
            .where(Application.candidate_id == candidate.id)
            .order_by(Application.applied_at.desc(), Application.created_at.desc())
        )
        if latest_application is not None:
            latest_application.status = "rejected"
            latest_application.current_stage = "rejected"

    create_timeline_event(
        db,
        candidate_id=candidate.id,
        event_type="candidate_rejected",
        title="Candidat refusé et conservé dans le vivier",
        description="Le candidat a été refusé pour une candidature et conservé dans le vivier.",
        metadata={"status": "rejected", "is_talent_pool": True, "application_id": str(application_id) if application_id else None},
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def reactivate_candidate(db: Session, candidate: Candidate, keep_in_talent_pool: bool = False) -> Candidate:
    now = db.execute(select(sa_func.now())).scalar_one()
    previous_status = candidate.status
    candidate.status = "active"
    candidate.is_talent_pool = keep_in_talent_pool
    candidate.reactivated_at = now
    candidate.last_decision_at = now
    create_timeline_event(
        db,
        candidate_id=candidate.id,
        event_type="candidate_reactivated",
        title="Candidat réactivé",
        description="Le candidat a été réactivé depuis le statut archivé ou vivier.",
        metadata={"previous_status": previous_status, "is_talent_pool": keep_in_talent_pool},
    )
    db.commit()
    db.refresh(candidate)
    return candidate
