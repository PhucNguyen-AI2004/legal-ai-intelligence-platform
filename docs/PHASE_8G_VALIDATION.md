# Phase 8G — Admin Dashboard V1 validation

## Status

Implemented and owner manually accepted on 2026-09-16. PHASE 8G ADMIN DASHBOARD V1: PASS — OWNER ACCEPTED. Phase 9 and Phase 10 have not started. Phase 9 and Phase 10 have not started. No stage, commit, push or application database migration was performed.

## Architecture and bootstrap

Initial migration head was `0005_conversations_and_messages`, with no existing admin mechanism. Head is now `0006_user_roles`. Users retain UUID identity, email, password hash, active flag and timestamps; the additive role column is non-null, defaults to `user`, and accepts only `user`/`admin` through a database check. Existing users become ordinary users. Registration rejects extra `role` fields with 422. `/auth/me` reads the persisted role through the existing current-user dependency. JWT shape and token storage are unchanged.

After reviewing the migration, run from the root in the configured local environment:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.scripts.promote_user --email admin@example.com
```

Use an account you already registered; the example address is a placeholder. Promotion is explicit and idempotent. Missing account exits 1 without creating one; success exits 0; database failure reports a generic error and exits 2. The CLI prints no credentials or password hashes. No automatic promotion or role-management API/UI exists. Refresh the frontend identity or sign in again after promotion.

## API contracts

All routes reuse `require_admin` → existing `get_current_user` → database user. Missing token: 401; authenticated ordinary user: 403; admin: 200. Inactive identity remains denied by existing auth. Demoting the persisted role denies the same token on subsequent requests. Successful responses use `Cache-Control: no-store`.

| Route | Shape | Query |
| --- | --- | --- |
| `GET /admin/overview` | `total_users`, `total_documents`, `total_conversations`, `total_messages`, `processing_counts`, `embedding_counts` | None |
| `GET /admin/users` | `{items,total,skip,limit}`; item: `id,email,role,created_at` | `skip>=0`, `limit=1..100` default 20; optional literal email substring, max 254 chars |
| `GET /admin/documents` | `{items,total,skip,limit}`; item: `id,owner_id,owner_email,title,original_filename,file_type,file_size,status,embedding_status,created_at` | Same pagination; optional `status` and `embedding_status` |

Processing values: uploaded, processing, processed, failed. Indexing values: pending, indexing, indexed, failed. Count maps contain observed database groups; the UI displays zero for absent known statuses. Lists sort by creation time descending then ID. Counts/pages are live queries, not a historical analytics snapshot; concurrent writes can change totals between requests. Invalid filters/pagination receive 422. Query database errors return generic 503, not internal details.

Dedicated admin schemas exclude password hashes, stored filenames, filesystem paths, descriptions/error strings, raw vectors, document/chunk text, prompts, answers, citations and transcripts. Display names and original filenames remain owner-provided metadata. Ordinary owner document, retrieval, RAG, conversation and message checks are unchanged, including for admin identities. No content-view or destructive admin action was added.

## Frontend

Routes: `/app/admin` overview, `/app/admin/users`, `/app/admin/documents`. The existing sidebar shows Admin only for the `/auth/me` role. Direct ordinary-user navigation displays access denied. The backend independently enforces role on each data request. There is no second admin flag.

Overview uses real counts and status distributions. Users have email search; documents have processing/indexing filters. Filtering resets pagination. Requests use the central authenticated API client, abort superseded work and avoid displaying a previous filter's data. Views provide loading, empty, retry and denied states. Tables wrap long metadata and become stacked rows below 600px; labels, headings, focus styles and reduced-motion rules use existing UI conventions. No browser validation is claimed.

## Automated validation evidence

| Command | Exact result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m compileall -q app` | PASS, exit 0 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_admin.py tests/test_auth.py tests/test_migrations.py --basetemp=.pytest_8g_resume -p no:cacheprovider` | 40 passed, 1 skipped, 17 warnings |
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_8g_full -p no:cacheprovider` | 182 passed, 2 skipped, 6 subtests passed, 17 warnings |
| `npm.cmd run lint` (frontend) | PASS, exit 0 |
| `npm.cmd run typecheck` (Codex sandbox) | Environment-limited by stale generated Next route types; not treated as an application defect |
| Owner-local `npm.cmd run build` | PASS |
| Owner-local `npm.cmd run typecheck` | PASS |
| `node --experimental-strip-types --test tests/*.test.mjs` (frontend) | 34 passed, 0 failed (4 new admin, 30 existing) |
| `npm.cmd run build` (frontend) | Environment-blocked: EPERM opening `.next/trace-build`; outside-sandbox retry declined |
| `.\node_modules\.bin\next.cmd typegen` (frontend) | Failed generation: EPERM opening `.next/types/routes.d.ts`; command misleadingly exits 0; outside-sandbox retry declined |
| `docker info --format '{{.ServerVersion}}'` | Docker configuration/pipe access denied; elevated retry declined; PostgreSQL suite not run |

