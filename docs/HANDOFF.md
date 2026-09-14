# Handoff

**LEGAL AI INTELLIGENCE PLATFORM — 2026-09-14, inspected HEAD `7a675b7`.**

**Completed / owner-reported PASS:** 1–7, 8A, 8B, 8C, 8D.

**NEXT: 8E Chat + RAG + Citations. 8E HAS NOT BEEN IMPLEMENTED.** Do not start it without an explicit user task. Do not advance into 8F, admin 8G, production/deployment or optional features automatically. Do not commit/push without explicit authorization.

## Inspect first

Read [AGENTS.md](../AGENTS.md), [PROJECT_CONTEXT](PROJECT_CONTEXT.md), [ARCHITECTURE](ARCHITECTURE.md), [ROADMAP](ROADMAP.md), [TESTING](TESTING.md), [DECISIONS](DECISIONS.md), then README.md and `git status`/`git log`. For future chat work inspect `app/api/conversations.py`, `app/schemas/conversation.py`, `app/services/chat.py`, `rag.py`, `query_rewrite.py`, and frontend `src/lib/conversations/`, `src/components/conversations/`, `src/components/chat/chat-composer.tsx`, central API client and AuthProvider. Never guess API contracts.

## Current architecture

FastAPI + SQLAlchemy + PostgreSQL/pgvector; upload → extract → chunk → local normalized E5 embeddings → owner-filtered cosine retrieval → context → LLM → citation validation. Migration head: `0005_conversations_and_messages`. Docker DB is `postgres:5432`; local host port is 5433.

Next.js workspace has real auth/documents/conversation CRUD and read-only persisted history/citation markers. Composer is disabled. Backend Phase 7 message endpoint already exists. History is context, never evidence; document IDs are per message. `/auth/me` and backend state are authoritative; localStorage token handling stays centralized.

## Commands

Root: `python -m compileall -q app`, `pytest -q`, `docker compose config --quiet`.

Frontend directory: `npm run lint`, `npm run typecheck`, `npm run build`.

Review: `git status`, `git diff --stat`, `git diff --check`. See TESTING.md for dedicated PostgreSQL tests, Windows venv/basetemp commands and mandatory manual integration coverage.

## Caveats

- README still contains stale “no frontend” claims. PASS history comes from the owner; this documentation task did not rerun runtime tests.
- Initial tree had 213 tracked test-artifact deletions under `.pytest_tmp*`; preserve existing changes. Leave `backup_before_phase6_fix.sql` untouched.
- Current lint/Git ignores cover a specific alternate `.next` directory, not all `.next-*`; Windows trace locks and pytest temp permissions need environment diagnosis.
- Uncited generated answers may return `grounded=false`; citation checking is reference validation, not semantic proof. No-context fallback is fixed Vietnamese. Provider failure may leave a saved user message; reconcile history before retries.
- Sidebar search covers loaded titles only. Citations reference live chunks and can disappear after source deletion/reprocessing.
- Never print private environment values or secrets. Never destroy database volumes as an ordinary Docker fix.
