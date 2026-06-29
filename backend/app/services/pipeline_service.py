from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Candidate


PIPELINE_STAGES = frozenset(
    {
        "preselectionne",
        "non_selectionne",
        "entretien_cabinet",
        "entretien_client",
        "profil_valide",
        "refus_candidat",
    }
)

EVALUATION_DECISIONS = frozenset(
    {
        "preselectionne",
        "non_selectionne",
        "profil_valide",
        "refus_candidat",
    }
)

STAGE_LABELS = {
    "preselectionne": "Présélectionné",
    "non_selectionne": "Non sélectionné",
    "entretien_cabinet": "Entretien cabinet",
    "entretien_client": "Entretien client",
    "profil_valide": "Profil validé",
    "refus_candidat": "Refus candidat",
}


def apply_pipeline_stage(
    db: Session,
    candidate_id: UUID,
    stage: str,
    job_offer_id: UUID | None = None,
) -> None:
    if stage not in PIPELINE_STAGES:
        return

    candidate = db.get(Candidate, candidate_id)
    if candidate is not None:
        candidate.status = stage
        if stage == "refus_candidat":
            candidate.is_talent_pool = True

    application = _resolve_application(db, candidate_id, job_offer_id)
    if application is not None:
        application.current_stage = stage
        application.status = _application_status_for_stage(stage)


def _resolve_application(db: Session, candidate_id: UUID, job_offer_id: UUID | None) -> Application | None:
    if job_offer_id is not None:
        application = db.scalar(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_offer_id == job_offer_id,
            )
        )
        if application is not None:
            return application

    return db.scalar(
        select(Application)
        .where(Application.candidate_id == candidate_id)
        .order_by(Application.applied_at.desc(), Application.created_at.desc())
    )


def _application_status_for_stage(stage: str) -> str:
    if stage in {"profil_valide", "preselectionne"}:
        return "shortlisted"
    if stage in {"refus_candidat", "non_selectionne"}:
        return "rejected"
    return "interviewing"
