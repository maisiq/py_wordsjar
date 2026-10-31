**ROADMAP: wordsjar backend**
Status as of 2026-10-31. This document continues the [pre-production review plan](docs/preprod-backend-plan.md): all P0 items from it are closed in a separate branch stack; here is what to do next, in what order, and how to know when a stage is finished.

**Where we are now**
Fixes are in 7 branches on top of `5ef1d6f` (not yet merged into `master`):
| Branch | Commit | Topic |
| --- | --- | --- |
| chore/checkpoint-pending-work | 7737d6b | previously uncommitted WIP |
| chore/backend/config-and-lifecycle | 105ab64 | config, logs, pool, health, CORS |
| fix/api/error-contract | 7c66c14 | error codes and format |
| fix/api/auth-session-store | 0ebe39c | sessions in DB, argon2, rate limit |
| fix/api/pagination-cursor | 29c06a0 | cursor signing and validation |
| fix/api/exam-verify | b3371d2 | atomic answer recording, cooldown |
| fix/api/words-normalization | cd2f30b | word normalization, statuses |
| chore/db/timestamptz | e11f3ba | timestamptz, cascades, index |

Migrations: `b4a7c1e5d920` (auth_session) → `c8e5d2f41a33` (word normalization) → `d3f9a1c72b48` (timestamptz).
What is consciously left as is: `/jar` does not return `rating`; tests and CI were not added; the `rating <= 5.0` filter in the exam queue is a no-op (see item 2.5).

**0. First Deployment Blockers · 2–3 days · P0**
Cannot deploy without this, even with closed bugs.
| # | Task | Why | DoD |
| --- | --- | --- | --- |
| 0.1 | Merge branch stack (in order or via PRs) | fixes exist only in branches | `master` contains all 8 commits, git log is linear or PR history |
| 0.2 | Run migrations on prod data copy | `c8e5d2f41a33` merges duplicates and deletes rows, `d3f9a1c72b48` changes types | `alembic upgrade head` and `downgrade` pass on copy, word/row counts match expected |
| 0.3 | `WORDSJAR_BACKEND_JWT_KEY` in secrets | container lacks `key` file, app won't start without var | 32+ char key in docker secret/vault, not in image or git |
| 0.4 | Remove `network_mode: host`, switch to docker network | `host` breaks isolation and fails outside Linux hosts | `docker-compose.yml`: `backend` service reachable by name, nginx proxies to `backend:8080` |
| 0.5 | Do not expose Postgres externally, password from secret | currently `5432` with password in compose/.env | DB port not published, password comes from environment |
| 0.6 | TLS and headers in nginx | tokens in `X-Auth-Token` travel over network | http→https redirect, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, http2 |
| 0.7 | Proxy timeouts ≥ server timeouts | `statement_timeout=15s`, default nginx `proxy_read_timeout=60s` is ok, but must be explicit | agreed values in config, documented in docs |
| 0.8 | Backups + practice recovery | migrations are irreversible regarding merged duplicates | daily dump, 14-day retention, recovery to copy performed at least once |
| 0.9 | Health probes in orchestrator | endpoints exist, no one polls them | liveness: `/healthz`, readiness: `/readyz`, restart: `unless-stopped` |
| 0.10 | Log collection | currently JSON logs to stdout and nothing else | logs ship to Loki/vector, searchable by `request_id` |
| 0.11 | `.env` → environment variables | `.env` file must not end up in image | image without `.env`, config only via env |

