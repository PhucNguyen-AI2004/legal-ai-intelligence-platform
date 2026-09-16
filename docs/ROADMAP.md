# Roadmap

## Current Phase 9C status — 2026-09-16

Phases 9A and 9B are owner accepted. Phase 9C is complete and owner accepted. Document processing and indexing now enqueue durable Redis/RQ work handled by a dedicated worker. See [Phase 9C validation](PHASE_9C_VALIDATION.md). Phase 9 remains in progress; 9D and Phase 10 have not started.

**Historical interim work: Pre-8G Chat UX refinement.** Completed and owner accepted; see [validation/checklist](PRE_8G_CHAT_UX_VALIDATION.md). This does not renumber phases or start 8G, 9 or 10.

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
| 8F | PASS — owner accepted | Frontend polish and regression; see PHASE_8F_VALIDATION.md |
| 8G | PASS — owner accepted | Read-only Admin Dashboard V1 |
| 9 | In progress — 9A/9B/9C PASS; owner accepted | Production engineering; 9D not started |
| 10 | Planned | Deployment: CI/CD, production configuration, portfolio packaging |

## Phase 8E boundary

**The owner confirmed 8E manual acceptance in the explicit 8F task.** [Phase 8E validation](PHASE_8E_VALIDATION.md) retains historical results. Phase 8F owner-local automated validation and manual regression both PASS; Phase 8F is owner accepted.

Phase 8F, 8G, 9A, 9B, and 9C are owner accepted. Phase 9D has not started. Commit/push only when requested. Do not automatically begin Phase 9D.Phase 8F, 8G, 9A, 9B, and 9C are owner accepted. Phase 9D has not started. Commit/push only when requested. Do not automatically begin Phase 9D.

## Optional later work

Hybrid search/reranking, legal versioning, OCR/tables, and RAG evaluation are future options, not current commitments or implemented features. HttpOnly cookies and refresh-token support are potential later auth hardening. Keep work to one authorized phase; do not silently bundle these into 8E.
