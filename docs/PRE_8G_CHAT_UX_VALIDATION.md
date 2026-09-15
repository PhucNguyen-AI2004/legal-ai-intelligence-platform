# Pre-8G Chat UX refinement

## Final Sources document reader — current status

Owner accepted all other Pre-8G behavior, including automatic Stop reconciliation and citation list/Back navigation. This final narrow pass changes only the selected source view into an in-drawer text document reader. Earlier preview/link descriptions below are historical and superseded by this section. Owner acceptance of the new reader remains pending.

### Architecture and behavior

Selecting a citation mounts a local reader; nothing is prefetched for other answers. It reads authenticated `GET /documents/{id}`, then `GET /documents/{id}/chunks?skip=...&limit=10` through the existing document API. The backend returns offset pagination, total, and chunks in ascending chunk_index order. The initial window starts two chunks before the citation where possible, even for citations far beyond the first page. Exact chunk UUID membership establishes cited evidence; the index is only a location hint, never proof of identity. If the window lacks the UUID, a one-chunk lookup at the citation index verifies availability before showing another window. Each requested page rechecks live document/citation access. Missing/reprocessed UUIDs fail unavailable.

The reader displays current document title/type and full extracted text of each loaded chunk, preserving whitespace, chunk separation and API order. No 280-character truncation, fabricated headings/pages or document management controls. Previous/next buttons progressively replace the ten-chunk window; the citation button explicitly returns to evidence. This bounds mounted content while making all current chunks accessible. Extraction/chunk overlap is preserved and labelled; this is a text reader, not a reconstruction of the original PDF/DOCX layout.

The cited article has a blue evidence treatment plus the visible label “Được trích dẫn [n]”. On first successful load, a stable element reference focuses it with preventScroll and adjusts only the reader viewport's scrollTop using measured element positions. No scrollIntoView on ancestors, fixed offsets or smooth-motion dependence. Ordinary rerenders do not reset scroll; explicit pagination/return-to-evidence actions intentionally reposition the reader. Reader content scrolls internally while Back/Close and pagination remain outside that scroll area. Existing list/Back focus return, Escape, source switching and modal shell are preserved. No full-document route link remains in the reader.

Loading, document-read error, chunk-read error and missing current citation have local reader states with read-only retry. Late results after source switch/Back/close are ignored. No competing global document store, backend write or citation mutation. A document can still change after a successful fetch; existing APIs have no immutable version/snapshot guarantee.

### Skill and exact changed files

Skill used: `D:/legal-ai-platform/.agents/skills/ui-ux-pro-max/SKILL.md`, previously read in full and applied to reader hierarchy, progressive disclosure, focus, labelled evidence, readable 16px typography, contained scroll, wrapping and reduced motion.

Created this pass:

- `frontend/src/lib/documents/source-reader.ts`
- `frontend/tests/source-reader.test.mjs`

Modified this pass:

- `frontend/src/components/chat/citation-source.tsx`
- `frontend/src/components/chat/message-sources.tsx` (list description only)
- `frontend/src/app/globals.css` (reader styles only)
- `docs/PRE_8G_CHAT_UX_VALIDATION.md`, `docs/HANDOFF.md`
- `.agent-handoff/LATEST_CODEX_REPORT.md` (ignored temporary report)

Deliberately unchanged this pass: Stop hook/reconciliation, composer, user/assistant bubble layout, SourcePicker and document_ids/reset behavior, conversation routing/persistence, API client/contracts, document management pages, auth, backend, database, RAG/search/embeddings, dependencies, strategy documents and skills.

### Validation evidence

