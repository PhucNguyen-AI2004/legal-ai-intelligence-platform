# Phase 9A — Production Engineering Foundation validation

## Status and scope

Phase 9A — Production Engineering Foundation: PASS — OWNER ACCEPTED. Phase 9 overall remains in progress. Phase 9B, 9C, 9D, and Phase 10 have not started. Phase 9 overall remains in progress. Phase 9B (Redis/rate limiting), 9C (workers/async pipeline), 9D, and Phase 10 have not started. No migration or frontend source change is required.

## Contracts

- Each request uses a canonical 36-character UUID request ID. A valid incoming `X-Request-ID` is normalized to lowercase and retained; absent, malformed, non-UUID, or oversized values are replaced with UUID4. Every response includes `X-Request-ID`.
- A request-scoped context variable makes the ID available to application logging without treating it as identity or authorization. It can later be copied into job metadata without adding a job abstraction now.
- Logs are JSON with timestamp, level, logger, event, and request ID where available. Completion events include method, path without query parameters, status code, and duration in milliseconds. Unexpected exceptions add only exception type and server traceback to server logs; clients receive a generic 500 response.
- Logs must not include authorization headers/JWTs, passwords/hashes, keys, database credentials, request bodies, prompts/answers, document/chunk content, embeddings, uploads, or email by default. Operation logs may include non-secret resource UUIDs and counts.
- `GET /health` remains DB-independent liveness: `200 {"status":"ok"}`. `GET /ready` executes only `SELECT 1`: success is `200 {"status":"ready"}`, failure is `503 {"status":"not_ready"}` with no exception detail. It never calls the LLM.
- CORS uses `FRONTEND_ORIGIN`, no wildcard and no credentials. It permits GET/POST/PATCH/DELETE/OPTIONS and Accept/Authorization/Content-Type/X-Request-ID, and exposes X-Request-ID.
- Responses add `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`. HSTS is omitted for local HTTP; CSP is omitted to avoid a cosmetic API policy or Swagger breakage. `/docs` and `/openapi.json` remain enabled.

## Automated evidence

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m compileall -q app` | PASS, exit 0 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_production_foundation.py --basetemp=.pytest_9a_final_review -p no:cacheprovider` | 10 passed, 3 warnings |
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_9a_full_final -p no:cacheprovider` | 192 passed, 2 skipped, 6 subtests passed, 17 warnings |

Skips are the existing PostgreSQL-only SQLSTATE diagnostic and Windows symlink privilege check. Warnings are existing Starlette/anyio/Alembic deprecations. Tests use fake embeddings/LLMs and consume no provider tokens.

## Owner manual validation (Windows + Docker Compose)

Use only synthetic, non-sensitive values in commands and logs.

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
$health = Invoke-WebRequest http://localhost:8000/health
$health.StatusCode; $health.Content; $health.Headers['X-Request-ID']
$ready = Invoke-WebRequest http://localhost:8000/ready
$ready.StatusCode; $ready.Content; $ready.Headers['X-Request-ID']
$docs = Invoke-WebRequest http://localhost:8000/docs
$openapi = Invoke-WebRequest http://localhost:8000/openapi.json
$docs.StatusCode; $openapi.StatusCode
```

Expected: backend/PostgreSQL healthy; health and readiness 200; non-empty UUID request headers; docs/OpenAPI 200. For a supplied ID:

```powershell
$id = [guid]::NewGuid().ToString()
$response = Invoke-WebRequest http://localhost:8000/health -Headers @{'X-Request-ID'=$id}
$response.Headers['X-Request-ID']; $id
```

The two IDs should match. In Swagger, confirm a protected endpoint without a token remains 401, an authenticated ordinary route succeeds, an ordinary user receives 403 from `/admin/overview`, and an admin receives 200. Verify normal document, RAG, conversation, and owner-isolation flows remain unchanged; do not invoke a paid LLM solely for 9A.

Open the frontend at its configured local origin and verify login plus ordinary API requests work. An unconfigured browser origin must not receive `Access-Control-Allow-Origin`. Inspect logs privately:

```powershell
docker compose logs --tail 100 backend
```

Confirm JSON completion entries contain request_id, method, status_code, and duration_ms. Confirm no bearer token, password, question/answer, document text, upload content, database URL, or secret appears. Do not paste credentials into the report.

## Known limitations

Readiness checks only the required database and has no separate timeout beyond the engine's configured connect timeout. It intentionally says nothing about LLM, Redis, workers, model cache, storage capacity, or downstream provider health. Request IDs are process/request correlation metadata, not globally guaranteed trace IDs. This phase adds no metrics/tracing platform and no production origin/TLS configuration.
