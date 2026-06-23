from uuid import UUID

from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AIMatchingResult,
    Application,
    Candidate,
    CandidateTimelineEvent,
    CVFile,
    Evaluation,
    ExtractedCVData,
    Interview,
    JobOffer,
)
from app.schemas.candidate import (
    CandidateHistoryApplication,
    CandidateHistoryCVFile,
    CandidateHistoryEvaluation,
    CandidateHistoryInterview,
    CandidateHistoryMatchingResult,
    CandidateHistoryRead,
    CandidateHistoryTimelineEvent,
    CandidateRead,
)
from app.services.timeline_service import create_timeline_event
from app.services.notification_service import notify_application_accepted, notify_application_rejected


def get_application(db: Session, application_id: UUID) -> Application | None:
    return db.get(Application, application_id)


def accept_application(db: Session, application: Application) -> Application:
    now = db.execute(select(sa_func.now())).scalar_one()
    candidate = db.get(Candidate, application.candidate_id)
    application.status = "hired"
    application.current_stage = "hired"
    if candidate is not None:
        job = db.get(JobOffer, application.job_offer_id)
        candidate.status = "hired"
        candidate.is_talent_pool = False
        candidate.last_decision_at = now
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="application_accepted",
            title="Application accepted",
            description="Recruiter accepted the application. Email notification is not enabled yet.",
            metadata={"application_id": str(application.id), "status": "hired", "current_stage": "hired"},
        )
        notify_application_accepted(db, candidate=candidate, application=application, job=job)
    db.commit()
    db.refresh(application)
    return application


def reject_application(db: Session, application: Application) -> Application:
    now = db.execute(select(sa_func.now())).scalar_one()
    candidate = db.get(Candidate, application.candidate_id)
    application.status = "rejected"
    application.current_stage = "rejected"
    if candidate is not None:
        job = db.get(JobOffer, application.job_offer_id)
        candidate.status = "rejected"
        candidate.is_talent_pool = True
        candidate.rejected_at = now
        candidate.last_decision_at = now
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="application_rejected",
            title="Application rejected and candidate kept in talent pool",
            description="Recruiter rejected the application and retained the candidate in the talent pool.",
            metadata={"application_id": str(application.id), "status": "rejected", "is_talent_pool": True},
        )
        notify_application_rejected(db, candidate=candidate, application=application, job=job)
    db.commit()
    db.refresh(application)
    return application


def reactivate_application(db: Session, application: Application) -> Application:
    now = db.execute(select(sa_func.now())).scalar_one()
    candidate = db.get(Candidate, application.candidate_id)
    application.status = "shortlisted"
    application.current_stage = "shortlisted"
    if candidate is not None:
        previous_status = candidate.status
        candidate.status = "active"
        candidate.is_talent_pool = False
        candidate.reactivated_at = now
        candidate.last_decision_at = now
        create_timeline_event(
            db,
            candidate_id=candidate.id,
            event_type="application_reactivated",
            title="Application reactivated",
            description="Recruiter reactivated the application while preserving candidate history.",
            metadata={
                "application_id": str(application.id),
                "application_status": "shortlisted",
                "previous_candidate_status": previous_status,
                "candidate_status": "active",
            },
        )
    db.commit()
    db.refresh(application)
    return application


def _matching_to_history(match: AIMatchingResult) -> CandidateHistoryMatchingResult:
    return CandidateHistoryMatchingResult(
        id=match.id,
        application_id=match.application_id,
        job_offer_id=match.job_offer_id,
        job_title=match.job_offer.title if match.job_offer else None,
        score=match.score,
        semantic_score=match.semantic_score,
        used_semantic_embedding=match.used_semantic_embedding,
        recommendation=match.recommendation,
        explanation=match.explanation,
        matched_skills=match.matched_skills,
        missing_skills=match.missing_skills,
        detailed_scores=match.detailed_scores,
        created_at=match.created_at,
    )


def _interview_to_history(interview: Interview) -> CandidateHistoryInterview:
    return CandidateHistoryInterview(
        id=interview.id,
        application_id=interview.application_id,
        interview_type=interview.interview_type,
        status=interview.status,
        scheduled_start_at=interview.scheduled_start_at,
        scheduled_end_at=interview.scheduled_end_at,
        location=interview.location,
        meeting_url=interview.meeting_url,
        notes=interview.notes,
    )


