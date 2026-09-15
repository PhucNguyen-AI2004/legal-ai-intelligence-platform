# Handoff

**LEGAL AI INTELLIGENCE PLATFORM — 2026-09-14, inspected HEAD `7a675b7`.**

**Completed / owner-reported acceptance:** 1-7 and 8A-8E. The explicit Phase 8F task confirms 8E manual acceptance.

**Phase 8F is owner accepted.** Implementation, owner-local automated validation, and owner manual regression all PASS. Owner-local Node writes, lint, typecheck, all 12 helper tests, and production build pass; no application build defect was reproduced locally. **CODEX SANDBOX BUILD VALIDATION: ENVIRONMENT-LIMITED BY NODE EPERM. NOT AN APPLICATION DEFECT.** Phase 8F is no longer blocked. Next administrative step: final Git review and commit. Do not begin Phase 8G until the Phase 8E/8F commit is reviewed and completed.

## Inspect first

Read [AGENTS.md](../AGENTS.md), [PROJECT_CONTEXT](PROJECT_CONTEXT.md), [ARCHITECTURE](ARCHITECTURE.md), [ROADMAP](ROADMAP.md), [TESTING](TESTING.md), [DECISIONS](DECISIONS.md), then README.md and `git status`/`git log`. For future chat work inspect `app/api/conversations.py`, `app/schemas/conversation.py`, `app/services/chat.py`, `rag.py`, `query_rewrite.py`, and frontend `src/lib/conversations/`, `src/components/conversations/`, `src/components/chat/chat-composer.tsx`, central API client and AuthProvider. Never guess API contracts.

## Current architecture

FastAPI + SQLAlchemy + PostgreSQL/pgvector; upload → extract → chunk → local normalized E5 embeddings → owner-filtered cosine retrieval → context → LLM → citation validation. Migration head: `0005_conversations_and_messages`. Docker DB is `postgres:5432`; local host port is 5433.

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
