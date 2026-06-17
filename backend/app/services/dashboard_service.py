from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AIMatchingResult, Candidate, CandidateTimelineEvent, Evaluation, Interview, JobOffer
from app.schemas.dashboard import DashboardActivity, DashboardCount, DashboardStatsRead


MATCHING_BUCKETS = (
    ("Strong matches", 85, 101),
    ("Good matches", 70, 85),
    ("Average matches", 50, 70),
    ("Weak matches", 0, 50),
)


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
        average_matching_score=average_matching_score,
        matching_score_buckets=_matching_buckets(matching_scores),
        recent_activities=_recent_activities(db),
    )


def _count_total(db: Session, model: type) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _count_where(db: Session, condition) -> int:
    return int(db.scalar(select(func.count()).where(condition)) or 0)


def _count_by_status(db: Session, column) -> list[DashboardCount]:
    statement = select(column, func.count()).group_by(column).order_by(column)
    return [DashboardCount(name=status or "unknown", count=int(count)) for status, count in db.execute(statement).all()]


def _as_percent(score: Decimal | float | int) -> float:
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
