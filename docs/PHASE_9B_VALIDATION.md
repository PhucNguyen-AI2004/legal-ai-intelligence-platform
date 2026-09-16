# Phase 9B — Redis Foundation and Rate Limiting validation

## Status

Phase 9B — Redis Foundation and Rate Limiting: PASS — OWNER ACCEPTED. Phase 9 remains in progress. Phase 9C, 9D, and Phase 10 have not started. Phase 9A is owner accepted.

## Runtime and lifecycle

Compose adds `redis:7-alpine` on the internal network only. Port 6379 is not published. `--save "" --appendonly no` disables persistence and no Redis volume exists: losing short-lived counters during an intentional restart is acceptable, while PostgreSQL remains the authoritative persisted store.

The backend declares the official `redis` Python client and creates one `redis.asyncio.Redis` instance/connection pool per process during FastAPI lifespan. Socket/connect timeout defaults to two seconds and shutdown calls `aclose()`. `REDIS_URL` defaults to `redis://localhost:6379/0` for local Python; Compose supplies `redis://redis:6379/0`. URLs and credentials are never logged.

## Algorithm, identities, and policies

A Lua script uses Redis server `TIME` to select a fixed 60-second bucket, atomically increments the key, sets or repairs its TTL, and returns counter/TTL. Keys use `legalai:ratelimit:<policy>:<identity-type>:<identity>:<window>` and always expire.

| Policy | Default | Routes | Identity |
| --- | ---: | --- | --- |
| `auth` | 10 / 60 seconds | `POST /auth/login`, `POST /auth/register` | actual peer IP |
| `ai` | 20 / 60 seconds | `POST /search`, `POST /rag/ask`, `POST /conversations/{id}/messages` | persisted user UUID |
| `document_write` | 10 / 60 seconds | `POST /documents`, `POST /documents/{id}/process`, `POST /documents/{id}/index` | persisted user UUID |

The peer address intentionally ignores `X-Forwarded-For`; Phase 10 must define trusted proxies before proxy headers can become authoritative. Authenticated dependencies reuse `CurrentUser` and never decode a second token.

Allowed responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining`. Exceeded requests return `429 {"detail":"Rate limit exceeded"}` plus those headers and `Retry-After`; the Redis key/identity is not exposed. Redis errors or malformed script results return `503 {"detail":"Rate limiting service unavailable"}` before protected endpoint work. Logs use `rate_limit_exceeded` or `rate_limit_backend_unavailable` with policy, path, status, retry interval, and Phase 9A request correlation—never raw identity, Redis URL, token, email, password, prompt, or document text.

`/health` remains liveness-only. `/ready` returns ready only when both PostgreSQL `SELECT 1` and Redis `PING` succeed. It never checks an LLM, worker, frontend, or external site and never identifies the failing host in its response.

## Automated evidence

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m compileall -q app tests` | PASS, exit 0 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_rate_limiting.py tests/test_production_foundation.py --basetemp=.pytest_9b_final -p no:cacheprovider` | 24 passed, 3 warnings |
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_9b_full_final -p no:cacheprovider` | 206 passed, 2 skipped, 6 subtests passed, 17 warnings |
| `docker compose config --quiet` | PASS; environment warned that the user Docker config was inaccessible |
| `docker compose up -d --build` | Environment-blocked: Docker API pipe access denied |

The skips remain PostgreSQL-only SQLSTATE diagnostics and Windows symlink privileges. Warnings are existing framework/Alembic deprecations. The local venv did not install the newly declared Redis package because network escalation was declined; tests use injected doubles and the production import is lazy. An owner Docker build installs it from `requirements.txt`.

## Owner Docker and endpoint checklist

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec redis redis-cli ping
```

Expected services are `postgres`, `redis`, and `backend`; Redis reports `PONG`. Then:

```powershell
$health = Invoke-WebRequest http://localhost:8000/health
$ready = Invoke-WebRequest http://localhost:8000/ready
$health.StatusCode; $health.Content; $health.Headers['X-Request-ID']
$ready.StatusCode; $ready.Content; $ready.Headers['X-Request-ID']
```

Both should return 200. Test 429 without consuming LLM tokens by submitting an intentionally invalid synthetic login repeatedly from the same machine:

```powershell
$body = @{email='nobody@example.invalid'; password='synthetic-wrong-password'} | ConvertTo-Json
1..11 | ForEach-Object {
  try {
    $r = Invoke-WebRequest http://localhost:8000/auth/login -Method Post -ContentType 'application/json' -Body $body
    [pscustomobject]@{Attempt=$_; Status=$r.StatusCode; RetryAfter=$r.Headers['Retry-After']; RequestId=$r.Headers['X-Request-ID']}
  } catch {
    $r = $_.Exception.Response
    [pscustomobject]@{Attempt=$_; Status=[int]$r.StatusCode; RetryAfter=$r.Headers['Retry-After']; RequestId=$r.Headers['X-Request-ID']}
  }
}
```

Initial attempts retain invalid-credential behavior; the threshold produces 429 with `Retry-After`, rate-limit headers, and `X-Request-ID`. Wait the indicated interval, then retry and expect normal processing. Optional synthetic inspection:

```powershell
docker compose exec redis redis-cli --scan --pattern 'legalai:ratelimit:*'
```

Keys contain internal IP/user UUID data; do not paste them into reports.

## Safe Redis failure check

```powershell
docker compose stop redis
Invoke-WebRequest http://localhost:8000/health
try { Invoke-WebRequest http://localhost:8000/ready } catch { [int]$_.Exception.Response.StatusCode }
try { Invoke-WebRequest http://localhost:8000/auth/login -Method Post -ContentType 'application/json' -Body $body } catch { [int]$_.Exception.Response.StatusCode }
docker compose start redis
docker compose exec redis redis-cli ping
(Invoke-WebRequest http://localhost:8000/ready).StatusCode
```

Expected: health stays 200; readiness and protected auth return 503 while Redis is stopped; after restart Redis reports PONG and readiness returns 200. This does not stop PostgreSQL or destroy any volume.

## Known limitations

Fixed windows allow boundary bursts and Redis restarts reset ephemeral counters. Limits are policy/identity controls, not global quotas or billing controls. Direct peer IP is correct for current local Docker exposure but must be revisited with an explicitly trusted Phase 10 proxy. Redis is not used for caching, sessions, queues, jobs, JWT revocation, or document processing. No frontend countdown UX was added.
