# MEMORY — what an agent must know about wordsjar

Read this before touching code, then read [ROADMAP.md](ROADMAP.md) — the project rules require checking it
before starting any task. The file map lives in [INDEX.md](INDEX.md); this file is the operational picture.

## 1. What the project is

A vocabulary trainer: the user browses an English→Russian dictionary, puts words into a "jar" and passes
an exam on them. Three parts, no shared package and no monorepo tooling:

- `backend/` — FastAPI + SQLAlchemy 2 async + PostgreSQL, Alembic migrations, JWT auth.
- `frontend/` — React 19 SPA (Vite, Bootstrap 5), talks to the backend over `/api/v1`.
- `ETL/` — a one-off scraper that produced the word list. Not wired into the app in any way.

## 2. House rules (from AGENTS.md — non-negotiable)

- Thinking, code, comments, docstrings, commit messages and files: **English**. Replies to the user: **Russian**.
- Commits: Conventional Commits (`fix(api): ...`, `chore(db): ...`).
- Python: PEP8, double-quoted strings. Comments explain **why**, never restate the next line, never
  reference the dialogue ("as discussed", "temporary fix").
- **Do not install new dependencies without confirmation.**
- Do not start work outside the current ROADMAP phase without asking; mark finished items `[x]` in
  `ROADMAP.md` and move the `(<- CURRENT TASK)` marker.

## 3. Running it locally (Windows, current checkout)

Backend (imports are flat, so the working directory must be `backend/app`):

```powershell
cd backend\app
..\.venv\Scripts\python.exe -m uvicorn --reload --host 0.0.0.0 --port 8080 --factory main:init
# or from the repo root: task back   (Taskfile.yml)
```

Frontend (dev server is bound to a host name, not localhost):

```powershell
cd frontend
npm ci          # once
npm run dev     # http://frontend.local.test:3000
npm run lint    # oxlint
npm run build   # production bundle in dist/
```

`frontend.local.test` must exist in the OS hosts file (`127.0.0.1 frontend.local.test`), otherwise the dev
server is unreachable by that name. Vite proxies `/api/v1` to `VITE_DEV_PROXY_TARGET`
(default `http://localhost:8080`), so the browser sees a single origin and CORS stays out of the picture.

Migrations (run from `backend/`, `env.py` imports `app.models.orm`):

```powershell
cd backend
$env:WORDSJAR_BACKEND_DB_DSN = "postgresql+psycopg://..."
alembic upgrade head
alembic current
```

`migrations/env.py` reads `WORDSJAR_BACKEND_DB_DSN` and also loads `backend/app/.env` via python-dotenv, so
a local `.env` is usually enough. `alembic.ini` takes the URL from that variable through `%(DB_URI)s`.

Docker: `docker compose up -d --build` builds both images. **Requires a root `.env`** (`env_file: .env`),
which is not in the working tree; the backend service runs with `network_mode: host` and nginx reaches it
through `host.docker.internal:8080`. Closing that (docker network, no host mode, no root `.env` in the
image) is ROADMAP item 0.4/0.5/0.11 — do not "fix" it as a side quest.

## 4. Configuration

Every backend setting is an environment variable with the `WORDSJAR_BACKEND_*` prefix; an optional
`backend/app/.env` is read on top (gitignored). Defaults come from `backend/app/core/config.py`.

| Variable | Default | Notes |
| --- | --- | --- |
| `WORDSJAR_BACKEND_DB_DSN` | *required* | async DSN, e.g. `postgresql+psycopg://user:pass@host/db` |
| `WORDSJAR_BACKEND_DB_ECHO` | `false` | SQL echo |
| `WORDSJAR_BACKEND_DB_POOL_SIZE` / `_MAX_OVERFLOW` / `_POOL_TIMEOUT` / `_POOL_RECYCLE` / `_POOL_PRE_PING` | `5` / `10` / `10.0` / `1800` / `true` | pool tuning |
| `WORDSJAR_BACKEND_DB_CONNECT_TIMEOUT` / `_STATEMENT_TIMEOUT_MS` / `_LOCK_TIMEOUT_MS` | `5` / `15000` / `5000` | applied as libpq `options` |
| `WORDSJAR_BACKEND_JWT_KEY` | — | signing key, **min 32 chars**, otherwise startup raises |
| `WORDSJAR_BACKEND_JWT_KEY_FILE_PATH` | `app/key` | used when `JWT_KEY` is empty (local dev file) |
| `WORDSJAR_BACKEND_JWT_CURSOR_SECRET` | derived from the signing key | dedicated secret for pagination cursors |
| `WORDSJAR_BACKEND_JWT_ACCESS_TOKEN_TTL` / `_REFRESH_TOKEN_TTL` | `43200` (12 h) / `604800` (7 d) | seconds |
| `WORDSJAR_BACKEND_JWT_ISS` / `_ALGORITHM` | `wordsjar` / `HS256` | |
| `WORDSJAR_BACKEND_APP_DEBUG` | `false` | debug also means console logs and docs |
| `WORDSJAR_BACKEND_APP_ENVIRONMENT` | `local` | `local` / `staging` / `production` |
| `WORDSJAR_BACKEND_APP_DOCS_ENABLED` | follows `debug` | `/docs` and `/openapi.json` |
| `WORDSJAR_BACKEND_CORS_ORIGINS` | `[]` | JSON list; entries without `http(s)://` are dropped with a warning |
| `WORDSJAR_BACKEND_CORS_ALLOW_METHODS` / `_ALLOW_HEADERS` | `GET,POST,DELETE,OPTIONS` / `Content-Type, X-Auth-Token, X-Refresh-Token, X-Request-ID` | |
| `WORDSJAR_BACKEND_CORS_ALLOW_CREDENTIALS` | `false` | wildcard origin plus credentials is logged as a warning |

