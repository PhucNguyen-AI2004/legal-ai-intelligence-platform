# LEGAL AI INTELLIGENCE PLATFORM

**Pre-8G Chat UX refinement:** frontend-only Stop waiting with draft copies and history reconciliation, per-answer Sources drawer, and cleaner user/assistant hierarchy are implemented. Owner manual acceptance and owner-local build remain pending. No backend cancellation or streaming; Phase 8G has not started. See [current validation](PRE_8G_CHAT_UX_VALIDATION.md).

Snapshot: 2026-09-14, inspected repository HEAD `7a675b7` (`feat: add conversations workspace and history`). Phase PASS labels below reflect the project owner's supplied history, not a fresh runtime certification during this documentation task.

## Purpose and workflow

A production-oriented legal document intelligence platform, intended to be technically serious, maintainable, portfolio-quality for AI/Data Engineering, and deployable later as a real product. It is not yet a fully hardened production deployment and must not become a generic ChatGPT clone.

Authentication → PDF/DOCX/TXT upload → text extraction/normalization → chunking → embeddings → pgvector retrieval → grounded RAG → citations → multi-turn conversations → frontend workspace.

## Technology and operating facts

| Area | Current choice |
| --- | --- |
| Backend | Python (Docker target 3.12), FastAPI, Uvicorn, synchronous SQLAlchemy 2.x, Alembic, psycopg |
| Database | PostgreSQL 16, pgvector, image `pgvector/pgvector:pg16-bookworm` |
| Connectivity | Local PostgreSQL `localhost:5433`; Docker `postgres:5432`; API `localhost:8000`; frontend `localhost:3000` |
| Configuration/auth | Pydantic Settings; UUID users, unique email, Argon2id hashes, HS256 JWT access tokens |
| Documents | UTF-8 TXT, DOCX through python-docx, text PDF through pypdf; default maximum 20 MiB; no OCR |
| Chunking | Paragraph-aware, character-based; CHUNK_SIZE=1200, CHUNK_OVERLAP=200 defaults |
| Embeddings | Local `intfloat/multilingual-e5-small`, 384 dimensions, normalized; `passage: ` documents and `query: ` queries |
| Retrieval | Exact cosine search in pgvector; owner, document state, model, and optional document filters |
| Generation | OpenAI-style chat-completion provider abstraction; secrets configured externally |
| RAG defaults | Similarity threshold 0.45; maximum context 12000 characters |
| History | CHAT_HISTORY_MAX_MESSAGES defaults to 6; bounded intent context, never evidence |
| Frontend | Next.js App Router, React, TypeScript, Tailwind CSS, ESLint, lucide-react, Inter |

Compose persists `postgres_data`, `document_storage`, and `model_cache`. Local storage defaults to `storage/documents`; Docker uses `/app/storage/documents`. Local and Docker storage are distinct. Settings validate the fixed embedding model/dimension. Consult `.env.example` and `frontend/.env.example` for variable names; never print private environment files or secret values.

## Development history

| Phase | Reported status | Delivered capability |
| --- | --- | --- |
| 1 Foundation | PASS | FastAPI, database, ORM, migrations, Docker, /health |
| 2 Authentication | PASS | Register/login/me, password hashing, JWT, owner boundaries |
| 3 Documents | PASS | Secure upload/storage, metadata, owner-isolated list/detail/delete |
| 4 Processing | PASS | Extraction, normalization, DocumentChunk, paragraph-aware chunks and statuses |
| 5 Embeddings | PASS | chunk_embeddings, indexing states, index endpoint and semantic search |
| 6 Grounded RAG | PASS | Retrieval/context, provider abstraction, citation validation and no-context handling |
| 7 Conversations | PASS | conversations/messages/message_citations, persistence and follow-up query rewriting |
| 8A Foundation | PASS | Frontend routes, shell/sidebar, design tokens, API foundation, visual auth/documents |
| 8B Authentication | PASS | AuthProvider, central token/client, /auth/me validation, guards, logout, CORS, session persistence |
| 8C Documents | PASS | Real upload/list/detail/delete/process/index/chunks, pagination and request states |
| 8D Conversations | PASS | Real sidebar CRUD, direct URL history, rename/delete, loaded-title search, pagination, responsive layout |

Recent history corroborates the sequence: `21ade67` RAG, `052fd8d` multi-turn, `abfdab9` 8A, `85eec92` 8B, `22c29a0` 8C, `7a675b7` 8D. Phase 8E enables sending, per-message selection, reconciliation and live citation previews. The owner confirmed manual acceptance in the explicit 8F task. Phase 8F polish is implemented and owner accepted. Owner-local lint, typecheck, 12/12 helper tests, production build, and manual regression all PASS. The remaining Codex sandbox Node EPERM is an execution-environment limitation, not an application defect. See [Phase 8F validation](PHASE_8F_VALIDATION.md).

## UX direction

Professional legal SaaS with a light theme, restrained navy/indigo, high readability, and familiar conversational interaction without directly copying ChatGPT visuals. Desktop first and responsive; sidebar approximately 272px expanded and 64px collapsed, with mobile drawer behavior. Backend state and URL navigation drive the workspace.

## Source reconciliation and caveats

- README's opening current-phase section and a later summary still say frontend is absent. These are historical claims; its Phase 8E addendum and current source supersede them.
- Owner-reported PASS history is broader than README's explicit manual confirmation of Phases 1–5. No historical test counts or fresh PASS results are inferred from commits.
- The grounded-only principle is stronger than current enforcement: `app/services/rag.py` and `chat.py` return generated text with `grounded=false`, empty citations when no citation markers are present. Invalid references fail closed. Citation validation checks reference membership, not semantic support for every claim. No-context fallback text is currently fixed Vietnamese, although answer prompts request the user's language. These are documented limitations, not fixes in this task.
- Conversation search filters loaded sidebar titles locally; it is not a backend-wide search endpoint. Saved citations now open live chunk previews; missing or changed sources show an unavailable state.
- Phase 8F generalizes frontend ESLint/Git exclusions to `.next-*` while retaining `.next` and node_modules exclusions. This is tooling hygiene, not a trace-lock workaround.
- Initial working tree contained 213 pre-existing tracked deletions under `.pytest_tmp/`, `.pytest_tmp2/`, and `.pytest_tmp3/` (71 each). Preserve them; ignored files can remain tracked. The tracked SQL backup also remains untouched.
- Prior Windows pytest permission issues and Docker/WSL/overlayfs incident are owner-provided operational history, not independently reproduced here.
