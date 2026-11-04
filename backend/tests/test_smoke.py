"""HTTP-layer smoke tests: no database, no external services.

The app is built by the real factory (``main.init``) against an unreachable
DSN, so this module proves that the process boots, the routes are registered,
authentication guards fire before any storage access, request validation
works, and errors come back in the stable envelope the frontend relies on.

The DB-backed user journey lives in ``test_smoke_db.py``.
"""

import pytest

from conftest import TEST_DB_DSN

#: Every route the API promises; a rename that forgets one of them fails here.
EXPECTED_PATHS = {
    "/healthz",
    "/readyz",
    "/api/v1/signup",
    "/api/v1/auth",
    "/api/v1/user/info",
    "/api/v1/logout",
    "/api/v1/refresh",
    "/api/v1/words",
    "/api/v1/words/{word}",
    "/api/v1/search",
    "/api/v1/jar",
    "/api/v1/exam",
}

#: Endpoints that must never serve an anonymous caller.
PROTECTED_REQUESTS = [
    ("GET", "/api/v1/jar"),
    ("POST", "/api/v1/jar"),
    ("DELETE", "/api/v1/jar"),
    ("GET", "/api/v1/exam"),
    ("POST", "/api/v1/exam"),
    ("GET", "/api/v1/user/info"),
    ("POST", "/api/v1/logout"),
    ("POST", "/api/v1/words"),
]


def test_app_boots_and_registers_every_route(app):
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)
    registered = {route.path for route in app.routes}
    missing = EXPECTED_PATHS - registered
    assert not missing, f"routes missing from the app: {sorted(missing)}"


def test_healthz_answers_without_a_database(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_the_database_as_down(client):
    """The app runs against an unreachable DSN, so the readiness probe must
    refuse traffic (503) instead of pretending everything is fine."""
    if TEST_DB_DSN:
        pytest.skip("covered by test_smoke_db.py when a database is configured")

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}


def test_openapi_schema_is_served(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "wordsjar"
    for path in ("/api/v1/signup", "/api/v1/auth", "/api/v1/words", "/api/v1/jar", "/api/v1/exam"):
        assert path in schema["paths"], f"{path} is missing from the OpenAPI schema"


def test_unknown_route_returns_the_error_envelope(client):
    response = client.get("/api/v1/definitely-not-here")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "http_404"
    assert body["detail"]
    assert body["request_id"]


def test_request_id_is_echoed_back(client):
    response = client.get("/healthz", headers={"X-Request-ID": "smoke-42"})

    assert response.headers["X-Request-ID"] == "smoke-42"


@pytest.mark.parametrize(("method", "path"), PROTECTED_REQUESTS)
def test_protected_endpoints_reject_anonymous_callers(client, method, path):
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.json()["code"] == "http_401"


def test_refresh_without_a_token_is_rejected(client):
    response = client.post("/api/v1/refresh")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_signup_validates_the_payload(client):
    response = client.post("/api/v1/signup", json={"username": "ab", "password": "short"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    fields = {error["field"] for error in body["errors"]}
    assert {"body.username", "body.password"} <= fields


def test_search_requires_a_query_of_at_least_two_characters(client):
    response = client.get("/api/v1/search", params={"query": "a"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_words_reject_an_unknown_sort_field(client):
    response = client.get("/api/v1/words", params={"sort": "password"})

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_sort_field"


def test_words_reject_a_forged_cursor(client):
    response = client.get("/api/v1/words", params={"cursor": "not-a-real-cursor"})

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_cursor"