The local `backend/app/.env` in this checkout sets `APP_DEBUG=True` and a localhost DSN, so runs here default
to coloured console logs and an open `/docs`.

Frontend: `VITE_API_BASE_URL` (default `/api/v1`) and `VITE_DEV_PROXY_TARGET` only. They are baked in at
build time. A build with a `localhost`/`127.0.0.1` API URL is refused on purpose (`vite.config.js`).

## 5. Architecture in one screen

Request flow: route → `api/deps.py` provider → service → repository → SQLAlchemy → PostgreSQL. Routes hold
no business logic and no SQL; services raise `core.errors.AppError` subclasses that already carry the HTTP
status and a stable `code`; `api/errors.py` is the single place that turns them into JSON.

- **Sessions**: `get_session` yields an `AsyncSession` and rolls back on any escaping exception.
  Repositories call `session.commit()` themselves — there is no request-level unit of work yet
  (ROADMAP 2.1).
- **Errors**: body is always `{"detail", "code", "request_id"}` (+ `errors` for 422). Unhandled exceptions
  become `500 internal_error` from `api/middleware/error.py`. `X-Request-ID` is echoed back and is present
  on every log line.
- **Auth**: tokens travel in the `X-Auth-Token` / `X-Refresh-Token` headers, never cookies. Access token is
  a JWT (HS256, `sub` = username, `role` claim); refresh tokens are opaque strings stored in
  `auth_session` as sha256. Refresh is single-use rotation: `consume()` does `DELETE ... RETURNING`, so a
  replayed refresh token gets `401 invalid_token`. Logout stores the access token hash with `kind="access"`
  until it expires, and every authenticated request checks `is_revoked`.
- **Roles**: `Security(get_userdata_strict, scopes=[...])` — `["user", "admin"]` on `/jar`, `["admin"]` on
  `POST /words`, no scope list (any valid token) on `/user/info`, `/logout` and both `/exam` routes; an
  anonymous caller gets 401, a valid token with the wrong role gets 403. `get_userdata` is the optional
  variant used by `GET /words` and `/search` to fill `in_jar`. No endpoint creates an admin — signup always
  writes `role="user"`, so the first admin has to be set in the database by hand.
- **Pagination**: keyset, signed cursor (base64 payload + HMAC), `Paginated[T]` with
  `items/has_next/has_prev/next_cursor/prev_cursor`. `per_page` max 100; search caps at 50 and is not
  paginated. Cursors are validated per endpoint: unknown sort field, bad signature, or a value that does
  not match the column are all `400 invalid_cursor`. `id` is always appended as a tiebreaker.
- **Word normalisation**: `normalize_word()` (lowercase + strip) on every read and write; the DB enforces
  uniqueness on `lower(btrim(en))`. `"Apple"` and `"apple"` are the same word.
- **Exam rating policy** (in `repository/jar.py`): correct → `rating += 0.5 * max(attempts, 1)` and
  `attempts += 1`; wrong → `attempts = 1`, `rating -= 0.25`; clamped to `[0.0, 5.0]`. A word is due again
  after `COOLDOWN = 1 day`; answering earlier is `409 not_due`. The update and the cooldown check are one
  atomic `UPDATE ... WHERE last_attempt < cutoff ... RETURNING`, so two parallel answers cannot both win.
  The queue query filters `rating <= MAX_RATING` (5.0), which is currently a **no-op** — a known issue,
  not a bug to fix silently (ROADMAP 2.5). `reverse` is set by the service as `idx % 2 == 0`.
- **Rate limiting**: in-process fixed windows keyed by client IP — login 10/min, signup 5/h, refresh 30/min,
  answering with `429` + `Retry-After`. Client IP comes from `X-Forwarded-For` (first value) or `X-Real-IP`.
  This only works with a single uvicorn worker (ROADMAP 2.7).
- **Logging**: `logger.init(debug, json_logs=not debug)` — JSON lines externally, coloured console in debug.
  The logger is named `"main"` (`LOGGER_NAME`), which the roadmap wants renamed (7.3).

## 6. Deliberate simplifications — do not "fix" without a decision

