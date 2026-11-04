"""Shared fixtures for the backend smoke tests.

The app package uses flat imports (``from core import config``), so
``backend/app`` must be on ``sys.path`` before the app can be imported, and
the test environment must be set before that import happens: the settings are
read from environment variables when ``main.init()`` runs.

Two execution modes:

* **default** — the app is configured with an unreachable DSN. Everything in
  ``test_smoke.py`` exercises the HTTP layer (routing, auth guards,
  validation, error envelopes) and needs no external services.
* **``WORDSJAR_TEST_DB_DSN`` set** — ``test_smoke_db.py`` additionally runs
  the alembic migrations against that database and walks the full user
  journey (signup -> login -> jar -> exam -> refresh -> logout). Point it at
  a dedicated, disposable database, never at one you care about.

Run everything against a local database::

    WORDSJAR_TEST_DB_DSN=postgresql+psycopg://postgres:postgres@localhost:5432/wordsjar_test \
        uv run pytest
"""

from __future__ import annotations

import os
import pathlib
import sys
import uuid

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
APP_DIR = BACKEND_DIR / "app"

# The app itself imports flat modules from backend/app; alembic's env.py
# imports the ORM as app.models.orm, which resolves against backend/.
for _path in (str(APP_DIR), str(BACKEND_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

#: A dedicated test database enables the DB-backed suite. Empty means
#: "HTTP-layer smoke tests only".
TEST_DB_DSN = os.environ.get("WORDSJAR_TEST_DB_DSN", "").strip()

#: ``main.init()`` requires a DSN and a JWT signing key even when the HTTP
#: suite never touches storage: the engine is lazy and only dials on the first
#: query. ``.invalid`` is reserved by RFC 6761 and can never resolve, which
#: makes "the database is down" a deterministic state instead of a race with
#: whatever happens to listen on localhost:5432.
DUMMY_DB_DSN = "postgresql+psycopg://wordsjar:wordsjar@wordsjar-db.invalid:5432/wordsjar"
TEST_JWT_KEY = "wordsjar-smoke-tests-only-not-a-production-key"

os.environ["WORDSJAR_BACKEND_DB_DSN"] = TEST_DB_DSN or DUMMY_DB_DSN
os.environ["WORDSJAR_BACKEND_JWT_KEY"] = TEST_JWT_KEY
# Keep /docs and /openapi.json available in every environment so that the
# schema can be smoke tested.
os.environ["WORDSJAR_BACKEND_APP_DOCS_ENABLED"] = "true"
os.environ["WORDSJAR_BACKEND_APP_ENVIRONMENT"] = "local"


def sync_dsn(dsn: str) -> str:
    """libpq form of a SQLAlchemy DSN: psycopg does not know '+psycopg'."""
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def unique_name(prefix: str) -> str:
    """A username or word stem that cannot collide between test runs."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@pytest.fixture(scope="session")
def app():
    """The FastAPI application built by the real factory with real config."""
    from main import init

    return init()


@pytest.fixture(scope="session")
def client(app):
    """HTTP client that talks ASGI in-process: no socket, no live server.

    Entering the context manager runs the application lifespan (startup and
    shutdown), so using this fixture is also the check that the process boots
    and tears down cleanly.
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Give every test its own rate limit budget.

    The limiters are in-process fixed windows shared by the whole session
    (signup: 5 per hour per client), so without a reset one journey test
    would spend the budget of all the others. ``_hits`` is private state, but
    the public ``reset()`` needs the exact keys and "every key" is what a test
    session wants.
    """
    from services.ratelimit import login_limiter, refresh_limiter, signup_limiter

    for limiter in (login_limiter, refresh_limiter, signup_limiter):
        limiter._hits.clear()


@pytest.fixture(scope="session")
def db_required():
    """Guard for the DB-backed suite.

    A missing ``WORDSJAR_TEST_DB_DSN`` is a normal skip; a *set but
    unreachable* one is a hard failure — silently skipping the DB suite would
    hide a misconfigured CI job.
    """
    if not TEST_DB_DSN:
        pytest.skip("WORDSJAR_TEST_DB_DSN is not set")

    import psycopg

    try:
        with psycopg.connect(sync_dsn(TEST_DB_DSN), connect_timeout=5):
            pass
    except psycopg.Error as exc:
        pytest.fail(f"WORDSJAR_TEST_DB_DSN is set but the database is unreachable: {exc}")


@pytest.fixture
def make_user(client):
    """Sign up a fresh user and return ``(username, password)``."""

    def _make_user(prefix: str = "smoke") -> tuple[str, str]:
        username = unique_name(prefix)
        password = "Smoke!23456"
        response = client.post(
            "/api/v1/signup", json={"username": username, "password": password}
        )
        assert response.status_code == 201, response.text
        return username, password

    return _make_user


@pytest.fixture
def login(client):
    """Authenticate and return the token pair (``access_token``/``refresh_token``)."""

    def _login(username: str, password: str) -> dict:
        response = client.post(
            "/api/v1/auth", json={"username": username, "password": password}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"] and body["refresh_token"]
        return body

    return _login
