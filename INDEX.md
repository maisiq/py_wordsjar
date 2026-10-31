# Project structure

`wordsjar` is an English→Russian vocabulary trainer: a FastAPI/PostgreSQL backend, a React SPA and a
scraper that builds the word list. This file maps the repository so a reader (human or agent) can find
the right file without searching. Operational knowledge — how to run, configure and extend it — lives in
[MEMORY.md](MEMORY.md).

## Top level

| Path | What it is |
| --- | --- |
| `backend/` | FastAPI application: routes, services, repositories, ORM models, Alembic migrations |
| `frontend/` | React 19 SPA (Vite, Bootstrap 5); has its own [README](frontend/README.md) |
| `ETL/` | Standalone scraper that fills `words.csv` from an external dictionary site |
| `docs/` | Documentation directory (currently empty; [ROADMAP.md](ROADMAP.md) references a missing `docs/preprod-backend-plan.md`) |
| `AGENTS.md` | Rules for agents working in this repository |
| `ROADMAP.md` | Current phase, ordered task list, release checklist |
| `MEMORY.md` | Project knowledge an agent needs before touching code |
| `Taskfile.yml` | Task shortcuts for local development (`back`, `react`, `run`; the `van` task is stale) |
| `docker-compose.yml` | Backend + frontend containers (backend uses `network_mode: host`) |
| `words.zip`, `words-freq.zip` | Word-list dumps used by the ETL; gitignored, not source |

## Backend (`backend/`)

The application is run with `backend/app` as the working directory, so its modules are imported as
top-level packages (`api`, `core`, `db`, `models`, `repository`, `services`, `logger`) — not as `app.*`.
That is why the tree below starts inside `app/`.

```
backend/
  Dockerfile            python:3.12-slim image, uv-managed venv, entrypoint runs migrations
  entrypoint.sh         alembic upgrade head, then uvicorn (1 worker, concurrency 200)
  start.sh              dev server: uvicorn --reload, same flags as entrypoint
  alembic.ini           script_location = migrations, url = %(DB_URI)s
  pyproject.toml        dependencies (no dev group, no test tooling)
  uv.lock               locked dependency graph
  .python-version       3.12
  app/
    main.py             app factory init(): settings, logging, pool, middlewares, routers, handlers
    key                 JWT signing key file for local dev (gitignored)
    .env                local settings, loaded by core.config (gitignored)
    core/
      config.py         pydantic-settings classes: App, Database, JWT, CORS + init()/get_*_settings()
      config.yaml       DEAD FILE: never read by any module
      errors.py         domain errors carrying status_code and machine-readable code
    db/
      postgres.py       async engine/sessionmaker, check_connection(), pool_status(), dispose()
    logger/
      logger.py         logging init, request id contextvar, JSON and console formatters
      __init__.py       re-exports get_logger, get_request_id, set_request_id, reset_request_id
    models/
      domain.py         pydantic domain models (Word, TestWord, JarWord, UserWord, User, Tokens) + enums
      orm.py            SQLAlchemy tables: users, words, user_word, auth_session
      mappers.py        ORM rows → domain models
    repository/
      __init__.py       re-exports JarRepository, SecretRepository, TokenStorage, UserRepository, WordRepository
      word.py           dictionary queries: list, search, get by word/id, insert
      jar.py            user_word queries: list with sort/cursor, add, delete, apply_answer, exam queue
      user.py           users queries: get by username, insert
      token.py          auth_session rows: store, consume (DELETE..RETURNING), is_revoked, revoke all, cleanup
      secret.py         process-wide cached JWT signing key and cursor secret
      columns.py        explicit {sort name: column} maps and cursor value coercion
      params.py         QueryParams passed from pagination down to repositories
    services/
      __init__.py       re-exports AuthService, ExamService, JarService, WordService
      auth.py           signup, sign-in, user info, refresh rotation, logout
      words.py          dictionary reads and admin add
      jar.py            add words to jar, list jar, delete from jar
      exam.py           exam queue, answer checking, answer recording, cooldown
      pagination.py     keyset pagination: signed cursors, Paginated[T], parse/validate helpers
      ratelimit.py      in-process fixed-window limiters (login 10/min, signup 5/h, refresh 30/min)
      helpers.py        argon2 hashing, JWT encode/decode, word/username normalisation
    api/
      deps.py           DI providers: session, repositories, services, auth dependencies, rate limits
      errors.py         exception handlers: AppError, HTTPException, RequestValidationError → JSON body
      middleware/
        request.py      request id, access log line, client_ip()
        error.py        last-resort 500 handler for anything that escaped the exception handlers
      v1/
        router.py       APIRouter(prefix="/api/v1") wiring the four feature routers
        schemas.py      request/response bodies (auth, jar, words, exam)
        mappers.py      domain Word → API Word
        routes/
          health.py     /healthz (liveness), /readyz (DB readiness), outside /api/v1
          auth.py       /signup, /auth, /user/info, /logout, /refresh
          words.py      /words (list, admin add), /search, /words/{word}
          jar.py        /jar (list, add, delete)
          exam.py       /exam (queue, answer)
  migrations/
    env.py              alembic environment; imports app.models.orm.Base, reads WORDSJAR_BACKEND_DB_DSN
    versions/           migrations, in order:
                          506c42677451 initial schema
                          1876d43d3995 search index
                          b4a7c1e5d920 auth_session table
                          c8e5d2f41a33 normalise words (merges duplicates)
                          d3f9a1c72b48 timestamptz + cascades
```