These are conscious choices recorded in `ROADMAP.md`; changing them is a task, not a cleanup:

- No tests and no CI anywhere (ROADMAP 5). Backend has no linter or formatter config either; keep PEP8 by hand.
- `cleanup_expired()` and `delete_for_user()` exist in `repository/token.py` but are **never called** —
  expired `auth_session` rows accumulate (ROADMAP 2.2).
- `rating <= 5.0` in the exam queue includes learned words; `reverse` depends on list position, not on
  per-word progress; the rating formula accelerates on streaks (ROADMAP 2.5).
- Cursor payload is readable base64 under the signature (ROADMAP 1.4); access token lives 12 h (3.1).
- `POST /jar` and `POST /exam` have no `Idempotency-Key` (1.2); double-clicking can produce a `409`.
- `backend/app/core/config.yaml` is a dead file (7.1). Duplicate ways to start the backend:
  `Taskfile.yml`, `backend/start.sh`, `backend/entrypoint.sh` (7.2).
- Deployment files (`docker-compose.yml`, the Dockerfiles, `nginx.conf`) are outside git (7.7), as are
  `frontend/` and `ETL/`.
- ETL is idempotency-free: it appends `words.csv` without a header and without deduplication, words are
  not normalised before insert, and the `count > 200_000` cutoff ends a run with a `RuntimeError`
  (`StopIteration` raised inside a generator); loading the CSV into `words` is manual (6.5).

### Dead names and traps (verified by reading, not guesses)

- Nothing reads `backend/app/core/config.yaml`. The CORS values in it (wildcard methods/headers,
  `credentials: true`) have **no effect** — real CORS comes from `WORDSJAR_BACKEND_CORS_*`, and origins
  without a scheme are dropped with a warning, so most entries in the local `.env` never apply.
- `WORDSJAR_BACKEND_WORK_DIR` in `backend/app/.env` maps to no settings field.
- Declared but unused: the `cachetools` dependency, `Roles.ANY`, `Word.is_valid_sort_field`,
  `RateLimiter.reset`, `AuthService.get_user`, `schemas.GetWordResponse` and `GetJarWordResponse`.
- `backend/app/.env` holds a hardcoded Postgres password (gitignored — never commit or print it), and
  `backend/app/key` is the local signing key that is **not** listed in `backend/.dockerignore`, so
  `COPY app/ app/` currently ships it inside the image.
- `backend/entrypoint.sh` runs `alembic upgrade head` (needs CWD `/app`, imports `app.models.orm`) and then
  `uvicorn --factory main:init` from that same directory, while `main.py` uses flat imports and lives in
  `/app/app`. The two steps want different working directories; verify a real container boot before
  trusting the deploy path (`--app-dir app` is the likely fix).
- Known layer inversions: `repository/word.py` imports the domain `Word` from `services.words`, and
  `api/deps.py` wires `JarRepository` into `ExamService`. Do not copy either pattern.

## 7. Repository state (this checkout)

- Branch `chore/db/timestamptz` is **9 commits ahead of `master`** (master tip `21d0cc8`); nothing is
  merged. The oldest commit of the stack is `5ef1d6f`, which `ROADMAP.md` calls the base of the review fix
  stack. Merge order and the branch list are in `ROADMAP.md` under "Where we are now"; ROADMAP item 0.1 is
  exactly "merge the stack".
- Untracked in the working tree: `frontend/`, `ETL/`, `Taskfile.yml`, `docker-compose.yml`, `AGENTS.md`,
  `ROADMAP.md`, `INDEX.md`, `MEMORY.md`, the Dockerfiles, `backend/entrypoint.sh`, `backend/start.sh`,
  `backend/app/core/config.yaml`. `docs/` is empty even though `ROADMAP.md` links a plan file in it.
- Ignored and never edit as source: `.venv/`, `node_modules/`, `dist/`, `*.rar`, `words*.zip`, `.env*`,
  `key*`.
- The app currently cannot run without a Postgres instance and a valid signing key; `main.init()` fails at
  startup, by design, when the key is missing or shorter than 32 characters.

## 8. Working agreements that save time

- Change the backend through the layer it belongs to: SQL only in `repository/`, decisions in `services/`,
  HTTP shape in `api/v1/`. A guard added in a route instead of a service will be missed by the other caller.
- The frontend depends on the backend's error `detail` strings and status codes (`src/api/errors.js` maps
  them to Russian). Changing an error message is an API change: check that file too.
- `frontend/src/api/axios.js` auto-refreshes on 401, but there is no redirect on a failed refresh — pages
  rely on the route guard. Keep that in mind when "fixing" auth UI.
- Prefer reading `frontend/README.md` for frontend specifics and [INDEX.md](INDEX.md) for file locations.
- Backend has no test suite, so verify changes by running the endpoint (`uvicorn` + `curl`) and, for
  migrations, `alembic upgrade head` followed by `alembic downgrade -1` on a copy.
