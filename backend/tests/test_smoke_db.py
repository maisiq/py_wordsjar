"""DB-backed smoke tests: the full user journey against a real PostgreSQL.

These run only when ``WORDSJAR_TEST_DB_DSN`` points at a reachable database.
The suite applies the alembic migrations to that database and writes test
data into it, so the DSN must reference a dedicated, disposable database::

    export WORDSJAR_TEST_DB_DSN=postgresql+psycopg://postgres:postgres@localhost:5432/wordsjar_test
    uv run pytest

All data is unique per run (uuid-suffixed usernames and words), so repeated
runs against the same database do not interfere with each other.
"""

import subprocess
import sys
import uuid

import pytest

from conftest import BACKEND_DIR, TEST_DB_DSN, sync_dsn

pytestmark = pytest.mark.skipif(
    not TEST_DB_DSN,
    reason="WORDSJAR_TEST_DB_DSN is not set; the DB-backed smoke suite is skipped",
)


@pytest.fixture(scope="session", autouse=True)
def migrated_database(db_required):
    """Apply the alembic migrations before the first DB-backed test.

    Runs in a subprocess: alembic's env.py reconfigures logging through
    ``fileConfig``, which would otherwise silence the application logger for
    the rest of the pytest session.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"


def sql(query: str, params: tuple = (), *, fetch: bool = False):
    """Run one statement against the test database with plain psycopg."""
    import psycopg

    with psycopg.connect(sync_dsn(TEST_DB_DSN), connect_timeout=5) as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall() if fetch else None
        conn.commit()
    return rows


@pytest.fixture
def seeded_word(db_required):
    """A word inserted straight into the dictionary.

    The API only lets admins add words and the first admin has to be made by
    hand, so seeding goes through SQL.
    """
    en = f"smoke{uuid.uuid4().hex[:12]}"
    ru = ["дым", "тестовое слово"]
    rows = sql(
        "INSERT INTO words (en, ru, transcription, examples) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (en, ru, "[sməʊk]", ["Smoke tests keep the build honest."]),
        fetch=True,
    )
    return {"id": rows[0][0], "en": en, "ru": ru}


def test_readyz_reports_the_database_as_up(client, db_required):
    response = client.get("/readyz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"
    assert body["pool"]["initialized"] is True


def test_unknown_word_is_a_clean_404(client, db_required):
    response = client.get(f"/api/v1/words/{uuid.uuid4().hex}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_forged_access_token_is_rejected(client, db_required):
    response = client.get("/api/v1/user/info", headers={"X-Auth-Token": "forged.token.value"})

    assert response.status_code == 401


def test_anonymous_can_browse_the_dictionary(client, db_required, seeded_word):
    response = client.get(
        "/api/v1/words", params={"sort": "id", "desc": "true", "per_page": 10}
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert seeded_word["en"] in {item["en"] for item in items}
    assert all(item["in_jar"] is False for item in items)


def test_full_user_journey(client, db_required, make_user, login, seeded_word):
    """signup -> login -> dictionary -> jar -> exam -> refresh -> logout."""
    username, password = make_user("journey")

    # Duplicate signup is a conflict, not a crash.
    response = client.post("/api/v1/signup", json={"username": username, "password": password})
    assert response.status_code == 409
    assert response.json()["code"] == "already_exists"

    # Wrong password is rejected with the generic credential error.
    response = client.post("/api/v1/auth", json={"username": username, "password": "WrongPass!1"})
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"

    tokens = login(username, password)
    auth = {"X-Auth-Token": tokens["access_token"]}

    response = client.get("/api/v1/user/info", headers=auth)
    assert response.status_code == 200
    assert response.json() == {"username": username, "role": "user"}

    # A regular user cannot write to the global dictionary.
    response = client.post(
        "/api/v1/words", headers=auth, json={"en": "hacked", "ru": ["взломано"]}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "http_403"

    # The seeded word is visible in the listing, in the search and on its
    # detail page — and it is not in the jar yet.
    response = client.get(
        "/api/v1/words", headers=auth, params={"sort": "id", "desc": "true", "per_page": 10}
    )
    assert response.status_code == 200
    page = response.json()
    assert {"items", "has_next", "has_prev", "next_cursor", "prev_cursor"} <= page.keys()
    assert seeded_word["en"] in {item["en"] for item in page["items"]}

    response = client.get("/api/v1/search", headers=auth, params={"query": seeded_word["en"]})
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["en"] for item in items] == [seeded_word["en"]]
    assert items[0]["in_jar"] is False

    response = client.get(f"/api/v1/words/{seeded_word['en']}")
    assert response.status_code == 200
    assert response.json()["en"] == seeded_word["en"]
    assert response.json()["ru"] == seeded_word["ru"]

    # Put the word into the jar; it shows up there and the search marks it.
    response = client.post(
        "/api/v1/jar", headers=auth, json={"words_en": [seeded_word["en"]], "status": "new"}
    )
    assert response.status_code == 201
    assert response.json() == {"count": 1}

    response = client.get("/api/v1/jar", headers=auth)
    assert response.status_code == 200
    assert [item["en"] for item in response.json()["items"]] == [seeded_word["en"]]

    response = client.get("/api/v1/search", headers=auth, params={"query": seeded_word["en"]})
    assert response.json()["items"][0]["in_jar"] is True

    # A fresh jar word is due for the exam right away.
    response = client.get("/api/v1/exam", headers=auth)
    assert response.status_code == 200
    exam_items = response.json()["items"]
    assert [item["en"] for item in exam_items] == [seeded_word["en"]]
    question = exam_items[0]

    # Answer correctly in the direction the exam asked for.
    answer = question["en"] if question["reverse"] else seeded_word["ru"][0]
    payload = {"word_id": question["id"], "answer": answer, "reverse": question["reverse"]}
    response = client.post("/api/v1/exam", headers=auth, json=payload)
    assert response.status_code == 200
    assert response.json() == {"result": True}

    # Answering again inside the cooldown is refused, not silently counted.
    response = client.post("/api/v1/exam", headers=auth, json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "not_due"

    # Deleting from the jar is idempotent.
    response = client.request(
        "DELETE", "/api/v1/jar", headers=auth, json={"word": seeded_word["en"]}
    )
    assert response.status_code == 200
    assert response.json()["deleted"] == 1

    response = client.request(
        "DELETE", "/api/v1/jar", headers=auth, json={"word": seeded_word["en"]}
    )
    assert response.json()["deleted"] == 0

    # Refresh rotates the session; the used token cannot be replayed.
    response = client.post(
        "/api/v1/refresh", headers={"X-Refresh-Token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    auth = {"X-Auth-Token": new_tokens["access_token"]}

    response = client.post(
        "/api/v1/refresh", headers={"X-Refresh-Token": tokens["refresh_token"]}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"

    # Logout revokes the access token: the profile is closed again.
    response = client.post("/api/v1/logout", headers=auth)
    assert response.status_code == 200
    assert response.json() == {"success": True}

    response = client.get("/api/v1/user/info", headers=auth)
    assert response.status_code == 401


def test_admin_can_add_words_to_the_dictionary(client, db_required, make_user, login):
    username, password = make_user("admin")
    # There is no self-service promotion in the API; the first admin is made
    # by hand, exactly like in a fresh deployment.
    sql("UPDATE users SET role = 'admin' WHERE username = %s", (username,))

    tokens = login(username, password)
    auth = {"X-Auth-Token": tokens["access_token"]}

    word = {
        "en": f"admin{uuid.uuid4().hex[:12]}",
        "ru": ["начальник"],
        "transcription": "[ˈædmɪn]",
        "examples": ["The admin added a word."],
    }
    response = client.post("/api/v1/words", headers=auth, json=word)
    assert response.status_code == 201
    assert response.json() == {"status": "ok"}

    # The same word twice is a conflict.
    response = client.post("/api/v1/words", headers=auth, json=word)
    assert response.status_code == 409
    assert response.json()["code"] == "already_exists"
