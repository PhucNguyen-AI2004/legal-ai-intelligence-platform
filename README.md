# Legal AI Intelligence Platform

## Project overview

Dự án portfolio hướng tới vị trí Fresher/Junior AI Engineer hoặc Data Engineer.
Mục tiêu dài hạn là xử lý tài liệu pháp luật và trả lời câu hỏi có dẫn nguồn.
**Phase 1 chỉ xây nền backend**, chưa xử lý hoặc trả lời nội dung pháp luật.

## Current phase

Đã có FastAPI, cấu hình môi trường, SQLAlchemy, PostgreSQL, Alembic và Docker.
Chưa có bảng business, upload, LLM, RAG, embedding, vector database, frontend
hoặc authentication. Đây là nền tảng có cấu trúc để mở rộng; chưa phải bản triển
khai production hoàn chỉnh (chưa có TLS, secrets manager, backup hay monitoring).

## Tech stack

| Thành phần | Vai trò |
| --- | --- |
| Python 3.12 | Runtime mục tiêu; Docker dùng đúng phiên bản này |
| FastAPI + Uvicorn | HTTP API và ASGI server |
| SQLAlchemy 2.x + psycopg 3 | Engine, connection pool, ORM session và PostgreSQL driver |
| PostgreSQL 16 | Database quan hệ |
| Alembic | Quản lý thay đổi schema có phiên bản |
| Pydantic Settings | Đọc và validate cấu hình |
| Docker + Docker Compose v2 | Đóng gói backend và chạy cùng database |

`requirements.txt` dùng khoảng phiên bản tương thích để dễ học. Chưa có lockfile
nên hai lần cài ở thời điểm khác nhau có thể nhận bản dependency khác nhau;
khi chuẩn bị release cần chốt bộ phiên bản đã kiểm thử.

## Current architecture

```text
HTTP client -> Uvicorn -> FastAPI -> GET /health -> {"status": "ok"}
                           |
                           +-> lifespan: SELECT 1 -> PostgreSQL

Future database endpoints -> Depends(get_db) -> Session -> Engine -> PostgreSQL
Alembic -----------------------------------------------> PostgreSQL schema
```

- Tách `api`, `core`, `db` vì mỗi phần có trách nhiệm riêng. Chưa tạo `models`,
  `schemas`, `services` khi chưa có nghiệp vụ cần dùng.
- Chọn SQLAlchemy đồng bộ để quản lý transaction đơn giản. Endpoint dùng database
  sau này nên là `def` để FastAPI chạy trong thread pool; không gọi truy vấn đồng
  bộ trực tiếp trong `async def`. Kiểm tra DB lúc startup đã dùng thread pool.
- Engine dùng chung connection pool; mỗi request lấy session riêng qua
  `Depends(get_db)`. Caller gọi `commit()` khi hoàn tất nghiệp vụ; dependency
  rollback khi có lỗi và luôn đóng session. Không dùng session toàn cục.
- `pool_pre_ping` kiểm tra connection trước khi lấy từ pool; không tự retry
  transaction đang chạy khi DB bị mất kết nối.
- Settings đọc `.env` ở thư mục gốc; biến môi trường hệ điều hành có ưu tiên cao
  hơn file. Thiếu cấu hình, sai APP_ENV hoặc sai driver URL sẽ báo lỗi sớm.
- Startup chạy `SELECT 1`: cấu hình sai hoặc DB chưa sẵn sàng thì ứng dụng không
  khởi động thành công. `/health` là **liveness**, không chứng minh DB còn hoạt
  động nếu DB ngừng chạy sau startup.
- Alembic dùng chung Settings và `Base.metadata`, không lưu URL trong INI và
  không gọi `create_all()`. Migration chạy riêng để tránh nhiều backend cùng sửa
  schema khi khởi động.
- Compose đợi PostgreSQL healthy trước khi tạo backend. Backend kiểm tra đăng
  nhập thực tế lúc startup vì `pg_isready` không xác thực đầy đủ credentials.
- Named volume giữ dữ liệu sau khi container bị tạo lại. Backend chạy non-root,
  không dùng `--reload` trong container; `.env` không được copy vào image.

