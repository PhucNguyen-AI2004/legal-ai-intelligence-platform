# Phase 8E completion fixes: validation and owner retest

**Current status:** The owner confirmed Phase 8E completion and manual acceptance in the explicit Phase 8F task. Results/checklists below are historical records, not a reversal of that acceptance. Fresh checks are recorded in [Phase 8F validation](PHASE_8F_VALIDATION.md); acceptance does not imply the historical Windows build failure passed.

Date: 2026-09-15. Status: implementation ready for owner retest with an external build blocker; **Phase 8E is NOT PASS until owner manual testing passes.** No Phase 8F/admin/backend work, commit or push.

## Owner observations before this fix

Owner reported working auth/workspace, conversation creation, sending, grounded answers, no-context answers, multi-turn context and citations. The follow-up did not invent unsupported contract-termination content. These observations apply to the pre-fix version, not completed acceptance of the changes below.

## Four verified causes and fixes

| Issue | Source finding | Fix |
| --- | --- | --- |
| Extra create prerequisite | /app/chat rendered ChatComposer without onSend, causing it to substitute a create button | NewChatWorkspace renders an immediate composer; existing provider createNew accepts an optional first message, queues it, navigates, then claims/sends once the URL is active |
| Prominent, growing selector | Composer owned and eagerly loaded the document list, with a large source summary and accumulating checkbox list | Compact optional source trigger; separate native dialog loads only on open and renders one 20-document page |
| Question stays in composer | Draft was cleared only after message POST succeeded; failures always retained it without examining persisted rows | Snapshot and clear synchronously on submit; provider reconciles after POST success/failure and classifies saved/not-saved/unknown before offering recovery |
| Too much citation text | Source started collapsed, but click exposed the entire live chunk | Compact markers remain default; explicit click loads the first non-empty paragraph, at most 280 characters including ellipsis, with close and existing document link |

## Architecture and exact behavior

The central API client, token storage, authenticated 401 behavior, owner boundaries and backend are unchanged. Active conversation remains selected by URL. ConversationProvider owns one useConversationMessages instance for keyed history and submission state, so queued first sends, active sends and recovery survive client route changes. No competing active-conversation ID is introduced.

The existing createNew flow serves both sidebar creation and automatic first-send creation. A synchronous creation lock lasts through destination navigation. Only a queued submission whose conversation matches the URL can start; a synchronous per-conversation claim prevents duplicate Enter/click events and Strict Mode replays. First-send failure remains associated with the newly created conversation, so recovery never creates another one. Returning with Back shows a fresh /app/chat draft; queued work is not replayed after it has started.

Composer captures trimmed content and current source IDs, clears visible text immediately, and shows a sending state/temporary pending question. The temporary question disappears when authoritative persisted messages arrive; it is not added to stored history. Pending submission blocks further sends. Existing Enter/Shift+Enter, IME and 4000-character checks remain.

Scope defaults to all eligible documents, omitting document_ids entirely. Specific IDs are snapshotted for one request. This fix retains the established stronger rule: selection resets to all documents at each submission attempt, including failure; it never comes from history. Creation failure restores text without sending a message; source selection still resets. After a failed message with no saved user row, draft restoration is explicit and the UI asks the user to choose source scope again if needed.

Provider refetches history after every message POST attempt and updates the sidebar from authoritative detail. Failed sends compare new user-message IDs and content against the pre-send history, so an identical earlier question does not falsely count as this send. Saved user turns keep the composer empty. A completed API failure with no matching new turn permits an explicit Restore draft action. Lost connections, aborted requests, and HTTP 408/502/504 remain unknown when a fresh GET has no matching row: the server may still be working. No POST is retried automatically. POST success with GET failure offers only history reload until synchronization succeeds. Recovery and error state stay associated with the conversation during navigation.

The picker renders only 20 document rows at a time, keeps selected IDs across pages up to 100, disables ineligible documents, and supports retry, previous/next, and refresh with selection reset. A native dialog supplies focus containment and Escape dismissal; page responses are ignored after closure/page change. Deleted/stale IDs remain subject to backend validation. Default all-documents mode works without any list request or eligible documents.

