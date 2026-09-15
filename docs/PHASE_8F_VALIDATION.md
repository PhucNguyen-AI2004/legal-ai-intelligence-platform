# Phase 8F: frontend polish and regression

Status: PASS — owner accepted. Automated application validation PASS on owner local environment and owner manual browser regression PASS. Phase 8E owner acceptance remains unchanged.. Phase 8E owner acceptance remains unchanged. No source, backend or dependency changes were required to establish the local build result.

## Current evidence by execution environment

Owner-provided evidence, run from `D:/legal-ai-platform/frontend` in normal local Windows:

- Node filesystem write test: **PASS**.
- `npm.cmd run build`: **PASS**, completing optimized production build, compilation, TypeScript, page data collection, static page generation and page optimization.
- Application build defect: **NOT reproduced locally**. The root issue is isolated to the Codex execution environment; the sandbox failure is not evidence that the application cannot build.
- Owner subsequently explicitly confirmed that `npm.cmd run lint`, `npm.cmd run typecheck`, and `node --experimental-strip-types --test tests/message-flow.test.mjs` also passed locally (12/12 helper tests). Together with the production-build PASS, all four local automated checks are confirmed. These are owner-reported results, not commands executed by Codex in this documentation task; no local exit codes or logs were supplied.

**CODEX SANDBOX BUILD VALIDATION: ENVIRONMENT-BLOCKED BY NODE EPERM.**

The sandbox itself has not been repaired. Earlier Node write/open probes failed on ordinary frontend files and new files as well as traces, while Windows API/Python probes succeeded. Combined with the owner-local write/build PASS, this isolates the failure to the execution environment. No specific trace lock holder or exact sandbox enforcement mechanism was identified.

Current automated application status, based on the owner-confirmed results:

PHASE 8F AUTOMATED APPLICATION VALIDATION: PASS ON OWNER LOCAL ENVIRONMENT.
PHASE 8F MANUAL REGRESSION: PASS.
PHASE 8F OWNER ACCEPTANCE: PASS.
CODEX SANDBOX BUILD VALIDATION: ENVIRONMENT-LIMITED BY NODE EPERM. NOT AN APPLICATION DEFECT.

## Initial audit and scoped fixes

The first pass inspected login/register, new/existing chat, documents list/detail, shared controls, shell/sidebar/header, and existing auth/message/source logic before editing. Findings are from source inspection, not a rendered browser audit.

| Finding | Phase 8F fix |
| --- | --- |
| Upload and rename/delete overlays used role attributes without native focus containment or Escape handling | Small shared native Modal; focus restoration when the original trigger remains mounted; Escape/Cancel blocked while mutations run; bounded dialog height and background scroll lock |
| Collapsing desktop sidebar removed JSX that mobile CSS could not restore; offscreen mobile links remained focusable | Separate native mobile drawer renders the full sidebar; desktop sidebar hidden at mobile widths; links close drawer; desktop resize dismisses drawer |
| Sidebar action menu could be clipped by its scrolling list, relied on hover, and lacked dismissal state | Actions expand within the row; always-visible trigger with expanded state; Escape/focus-leave dismissal; header actions reset on route changes |
| Long filenames, detail headings, metadata and chunk text could enlarge flex/grid children | Allow shrinking and word wrapping; bound table filename display; retain full names in detail/title attributes and an explicitly focusable table scroll region |
| Disabled controls and focus treatments varied; source controls were small on touch | Shared disabled styles, stronger focus outlines, larger mobile controls, reduced-motion support and skip-to-content link |
| Small success/pending badges used light foreground colors | Darker semantic status text; existing written status labels retained |
| Failed initial document load also displayed the empty-library invitation; errors lacked retry | Separate load failure from empty library; GET-only list/detail retries; list-delete errors visible inside confirmation |
| Suggested prompts and settings appeared clickable with no behavior; filter was a disabled placeholder | Remove inactive controls; retain immediate chat composer and existing search, clearly scoped to current document page |
| Registration password constraints were only explained after failure | Short visible requirement hint; pending submission guard; central auth untouched |
| Ignore rules covered only one alternate Next build directory | Generalize frontend Git/ESLint `.next-*` exclusions; no generated-file edits or disabled lint rules |

The established light navy/indigo styling and CSS architecture are retained. This phase does not add chat features or redesign the product.

## Regression evidence and limits

- **Chat:** inspected existing synchronous creation/send guards, Enter/Shift+Enter/IME handling, immediate draft clearing, per-submission source reset, URL selection, keyed request state, GET reconciliation and persistence-aware recovery. These paths were not changed. All 12 existing helper tests pass, covering source snapshots/omission, saved/unknown persistence and bounded Unicode citation previews. This is not an interactive end-to-end chat PASS.
- **Documents:** process/index/delete API implementations and server-authoritative refetch behavior remain intact. Changes concern presentation, retry and dialogs. Upload/process/index/pagination/delete were not executed against a user account in this task.
- **Auth:** inspected AuthProvider, guards and central API client; `/auth/me`, localStorage token module, public login errors and global authenticated 401 handling remain unchanged. No real login/register/logout was executed.
- **Responsive/accessibility:** source reviewed for desktop/tablet/mobile breakpoints; 1440/1024/768/390px browser checks and keyboard/screen-reader interaction remain pending. The documents table intentionally retains local horizontal scrolling for its columns. Native dialog focus behavior still requires browser verification, particularly after successful deletion removes the trigger.
- **Tests:** no tests added or changed; pure message/citation logic unchanged. No browser framework or dependency installed.

