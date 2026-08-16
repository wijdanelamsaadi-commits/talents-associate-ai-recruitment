"""add job reference titles

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union
import re
import unicodedata
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.data.job_reference_titles import JOB_REFERENCE_TITLES


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    if "job_reference_titles" not in _tables():
        op.create_table(
            "job_reference_titles",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("normalized_title", sa.String(length=180), nullable=False),
            sa.Column("source", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_job_reference_titles_normalized_title"), "job_reference_titles", ["normalized_title"], unique=True)

    existing = set(
        bind.execute(sa.text("SELECT normalized_title FROM job_reference_titles")).scalars().all()
    )
    rows = []
    for title in JOB_REFERENCE_TITLES:
        clean_title = re.sub(r"\s+", " ", title).strip()
        normalized_title = _normalize(clean_title)
        if clean_title and normalized_title not in existing:
            rows.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": clean_title,
                    "normalized_title": normalized_title,
                    "source": "system",
                }
            )
            existing.add(normalized_title)
    if rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO job_reference_titles (id, title, normalized_title, source)
                VALUES (:id, :title, :normalized_title, :source)
                """
            ),
            rows,
        )


def downgrade() -> None:
    if "job_reference_titles" not in _tables():
        return
    op.drop_index(op.f("ix_job_reference_titles_normalized_title"), table_name="job_reference_titles")
    op.drop_table("job_reference_titles")


def _normalize(value: str | None) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("’", "'").replace("-", " ").replace("_", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