Citations fetch only on click. The existing chunk API uses skip=chunk_index and limit=1; the returned UUID must match the citation. Preview displays the first non-empty paragraph, capped at 280 characters including ellipsis, with normalized whitespace and no internal scrolling, honestly labeled as a short preview of the live source, not an invented semantically selected quote. Close collapses it; document detail opens in a new tab. Missing/reprocessed chunks and 404/network errors produce a local unavailable/retry state. No raw vectors, HTML rendering or legal-correctness guarantees are introduced.

## Verified backend contract (unchanged)

- POST /conversations/{id}/messages: trimmed content 1-4000, top_k default 5/range 1-10, optional document_ids null or 1-100 IDs; [] invalid. Returns one assistant MessageRead.
- User message commits before rewriting/retrieval/generation; provider failure may leave it saved. History informs intent only; fresh retrieved chunks supply evidence on every turn.
- Citation fields: citation_index, document_id, document_name, chunk_id, chunk_index, similarity_score. References point to live rows, not immutable snapshots.
- Owner document list and chunks use skip/limit. Retrieval eligibility remains processed/indexed and matching model; UI does not replace backend authorization/model checks.

## Related races addressed

- Shared history-read promises let every Strict Mode/remount caller observe failures rather than silently treating an in-flight GET as success.
- Provider request state survives switching conversations; source/draft UI state stays route-local.
- Removed the previous redundant post-send detail effect GET; one orchestration path performs reconciliation, with explicit reload on failure.
- Sidebar list refresh detects changes made while a list request was pending and refetches once. Continued changes show a reload prompt rather than overwrite the new entry or loop indefinitely.
- Delete remains blocked while a submission/history refresh is active; deleted history/submission entries are removed from provider memory.
- Source IDs reset and dialogs close on submit; citation components are keyed by live chunk ID to avoid reused previews after a changed relationship.

## Automated validation actually executed

| Check | Result | Exact evidence |
| --- | --- | --- |
| npm.cmd run lint | PASS | Final exit 0; no errors/warnings |
| npm.cmd run typecheck | PASS | Final exit 0 |
| node --experimental-strip-types --test tests/message-flow.test.mjs | PASS | 7 tests, 7 pass, 0 fail; Node 24.14.1; harmless MODULE_TYPELESS_PACKAGE_JSON warning, package module mode left unchanged |
| npm.cmd run build | FAIL / EXTERNAL BLOCKER | Exit 1 before compilation: EPERM opening frontend/.next/trace-build |
| Build process/permission diagnosis | BLOCKED | Elevated read-only inspection request rejected by user; no dev processes stopped and no generated directory removed |
| HTTP smoke using Node http | PASS, limited | Existing localhost:3000 /login, /app/chat and /app/chat/00000000-0000-0000-0000-000000000001: 200 HTML without Internal Server Error; localhost:8000 /health: 200 |
| Authenticated browser runtime of these fixes | SKIPPED | No configured browser automation/browser plugin available; no authenticated interaction was executed in this fix task |
| Backend validation | SKIPPED | No backend changes; no new backend PASS claimed |
| Scoped git diff / diff --check | PASS | Authored changes reviewed; whitespace checks clean, ordinary LF/CRLF notices only |
| Owner acceptance | PENDING | Updated checklist below is not marked as executed |

npm.cmd invokes the requested npm scripts while avoiding the known PowerShell npm.ps1 launcher policy. HTTP smoke reuses already-running servers and does not establish browser hydration or authenticated user flows. Build failure is environmental; no source workaround, dependency upgrade, generated-file edit or database cleanup was attempted.

## Owner retest checklist (all pending for this fix)

