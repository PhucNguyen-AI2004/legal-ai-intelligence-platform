# Roadmap

**Authorized interim work: Pre-8G Chat UX refinement.** Implemented, owner acceptance pending; see [validation/checklist](PRE_8G_CHAT_UX_VALIDATION.md). This does not renumber phases or start 8G, 9 or 10.

Status baseline supplied by the project owner, reconciled with source on 2026-09-14. Historical PASS is not a new validation result.

| Phase | Status | Scope |
| --- | --- | --- |
| 1 | Completed / PASS | Foundation |
| 2 | Completed / PASS | Authentication |
| 3 | Completed / PASS | Documents |
| 4 | Completed / PASS | Document processing |
| 5 | Completed / PASS | Embeddings and pgvector search |
| 6 | Completed / PASS | Grounded RAG |
| 7 | Completed / PASS | Conversations and multi-turn backend |
| 8A | Completed / PASS | Frontend foundation |
| 8B | Completed / PASS | Frontend authentication |
| 8C | Completed / PASS | Document workspace |
| 8D | Completed / PASS | Conversation CRUD and read-only history workspace |
| **8E** | **Completed / owner-manually accepted** | **Chat + RAG + Citations frontend integration** |
| 8F | Implemented; validation incomplete, not PASS | Frontend polish and regression; see PHASE_8F_VALIDATION.md |
| 8G | Deferred | Admin dashboard |
| 9 | Planned | Production engineering: background work, logging, rate limits, testing/hardening |
| 10 | Planned | Deployment: CI/CD, production configuration, portfolio packaging |

## Phase 8E boundary

**The owner confirmed 8E manual acceptance in the explicit 8F task.** [Phase 8E validation](PHASE_8E_VALIDATION.md) retains historical results. Phase 8F owner-local automated validation and manual regression both PASS; Phase 8F is owner accepted.

Phase 8F is complete and owner accepted. Final Git review and commit remain before starting Phase 8G. Never automatically begin admin 8G. Commit/push only when requested. Never automatically begin admin 8G.

## Optional later work

Hybrid search/reranking, legal versioning, OCR/tables, and RAG evaluation are future options, not current commitments or implemented features. HttpOnly cookies and refresh-token support are potential later auth hardening. Keep work to one authorized phase; do not silently bundle these into 8E.