**1. API Contract and Compatibility · 1 week · P1**
| # | Task | Comment |
| --- | --- | --- |
| 1.1 | Fix error format in OpenAPI schema | Describe `{"detail", "code", "request_id", "errors"?}` as a component, reference it in all responses; frontend already relies on `detail` |
| 1.2 | `Idempotency-Key` for `POST /jar` and `POST /exam` | double-click and retry on timeout currently yield 409 `not_due` / duplicates; key + response table (or at least "do not change rating twice within N seconds") |
| 1.3 | Decide fate of `409 not_due` | either keep (it's an honest conflict) or respond 200 with `applied: false` — decide with frontend and document |
| 1.4 | Do not expose internal sort fields in cursor | cursor is signed, but payload is base64: `field: ["rating","id"]` is readable; either encrypt or replace with opaque monotonic key |
| 1.5 | Versioning policy | `/api/v1` exists; document rule "breaking change → v2 + 3 months v1 support" |
| 1.6 | Prod CORS config | remove `localhost` origins from `WORDSJAR_BACKEND_CORS_ORIGINS` on prod; currently invalid ones are silently dropped with warning — ok, but prod list must be explicit |
| 1.7 | Limit `word` length in `GET /words/{word}` | currently `str` without bounds, while `refresh` handler is limited; minor, but saves DB traffic |

**2. Reliability and Data · 2–3 weeks · P1**
**2.1 Transactions and unit of work**
Repositories commit themselves (`session.commit()` inside methods). Works for single operations, but composite scenarios (add word + update jar, revoke token + write audit) are risky.
- [ ] One commit per HTTP request: `async with session.begin()` in dependency, repositories only `flush()`.
- [ ] Explicit rollback points, test "error in middle → nothing written".
- [ ] Remove `rollback()` from repositories, keep it in one place (currently scattered: `word.py`, `user.py`).

**2.2 Resilience to failures**
- [ ] Retries on transient connection errors (`OperationalError`, dropped connection) with backoff at request level, not entire loop.
- [ ] Request processing timeout (server `statement_timeout` exists, add `asyncio.timeout` for external calls).
- [ ] Periodic `auth_session` cleanup: `TokenStorage.cleanup_expired()` is implemented but not called — hook up on startup and hourly (asyncio task in lifespan).
- [ ] Rate limiter `_hits` growth limit exists (`_prune`), but with >1 worker the limiter "smears" — see 2.7.

**2.3 Migrations as a process**
- [ ] `alembic check` (autogenerate diff) in review: model and DB must not diverge.
- [ ] Rule: every migration must have a meaningful `downgrade`, tested on a copy.
- [ ] Document in docs: migrations `c8e5d2f41a33`/`d3f9a1c72b48` change data, backup required before them.

**2.4 Performance**
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` on real volumes for `/words`, `/search`, `/jar`, `/exam`; currently only prefix-search and exam index are checked — need full report.
- [ ] Verify `/words?sort=en` does not sort the whole table: `words_en_key` exists, but `ORDER BY en LIMIT n` + keyset is a candidate for index-only scan.
- [ ] `VACUUM/ANALYZE` after mass ETL loads; tune autovacuum for volume.
- [ ] Target metrics: p95 < 150ms at `per_page=30` with 20k words, 1k jar rows per user.

**2.5 Exam product logic (decide, then code)**
- [ ] Filter `rating <= 5.0` is a no-op, includes learned words. Likely should be `< 5.0` (do not ask learned words). Product decision.
- [ ] `attempts` resets to 1 on error, but points grow as `0.5 * attempts` — meaning rating accelerates on a streak of correct answers. Is this intended? Document formula.
- [ ] `reverse = idx % 2` — translation direction depends on output position, not word progress. After SRS (6.1), direction must be stored in data.

**2.6 Data and DB operations**
- [ ] `auth_session` storage policy (row TTL = token TTL, cleaned by task).
- [ ] Monitor table size and bloat.
- [ ] Verify `ON DELETE CASCADE` does not delete too much when deleting a word from the global dictionary: word deleted → disappears from all users' jars. Expected, but must be a conscious decision (alternative: soft delete word).

**2.7 Worker scaling**
- [ ] Currently `--workers 1` and in-memory limiter. If more are needed — Redis for rate limiting and optionally caching.
- [ ] Trust in `X-Forwarded-For`: currently takes first address from header — can be spoofed on direct backend access. Allow only via `--forwarded-allow-ips` from nginx.

**3. Security · 1–2 weeks · P1**
| # | Task | Comment |
| --- | --- | --- |
| 3.1 | Shorten access token TTL | currently 12 hours; with 7-day refresh, 30–60 mins is enough — smaller window for stolen token |
| 3.2 | Signing key rotation | need `kid` in header and support for two keys simultaneously, otherwise key change = mass logout |
| 3.3 | Reuse detection for refresh | reusing a refresh token currently yields 401; better to revoke all user sessions (sign of theft) |
| 3.4 | Audit of admin actions | `POST /words` (admin) is not logged as an action: who added what |
| 3.5 | Password leak checking | HIBP k-anonymity, optional, on registration/password change |
| 3.6 | Dependency scanning | `pip-audit` in CI (when CI exists), currently manual per sprint |
| 3.7 | Request body size limit | nginx `client_max_body_size` (1 MB) in addition to Pydantic limits |
| 3.8 | Secrets in repository | check history (`.env`, `key`) before publishing repo; `.gitignore` already covers `.env*` and `key*` |

**4. Observability · 1 week · P1**
- [ ] `/metrics` in Prometheus format: `prometheus-fastapi-instrumentator` + custom metrics — DB pool size, request duration per route, 4xx/5xx count, exam queue length.
- [ ] Dashboard: RPS, p50/p95/p99, error rate, pool, DB latency.
- [ ] Alerts: 5xx > 1% over 5 min, p95 > 500ms, `readyz` down, pool exhausted, free space < 15%, backup missed for 26 hours.
- [ ] Pass `request_id` to nginx access log (currently `X-Request-ID` header is returned, need to link logs).
- [ ] Tracing (OpenTelemetry) — optional, but helps catch N+1 in `/jar` and `/exam`.
- [ ] External synthetics: login + one request per minute from outside.

**5. Quality: Tests and CI · 2 weeks · P2 (consciously postponed)**
Currently no tests or CI — this was a decision, not an oversight. When ready:
- [ ] `pytest` + `httpx.ASGITransport` for routes, real Postgres in `testcontainers` for repositories.
- [ ] Test pyramid: unit for services (no DB), integration for repositories, contract for routes (error codes and bodies).
- [ ] `ruff` (lint + format) and `mypy`/`pyright` in pre-commit.
- [ ] CI: lint → types → migrations on clean DB → tests → image build → tag.
- [ ] Contract API checks against OpenAPI (schemathesis) — catches error format regressions.
- [ ] Seed data for local dev (dictionary + user) instead of manual INSERTs.
- [ ] CHANGELOG and rule "one change — one Conventional Commits commit".

**6. Product Horizon · Quarter+ · P2**
- **Spaced Repetition (SRS):** Replace "rating + 1 day" with `due_at` and intervals (1 → 3 → 7 → 14 → 30 days, step back on error). Changes schema (`user_word.due_at`, `interval_days`), `/exam` and `/exam POST` logic. Most valuable product step: current repetition model is linear and non-adaptive.
- **Translation direction as data:** Currently direction is a function of list position. Need progress per (word, direction) pair or at least per word.
- **Progress statistics:** Endpoints "how many learned / in progress / streak" for the main page; currently frontend calculates this itself or not at all.
- **Search:** `startswith` works only for exact word beginnings; `pg_trgm` + `unaccent` will enable typo-tolerant and Cyrillic search, plus ranking.
- **ETL as a separate process:** `ETL/` catalog outside git: loading must be idempotent (`ON CONFLICT DO NOTHING`), normalize word before insertion (unique `lower(en)` now prevents duplicates but crashes on "Apple" in CSV), and log load report.
- **Jar import/export (CSV/Anki):** frequent user request for dictionaries.
- **Pronunciation and examples:** `transcription` exists, audio does not yet.

**7. Technical Debt · P2, as touched**
- [ ] `backend/app/core/config.yaml` — dead file, not read; delete.
- [ ] Duplicate entry points: `Taskfile.yml`, `backend/start.sh`, `backend/entrypoint.sh` — keep one launch method and document it.
- [ ] Logger name `"main"` → `"wordsjar"`.
- [ ] Global settings (`config.init()` + `get_*_settings()`) → DI/`app.state`, so tests can spin up app with different config.
- [ ] `api/v1/schemas.py` has grown — split by feature next to routes.
- [ ] `frontend/` not in git: either in this repo or separate with its own CI.
- [ ] Root contains `words.zip`, `words-freq.zip`, `vanilla_frontend__depr.rar` — move to `.gitignore` or artifacts, not working directory.
- [ ] `docker-compose.yml`, `Dockerfile`, `nginx.conf` not in git — either in repo or separate deploy repo (otherwise nothing to review or rollback).

**8. Work Order**
| Sprint | Duration | Content |
| --- | --- | --- |
| S0 | 2–3 days | Section 0 entirely: merge, migrations, secrets, network, TLS, backups, probes |
| S1 | 1 week | 1.1–1.3 (contract, idempotency) + 4.1–4.3 (metrics, dashboard, alerts) |
| S2 | 1 week | 3.1–3.4 (TTL, kid, reuse detection, audit) + 1.4 (cursor) |
| S3 | 1–2 weeks | 2.1–2.4 (unit of work, retries, cleanup, EXPLAIN) |
| S4 | 2 weeks | 2.5 + 6.1 (exam decision and SRS) |
| S5 | 2 weeks | Section 5 (tests and CI) — when agreed it's time |

**Rule:** Until S0 is closed, new features do not start. S1–S3 can be done in parallel with product work, they do not change the API contract for the frontend.

**9. "Ready for Prod Operation" Criteria**
- [ ] 0 unhandled 500s per day under normal traffic (all errors are 4xx with clear `code`).
- [ ] p95 < 150ms on `/words`, `/jar`, `/exam` at `per_page=30`.
- [ ] Cold start < 3s, `readyz` green within 5s of startup.
- [ ] Backup recovery tested on copy, recovery time known.
- [ ] Alerts go to a channel that is actually read; there is an on-call person.
- [ ] JWT key and DB password rotation documented and performed at least once.
- [ ] All migrations apply to an empty DB from scratch (`upgrade head` on clean volume).

**Appendix A. Release Checklist**
```bash
# 1. Backup
pg_dump "$DSN" > backup_$(date +%F_%H%M).sql

# 2. Migrations
cd backend && alembic current && alembic upgrade head && alembic current

# 3. Smoke
curl -fsS https://api.example/healthz
curl -fsS https://api.example/readyz
curl -fsS "https://api.example/api/v1/words?per_page=1" | head -c 200
curl -sS -o /dev/null -w '%{http_code}\n' https://api.example/api/v1/words/zzzz   # 404 + code=not_found
curl -sS -o /dev/null -w '%{http_code}\n' "https://api.example/api/v1/words?per_page=0"  # 422

# 4. Rollback on problem
cd backend && alembic downgrade -1   # remember: c8e5d2f41a33 does not restore merged duplicates
```

**Appendix B. Known Limitations After the Stack**
| Limitation | Impact | When to fix |
| --- | --- | --- |
| Rate limit in process memory, `--workers 1` | limits weaken when scaling | 2.7, before moving to >1 worker |
| Cursor payload readable in base64 | sort fields visible, but not data | 1.4 |
| Access token lives 12 hours | larger window for stolen token | 3.1 |
| `rating <= 5.0` is a no-op | learned words appear in exam | 2.5 (decision) |
| `reverse` by index parity | translation direction unpredictable | 6.2 |
| No tests and CI | regressions caught manually | 5 |
| Deploy files outside git | nothing to review or rollback | 7 |
| ETL outside git and without idempotency | duplicates/crashes on reload | 6.5 |
