# Phase 9C — Background Worker and Async Document Pipeline validation

## Status

Phase 9C — Background Worker and Async Document Pipeline: PASS — OWNER ACCEPTED. Phases 9A and 9B are owner accepted. Phases 9A and 9B are owner accepted. Phase 9 remains in progress; Phase 9D and Phase 10 have not started.

## Architecture and contracts

RQ was selected because processing/indexing are synchronous Python operations and Redis already exists. One named `documents` queue handles only document processing and indexing. The worker uses the backend image and explicit SQLAlchemy session lifecycles; it receives only document UUID and originating request ID, then reloads authoritative PostgreSQL state. JWTs, sessions, ORM objects, file bytes, paths, content, chunks, and vectors never enter job arguments.

Phase 9B Redis persistence was intentionally disabled because counters were disposable. Phase 9C accepts queued work, so Compose now enables AOF with `appendfsync everysec` and mounts `redis_data:/data`. This substantially improves restart durability but still has the documented Redis every-second persistence window; it is not a claim of zero-loss distributed delivery.

| Endpoint | New response | Persisted claim |
| --- | --- | --- |
| `POST /documents/{id}/process` | 202 `{document_id,job_id,job_type:"process",status:"queued"}` | `status=processing`, indexing reset to pending |
| `POST /documents/{id}/index` | 202 `{document_id,job_id,job_type:"index",status:"queued"}` | `embedding_status=indexing` |

Existing `processing` and `indexing` values mean accepted/queued or running. `processed`, `indexed`, and `failed` remain terminal product states, so no migration, jobs table, or RQ status API was added. `GET /documents/{id}` remains the status source. Ownership/state checks and a row lock precede enqueue. A claimed state prevents duplicate enqueue; queue failure restores the prior state and returns generic 503.

The worker invokes the existing extraction/chunking and E5 indexing services with `already_claimed=True`. Successful jobs reach processed/indexed. Permanent failures retain safe existing failure messages and do not retry. Database operational failures propagate as a dedicated retryable error; RQ is configured for at most two retries after 5 and 30 seconds. The final failure callback marks an active document failed. Missing/deleted targets are logged and ignored safely.

Structured events are `document_job_enqueued`, `document_job_started`, `document_job_completed`, `document_job_retrying`, and `document_job_failed`. They contain request ID, RQ job ID, job type, document UUID, safe outcome, duration/attempt where relevant. They exclude document content, extracted text, chunks, vectors, file bytes/paths, JWTs, email, passwords, Redis URL, and raw exception strings.

`/health` and `/ready` are unchanged from 9B; readiness checks PostgreSQL and Redis, not a worker heartbeat. Worker operation is checked independently through Compose/RQ inspection.

## Frontend behavior

The existing document views now understand the 202 queued response. They immediately refetch authoritative state, retain the current status badges/actions, and silently poll every three seconds only while `processing` or `indexing`. Polling stops on a terminal state, component unmount, or after 40 attempts/two minutes. Feedback says the request was queued rather than falsely claiming completion. No page redesign, WebSocket, SSE, or generic job UI was added.

The `ui-ux-pro-max` skill guided the immediate feedback, stable existing status UI, contextual live status, finite polling, and cleanup. Its Next.js dataset returned no verified polling-specific match after one retry, so standard React effect cleanup was used explicitly.

## Automated evidence

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m compileall -q app tests` | PASS |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_background_jobs.py --basetemp=.pytest_9c_jobs_final -p no:cacheprovider` | 11 passed, 3 warnings |
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_9c_full_final -p no:cacheprovider` | 217 passed, 2 skipped, 6 subtests passed, 17 warnings |
| `docker compose config --quiet` | PASS; inaccessible user Docker config warning |
| `docker compose up -d --build` | Environment-limited: Docker API pipe permission denied; elevated retry was not authorized |
| `npm.cmd run lint` | PASS |
| `npm.cmd run typecheck` | PASS |
| `node --experimental-strip-types --test tests/*.test.mjs` | 37 passed, 0 failed |
| `npm.cmd run build` | Environment-limited: EPERM opening `.next/trace-build`; outside-sandbox retry declined |

Backend skips and warnings are unchanged platform/framework items. Tests inject Redis/RQ queues and fake embeddings; no model download, real LLM, or paid provider is used. The local venv lacks Redis/RQ because package download approval was previously declined; Docker installs declared dependencies during build.

## Owner Docker and API validation

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec redis redis-cli ping
docker compose exec worker rq info -u redis://redis:6379/0
docker compose logs --tail 100 worker
```

Expected services: `postgres`, `redis`, `backend`, `worker`; Redis returns `PONG`; RQ reports the `documents` queue/worker. Do not paste private IDs or configuration into reports.

In Swagger or the browser:

1. Login and upload a safe small TXT file. Upload remains synchronous and ends at `uploaded`.
2. Call process once: expect 202 promptly, `status=queued`, job ID, and response `X-Request-ID`; document detail becomes `processing`.
3. Immediately call process again: expect 409 and no second job.
4. Observe worker logs with the same request ID/job/document metadata and no content.
5. Poll or watch the browser detail until `processed`; chunks then appear.
6. Call index: expect 202 promptly and `embedding_status=indexing`; duplicate returns 409; terminal state becomes `indexed`.
7. Verify search/RAG behavior remains unchanged after indexing. Use fake/safe content and do not invoke a paid provider merely to validate queue mechanics.
8. Try another owner and a missing UUID: generic 404 and no job.
9. Stop the worker, enqueue a job, verify it remains processing/indexing, restart worker, and verify completion:

```powershell
docker compose stop worker
docker compose exec redis redis-cli LLEN rq:queue:documents
docker compose start worker
docker compose logs --tail 100 worker
```

## Safe failure and restart durability checks

Queue acceptance must fail closed if Redis is stopped:

```powershell
docker compose stop redis
try { Invoke-WebRequest http://localhost:8000/ready } catch { [int]$_.Exception.Response.StatusCode }
docker compose start redis
docker compose exec redis redis-cli ping
```

For AOF restart survival without destroying volumes:

1. `docker compose stop worker`
2. Enqueue one safe document process job and confirm `LLEN rq:queue:documents` is at least one.
3. `docker compose restart redis`
4. Confirm the queue length remains nonzero.
5. `docker compose start worker`
6. Confirm the document reaches its terminal state.

Never use `docker compose down -v`, remove `redis_data`, or prune volumes. AOF everysec can theoretically lose up to roughly one second of writes during an abrupt host/process failure; an orderly restart should retain the queued job.

## Known limitations

- Existing active states intentionally combine queued and running; there is no separate queued timestamp or queue-position UI.
- No worker heartbeat is part of backend readiness. Operators validate worker availability through Compose/RQ.
- Polling stops after two minutes; a longer job continues server-side and a manual refresh shows its eventual state.
- RQ provides at-least-once-style execution behavior, not a cross-database/Redis transaction. State claims, duplicate rejection, idempotent replacement transactions, AOF, and safe failure recovery reduce risk but do not constitute exactly-once delivery.
- Only database operational failures are automatically retried. Deterministic extraction/model/output failures do not loop.
- Redis remains shared by rate limits and RQ but uses namespaced keys and one container; no caching, chat jobs, scheduler, generic workflow, or automatic upload-to-index pipeline exists.