Tham khảo chính thức: [SQLAlchemy sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics/),
[Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## Folder structure

```text
app/
  __init__.py
  main.py
  api/
    __init__.py
    health.py
  core/
    __init__.py
    config.py
  db/
    __init__.py
    base.py
    session.py
alembic/
  env.py
  script.py.mako
  versions/.gitkeep
alembic.ini
Dockerfile
docker-compose.yml
requirements.txt
.dockerignore
.gitignore
.env.example
.env                 # Local only, không commit
README.md
```

## Cấu hình môi trường

Chạy lệnh từ thư mục gốc repository. Nếu chưa có `.env`, PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash: `cp .env.example .env`. Không ghi đè `.env` nếu đã tùy chỉnh.

`APP_NAME` là tên hiển thị trong OpenAPI; `APP_ENV` nhận `development`, `test`,
`production` (hiện chưa thay đổi hành vi ứng dụng); `DATABASE_URL` là URL SQLAlchemy
cho Python chạy local. `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` cấu hình
container và tạo URL nội bộ cho backend trong Compose.

Các giá trị `legal_ai_dev` / `local_dev_only_change_me` là giá trị development công
khai, không phải secret thật. Nếu đổi user/password/database, cập nhật cả các biến
POSTGRES và DATABASE_URL local. Compose dùng host `postgres`, local dùng `localhost`.
Mẫu Compose ghép URL trực tiếp, nên dùng password development chỉ có chữ, số và `_`.
Nếu dùng ký tự đặc biệt như `@`, `:`, `%`, cần percent-encode phần password trong URL
và sửa Compose để nhận URL đã encode; POSTGRES_PASSWORD vẫn là giá trị thô.

## Cách chạy bằng Docker

Cần Docker Desktop đang chạy Linux containers và Docker Compose v2.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Phase 1 chưa có revision nên `current` không in revision ID là bình thường.
Alembic có thể tạo bảng kỹ thuật `alembic_version`; không có bảng business.
Migration không tự chạy trong Dockerfile hoặc khi start API.

```powershell
Invoke-RestMethod http://localhost:8000/health
docker compose exec postgres psql -U legal_ai_dev -d legal_ai -c "SELECT 1;"
```

Nếu đã đổi user, thay `legal_ai_dev` tương ứng. Dừng stack và giữ dữ liệu:

```powershell
docker compose down
```

## Cách chạy local

Cài Python 3.12; dùng PostgreSQL trong Docker và backend trên máy:

```powershell
docker compose up -d postgres
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Nếu `.venv` đã tạo bằng Python khác, tạo lại bằng 3.12 hoặc dùng tên `.venv312`
và điều chỉnh đường dẫn; thêm tên môi trường mới vào `.gitignore`.
Không bắt buộc activate venv nên tránh lỗi ExecutionPolicy của PowerShell.
Trên Linux/macOS: dùng `python3.12 -m venv .venv`, sau đó `.venv/bin/python`.
Nếu PostgreSQL đã cài local, tạo DB `legal_ai`, user/password phù hợp và cập nhật
DATABASE_URL; không cần chạy container postgres.

Không chạy đồng thời backend Docker và backend local trên cổng 8000.
Nếu đang chạy cả stack, dùng `docker compose stop backend` trước khi chạy local.

## Cách kiểm tra /health

Truy cập `http://localhost:8000/health` hoặc:

```powershell
curl.exe -i http://localhost:8000/health
```

Kỳ vọng HTTP 200, JSON `{"status":"ok"}`. OpenAPI UI có sẵn tại
`http://localhost:8000/docs`; đây là tài liệu API do FastAPI cung cấp.

## Kiểm tra và migration

```powershell
.\.venv\Scripts\python.exe -m compileall -q app alembic
.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
docker compose config --quiet
```

Import và offline migration không chứng minh đã kết nối PostgreSQL. Cần chạy
stack, online migration và kiểm tra HTTP để xác nhận tích hợp thực tế.

Kết quả kiểm tra khi khởi tạo workspace:

- Đạt: compile Python, cú pháp tương thích Python 3.12, đọc/validate Settings
  (cả giá trị sai), metadata chưa có bảng, HTTP 200 và JSON của health router
  trong ứng dụng kiểm tra riêng, parse YAML và kiểm tra cấu trúc Compose.
- Các kiểm tra runtime trên dùng package có sẵn của Python 3.13, chưa xác nhận
  bộ dependency trong requirements trên Python 3.12.
- Chưa đạt kiểm tra import toàn bộ app vì máy thiếu `psycopg`; chưa chạy được
  Alembic CLI vì chưa cài Alembic. Cài dependency từ PyPI bị chặn mạng và yêu cầu
  cấp quyền tải bị từ chối.
- Chưa chạy Docker build, `docker compose config`, PostgreSQL hoặc migration
  online/offline vì thiếu công cụ/dependency. Kiểm tra YAML không thay thế được
  việc validate và chạy bằng Docker Compose.

Khi có model ở phase sau: kế thừa Base, import model trong `alembic/env.py`, chạy
`alembic revision --autogenerate -m "describe change"`, review migration rồi mới
`alembic upgrade head`. Chạy tạo revision local để file nằm trong repository.

## Planned next phases

1. Upload tài liệu, lưu file/metadata, validation và migration business đầu tiên.
2. Trích xuất, làm sạch, chunking văn bản và pipeline xử lý dữ liệu.
3. Embedding, vector storage, retrieval và đánh giá retrieval.
4. RAG, trả lời câu hỏi với citation và lịch sử hội thoại.
5. Authentication, chuẩn hóa REST API, kiểm thử và hardening.
6. Deploy production, logging/monitoring cơ bản, backup và CI/CD.

Đây là lộ trình dự kiến; chỉ Phase 1 được triển khai trong phiên bản này.

## Troubleshooting

| Vấn đề | Cách xử lý |
| --- | --- |
| Không tìm thấy docker | Cài Docker Desktop, bật Linux containers, mở terminal mới |
| `py -3.12` không có | Cài Python 3.12 hoặc chạy toàn bộ qua Docker |
| Settings ValidationError | Kiểm tra `.env`, APP_ENV và tiền tố `postgresql+psycopg://` |
| Connection refused | Kiểm tra DB đang chạy, cổng 5432 và host local/Compose |
| Password authentication failed | Đồng bộ các biến; thay `.env` không đổi password của DB đã nằm trong volume |
| Cổng 8000/5432 đã được dùng | Dừng tiến trình trùng hoặc đổi host port; local DATABASE_URL phải dùng host port mới |
| Backend chưa healthy | Xem `docker compose logs backend postgres`; `/health` không chạy trước khi startup DB check thành công |
| `alembic current` không có ID | Bình thường khi chưa có revision |
| Model mới không được autogenerate | Import model vào Alembic env trước khi so sánh metadata |

Với database đã khởi tạo, đổi password bằng SQL có kiểm soát hoặc giữ cấu hình
cũ. `docker compose down -v` sẽ **xóa dữ liệu volume**; chỉ dùng khi chủ động muốn
reset toàn bộ database development.