- `npm.cmd run lint`: PASS, exit 0.
- `npm.cmd run typecheck`: PASS, exit 0.
- `node --experimental-strip-types --test tests/message-flow.test.mjs tests/submission-lifecycle.test.mjs tests/citation-drilldown.test.mjs tests/source-reader.test.mjs`: PASS, **30/30**, 0 failures. Breakdown: 12 message helpers, 7 lifecycle, 4 drill-down, 7 reader tests. Existing MODULE_TYPELESS_PACKAGE_JSON warning remains.
- Reader tests verify late citation windows, full text/API ordering, off-window UUID revalidation, replaced UUID unavailability, document/chunk failures and GET-only retry, loading settlement, scope preservation and absence of document navigation/management controls. Existing tests preserve list/select/Back/switch/isolation and accepted Stop behavior.
- `npm.cmd run build`: environment-limited, exit 1 before compilation, EPERM opening `frontend/.next/trace`, errno -4048. Outside-sandbox retry requested and declined; no workaround or cleanup.
- Scoped `git diff --check -- frontend docs`: PASS, exit 0; normal LF/CRLF notices. Prior tracked/untracked changes preserved. Exact final status/stat recorded in ignored handoff. No stage/commit/push.
- Authenticated browser interaction, real-source integration, viewport screenshots and keyboard scroll/focus were not executed in this pass; existing tooling has no configured browser automation. Source review and pure tests do not establish manual acceptance. Backend tests not rerun because backend is unchanged.

### Owner reader checklist

- [ ] Single source: Nguồn → select → document content inside drawer; cited chunk highlighted/focused; Back returns to same list; route unchanged.
- [ ] Late citation in a large document: correct chunk loads initially; previous/next show ordered full text; return-to-citation works; manual scrolling is not repeatedly reset.
- [ ] Multiple sources: select 1, Back, select 2; correct document/evidence each time without mixing answers.
- [ ] Chat stays in position; close returns focus/context; pre-send Document B stays selected while browsing old Document A evidence.
- [ ] Missing/reprocessed source and document/chunk network failures show local error/unavailable state; retry performs reads only.
- [ ] 1440/1024/768/390px: readable text, contained scrolling, long titles, accessible Back/Close and no horizontal overflow.
- [ ] Keyboard source selection, evidence focus, reader scrolling, Back, Close/Escape, focus return and reduced motion.
- [ ] Owner-local `npm.cmd run build` before final acceptance.

PRE-8G SOURCES DOCUMENT READER IMPLEMENTED. OWNER MANUAL ACCEPTANCE REQUIRED. PHASE 8G HAS NOT STARTED.

---

## Corrective pass — current status (2026-09-15)

The owner accepted the blue user bubbles, assistant flow, compact Sources control/right drawer, Send/Stop control, editable restoration, scope/reset, live verification and responsive direction. Two remaining findings prompted this narrow correction: Stop required unnecessary acknowledgement and source inspection needed list/detail drill-down inside the drawer.

This section supersedes the acknowledgement and expandable-source descriptions in the historical implementation report below. No new acceptance is inferred for this corrective pass.

### Stop correction

Intentional Stop is interruption metadata, not a POST error. The existing hook still owns AbortController, restores the editable copy immediately and automatically fetches authoritative history. Successful reconciliation marks the stopped submission ready without a user acknowledgement, clears the temporary neutral status and enables explicit sending. Editing stays available during reconciliation and failure; sending remains guarded while history is unresolved. A genuine GET failure shows a compact “Không thể đồng bộ lịch sử” / “Thử lại” state. Retry is GET-only and successful retry unlocks automatically. Ordinary provider-failure recovery is unchanged.

Saved original questions remain in backend history. Missing rows remain classified unknown rather than falsely unsaved. Ready means client reconciliation completed, not that server generation stopped. Existing concurrency/cross-tab limitations remain; no server cancellation, streaming, generation persistence or automatic resend. First-message routing and conversation creation remain unchanged.

### Sources correction

`Nguồn · n` opens the selected answer's list of semantic citation buttons. Selection replaces the list with one citation detail inside the same drawer: title/number, chunk label, verified bounded excerpt and secondary “Xem tài liệu đầy đủ ↗” link in a new tab. “Tất cả nguồn” returns to the list; another selection displays only that citation. Closing/reopening resets to the list. No chat navigation or pre-send SourcePicker mutation.

Detail focuses its heading; Back restores focus to the selected citation button. Existing native Modal retains Escape/close, focus containment/return, desktop right-panel layout, mobile full-height layout, internal scrolling and reduced motion. Chunk UUID verification and the 280-code-point excerpt policy are preserved through a pure helper. Missing/reprocessed chunks show unavailable state and retry; no old excerpt is fabricated. The full document workspace is unchanged.

### Skill and files

Skill: `D:/legal-ai-platform/.agents/skills/ui-ux-pro-max/SKILL.md`. Applied neutral interruption feedback, progressive disclosure, predictable Back, focus management, restrained information density, safe wrapping and existing reduced-motion behavior.