Backend tests use actual Alembic migrations on SQLite, fake embeddings and fake LLMs. Skips: PostgreSQL-only SQLSTATE diagnostics and Windows symlink privileges. Warnings are existing Starlette/anyio/Alembic deprecations; Node reports its existing module-type warning. Initial focused validation exposed SQLite foreign-key failure from rebuilding users and an old head assertion; both were corrected before the passing runs above. Populated upgrade/downgrade regression and invalid-role constraint checks pass on SQLite. Production PostgreSQL migration remains to be validated.

ADMIN ENDPOINT TESTS DO NOT CONSUME LLM API TOKENS.

## Exact manual Swagger checklist — PASS

1. Apply migration in the intended local environment, start the API, open `http://localhost:8000/docs`.
2. Clear Swagger Authorize; execute each `GET /admin/*` route: expect 401.
3. Register two ordinary test accounts via `POST /auth/register`; supplying a `role` property must return 422. Login via `POST /auth/login` and authorize with the returned bearer token without copying it into reports. `/auth/me` must show `role=user`.
4. Call each admin route as that user: expect 403. Upload safe test documents under both owners; record IDs privately. Normal document/list/conversation access must remain owner-scoped; foreign IDs return generic 404. Verify search/RAG/message ownership with existing TESTING.md scenarios separately.
5. Run the explicit promotion command for one existing account. Repeat: success. Run against an unregistered placeholder: not-found, no account created. `/auth/me` for promoted account must report admin.
6. As admin, `GET /admin/overview`: compare totals and status groups with the prepared database records. Only counts, no contents or health claims.
7. `GET /admin/users?skip=0&limit=1`, then `skip=1`: correct pages and total. Search `email` substring: correct matches. Confirm item fields match the allowlist and no hashes/tokens occur.
8. `GET /admin/documents?skip=0&limit=1`, then next page: cross-user metadata and correct owner identity. Filter by `status=processed` and `embedding_status=indexed`, separately and together; compare with fixture states. Invalid status or `limit=101`: 422. Confirm no storage paths, vectors, text, error strings or chat contents.
9. Admin calling an ordinary owner endpoint with the other owner's ID still receives 404. Log out and remove Swagger authorization.

## Exact manual browser checklist — PASS

1. Start the configured frontend; ordinary user login: Admin nav absent. Visit all three `/app/admin*` URLs directly: access denied; return-to-chat link works.
2. Admin login: Admin visible in desktop sidebar/mobile drawer. Open overview and compare displayed metrics with Swagger. Navigate Users/Documents; current tab and heading must match.
3. Use at least 21 safe test records to verify Next/Previous, first/last disabled controls. Search email and clear search; filters reset to page one. Test each document filter, combined filters and no matches.
4. Refresh each direct admin URL: `/auth/me` restores access. Log out and sign in as ordinary user: no previous admin data should appear.
5. Simulate offline/failed request in browser tools: loading, error and retry must work; changing filters quickly must not restore stale results. Verify backend 403 after persisted role removal blocks data on the next request.
6. At 1440, 1024, 768 and 390px: inspect long filenames/emails/UUIDs, cards, filters, pagination and mobile drawer; no horizontal page overflow. Tab/Shift+Tab through navigation and controls: visible focus, meaningful labels, no trap. Inspect table headers/cells with a screen reader, including mobile stacked rows; enable reduced motion.
7. Rerun owner-local `npm.cmd run build` and `npm.cmd run typecheck`. Stop the relevant dev process first if it holds generated files. Use Next's type generation/build to synchronize routes; do not hand-edit `.next` files. Follow TESTING.md for safe generated-output cleanup only if necessary.
8. Run the dedicated disposable PostgreSQL test Compose commands from TESTING.md; application volumes must remain untouched. Record results before accepting Phase 8G.

## Git review and limits

No stage/commit/push. Scoped source diff review and whitespace check completed. Full Git inspection encounters pre-existing inaccessible tracked `.pytest_tmp*` artifacts; these were not cleaned or changed by this task. Pre-existing `.agents/` and strategy documents remain untouched. Temporary `.agent-handoff/LATEST_CODEX_REPORT.md` is ignored and must not be committed. Owner-local application DB migration/bootstrap, live Swagger security checks, frontend build/typecheck, browser validation, responsive checks and accessibility checks PASS. Phase 8G is owner accepted. Phase 9 has not started. A passing SQLite suite is not owner acceptance or production migration certification.
