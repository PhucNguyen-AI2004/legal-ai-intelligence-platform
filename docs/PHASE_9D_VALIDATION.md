# Phase 9D — Integration / Hardening Regression

Status: **Phase 9D — Integration / Hardening Regression: PASS — OWNER ACCEPTED.** Phases 9A–9C are owner accepted. Phase 9 — Production Engineering: PASS — COMPLETE. Phase 10 has not started.

## Scope and architecture findings

Inspected HEAD `46ef5c8`, migration head `0006_user_roles`, production middleware/readiness, Redis rate limiting, RQ queue/worker, owner-scoped document/search/RAG/chat/admin contracts, frontend polling, and Compose. The topology remains `postgres`, `redis`, `backend`, and `worker`; Redis has AOF everysec plus `redis_data`, no host port; the worker has no host port and shares document/model-cache volumes. PostgreSQL persistence is unchanged.

No migration or production-code fix was required. Existing behavior composes safely: rate limiting resolves before route work; owned rows are locked and claimed before enqueue; enqueue failure restores authoritative state; duplicates receive 409; worker execution reloads authoritative state; duplicate/stale delivery cannot replace chunks or embeddings after terminal completion; bounded retry exhaustion records a safe failure.

## Automated integration matrix

The new focused suite covers 401/404/409/422/503/500 request IDs and security headers, Redis limiter rejection before queue work, safe queue rollback, duplicate process/index worker delivery, foreign-owner document/process/index/chunk/RAG denial, sanitized correlated 500s, and log sentinels. Existing full-suite coverage continues to prove owner-filtered search, RAG document scope, conversation ownership/persistence/citations, admin 401/403/200, readiness, atomic Lua rate limiting, and worker retry/failure behavior.

Frontend regression verifies active-state-only polling, one timeout per render cycle, cleanup on rerender/unmount, finite 40-attempt budget, authoritative refetch after action errors, and no false completion feedback. UI/UX Pro Max guidance confirmed the existing explicit feedback, disabled actions, cleanup, and error visibility; no redesign was appropriate.

## Exact automated results

| Command | Result |
| --- | --- |
| `python -m compileall -q app tests` | PASS |
| focused `tests/test_phase9d_hardening.py` | 9 passed, 3 warnings |
| Phase 9A `tests/test_production_foundation.py` | 10 passed, 3 warnings |
| Phase 9B `tests/test_rate_limiting.py` | 14 passed, 3 warnings |
| Phase 9C `tests/test_background_jobs.py` | 11 passed, 3 warnings |
| full backend suite | 226 passed, 2 skipped, 6 subtests passed, 17 warnings |
| `docker compose config --quiet` | PASS; inaccessible user Docker config warning |
| `npm.cmd run lint` | PASS |
| `npm.cmd run typecheck` | PASS |
| `node --experimental-strip-types --test tests/*.test.mjs` | 39 passed, 0 failed |
| `npm.cmd run build` | Environment-limited: EPERM opening `frontend/.next/trace-build` |

The skips are the existing PostgreSQL-only SQLSTATE diagnostic and Windows symlink-privilege tests. Warnings are existing Starlette/httpx, AnyIO, Alembic, Node module-type, and Docker user-config warnings. No external LLM, model download, or network call was used.

## Owner Docker smoke and failure matrix

```powershell
docker compose up -d --build
docker compose ps
docker compose exec redis redis-cli ping
docker compose exec worker rq info -u redis://redis:6379/0
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Expect four running services, `PONG`, an RQ worker listening on `documents`, and 200 from health/readiness. Then verify browser login, documents, chat/citations, and read-only admin access with appropriate user roles.

Redis failure: run `docker compose stop redis`; `/health` stays 200, `/ready` becomes 503, rate-limited writes and document enqueue fail safely with 503. Run `docker compose start redis`, wait for healthy, then verify `PONG`, `/ready` 200, and enqueue recovery.

Worker recovery: run `docker compose stop worker`, enqueue one safe small document job, inspect `docker compose exec redis redis-cli LLEN rq:queue:documents`, then `docker compose start worker` and confirm the document reaches its terminal state. For ordinary Redis restart durability, keep the worker stopped, enqueue one job, run `docker compose restart redis`, verify the queue remains, start the worker, and confirm completion. Never use `down -v`, remove volumes, or stop/remove PostgreSQL.

Concurrency: use a UI double-click or two PowerShell jobs against the same authenticated process/index endpoint. Expect one 202 and one 409, one RQ job, and no duplicate chunks/embeddings. Repeat with two users to confirm independent rate-limit buckets. Do not invoke RAG/LLM for this check.

## Security, privacy, and failure behavior

Foreign resources retain generic 404 behavior inside each API contract. Rate-limit and queue failures occur before expensive processing/provider work. Unexpected exceptions return only `{"detail":"Internal server error"}` and retain request/security headers. Structured logs may carry request/job/document IDs, route, policy, status, attempt, and duration; regression sentinels for credentials and private payloads are absent. DB/Redis/queue details are not returned to clients.

## Known limitations

- RQ plus Redis AOF everysec is not exactly-once or zero-loss delivery.
- `/ready` checks PostgreSQL and Redis, not worker heartbeat.
- Catastrophic loss after a state claim can leave `processing`/`indexing` active; there is no scheduler/reaper, so operator review may be required.
- Frontend polling stops after two minutes; server work continues and manual refresh shows later state.
- Backend/RQ and PostgreSQL do not share a distributed transaction.
- No reverse proxy/TLS, deployment automation, autoscaling, distributed tracing platform, OCR, hybrid retrieval, or legal versioning is introduced in this phase.

## Manual acceptance still required

Run the Docker smoke/failure/restart/concurrency matrix above, verify browser auth/documents/chat/admin flows, and confirm logs correlate IDs without private content. Only the owner may mark Phase 9D and Phase 9 accepted.