Created this pass: `frontend/tests/citation-drilldown.test.mjs`.

Modified this pass: `use-conversation-messages.ts`, `conversation-detail-workspace.tsx`, `message-sources.tsx`, `citation-source.tsx`, `message-flow.ts`, `globals.css`, `submission-lifecycle.test.mjs`, this validation document, `docs/HANDOFF.md` and the ignored `.agent-handoff/LATEST_CODEX_REPORT.md`.

Deliberately unchanged this pass: composer/base message design, source picker, API transport/contracts, auth, backend/database, RAG/retrieval, document workspace, creation routing, dependencies, strategy documents and skills. No phase advancement.

### Corrective validation

From `frontend/`:

| Command | Result |
| --- | --- |
| `npm.cmd run lint` | PASS, exit 0 |
| `npm.cmd run typecheck` | PASS, exit 0 |
| `node --experimental-strip-types --test tests/message-flow.test.mjs` | PASS, 12/12 |
| `node --experimental-strip-types --test tests/submission-lifecycle.test.mjs` | PASS, 7/7 |
| `node --experimental-strip-types --test tests/citation-drilldown.test.mjs` | PASS, 4/4 |
| `npm.cmd run build` | Environment-limited, exit 1: EPERM opening `.next/trace-build`, errno -4048, before compilation |
| Outside-sandbox build retry | Declined by user; not executed |

Total: 23 passed, 0 failed. Existing MODULE_TYPELESS_PACKAGE_JSON warning remains. Initial lifecycle test update placed a ready-state assertion before GET completion; corrected the test placement and reran successfully. No lint rule, compiler setting or source workaround was introduced for the build limitation.

Lifecycle tests cover immediate copies/edits, send guards, successful automatic readiness without acknowledgement, no automatic resend, failed GET and GET-only retry, retry auto-unlock, saved/unknown history and first-send duplicate prevention. Four source helper tests cover list/selection/back/switch resolution, current-answer membership, replaced/missing/empty live chunks and scope isolation. Focus, rendering and the secondary document action were source-reviewed; pure callback/helper tests do not establish browser behavior. No authenticated browser regression or new viewport checks were executed in this pass.

### Short owner corrective checklist

- [ ] Send → Stop: copy appears and editing works immediately; neutral synchronization feedback disappears and Send unlocks automatically; no acknowledgement or automatic resend.
- [ ] Fail history reconciliation: compact retry appears, editing remains possible, sending stays guarded. Retry performs only GET and successful retry unlocks automatically.
- [ ] First-message Stop stays in one created conversation and preserves the saved original question.
- [ ] One citation: Nguồn → list → detail inside drawer → Back. Full document link is secondary and opens a new tab.
- [ ] Multiple citations: select 1, Back, select 2; only the selected detail appears. No navigation away from chat or mixing answers. Test deleted/reprocessed source and retry.
- [ ] Opening/using the drawer leaves next-question scope unchanged.
- [ ] Desktop/mobile: long titles/excerpts wrap, no page horizontal scroll; keyboard list/detail/Back, Escape, focus return and reduced motion work.
- [ ] Rerun production build owner-local before acceptance.

Git: scoped diff/whitespace review passed. Whole-tree historical artifact diagnostics are isolated with scoped checks. Pre-existing edits/untracked files preserved; no stage, commit or push. Current exact status/stat is recorded in the ignored handoff report. Git stat includes the earlier uncommitted refinement and omits untracked files.

PRE-8G CHAT UX CORRECTIVE PASS IMPLEMENTED. OWNER MANUAL ACCEPTANCE REQUIRED. PHASE 8G HAS NOT STARTED.

---

## Historical initial implementation report

Implemented 2026-09-15; owner manual acceptance required. Phase 8G has not started. No commit or push.

## 1. UI/UX skill used

`D:/legal-ai-platform/.agents/skills/ui-ux-pro-max/SKILL.md` (read in full). Applied web accessibility, visible focus, semantic icon controls, 44px controls, readable line height, bounded wrapping, progressive source disclosure, native modality, focus return, contained scrolling and reduced motion. Focused local UX and React searches informed implementation; existing navy/blue tokens and Lucide icons retained.

