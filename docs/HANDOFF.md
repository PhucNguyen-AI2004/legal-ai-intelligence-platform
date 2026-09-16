# Handoff

## Current Phase 9D status — 2026-09-16

Phases 9A, 9B, and 9C are owner accepted. Phase 9D integration and hardening regression is implemented; Phases 9A, 9B, 9C, and 9D are complete and owner accepted. Phase 9 — Production Engineering is complete. Phase 10 has not started. Focused coverage now proves cross-contract ownership, pre-enqueue failure behavior, duplicate worker-delivery idempotency, generic correlated errors, transport headers, frontend polling cleanup, and authoritative error reconciliation. No production contract, migration, or deployment topology changed. See [Phase 9D validation](PHASE_9D_VALIDATION.md). Phase 9 is not yet complete and Phase 10 has not started.

## Current Phase 9C status — 2026-09-16

Phases 9A and 9B are owner accepted. Phase 9C is complete and owner accepted. Process/index endpoints claim PostgreSQL state and return 202 after enqueueing identifiers on the named RQ `documents` queue. A dedicated worker reloads authoritative state and uses the existing synchronous services. Redis uses AOF everysec and a named volume because it holds accepted work. The frontend shows queued state and polls active documents for at most two minutes. See [Phase 9C validation](PHASE_9C_VALIDATION.md). This is historical 9C architecture context; current 9D status is above.

**Historical interim work: Pre-8G Chat UX refinement.** Completed and owner accepted before Phase 8G; see validation/checklist. All other Pre-8G behavior is owner accepted. Selected citations now open full extracted chunk text inside the existing drawer, with ten-chunk pagination, exact UUID evidence verification, contained focus/scroll and labelled highlighting. No document-workspace navigation or management UI. Stop and source scope are unchanged; backend/API/database unchanged. Lint/typecheck and 30 tests pass; sandbox build EPERM on `.next/trace`, outside-sandbox retry declined. See [reader validation/checklist](PRE_8G_CHAT_UX_VALIDATION.md). No stage/commit/push; Phase 8G has not started.

**Historical: Pre-8G corrective pass — PASS, owner accepted.** Owner accepted the previous visual direction and core behavior. The two corrections remove Stop acknowledgement after successful automatic reconciliation and add per-answer source list → citation detail → Back inside the existing drawer. Full-document navigation is secondary. Lint/typecheck and 23 tests pass; production build is sandbox EPERM-limited, elevated retry declined. See [current corrective evidence/checklist](PRE_8G_CHAT_UX_VALIDATION.md). This supersedes the earlier explicit-review requirement for user-initiated Stop. Backend/API/database unchanged; no stage/commit/push; 8G unstarted.

**Historical: Pre-8G Chat UX refinement — PASS, owner accepted.** Client-only Stop, editable copies/history reconciliation, per-answer Sources drawer and message hierarchy are documented in [validation](PRE_8G_CHAT_UX_VALIDATION.md). Lint/typecheck and 19 tests pass; build remains sandbox EPERM-limited and outside-sandbox execution was declined. No commit/push; Phase 8G has not started. Existing Phase 8F acceptance remains unchanged.

**LEGAL AI INTELLIGENCE PLATFORM — 2026-09-14, inspected HEAD `7a675b7`.**

**Completed / owner-reported acceptance:** 1-7 and 8A-8E. The explicit Phase 8F task confirms 8E manual acceptance.

**Phase 8F is owner accepted.** Implementation, owner-local automated validation, and owner manual regression all PASS. Owner-local Node writes, lint, typecheck, all 12 helper tests, and production build pass; no application build defect was reproduced locally. **CODEX SANDBOX BUILD VALIDATION: ENVIRONMENT-LIMITED BY NODE EPERM. NOT AN APPLICATION DEFECT.** Phase 8F is no longer blocked. Next administrative step: final Git review and commit. Do not begin Phase 8G until the Phase 8E/8F commit is reviewed and completed.

## Inspect first

Read [AGENTS.md](../AGENTS.md), [PROJECT_CONTEXT](PROJECT_CONTEXT.md), [ARCHITECTURE](ARCHITECTURE.md), [ROADMAP](ROADMAP.md), [TESTING](TESTING.md), [DECISIONS](DECISIONS.md), then README.md and `git status`/`git log`. For future chat work inspect `app/api/conversations.py`, `app/schemas/conversation.py`, `app/services/chat.py`, `rag.py`, `query_rewrite.py`, and frontend `src/lib/conversations/`, `src/components/conversations/`, `src/components/chat/chat-composer.tsx`, central API client and AuthProvider. Never guess API contracts.

## Current architecture

FastAPI + SQLAlchemy + PostgreSQL/pgvector; upload → extract → chunk → local normalized E5 embeddings → owner-filtered cosine retrieval → context → LLM → citation validation. Migration head: `0006_user_roles` (apply migration before running the updated application). Docker DB is `postgres:5432`; local host port is 5433.

Next.js workspace has real auth/documents/conversation CRUD, message sending with authoritative history reconciliation, per-message source selection, grounding labels and live citation previews. Backend Phase 7 message endpoint already exists. History is context, never evidence; document IDs are per message. `/auth/me` and backend state are authoritative; localStorage token handling stays centralized.

Phase 8E provides immediate first-send creation, per-message sources, draft clearing with persistence-aware recovery, and bounded click-only citations. Phase 8F preserves this logic and improves native dialogs, mobile navigation, focus/disabled styles, long-content wrapping and document error recovery. Phase 8E owner acceptance remains historical context; Phase 8F now has its own completed owner-local automated validation and owner manual acceptance.

## Commands

Root: `python -m compileall -q app`, `pytest -q`, `docker compose config --quiet`.

Frontend directory: `npm run lint`, `npm run typecheck`, `npm run build`.

Review: `git status`, `git diff --stat`, `git diff --check`. See TESTING.md for dedicated PostgreSQL tests, Windows venv/basetemp commands and mandatory manual integration coverage.

## Caveats

- README still contains stale “no frontend” claims. PASS history comes from the owner; this documentation task did not rerun runtime tests.
- Initial tree had 213 tracked test-artifact deletions under `.pytest_tmp*`; preserve existing changes. Leave `backup_before_phase6_fix.sql` untouched.
- Phase 8F lint/Git ignores cover arbitrary frontend `.next-*` directories. Windows trace EPERM and pytest temp permissions remain environment issues.
- Uncited generated answers may return `grounded=false`; citation checking is reference validation, not semantic proof. No-context fallback is fixed Vietnamese. Provider failure may leave a saved user message; reconcile history before retries.
- Sidebar search covers loaded titles only. Citations reference live chunks and can disappear after source deletion/reprocessing.
- Never print private environment values or secrets. Never destroy database volumes as an ordinary Docker fix.