1. [ ] Open /app/chat: type immediately; no manual create prerequisite.
2. [ ] First Enter creates exactly one conversation, changes URL, sends exactly one user message, and adds one sidebar entry.
3. [ ] Refresh the new direct URL: user/assistant history persists in sequence order. Browser Back returns to a fresh new-chat view without replaying the first send.
4. [ ] Ask a context-dependent follow-up; verify evidence-based multi-turn behavior.
5. [ ] Ask without opening Sources: request omits document_ids and uses all eligible documents; test an empty library too.
6. [ ] Explicitly select Document A and send; inspect request scope.
7. [ ] Select Document B next turn; ensure A is not inherited.
8. [ ] Send next turn untouched: all-documents scope. Test multiple selections, page navigation, refresh, stale/deleted/reprocessed IDs, 100-selection limit and no eligible rows.
9. [ ] Composer clears immediately on submission, including slow requests. Shift+Enter inserts a newline; IME Enter does not send prematurely.
10. [ ] Double-click Send, press Enter twice quickly and press Enter during pending creation/send: one conversation and one intended message only.
11. [ ] Grounded answer renders backend grounding and persisted citations without correctness claims.
12. [ ] Unsupported question returns clear no-context/ungrounded behavior without a UI crash.
13. [ ] One/multiple citations stay compact by default; no full chunk appears automatically.
14. [ ] Click, close and switch citations; each excerpt is bounded, and Open document works. Test a long chunk and deleted/reprocessed source/404.
15. [ ] Refresh and verify saved markers, direct links and missing live relationships remain safe.
16. [ ] Safely exercise provider failure: saved user row stays visible, composer stays empty, reload is GET-only. Exercise no-row API failure: explicit Restore draft does not create a new conversation. Exercise network loss and failed reconciliation: no automatic restore/resend.
17. [ ] Direct conversation URL and navigation during a send work; return shows completed history or its recovery state, independent source picker and no stale draft.
18. [ ] Rename/delete/sidebar pagination remain correct. Attempt deletion during sending; test creating a different conversation while a previous send is unresolved.
19. [ ] Login/logout, authenticated 401 and two-user owner isolation regressions.
20. [ ] Mobile/desktop: source dialog focus/Tab/Escape, page controls, long answers/source titles and citation controls remain usable.
21. [ ] Creation failure restores the draft and shows error. Test navigation failure/Back around first-send creation; ensure no duplicate creation/replay.
22. [ ] Resolve the exact Windows Next.js process/permission blocker, rerun build, and record result before complete automated frontend PASS.

## Deliberately outside scope / limitations

- Full reloads and separate tabs do not share the in-memory send guard. No backend idempotency contract exists; the frontend cannot establish exactly-once delivery across network loss. A lost create response can leave an empty server conversation; no automatic creation retry occurs.
- Route-local drafts and selected IDs are not persisted across navigation. Captured submitted questions and recovery do survive navigation within the mounted provider.
- Citation excerpt is the beginning of the live chunk, not a semantic highlight. The backend supplies no quote span or immutable snapshot. Zero-citation grounding reasons remain indistinguishable in MessageRead.
- Existing static suggested-prompt buttons, streaming, auto-scroll, full corpus search/metadata filters and general Phase 8F polish were not changed.

## Git preservation

Pre-existing Phase 8E implementation and docs remain uncommitted. Also preserved: 213 tracked deleted/inaccessible .pytest_tmp* paths; the existing frontend/next-env.d.ts generated import difference; untracked CAREER_STRATEGY.md, LEARNING_CONTEXT.md and PORTFOLIO_STRATEGY.md. SQL backup untouched. No staging, commit, push, dependency changes or generated output included. Temporary report remains ignored.

## Citation-preview follow-up validation

Owner accepted the previous compact default marker but requested a shorter clicked preview. Current helper prefers the first non-empty paragraph and caps displayed output at 280 Unicode code points including ellipsis; whitespace is normalized and the internal scroll area removed. Empty sources have local feedback. No semantic support span is inferred.

Current checks: npm.cmd run lint and npm.cmd run typecheck PASS; node --experimental-strip-types --test tests/message-flow.test.mjs PASS (12/12). npm.cmd run build remains blocked, this run with EPERM opening frontend/.next/trace (previously trace-build). Authenticated click/close/second-citation/document navigation/refresh/deleted-source/mobile checks remain pending owner retest. See the ignored latest Codex report for exact scope and edge cases; no Phase 8E PASS claimed.