## 2. Architecture review

The existing provider owns keyed histories, queued first submissions, synchronous duplicate guards and GET reconciliation after every POST attempt. The server commits the user before generation; citation references point to live chunks. Source selection snapshots apply to one submission and reset immediately. Central `apiRequest` already forwards RequestInit, including AbortSignal. Backend/API/database changes were not required or made.

Contracts used unchanged: POST /conversations; POST /conversations/{id}/messages; GET /conversations/{id}; GET /documents/{id}/chunks?skip={chunk_index}&limit=1. Authentication, ownership, RAG and grounding stay backend-authoritative.

## 3. Files changed

Created:

- `frontend/src/components/chat/message-sources.tsx`
- `frontend/tests/submission-lifecycle.test.mjs`
- `docs/PRE_8G_CHAT_UX_VALIDATION.md`
- `.agent-handoff/LATEST_CODEX_REPORT.md` (temporary ignored report)

Modified:

- `frontend/src/components/chat/chat-composer.tsx`
- `frontend/src/components/conversations/conversation-detail-workspace.tsx`
- `frontend/src/components/conversations/use-conversation-messages.ts`
- `frontend/src/lib/conversations/conversation-api.ts`
- `frontend/src/lib/conversations/message-flow.ts`
- `frontend/src/app/globals.css`
- `docs/ARCHITECTURE.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/PROJECT_CONTEXT.md` (current-task addenda)

Deliberately unchanged: backend files, migrations, auth/token/client implementation, conversation creation/provider routing, new-chat workspace, source picker, live citation verifier, workspace navigation, dependencies and phase numbering.

## 4. Send/Stop implementation

Lifecycle: no submission (idle), queued, sending, stopping, reconciling, settled. Existing recovery metadata stays within the same submission model. The hook owns one AbortController per active conversation POST; the API forwards its signal. Composer receives an onStop action without HTTP knowledge. Future transport/streaming work can extend this boundary without rewriting composer persistence behavior.

Stop immediately records a provider-held editable copy, aborts client waiting and starts authoritative reconciliation. Edits survive reconciliation and client route changes while the provider remains mounted. A copy is not an unsent message; no saved row is removed and no POST is retried. Source scope is not restored or inherited.

Sending stays blocked during reconciliation or a failed GET. After a successful GET, the existing explicit history-review acknowledgement unlocks a later explicit send while preserving edits. GET-only reload remains available during recovery. A saved user row is retained; absent rows after abort remain unknown. Duplicate clicks, Enter and queued-first-send replays are guarded synchronously. Stop on the first message stays in its already-created conversation; it does not create/delete/navigate to another conversation. Conversation creation itself is not cancellable; Stop appears once the message POST starts on the destination route.

Limitations: client abort and a completed history GET cannot establish that server generation stopped. The backend can finish later, and there is no generation status, terminal-failure, cancellation or idempotency contract. History-review acknowledgement is a user decision, not proof of server completion. Sending while a prior server operation remains active can encounter the existing sequence-number concurrency limitation. No exactly-once/cross-tab guarantee is claimed. Full page reload clears in-memory draft copies. True server cancellation and streaming remain later enhancements.

## 5. Sources UX

Each assistant answer with persisted citations has a compact `Nguồn · n` button. It opens a read-only right drawer, full-width on small screens. The existing native Modal provides Escape dismissal, focus containment, background inertness and trigger focus return. Body scrolling locks and stable scrollbar space avoids horizontal movement; the panel scrolls internally.

Numbered source entries retain their document names and chunk labels. Click an entry to fetch and verify the live chunk UUID through the existing CitationSource. Excerpts remain first-paragraph previews capped at 280 Unicode code points, with retry/unavailable states and a document link opening a new tab. Opening the drawer itself does not fetch every chunk. Inline [n] text is preserved and maps to the numbered panel entries; inline click handling was not added. No source scope mutation, fabricated metadata, local grounding inference or vectors.

## 6. Message layout

User questions use content-sized, right-aligned blue bubbles with bounded width, visible role labels and preserved multiline wrapping. Assistant answers flow without a large card/border, with 16px text and 1.75 line height within the existing 800px conversation measure. Backend grounding labels and recovery notices remain visible. Desktop panel width is at most 460px; mobile is full-width/full-height using dvh. Existing reduced-motion rule disables panel animation.

