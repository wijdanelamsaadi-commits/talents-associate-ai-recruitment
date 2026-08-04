import os
import subprocess
import sys
from pathlib import Path

from app.core.config import DEFAULT_CORS_ORIGINS
from app.core.config import Settings


def test_cors_origins_default_values_are_preserved():
    settings = Settings(_env_file=None)

    assert settings.CORS_ORIGINS == DEFAULT_CORS_ORIGINS


def test_cors_origins_accept_json_list_string():
    settings = Settings(
        CORS_ORIGINS='["https://recruteur.talentsag.ma"]',
        _env_file=None,
    )

    assert settings.CORS_ORIGINS == ["https://recruteur.talentsag.ma"]


def test_cors_origins_accept_python_list_string():
    settings = Settings(
        CORS_ORIGINS="['https://recruteur.talentsag.ma']",
        _env_file=None,
    )

    assert settings.CORS_ORIGINS == ["https://recruteur.talentsag.ma"]


def test_cors_origins_accept_comma_separated_string():
    settings = Settings(
        CORS_ORIGINS="https://recruteur.talentsag.ma, https://talentsag.ma,",
        _env_file=None,
    )

    assert settings.CORS_ORIGINS == [
        "https://recruteur.talentsag.ma",
        "https://talentsag.ma",
    ]


def test_cors_origins_accept_single_url():
    settings = Settings(
        CORS_ORIGINS="https://recruteur.talentsag.ma",
        _env_file=None,
    )

    assert settings.CORS_ORIGINS == ["https://recruteur.talentsag.ma"]


def test_cors_origins_ignore_empty_values():
    settings = Settings(
        CORS_ORIGINS=" https://recruteur.talentsag.ma, , https://talentsag.ma ",
        _env_file=None,
    )

    assert settings.CORS_ORIGINS == [
        "https://recruteur.talentsag.ma",
        "https://talentsag.ma",
    ]


def test_passenger_wsgi_import_accepts_supported_cors_formats():
    backend_root = Path(__file__).resolve().parents[1]
    supported_values = [
        '["https://recruteur.talentsag.ma"]',
        "['https://recruteur.talentsag.ma']",
        "https://recruteur.talentsag.ma,https://talentsag.ma",
        "https://recruteur.talentsag.ma",
    ]

    for cors_value in supported_values:
        env = os.environ.copy()
        env["CORS_ORIGINS"] = cors_value

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from passenger_wsgi import application; print(type(application).__name__)",
            ],
            cwd=backend_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "ASGIMiddleware" in result.stdout
