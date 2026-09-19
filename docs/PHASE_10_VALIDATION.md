# Phase 10 — Deployment / Productionization Validation

Status: **PASS — implementation complete; local owner productionization acceptance complete.**

No external/public deployment, DNS/firewall mutation, real production secret publication, or destructive Docker volume operation was performed.

## Production architecture

The validated local production stack consists of Caddy, standalone Next.js, FastAPI, an RQ worker, PostgreSQL with pgvector, and Redis with AOF persistence.

Production uses the standalone `docker-compose.prod.yml`.

Caddy is the only public entry point. PostgreSQL and Redis remain on the internal `data` network. Backend and worker share persistent document storage and rebuildable embedding-model cache volumes.

FastAPI uses an empty development-default `ROOT_PATH`. Production Compose sets `ROOT_PATH=/api`.

Caddy strips the external `/api` prefix before forwarding requests, while FastAPI uses `root_path=/api` so generated external URLs such as Swagger OpenAPI remain correct.

The RQ worker explicitly disables the backend image HTTP healthcheck because the worker process has no HTTP listener.

Migration head remains `0006_user_roles`.

Alembic migration remains an explicit one-shot operator action through the `migrate` profile.

## Automated validation

- Backend compileall: PASS.
- Full backend pytest: PASS — 240 passed, 2 skipped, 17 warnings, 6 subtests passed.
- Phase 10 configuration tests: PASS — 13 passed.
- Dedicated PostgreSQL regression: PASS — 242 passed, 17 warnings, 6 subtests passed.
- Dedicated PostgreSQL test-stack cleanup: PASS.
- Frontend lint: PASS.
- Frontend typecheck: PASS.
- Frontend Node tests: PASS — 39 passed.
- Frontend production build: PASS.
- Development Compose `config --quiet`: PASS.
- Production Compose `config --quiet`: PASS.
- GitHub Actions YAML safe-load: PASS.
- Backend production Docker image build: PASS.
- Frontend production Docker image build: PASS.
- Bash syntax validation for production scripts: PASS.
- ShellCheck for production scripts: PASS.
- `validate-production-config.sh` runtime validation: PASS.
- `smoke-production.sh` proxy smoke: PASS.
- `git diff --check`: PASS, with Windows line-ending warnings only.

Validated GitHub workflows are `.github/workflows/ci.yml` and `.github/workflows/image-build.yml`.

The image workflow validates builds without publishing images.

## Production runtime validation

The production stack was confirmed running with backend, frontend, PostgreSQL, Redis, reverse proxy, and worker.

Backend and worker remained stable without restart loops.

PostgreSQL, migration state, pgvector, expected tables, indexes, constraints, and foreign keys were verified.

RQ worker availability and document queue behavior were verified.

No recurring Docker I/O corruption, read-only filesystem error, or application restart loop remained after Docker storage recovery.

## Owner production simulation

The local owner production simulation passed for:

- proxy `/`
- `/api/health`
- `/api/ready`
- authentication
- document upload/process/index
- direct semantic search
- chat/RAG/citations
- multi-turn chat
- admin authorization
- rate limiting
- request IDs
- security headers
- Redis restart persistence
- worker queue behavior
- worker stop/recovery

## Direct semantic search

Authenticated `POST /api/search` was exercised through Caddy.

The query `WORKER-PHOENIX-9182` returned the expected document as the highest relevant result using `intfloat/multilingual-e5-small`.

This confirms direct semantic retrieval works independently of the chat/RAG path.

## Admin authorization

An admin account successfully accessed `GET /api/admin/overview`.

A temporary normal user was denied the same endpoint with HTTP 403 and the message `Administrator access required`.

The temporary user was removed after testing.

## Rate limiting

Production runtime values were confirmed as `AUTH=10`, `AI=20`, `DOCUMENT_WRITE=10`, and `WINDOW=60`.

AI semantic-search requests 1 through 20 returned HTTP 200.

The next request returned HTTP 429 with rate-limit headers including `Retry-After`.

No paid LLM call was required for this validation.

## Request ID and security headers

A production request through Caddy returned HTTP 200 with:

- generated `X-Request-ID`
- `X-Content-Type-Options=nosniff`
- `X-Frame-Options=DENY`
- `Referrer-Policy=no-referrer`

This confirms application request tracing and security headers survive the production reverse proxy.

## Redis persistence

A temporary Redis key was created, Redis was restarted, and the key remained available after restart.

This validates the configured Redis AOF persistence across a normal container restart.

The temporary key was deleted afterward.

## Worker stop and recovery

The worker was stopped while the document queue was empty.

A synthetic document-processing job was queued while the worker was offline.

The queue increased from 0 to 1 and the job remained queued.

After restarting the worker, the queue returned to 0.

The document reached `status=processed` with an empty `processing_error`.

This demonstrates that a queued RQ job survives temporary worker unavailability and is processed after worker recovery.

The synthetic document, temporary user, Redis test key, and temporary filesystem artifact were cleaned up after validation.

## RAG and citation validation

Manual end-to-end RAG validation passed.

The indexed test document containing `WORKER-PHOENIX-9182` was retrieved correctly.

Chat returned the expected synthetic content with citations.

Citation/source navigation was manually checked against the expected document/chunk.

Multi-turn conversation behavior also passed.

## Backup validation

`scripts/backup-production.sh` was executed successfully against the running production simulation.

The successful backup produced `postgres.dump`, `documents.tar.gz`, and `SHA256SUMS`.

The PostgreSQL dump was validated with `pg_restore --list` and reported PostgreSQL custom format with the expected application objects.

The document archive passed `tar -tzf` validation.

`sha256sum -c SHA256SUMS` returned OK for both backup artifacts.

An earlier failed backup attempt was caused by Docker Desktop WSL integration being disabled for Ubuntu.

After enabling Docker Desktop WSL integration for Ubuntu, the same script completed successfully without requiring a functional script change.

## Production scripts

Validated scripts are:

- `scripts/backup-production.sh`
- `scripts/smoke-production.sh`
- `scripts/validate-production-config.sh`

All three pass Bash syntax validation and ShellCheck.

## Git and secret hygiene

Real `.env` and `.env.production` files are not tracked and are ignored by Git.

`.env.production.example` contains only documented placeholder/synthetic values and is intentionally safe to commit.

`.agents/` is ignored and is not part of application source.

Temporary Docker diagnostic and Phase 10 smoke artifacts were moved outside the repository.

Post-validation Git status showed no newly generated runtime/test artifact in the repository.

## Known limitations

RQ plus Redis AOF does not provide exactly-once job execution.

PostgreSQL and Redis do not participate in a distributed transaction.

Backend readiness does not include a worker heartbeat.

There is no stale-job reaper.

There is no autoscaling, OCR pipeline, hybrid retrieval/reranking, legal-document versioning, distributed tracing, or hosted monitoring platform.

External domain, DNS, firewall, real public HTTPS deployment, and provider-specific production secret provisioning remain operator deployment tasks.

## Acceptance

Phase 10 — Deployment / Productionization is **PASS — complete and owner accepted locally**.

No unresolved Phase 10 implementation blocker was found in the completed local production simulation.

External/public deployment remains a separate environment-specific deployment activity.