"""Passenger WSGI entrypoint for the Talents Associate FastAPI backend.

cPanel Setup Python App / Passenger expects a WSGI callable named
``application``. The project itself is ASGI, so Passenger calls this WSGI
adapter, which forwards requests to the FastAPI app.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a2wsgi import ASGIMiddleware


BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app as fastapi_app  # noqa: E402


application = ASGIMiddleware(fastapi_app)