def _evaluation_to_history(evaluation: Evaluation) -> CandidateHistoryEvaluation:
    return CandidateHistoryEvaluation(
        id=evaluation.id,
        application_id=evaluation.application_id,
        interview_id=evaluation.interview_id,
        evaluator_name=evaluation.evaluator_name,
        rating=evaluation.rating,
        technical_score=evaluation.technical_score,
        soft_skills_score=evaluation.soft_skills_score,
        motivation_score=evaluation.motivation_score,
        communication_score=evaluation.communication_score,
        culture_fit_score=evaluation.culture_fit_score,
        global_score=evaluation.global_score,
        recommendation=evaluation.recommendation,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        comments=evaluation.comments,
        notes=evaluation.notes,
        submitted_at=evaluation.submitted_at,
    )


def get_candidate_history(db: Session, candidate_id: UUID) -> CandidateHistoryRead | None:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        return None

    cv_files = list(
        db.scalars(
            select(CVFile)
            .where(CVFile.candidate_id == candidate_id)
            .options(selectinload(CVFile.extracted_data))
            .order_by(CVFile.uploaded_at.desc(), CVFile.created_at.desc())
        ).all()
    )
    extracted_by_cv_id = {
        extracted.cv_file_id: extracted
        for extracted in db.scalars(select(ExtractedCVData).where(ExtractedCVData.candidate_id == candidate_id)).all()
    }

    applications = list(
        db.scalars(
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .options(
                selectinload(Application.job_offer),
                selectinload(Application.matching_results).selectinload(AIMatchingResult.job_offer),
                selectinload(Application.interviews),
                selectinload(Application.evaluations),
            )
            .order_by(Application.applied_at.desc(), Application.created_at.desc())
        ).all()
    )
    all_matches = list(
        db.scalars(
            select(AIMatchingResult)
            .where(AIMatchingResult.candidate_id == candidate_id)
            .options(selectinload(AIMatchingResult.job_offer))
            .order_by(AIMatchingResult.created_at.desc())
        ).all()
    )
    all_interviews = list(
        db.scalars(
            select(Interview)
            .where(Interview.candidate_id == candidate_id)
            .order_by(Interview.scheduled_start_at.desc())
        ).all()
    )
    all_evaluations = list(
        db.scalars(
            select(Evaluation)
            .where(Evaluation.candidate_id == candidate_id)
            .order_by(Evaluation.submitted_at.desc().nullslast(), Evaluation.created_at.desc())
        ).all()
    )
    timeline_events = list(
        db.scalars(
            select(CandidateTimelineEvent)
            .where(CandidateTimelineEvent.candidate_id == candidate_id)
            .order_by(CandidateTimelineEvent.occurred_at.desc(), CandidateTimelineEvent.created_at.desc())
        ).all()
    )

    return CandidateHistoryRead(
        candidate=CandidateRead.model_validate(candidate),
        cv_files=[
            CandidateHistoryCVFile(
                id=cv_file.id,
                original_filename=cv_file.original_filename,
                mime_type=cv_file.mime_type,
                file_size_bytes=cv_file.file_size_bytes,
                parsing_status=cv_file.parsing_status,
                parser_model=extracted_by_cv_id.get(cv_file.id).parser_model if extracted_by_cv_id.get(cv_file.id) else None,
                uploaded_at=cv_file.uploaded_at,
            )
            for cv_file in cv_files
        ],
        applications=[
            CandidateHistoryApplication(
                id=application.id,
                job_offer_id=application.job_offer_id,
                job_title=application.job_offer.title if application.job_offer else "Offre inconnue",
                company_name=application.job_offer.company_name if application.job_offer else None,
                source=application.source,
                status=application.status,
                current_stage=application.current_stage,
                applied_at=application.applied_at,
                cv_file_id=application.cv_file_id,
                matching_results=[_matching_to_history(match) for match in application.matching_results],
                interviews=[_interview_to_history(interview) for interview in application.interviews],
                evaluations=[_evaluation_to_history(evaluation) for evaluation in application.evaluations],
            )
            for application in applications
        ],
        matching_results=[_matching_to_history(match) for match in all_matches],
        interviews=[_interview_to_history(interview) for interview in all_interviews],
        evaluations=[_evaluation_to_history(evaluation) for evaluation in all_evaluations],
        timeline_events=[
            CandidateHistoryTimelineEvent(
                id=event.id,
                event_type=event.event_type,
                title=event.title,
                description=event.description,
                metadata=event.event_metadata,
                created_at=event.occurred_at,
            )
            for event in timeline_events
        ],
    )