## Backend HTTP surface

`/api/v1` prefix unless noted. Auth is carried by the `X-Auth-Token` header (`X-Refresh-Token` for refresh).

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/healthz` | — | liveness, no DB access |
| GET | `/readyz` | — | readiness: DB ping + pool counters |
| POST | `/api/v1/signup` | — | create user (rate limited) |
| POST | `/api/v1/auth` | — | sign in, returns access + refresh tokens (rate limited) |
| GET | `/api/v1/user/info` | access | current username and role |
| POST | `/api/v1/logout` | access | revoke tokens |
| POST | `/api/v1/refresh` | refresh header | rotate tokens (rate limited) |
| GET | `/api/v1/words` | optional | paginated dictionary; `in_jar` set for signed-in users |
| POST | `/api/v1/words` | admin | add a word to the global dictionary |
| GET | `/api/v1/words/{word}` | — | one word |
| GET | `/api/v1/search?query=` | optional | prefix/word search, `per_page` capped at 50, not cursor paginated |
| GET | `/api/v1/jar` | user, admin | paginated jar, `order_by` + `desc` |
| POST | `/api/v1/jar` | user, admin | add up to 1000 words, optional `status` |
| DELETE | `/api/v1/jar` | user, admin | remove one word (payload in the request body) |
| GET | `/api/v1/exam` | any signed-in | exam queue, fixed sort `rating, last_attempt, id` |
| POST | `/api/v1/exam` | any signed-in | check and record an answer (`word_id`, `answer`, `reverse`) |

Errors use one shape everywhere: `{"detail": str, "code": str, "request_id": str}` plus `errors` for
validation failures.

## Frontend (`frontend/`)

```
frontend/
  package.json          React 19, vite 8, oxlint; scripts: dev, build, lint, preview
  vite.config.js        dev host frontend.local.test:3000, proxy /api/v1, refuses localhost API in build
  index.html            SPA shell
  Dockerfile            node:22 build stage → nginx:alpine runtime with HEALTHCHECK
  docker/
    nginx.conf          SPA fallback, static caching, /api/v1 proxy to the backend, /healthz
    security-headers.conf  CSP and security headers (HSTS left to the TLS terminator)
  public/               favicon.ico, delete-word-x.png
  src/
    main.jsx            mount: StrictMode > ErrorBoundary > Router > AuthProvider > App + Toaster
    App.jsx             routes and footer
    api/
      axios.js          axios instance, localStorage token store, 401 auto-refresh
      errors.js         backend error → Russian user-facing message
    context/AuthContext.jsx   user state, login/register/logout
    hooks/
      useCursorPagination.js  cursor pagination with stale-response protection
      useDeleteWord.js        shared "remove from jar" flow with confirm modal state
    routes/ProtectedRoute.jsx redirect to /login preserving the target
    pages/              Home (list + search), Jar, Exam (lazy chunk), Login, Registration, NotFound
    components/         Layout, Sidebar, Logo, Menu, SearchBar, AuthButton, WordCard,
                        WordDetailModal, AddWordForm (admin), AddToJarModal, DeleteWordModal,
                        Pagination, SortDropdown, BackButton, ErrorBoundary
    styles/main.css     single global stylesheet on top of Bootstrap
    utils/password.js   password strength check used by the registration form
    assets/             UNUSED images: hero.png, second.png, third.png, icons.svg
```

Routes: `/` (Home), `/jar` and `/tests` (protected), `/login`, `/signup`, `*` → NotFound.

## ETL (`ETL/`)

```
ETL/
  main.py             scraper/parser: unigram_freq.csv → word pages → words.csv (SQL array literals)
  unigram_freq.csv    input word list with frequencies (untracked, large)
  current_row         resume checkpoint: line number already consumed
  ETL_run_archive.rar previous run output (gitignored)
  pyproject.toml      beautifulsoup4 + requests, Python 3.12
```

The ETL does not touch the database: it writes a CSV that is loaded into `words` separately. It is not
in git, has no idempotency and no tests — see `ROADMAP.md` section 6 for the planned rework.
