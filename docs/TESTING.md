# Testing and review

Implementation existing does not establish PASS. Use inspect → implement → automated validation → manual integration testing → Git review. Commit and push follow only when explicitly authorized. Record actual commands, results, skips, environment limitations, and manual coverage; do not turn a skipped check into PASS.

## Backend validation

From the repository root with the project virtual environment activated:

```powershell
python -m compileall -q app
pytest -q
docker compose config --quiet
```

On Windows without activation, use `.\.venv\Scripts\python.exe -m compileall -q app` and `.\.venv\Scripts\python.exe -m pytest -q`. Backend behavior changes require backend regression tests; targeted tests help diagnosis but do not substitute for the required suite.

Tests cover auth/security, uploads, extraction/chunking, embeddings/search, RAG/context, conversations and migrations. `tests/conftest.py` normally uses SQLite with test-only cosine emulation, actual Alembic migrations, fake embeddings, and isolated test settings. RAG/conversation tests inject fake LLMs; ordinary automated tests do not establish real-provider quality or real-model retrieval behavior. Real model downloads are forbidden by the default test fixture.

TEST_DATABASE_URL enables PostgreSQL testing; it must use psycopg and a database name ending `_test`. Fixtures create/drop an isolated schema. Never point tests at the application database or print the URL. Migration tests exercise upgrade/downgrade, constraints, cascades and metadata; PostgreSQL checks are needed for real pgvector behavior.

## Docker validation

Use quiet configuration validation to avoid printing resolved credentials. Check `docker compose ps` and `/health` for basic operation; `/health` is liveness and startup checks DB connectivity, so it is not a continuous database readiness test.

Dedicated disposable PostgreSQL tests (from repository root):

```powershell
docker compose -p legal-ai-context-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-context-tests -f docker-compose.test.yml down
```

The test Compose file uses `postgres-test`, a tmpfs database, no application database volumes and no host database port. The commands above apply only to that explicit test project. Do not add `-v`, prune volumes, or use destructive cleanup against the normal application stack. Diagnose Docker Desktop/WSL/overlayfs problems before changing anything; preserve database data. Inspect logs privately and sanitize before sharing.

## Frontend validation

From `frontend/`, all must PASS for frontend changes:

```powershell
npm run lint
npm run typecheck
npm run build
```

Scripts come from `frontend/package.json`; typecheck runs TypeScript without incremental output. There is currently no frontend automated browser-test script in that file. Do not invent a completed browser suite.

## Manual integration checklist

- Auth: register, login, refresh protected direct URL, validate /auth/me identity, logout, expired/invalid-token handling, and separate public login errors from global authenticated 401 handling.
- Documents: upload TXT/DOCX/text PDF; reject unsupported/oversized input; process/index; inspect chunks and backend states after refetch; paginate; refresh detail; test delete confirmation and errors. Verify scanned-PDF behavior without claiming OCR.
- Conversations through 8D: create/select, direct URL and refresh, read ordered persisted history, rename, delete, loaded-title search, pagination, active URL highlight, empty/loading/error states. Confirm deleting a conversation preserves documents. Composer remains disabled.
- Privacy: use two accounts to verify document, conversation, retrieval and citation boundaries; foreign IDs should not reveal another owner's resources.
- Backend RAG/multi-turn: with safe test documents and configured provider/model, verify first-turn raw query, follow-up rewrite, per-message scope changes, omitted scope without inheritance, relevant citations, no-context and provider failures. Never paste tokens or sensitive legal documents into reports. Account for persisted user messages after a provider failure.
- Responsive UX: expanded/collapsed desktop sidebar and mobile drawer; readable document/history views.

Phase 8E message sending and clickable sources are owner-manually accepted. Use [the Phase 8F checklist](PHASE_8F_VALIDATION.md) for current regression and [Phase 8E](PHASE_8E_VALIDATION.md) for detailed historical scenarios. The composer is enabled, superseding the historical 8D check above. Helpers run with `node --experimental-strip-types --test tests/message-flow.test.mjs` from frontend. Use `npm.cmd` if PowerShell blocks npm.ps1. Automated tests do not replace manual integration.

## Windows and generated files

For Next.js EPERM trace-file locks: stop the relevant `npm run dev` process, close holders of `.next`, remove stale generated `.next` only when necessary and after verifying its exact project path, then rerun build. Do not change source to hide a filesystem lock or edit generated framework files.

Required lint exclusions are `.next/`, `.next-*/`, and `node_modules/`. Phase 8F updates ESLint and Git exclusions to cover arbitrary frontend `.next-*` variants. No generated output is edited or ESLint/TypeScript rule disabled.

For pytest temporary-directory permissions, choose a fresh, dedicated project-local path, for example:

```powershell
python -m pytest -q --basetemp=.pytest_context_run
```

Pytest can clear its basetemp directory. Ensure this path is disposable, stays inside the workspace, and contains no user data; do not reuse tracked historical temp paths. Ignore rules do not remove files already tracked by Git.

## Git and documentation-only review

Run `git status` before work, before staging, and again before commit. Review `git diff --stat`, scoped diffs, and `git diff --check`; untracked documentation also requires direct content review because ordinary diff omits it. Stage only reviewed paths when authorized. Exclude secrets, uploads, generated builds/dependencies and test caches. Leave `backup_before_phase6_fix.sql` unchanged; cleanup is a separate explicit task.

For this context-pack task, validate the seven requested Markdown files, their source references, links, phase boundaries and changes relative to initial Git status. No application code changed, so runtime builds/tests and manual product tests are not required to validate this documentation edit and must not be claimed as newly passed. Preserve the pre-existing tracked test-artifact deletions.

## Phase 8G admin validation

See [PHASE_8G_VALIDATION](PHASE_8G_VALIDATION.md) for bootstrap, manual API/browser checks, test evidence and environment limitations. From the root, run `.\.venv\Scripts\python.exe -m pytest -q tests/test_admin.py tests/test_auth.py tests/test_migrations.py --basetemp=.pytest_8g_owner_focused -p no:cacheprovider`, then the full suite with a fresh project-local basetemp. From frontend, run `node --experimental-strip-types --test tests/*.test.mjs` in addition to lint/typecheck/build. After adding routes, `npx next typegen` regenerates stale route types; do not edit generated files manually.

ADMIN ENDPOINT TESTS DO NOT CONSUME LLM API TOKENS.
