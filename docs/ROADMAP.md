# Roadmap

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
| **8E** | **NEXT — NOT IMPLEMENTED** | **Chat + RAG + Citations frontend integration** |
| 8F | Planned | Frontend polish and regression |
| 8G | Deferred | Admin dashboard |
| 9 | Planned | Production engineering: background work, logging, rate limits, testing/hardening |
| 10 | Planned | Deployment: CI/CD, production configuration, portfolio packaging |

## Phase 8E boundary

**8E HAS NOT BEEN IMPLEMENTED.** Its planned scope is sending user messages, per-message selected document_ids, multi-turn interaction, grounded assistant responses, citations, clickable citation/source UX, and loading/error/no-context states. Backend Phase 7 messaging and Phase 8D saved citation markers already exist; they do not mean frontend 8E is complete.

Starting 8E requires an explicit user task. Inspect backend routes/schemas and current services before integrating. Complete automated validation, manual integration testing, and Git review before claiming PASS. Commit/push only when explicitly requested. Never automatically begin 8F or admin work afterward.

## Optional later work

Hybrid search/reranking, legal versioning, OCR/tables, and RAG evaluation are future options, not current commitments or implemented features. HttpOnly cookies and refresh-token support are potential later auth hardening. Keep work to one authorized phase; do not silently bundle these into 8E.
