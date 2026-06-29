"""unify interview evaluation pipeline stages

Revision ID: 20260627_interview_eval_pipeline
Revises: 20260627_job_fields
Create Date: 2026-06-27 16:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260627_interview_eval_pipeline"
down_revision: str | None = "20260627_job_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INTERVIEW_TYPES = ("entretien_cabinet", "entretien_client")
PIPELINE_STATUSES = (
    "preselectionne",
    "non_selectionne",
    "entretien_cabinet",
    "entretien_client",
    "profil_valide",
    "refus_candidat",
)
EVALUATION_DECISIONS = ("preselectionne", "non_selectionne", "profil_valide", "refus_candidat")


def _check_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute(
        """
        UPDATE interviews
        SET interview_type = CASE interview_type
            WHEN 'screening' THEN 'entretien_cabinet'
            WHEN 'technical' THEN 'entretien_cabinet'
            WHEN 'hr' THEN 'entretien_cabinet'
            WHEN 'manager' THEN 'entretien_client'
            WHEN 'final' THEN 'entretien_client'
            ELSE interview_type
        END
        """
    )
    op.execute(
        """
        UPDATE interviews
        SET status = CASE status
            WHEN 'scheduled' THEN 'entretien_cabinet'
            WHEN 'completed' THEN 'profil_valide'
            WHEN 'cancelled' THEN 'refus_candidat'
            WHEN 'rescheduled' THEN 'entretien_cabinet'
            WHEN 'no_show' THEN 'non_selectionne'
            ELSE status
        END
        """
    )

    op.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS ck_interviews_type")
    op.execute(
        f"""
        ALTER TABLE interviews
        ADD CONSTRAINT ck_interviews_type CHECK (interview_type IN ({_check_values(INTERVIEW_TYPES)}))
        """
    )
    op.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS ck_interviews_status")
    op.execute(
        f"""
        ALTER TABLE interviews
        ADD CONSTRAINT ck_interviews_status CHECK (status IN ({_check_values(PIPELINE_STATUSES)}))
        """
    )

    op.execute(
        """
        UPDATE evaluations
        SET technical_score = LEAST(5, GREATEST(1, ROUND(technical_score / 20.0))),
            soft_skills_score = LEAST(5, GREATEST(1, ROUND(soft_skills_score / 20.0))),
            motivation_score = LEAST(5, GREATEST(1, ROUND(motivation_score / 20.0))),
            communication_score = LEAST(5, GREATEST(1, ROUND(communication_score / 20.0))),
            culture_fit_score = LEAST(5, GREATEST(1, ROUND(culture_fit_score / 20.0))),
            rating = LEAST(5, GREATEST(1, COALESCE(rating, ROUND(global_score / 20.0))))
        WHERE technical_score IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE evaluations
        SET recommendation = CASE recommendation
            WHEN 'strong_yes' THEN 'profil_valide'
            WHEN 'yes' THEN 'preselectionne'
            WHEN 'hold' THEN 'preselectionne'
            WHEN 'no' THEN 'non_selectionne'
            WHEN 'strong_no' THEN 'refus_candidat'
            ELSE recommendation
        END
        """
    )

    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_technical_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_soft_skills_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_motivation_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_communication_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_culture_fit_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_global_score")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_recommendation")

    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_technical_score "
        "CHECK (technical_score IS NULL OR technical_score BETWEEN 1 AND 5)"
    )
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_soft_skills_score "
        "CHECK (soft_skills_score IS NULL OR soft_skills_score BETWEEN 1 AND 5)"
    )
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_motivation_score "
        "CHECK (motivation_score IS NULL OR motivation_score BETWEEN 1 AND 5)"
    )
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_communication_score "
        "CHECK (communication_score IS NULL OR communication_score BETWEEN 1 AND 5)"
    )
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_culture_fit_score "
        "CHECK (culture_fit_score IS NULL OR culture_fit_score BETWEEN 1 AND 5)"
    )
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_global_score "
        "CHECK (global_score IS NULL OR global_score BETWEEN 1 AND 5)"
    )
    op.execute(
        f"""
        ALTER TABLE evaluations
        ADD CONSTRAINT ck_evaluations_recommendation CHECK (recommendation IN ({_check_values(EVALUATION_DECISIONS)}))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_recommendation")
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_recommendation "
        "CHECK (recommendation IN ('strong_yes', 'yes', 'hold', 'no', 'strong_no'))"
    )
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_global_score")
    op.execute(
        "ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_global_score "
        "CHECK (global_score IS NULL OR global_score BETWEEN 0 AND 100)"
    )
    for column in (
        "technical_score",
        "soft_skills_score",
        "motivation_score",
        "communication_score",
        "culture_fit_score",
    ):
        op.execute(f"ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_{column}")
        op.execute(
            f"ALTER TABLE evaluations ADD CONSTRAINT ck_evaluations_{column} "
            f"CHECK ({column} IS NULL OR {column} BETWEEN 0 AND 100)"
        )

    op.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS ck_interviews_status")
    op.execute(
        "ALTER TABLE interviews ADD CONSTRAINT ck_interviews_status "
        "CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show'))"
    )
    op.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS ck_interviews_type")
    op.execute(
        "ALTER TABLE interviews ADD CONSTRAINT ck_interviews_type "
        "CHECK (interview_type IN ('screening', 'technical', 'hr', 'manager', 'final'))"
    )