## 7. Tests

Existing 12 message-flow tests pass. Seven new tests exercise real hook callbacks with a minimal state/ref host and mocked transport: normal send/source snapshot; duplicate/queued first-send claims; client abort classification/phase guard; first-message Stop with saved user; Stop with unknown persistence; failed GET recovery plus Stop/response race; provider failure preserving saved user semantics. Tests verify editable copies are not overwritten, no automatic resend, and explicit subsequent sends use the same conversation with fresh source scope.

This host does not simulate React rendering, browser events, focus or effect scheduling; those remain manual checks.

## 8. Validation evidence

Commands run from frontend:

| Command/check | Result |
| --- | --- |
| `npm.cmd run lint` | PASS, exit 0 after fixing a test-harness hook-call naming diagnostic; no rule disabled |
| `npm.cmd run typecheck` | PASS, exit 0 |
| `node --experimental-strip-types --test tests/message-flow.test.mjs tests/submission-lifecycle.test.mjs` | PASS, 19 tests, 19 passed, 0 failures; existing MODULE_TYPELESS_PACKAGE_JSON warning |
| `npm.cmd run build` | Environment-limited, exit 1 before compilation: EPERM opening `frontend/.next/trace`, errno -4048 |
| Outside-sandbox build | Requested after EPERM; declined by user, not executed |
| Existing runtime HTTP smoke | Frontend localhost:3000 /login 200; backend localhost:8000 /health 200 |
| Authenticated browser/manual flows | Not executed; no configured browser tool or installed Playwright/Puppeteer; no browser dependency added |
| Backend suite | Not run; no backend changes |

No source/config workaround, process termination, generated-output deletion or database cleanup. Build must be rerun owner-local; this sandbox error does not establish an application build defect.

## 9. Manual owner checklist (all pending)

- [ ] Normal send, Enter, Shift+Enter, Vietnamese IME and 4000-character boundary; rapid double Enter/click sends once.
- [ ] Slow response: Send becomes labelled keyboard-accessible Stop; clicking restores an editable copy immediately, focuses the composer and never auto-resends.
- [ ] Edit during GET reconciliation; submission remains blocked. Simulate failed GET; reload is GET-only and preserves edits. Review saved/unknown history before explicitly sending again.
- [ ] First-message Stop: exactly one created conversation, stable URL, persisted user retained, editable copy preserved; no automatic retry. Navigate away/back during Stop/reconciliation.
- [ ] Long/multiline user question wraps in a right bubble; long assistant answer flows without a card. Grounded, ungrounded and error notices remain clear.
- [ ] Compact Nguồn control opens sources for the chosen answer. Close, Escape, Tab/Shift+Tab containment and focus return work. Switch to another answer; inspect multiple numbered citations.
- [ ] Long document names wrap. Expand previews, retry errors, test deleted/reprocessed/missing sources, and open document in a new tab. Match inline [n] to panel entries.
- [ ] Default all documents; select A/send/reset; select B/send/reset; next send uses all documents. Stopped draft does not restore A/B automatically.
- [ ] Check 1440, 1024, 768 and 390px: bubble/read width, composer/Stop, drawer, navigation, long names, zoom and no page-level horizontal scrolling.
- [ ] Keyboard-only operation, visible/unobscured focus, screen-reader labels/status, Escape and reduced motion.
- [ ] Real provider/network failure, refresh history, auth expiration and two-owner document/citation privacy regressions.
- [ ] Rerun owner-local `npm.cmd run build` and record result before acceptance.

## 10. Git review

Scoped authored diff reviewed; scoped `git diff --check -- frontend docs` is clean. Whole-tree `git diff --check` returns exit 0 but emits permission diagnostics for pre-existing tracked `.pytest_tmp*` artifacts; it is not a clean inspection of those artifacts. Initial 213 artifact deletions and untracked skills/strategy documents are preserved. New files reviewed directly because ordinary git diff omits them. Exact status/stat is captured in the ignored handoff report. No staging, commit or push.

## 11. Scope confirmation

PRE-8G CHAT UX REFINEMENT IMPLEMENTED. OWNER MANUAL ACCEPTANCE REQUIRED. PHASE 8G HAS NOT STARTED.
