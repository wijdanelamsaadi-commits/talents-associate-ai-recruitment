from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AIMatchingResult, Application, Candidate, CandidateTimelineEvent, Evaluation, Interview, JobOffer, OutlookCVImport
from app.schemas.dashboard import (
    PIPELINE_STAGES,
    DashboardActivity,
    DashboardCount,
    DashboardJobOption,
    DashboardPipelineRead,
    DashboardStatsRead,
    JobPipelineRead,
    PipelineStageCount,
)

MATCHING_BUCKETS = (
    ("Strong matches", 85, 101),
    ("Good matches", 70, 85),
    ("Average matches", 50, 70),
    ("Weak matches", 0, 50),
)

JOB_STATUS_FILTER_MAP = {
    "en_cours": ("open", "paused"),
    "cloture": ("closed",),
    "annule": ("archived", "draft"),
}


def get_dashboard_stats(db: Session) -> DashboardStatsRead:
    matching_scores = [_as_percent(score) for score in db.scalars(select(AIMatchingResult.score)).all()]
    average_matching_score = (
        round(sum(matching_scores) / len(matching_scores), 2)
        if matching_scores
        else None
    )

    return DashboardStatsRead(
        total_candidates=_count_total(db, Candidate),
        candidate_counts=_count_by_status(db, Candidate.status),
        total_jobs=_count_total(db, JobOffer),
        open_jobs=_count_where(db, JobOffer.status == "open"),
        job_counts=_count_by_status(db, JobOffer.status),
        total_interviews=_count_total(db, Interview),
        upcoming_interviews=_count_where(
            db,
            (Interview.status.in_(["scheduled", "rescheduled"]))
            & (Interview.scheduled_start_at >= datetime.now(timezone.utc)),
        ),
        interview_counts=_count_by_status(db, Interview.status),
        total_evaluations=_count_total(db, Evaluation),
        total_outlook_imports=_count_total(db, OutlookCVImport),
        total_outlook_imported=_sum_column(db, OutlookCVImport.imported_count),
        average_matching_score=average_matching_score,
        matching_score_buckets=_matching_buckets(matching_scores),
        recent_activities=_recent_activities(db),
    )


def get_dashboard_pipeline(
    db: Session,
    *,
    job_id: UUID | None = None,
    job_status: str | None = None,
    client: str | None = None,
    location: str | None = None,
    opened_from: date | None = None,
    opened_to: date | None = None,
) -> DashboardPipelineRead:
    all_jobs = db.scalars(select(JobOffer).order_by(JobOffer.created_at.desc())).all()
    filtered_jobs = [
        job
        for job in all_jobs
        if _matches_job_filters(job, job_id, job_status, client, location, opened_from, opened_to)
    ]

    pipelines = [_build_job_pipeline(db, job) for job in filtered_jobs]

    return DashboardPipelineRead(
        filter_options={
            "jobs": [
                DashboardJobOption(
                    id=job.id,
                    title=job.title,
                    company_name=job.company_name,
                    location=job.location,
                    status=job.status,
                    opened_at=job.opened_at,
                )
                for job in all_jobs
            ],
            "clients": sorted({job.company_name for job in all_jobs if job.company_name}),
            "locations": sorted({job.location for job in all_jobs if job.location}),
        },
        pipelines=pipelines,
    )


def _matches_job_filters(
    job: JobOffer,
    job_id: UUID | None,
    job_status: str | None,
    client: str | None,
    location: str | None,
    opened_from: date | None,
    opened_to: date | None,
) -> bool:
    if job_id is not None and job.id != job_id:
        return False
    if job_status and job_status != "all":
        allowed_statuses = JOB_STATUS_FILTER_MAP.get(job_status)
        if allowed_statuses and job.status not in allowed_statuses:
            return False
    if client and (job.company_name or "") != client:
        return False
    if location and (job.location or "") != location:
        return False
    if opened_from and (job.opened_at is None or job.opened_at.date() < opened_from):
        return False
    if opened_to and (job.opened_at is None or job.opened_at.date() > opened_to):
        return False
    return True


def _build_job_pipeline(db: Session, job: JobOffer) -> JobPipelineRead:
    stage_counts: dict[str, int] = {stage: 0 for stage, _ in PIPELINE_STAGES}

    applications = db.scalars(
        select(Application).where(Application.job_offer_id == job.id)
    ).all()

    stage_counts["recu"] = len(applications)

    if applications:
        candidate_ids = {application.candidate_id for application in applications}
        candidates = db.scalars(select(Candidate).where(Candidate.id.in_(candidate_ids))).all()
        candidate_status_by_id = {candidate.id: candidate.status for candidate in candidates}

        for application in applications:
            candidate_status = candidate_status_by_id.get(application.candidate_id)
            if candidate_status in stage_counts:
                stage_counts[candidate_status] += 1

    return JobPipelineRead(
        job_id=job.id,
        title=job.title,
        company_name=job.company_name,
        location=job.location,
        status=job.status,
        opened_at=job.opened_at,
        stages=[
            PipelineStageCount(stage=stage, label=label, count=stage_counts[stage])
            for stage, label in PIPELINE_STAGES
        ],
    )


def _count_total(db: Session, model: type) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _count_where(db: Session, condition) -> int:
    return int(db.scalar(select(func.count()).where(condition)) or 0)


def _count_by_status(db: Session, column) -> list[DashboardCount]:
    statement = select(column, func.count()).group_by(column).order_by(column)
    return [DashboardCount(name=status or "unknown", count=int(count)) for status, count in db.execute(statement).all()]


def _sum_column(db: Session, column) -> int:
    return int(db.scalar(select(func.coalesce(func.sum(column), 0))) or 0)


def _as_percent(score) -> float:
    numeric_score = float(score)
    return round(numeric_score * 100, 2) if numeric_score <= 1 else round(numeric_score, 2)


def _matching_buckets(scores: list[float]) -> list[DashboardCount]:
    buckets: list[DashboardCount] = []
    for label, minimum, maximum in MATCHING_BUCKETS:
        buckets.append(
            DashboardCount(
                name=label,
                count=sum(1 for score in scores if minimum <= score < maximum),
            )
        )
    return buckets


def _recent_activities(db: Session) -> list[DashboardActivity]:
    statement = (
        select(CandidateTimelineEvent)
        .order_by(CandidateTimelineEvent.occurred_at.desc(), CandidateTimelineEvent.created_at.desc())
        .limit(10)
    )
    activities = []
    for event in db.scalars(statement).all():
        activities.append(
            DashboardActivity(
                id=event.id,
                candidate_id=event.candidate_id,
                event_type=event.event_type,
                title=event.title,
                description=event.description,
                metadata=event.event_metadata,
                created_at=event.occurred_at,
            )
        )
    return activities
