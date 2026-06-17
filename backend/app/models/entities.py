from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'recruiter', 'hiring_manager')", name="ck_users_role"),
        CheckConstraint("status IN ('active', 'invited', 'suspended', 'deleted')", name="ck_users_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="recruiter", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owned_candidates: Mapped[list[Candidate]] = relationship(back_populates="owner")
    uploaded_cv_files: Mapped[list[CVFile]] = relationship(back_populates="uploaded_by")
    created_job_offers: Mapped[list[JobOffer]] = relationship(back_populates="created_by")


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        CheckConstraint(
            "source IN ('manual', 'cv_upload', 'linkedin_csv', 'candidate_portal', 'referral', 'other')",
            name="ck_candidates_source",
        ),
        CheckConstraint(
            "status IN ('new', 'active', 'shortlisted', 'interviewing', 'offered', 'hired', 'rejected', 'archived')",
            name="ck_candidates_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="new", index=True, nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    owner: Mapped[User | None] = relationship(back_populates="owned_candidates")
    cv_files: Mapped[list[CVFile]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    extracted_cv_data: Mapped[list[ExtractedCVData]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    skills: Mapped[list[CandidateSkill]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    experiences: Mapped[list[Experience]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    education: Mapped[list[Education]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    applications: Mapped[list[Application]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    timeline_events: Mapped[list[CandidateTimelineEvent]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class CVFile(TimestampMixin, Base):
    __tablename__ = "cv_files"
    __table_args__ = (
        CheckConstraint("file_size_bytes IS NULL OR file_size_bytes >= 0", name="ck_cv_files_file_size"),
        CheckConstraint(
            "parsing_status IN ('pending', 'processing', 'parsed', 'failed')",
            name="ck_cv_files_parsing_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    parsing_status: Mapped[str] = mapped_column(String(30), default="pending", index=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="cv_files")
    uploaded_by: Mapped[User | None] = relationship(back_populates="uploaded_cv_files")
    extracted_data: Mapped[ExtractedCVData | None] = relationship(back_populates="cv_file", cascade="all, delete-orphan")


class ExtractedCVData(TimestampMixin, Base):
    __tablename__ = "extracted_cv_data"
    __table_args__ = (
        Index("ix_extracted_cv_data_parsed_json", "parsed_json", postgresql_using="gin"),
        CheckConstraint(
            "total_years_experience IS NULL OR total_years_experience >= 0",
            name="ck_extracted_cv_data_total_years",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="ck_extracted_cv_data_confidence",
        ),
        CheckConstraint(
            "parsing_status IN ('extracted', 'empty', 'failed')",
            name="ck_extracted_cv_data_parsing_status",
        ),
        CheckConstraint("status IN ('parsed', 'needs_review', 'approved', 'failed')", name="ck_extracted_cv_data_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cv_file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cv_files.id", ondelete="CASCADE"), unique=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB)
    ai_output: Mapped[dict | None] = mapped_column(JSONB)
    summary: Mapped[str | None] = mapped_column(Text)
    total_years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    highest_degree: Mapped[str | None] = mapped_column(String(150))
    language_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    parser_model: Mapped[str | None] = mapped_column(String(100))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    parsing_status: Mapped[str] = mapped_column(String(30), default="extracted", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="parsed", index=True, nullable=False)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cv_file: Mapped[CVFile] = relationship(back_populates="extracted_data")
    candidate: Mapped[Candidate] = relationship(back_populates="extracted_cv_data")


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), index=True)

    candidates: Mapped[list[CandidateSkill]] = relationship(back_populates="skill", cascade="all, delete-orphan")


class CandidateSkill(TimestampMixin, Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skills_candidate_skill"),
        CheckConstraint(
            "proficiency_level IS NULL OR proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')",
            name="ck_candidate_skills_proficiency",
        ),
        CheckConstraint("years_experience IS NULL OR years_experience >= 0", name="ck_candidate_skills_years"),
        CheckConstraint(
            "source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal', 'ai_inference')",
            name="ck_candidate_skills_source",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="ck_candidate_skills_confidence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    proficiency_level: Mapped[str | None] = mapped_column(String(30))
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    source: Mapped[str] = mapped_column(String(40), default="cv_parsing", index=True, nullable=False)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    candidate: Mapped[Candidate] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="candidates")


class Experience(TimestampMixin, Base):
    __tablename__ = "experiences"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_experiences_dates"),
        CheckConstraint(
            "source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal')",
            name="ck_experiences_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(180))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(40), default="cv_parsing", nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="experiences")


class Education(TimestampMixin, Base):
    __tablename__ = "education"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_education_dates"),
        CheckConstraint(
            "source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal')",
            name="ck_education_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    institution_name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    degree: Mapped[str | None] = mapped_column(String(180))
    field_of_study: Mapped[str | None] = mapped_column(String(180))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    grade: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(40), default="cv_parsing", nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="education")


class JobOffer(TimestampMixin, Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        CheckConstraint(
            "employment_type IN ('full_time', 'part_time', 'contract', 'internship', 'temporary')",
            name="ck_job_offers_employment_type",
        ),
        CheckConstraint("work_mode IN ('onsite', 'remote', 'hybrid')", name="ck_job_offers_work_mode"),
        CheckConstraint("status IN ('draft', 'open', 'paused', 'closed', 'archived')", name="ck_job_offers_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(120))
    location: Mapped[str | None] = mapped_column(String(180))
    employment_type: Mapped[str] = mapped_column(String(40), default="full_time", nullable=False)
    work_mode: Mapped[str] = mapped_column(String(30), default="onsite", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True, nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[User | None] = relationship(back_populates="created_job_offers")
    applications: Mapped[list[Application]] = relationship(back_populates="job_offer", cascade="all, delete-orphan")
    matching_results: Mapped[list[AIMatchingResult]] = relationship(back_populates="job_offer", cascade="all, delete-orphan")


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_offer_id", name="uq_applications_candidate_job"),
        CheckConstraint(
            "source IN ('recruiter', 'candidate_portal', 'linkedin_csv', 'referral', 'other')",
            name="ck_applications_source",
        ),
        CheckConstraint(
            "status IN ('submitted', 'screening', 'shortlisted', 'interviewing', 'offer', 'hired', 'rejected', 'withdrawn')",
            name="ck_applications_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    job_offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offers.id", ondelete="CASCADE"), index=True)
    cv_file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cv_files.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(50), default="recruiter", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="submitted", index=True, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(80))
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job_offer: Mapped[JobOffer] = relationship(back_populates="applications")
    matching_results: Mapped[list[AIMatchingResult]] = relationship(back_populates="application", cascade="all, delete-orphan")
    interviews: Mapped[list[Interview]] = relationship(back_populates="application", cascade="all, delete-orphan")
    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="application", cascade="all, delete-orphan")


class AIMatchingResult(TimestampMixin, Base):
    __tablename__ = "ai_matching_results"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 1", name="ck_ai_matching_results_score"),
        CheckConstraint("rank_position IS NULL OR rank_position > 0", name="ck_ai_matching_results_rank"),
        CheckConstraint(
            "status IN ('generated', 'reviewed', 'accepted', 'dismissed')",
            name="ck_ai_matching_results_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    job_offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offers.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), index=True, nullable=False)
    rank_position: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)
    matched_skills: Mapped[dict | None] = mapped_column(JSONB)
    missing_skills: Mapped[dict | None] = mapped_column(JSONB)
    embedding_version: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="generated", index=True, nullable=False)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped[Application | None] = relationship(back_populates="matching_results")
    job_offer: Mapped[JobOffer] = relationship(back_populates="matching_results")


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint("interview_type IN ('screening', 'technical', 'hr', 'manager', 'final')", name="ck_interviews_type"),
        CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show')",
            name="ck_interviews_status",
        ),
        CheckConstraint(
            "scheduled_end_at IS NULL OR scheduled_end_at > scheduled_start_at",
            name="ck_interviews_schedule",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    scheduled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    interviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    interview_type: Mapped[str] = mapped_column(String(40), default="screening", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", index=True, nullable=False)
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meeting_url: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(180))
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="interviews")
    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="interview", cascade="all, delete-orphan")


class Evaluation(TimestampMixin, Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_evaluations_rating"),
        CheckConstraint(
            "recommendation IN ('strong_yes', 'yes', 'hold', 'no', 'strong_no')",
            name="ck_evaluations_recommendation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    interview_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    evaluator_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    recommendation: Mapped[str] = mapped_column(String(30), default="hold", index=True, nullable=False)
    strengths: Mapped[str | None] = mapped_column(Text)
    weaknesses: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    interview: Mapped[Interview | None] = relationship(back_populates="evaluations")
    application: Mapped[Application] = relationship(back_populates="evaluations")


class CandidateTimelineEvent(TimestampMixin, Base):
    __tablename__ = "candidate_timeline_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('note', 'email', 'call', 'status_change', 'cv_uploaded', 'interview_scheduled', "
            "'evaluation_added', 'ai_match_generated', 'portal_update')",
            name="ck_candidate_timeline_events_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), index=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    candidate: Mapped[Candidate] = relationship(back_populates="timeline_events")
