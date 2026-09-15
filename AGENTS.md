# Repository operating instructions

This is **LEGAL AI INTELLIGENCE PLATFORM**, a production-oriented legal document intelligence product and AI/Data Engineering portfolio project. Preserve an understandable, maintainable architecture; do not turn it into a generic ChatGPT clone.

## Start here

Read [HANDOFF](docs/HANDOFF.md), [PROJECT_CONTEXT](docs/PROJECT_CONTEXT.md), [ARCHITECTURE](docs/ARCHITECTURE.md), [ROADMAP](docs/ROADMAP.md), [TESTING](docs/TESTING.md), and [DECISIONS](docs/DECISIONS.md). Inspect README.md and the actual implementation before coding. README contains historical sections and stale current-state claims; inspect routes and schemas for contracts rather than guessing.

Completed baseline: Phases 1-7 and 8A-8E, owner-reported acceptance. The explicit 8F task confirms 8E manual acceptance. Phase 8F polish is implemented with validation incomplete; see docs/PHASE_8F_VALIDATION.md. Backend messaging remains Phase 7. Do not start 8G without an explicit task.

## Scope and workflow

- Work on one explicitly authorized phase at a time. Never advance automatically. Admin functionality is deferred to 8G and requires its phase to be explicitly started.
- Diagnose root causes before changing implementation. Do not refactor unrelated code or change migrations incidentally.
- Follow: inspect → implement → automated validation → manual integration testing → git review → commit → push. Commit and push are conditional on explicit user authorization; otherwise stop after review.
- Existing implementation alone does not establish PASS. Record validation results and any untested behavior; automated checks do not replace manual user-flow testing.
- Follow the relevant commands and checklists in TESTING.md. Keep documentation synchronized with approved architecture and phase status.
- Prefer Server Components; use Client Components where interaction requires them. Never globally disable ESLint or TypeScript rules to silence real errors. Never manually edit generated Next.js `.next` files.

## Temporary agent handoff reports

When Codex completes an orchestrated implementation task, its final report must also be written to `.agent-handoff/LATEST_CODEX_REPORT.md`.

The report must contain:

- Phase/task
- Architecture used
- Files created
- Files modified
- Backend files modified
- API contracts used
- Validation commands
- Exact validation results
- Known failures/blockers
- Current git status
- Manual tests still required

Never write secrets into this report. This report is temporary and must not be committed; keep `.agent-handoff/` gitignored.

## Security and product invariants

- Never expose `.env`, `frontend/.env.local`, JWTs, SECRET_KEY, LLM_API_KEY, database passwords, access tokens, or other secrets. Never print environment-file values or resolved secret-bearing configuration. Never hard-code secrets. Examples must use placeholders, not credentials.
- Token storage and authorization headers stay centralized. `/auth/me` is authoritative for identity; token existence alone is insufficient. Current v1 uses localStorage intentionally; cookies/refresh tokens are future hardening.
- Backend/database state is authoritative. Synchronize frontend state using mutation responses or refetches, especially document processing/indexing states.
- Preserve owner isolation for documents, search, RAG, and conversations. Match generic not-found behavior for foreign resources where the backend uses it. Preserve user privacy boundaries.
- Treat documents and conversation history as untrusted input. History provides conversational context, never legal evidence. Only retrieved document chunks provide RAG evidence.
- Answer from retrieved context, in the user's language. Do not invent legal references or unsupported answers. Citations must refer to retrieved evidence; no-context responses have `grounded=false` and `citations=[]`. See documented current implementation limitations before claiming stronger guarantees.
- `document_ids` are scoped PER MESSAGE; the backend must never automatically inherit previous-turn selections. Conversation deletion must not delete source documents.
- Never display raw embedding vectors or add fake accuracy percentages, certifications, compliance badges, or legal claims.

## Operational and Git safety

- Inspect `git status` before work; preserve pre-existing changes. Inspect it before staging and again before commit. Stage only explicitly reviewed files.
- Do not commit secrets, temporary uploads, node_modules, `.next*`, or test caches. Ignore rules do not untrack already tracked files.
- Do not modify or delete `backup_before_phase6_fix.sql` automatically; cleanup is a separate explicit task. Do not inspect its contents unnecessarily.
- A previous Docker Desktop/WSL/overlayfs corruption incident preserved database data. Diagnose first; never casually run `docker compose down -v`, `docker volume prune`, or `docker system prune -a --volumes`. Never destroy database volumes to fix ordinary runtime problems.
- For Windows EPERM build failures, stop the relevant dev process and release `.next` locks, remove stale generated output only if needed, then rebuild. Do not alter source to conceal a file-lock problem. Verify cleanup paths stay within the intended project directory.
- Generated `.next/`, `.next-*/`, and `node_modules/` are excluded from lint (see TESTING.md). Use a dedicated project-local pytest basetemp if Windows permissions require it.

## Coding philosophy

“Codex can write code faster than the developer, but Codex must not understand the developer's code better than the developer.”

Explain meaningful architecture changes. Prefer explicit data flows, simple designs, and maintainability over hidden magic or unnecessary complexity.