## Historical Codex sandbox commands and results

The following were executed previously inside the Codex sandbox from `frontend/`; they are not owner-local results. No commands were rerun for this documentation update.

| Command | Result |
| --- | --- |
| `npm.cmd run lint` | Final PASS, exit 0, no diagnostics. Initial pass caught two leftover icon references after inactive-control removal; fixed before final pass. |
| `npm.cmd run typecheck` | Final PASS, exit 0. Initial same two references fixed. |
| `node --experimental-strip-types --test tests/message-flow.test.mjs` | PASS, 12/12, exit 0. Existing MODULE_TYPELESS_PACKAGE_JSON warning; package module mode unchanged. |
| `npm.cmd run build` | FAIL, exit 1 before compilation. First run EPERM opening `.next/trace`; final run EPERM opening `.next/trace-build`, errno -4048. |

Build diagnosis:

1. `Get-CimInstance Win32_Process -Filter "Name = 'node.exe'"` filtered by command lines matching `next|legal-ai-platform`: Windows access denied, HRESULT 0x80041003.
2. `Get-Item -Force -LiteralPath` on exact `D:/legal-ai-platform/frontend/.next`, `trace` and `trace-build`: ordinary directory/Archive files, no link/reparse targets.
3. Outside-sandbox request for the same filtered process query and `Get-Command handle.exe,handle64.exe`: rejected by user before execution.
4. No lock holder or specific relevant PID was confirmed. No processes stopped, no `.next` removed, no ACL/source workaround. Subsequent owner-local evidence above isolates this as a Codex environment limitation; only the sandbox build remains blocked.

Historical Codex runtime probe (not a statement about the current owner-local server): Node HTTP GETs to localhost:3000 `/login`, `/register`, `/app/chat`, `/app/documents`, and chat/document detail with a synthetic UUID all returned ECONNREFUSED. No server was running at the probed address. No new dev server was started against the unresolved build-output access problem. No browser tooling is configured; no viewport screenshots, hydration or authenticated runtime PASS claimed.

Git review: status/stat/scoped diffs and diff whitespace checks reviewed. Pre-existing Phase 8E work, local skills/strategy documents and historical tracked `.pytest_tmp*` artifacts preserved. Generated builds/dependencies and the handoff report remain ignored. Historical pytest permission warnings and LF/CRLF notices are separate from authored whitespace errors. Exact final status is in the ignored handoff report.

## Owner manual regression checklist

The owner completed the Phase 8F manual regression checklist and reported PASS for all items below:

- [x] Auth: register, invalid registration/login, login, protected direct URL, refresh session, logout and authenticated 401; public login errors stay local.
- [x] Documents: empty library, upload TXT/DOCX/text PDF, failed upload, list/detail, process, index, chunks, current-page search, pagination, delete/cancel/error and GET retry. Use long filenames, descriptions and unbroken chunk text.
- [x] Conversations: immediate `/app/chat` composer, exactly one auto-created conversation/first send, Enter vs Shift+Enter/IME, rapid duplicate send, multi-turn, direct URL/refresh, route switching during requests, rename/delete, sidebar loaded-title search and load more.
- [x] Sources/RAG: all-documents default, explicit A then B then default again, no inherited selection, grounded and no-context answers, follow-up query and provider/network/reconciliation failure recovery; no automatic resend.
- [x] Citations: compact default, open/close, long Unicode excerpt bounded to 280 code points, another citation, open document, missing/deleted/reprocessed source and retry.
- [x] Keyboard: skip link, visible focus, sidebar actions, Escape/focus-leave dismissal, upload/source/rename/delete dialogs, Tab/Shift+Tab containment, cancel focus return, busy dismissal guard, and focus after successful deletion.
- [x] Responsive: approximately 1440, 1024, 768 and 390px; expanded/collapsed desktop, collapse then resize/open mobile, close/navigate/resize drawer, source dialog, long answers/names, upload dialog on short viewport, document table scroll and detail. Check zoom and reduced motion.
Owner-local automated checks are confirmed PASS and are separate from the pending manual checklist above. Sandbox repair is not a prerequisite for local browser testing.

Phase 8F is fully owner accepted. Automated application validation PASS on the owner local environment, and owner browser/manual regression PASS. The Codex sandbox build remains environment-limited by Node EPERM, but this was not reproduced locally and is not an application defect. Phase 8G must not begin until the Phase 8E/8F Git review and commit are completed.
