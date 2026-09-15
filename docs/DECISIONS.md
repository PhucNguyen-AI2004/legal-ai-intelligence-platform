# Architecture decisions

These notes capture existing choices and owner-specified constraints, preserved by Phase 8E frontend integration. See ARCHITECTURE.md for source locations and PROJECT_CONTEXT.md for enforcement limitations.

## ADR-01 — PostgreSQL and pgvector semantic search

**Accepted.** Keep relational metadata, ownership filters and chunk vectors in one database. Exact cosine search makes retrieval explicit and avoids operating a separate vector service. Consequence: current search is simple and inspectable; ANN indexes, hybrid retrieval and reranking remain later performance/quality decisions.

## ADR-02 — Multilingual E5 conventions

**Accepted.** Local `intfloat/multilingual-e5-small` supports the multilingual document workflow without paid embedding calls. Normalize 384-dimensional vectors and use `passage: ` for documents, `query: ` for queries to match the model's retrieval conventions. Model/dimension validation prevents mismatches; changing models requires deliberate schema/reindex planning.

## ADR-03 — Grounded-only RAG policy

**Accepted policy, with known enforcement limits.** Legal answers require retrieved evidence rather than invented legal references. Threshold and bound context, label documents untrusted, and validate citation references. No context means `grounded=false`, `citations=[]`, without answer generation. Current uncited generated answers can still be returned as ungrounded, and citation membership does not prove semantic support; do not claim stronger guarantees than implemented.

## ADR-04 — Conversation history is not evidence

**Accepted.** Previous assistant/user claims may be wrong or malicious. Use history only to resolve conversational intent; retrieve fresh document chunks for evidence. History cannot justify a legal claim or become a citation source.

## ADR-05 — Rewrite follow-up queries

**Accepted.** Follow-ups often omit subjects needed for semantic retrieval. Use bounded recent history (default 6 messages) to rewrite a standalone query. First turns use the raw question and avoid a rewrite call. Consequence: follow-ups may incur rewrite plus answer-generation calls; even a no-context follow-up may spend a rewrite call.

## ADR-06 — Document selection is per message

**Accepted.** Users can change evidence scope between turns. Pass the current message's `document_ids` only; backend scope must not silently inherit earlier selections. Omitted/null scope searches the owner's eligible library. Validate all supplied IDs against ownership.

## ADR-07 — /auth/me controls current identity

**Accepted.** Token presence does not prove token validity or current user state. AuthProvider validates sessions through `/auth/me`, while backend dependencies enforce identity and ownership on requests. Central authenticated 401 handling clears expired sessions consistently.

## ADR-08 — localStorage is a temporary v1 tradeoff

**Accepted for v1.** The existing backend issues stateless access tokens; one token-storage module gives the frontend simple persistence and consistent logout. Browser JavaScript can access these tokens, so XSS remains a material tradeoff. HttpOnly cookies and refresh-token support are potential later hardening requiring backend design, not a silent frontend-only change.

## ADR-09 — Backend-authoritative document states

**Accepted.** Processing and indexing can fail or conflict independently of UI actions. Use server responses/refetches instead of inventing success locally. The UI reflects persisted state and exposes appropriate recovery/error feedback.

## ADR-10 — Active conversation comes from URL

**Accepted.** `/app/chat/[conversationId]` supports direct links, refresh and browser navigation without a competing active-ID store. Sidebar and header derive selection from the route; loaded list state is presentation data, not navigation authority.

## ADR-11 — Owner isolation and privacy

**Accepted.** Legal documents and conversations must remain private to their owner. Filter backend operations and retrieval by authenticated identity and use generic not-found behavior for foreign resources where implemented. UI guards are usability measures, not substitutes for backend authorization. Conversation deletion removes its messages/citations without deleting source documents.

## ADR-12 — No destructive Docker fixes

**Accepted operational rule.** A prior Docker Desktop/WSL/overlayfs incident preserved database data. Ordinary runtime faults do not justify deleting persistence. Diagnose first; avoid volume-removal/prune commands and use the separate disposable test Compose project for database tests.

## ADR-13 — Explicit, understandable architecture

**Accepted.** Keep routes, schemas, services, models and transaction ownership visible; use synchronous SQLAlchemy with request-scoped sessions rather than unnecessary abstraction. Prefer Server Components and central client/token modules, adding client boundaries for interaction. Explain meaningful changes so the developer can understand and maintain their own code.
