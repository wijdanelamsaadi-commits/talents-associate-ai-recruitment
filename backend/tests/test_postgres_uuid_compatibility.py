import uuid
from pathlib import Path

from sqlalchemy.dialects.postgresql import UUID

from app.models import Base
from app.models.entities import User


FORBIDDEN_MIGRATION_TOKENS = (
    "CREATE EXTENSION",
    "pgcrypto",
    "gen_random_uuid",
)


def test_uuid_columns_do_not_use_server_side_gen_random_uuid():
    uuid_columns = [
        column
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, UUID)
    ]

    assert uuid_columns
    for column in uuid_columns:
        server_default = str(column.server_default.arg) if column.server_default else ""
        assert "gen_random_uuid" not in server_default


def test_migrations_do_not_depend_on_pgcrypto_or_gen_random_uuid():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))

    assert migration_files
    for migration_file in migration_files:
        content = migration_file.read_text(encoding="utf-8")
        for forbidden_token in FORBIDDEN_MIGRATION_TOKENS:
            assert forbidden_token not in content, migration_file.name


def test_sqlalchemy_model_uses_python_uuid_default():
    default = User.__table__.c.id.default

    assert default is not None
    generated_id = default.arg(None)
    assert isinstance(generated_id, uuid.UUID)
