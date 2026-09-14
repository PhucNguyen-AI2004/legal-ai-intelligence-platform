# Legal AI Intelligence Platform

## Project overview

Dự án portfolio hướng tới vị trí Fresher/Junior AI Engineer hoặc Data Engineer.
Mục tiêu dài hạn là xử lý tài liệu pháp luật và trả lời câu hỏi có dẫn nguồn.
**Phase 6 bổ sung single-turn RAG answer và citations**, dùng lại semantic retrieval
của Phase 5. Hướng dẫn cấu hình provider và kiểm tra ở mục **Phase 6** bên dưới.

## Current phase

Đã có FastAPI, cấu hình môi trường, SQLAlchemy, PostgreSQL, Alembic, Docker,
bảng users, đăng ký, đăng nhập bằng JWT, upload/lưu metadata, list/detail/delete
tài liệu thuộc user hiện tại, xử lý tài liệu, index embeddings, semantic search và RAG. Phase 1–5 đã được
người dùng xác nhận test thực tế.
Chưa có OCR, streaming, frontend, social login,
refresh token, email verification, forgot password hoặc role/permission phức tạp.
Đây là nền tảng có cấu trúc để mở rộng; chưa phải bản triển
khai production hoàn chỉnh (chưa có TLS, secrets manager, backup hay monitoring).

## Tech stack

| Thành phần | Vai trò |
| --- | --- |
| Python 3.12 | Runtime mục tiêu; Docker dùng đúng phiên bản này |
| FastAPI + Uvicorn | HTTP API và ASGI server |
| SQLAlchemy 2.x + psycopg 3 | Engine, connection pool, ORM session và PostgreSQL driver |
| PostgreSQL 16 | Database quan hệ |
| pgvector | Lưu vector và exact cosine search trong PostgreSQL |
| Sentence Transformers + PyTorch CPU | Local multilingual embeddings, không dùng paid API |
| Alembic | Quản lý thay đổi schema có phiên bản |
| Pydantic Settings | Đọc và validate cấu hình |
| Pydantic v2 + email-validator | Validate email, password và response công khai |
| pwdlib + Argon2id | Hash và verify password có salt ngẫu nhiên |
| PyJWT (HS256) | Ký và verify access token |
| pytest + HTTPX | Test auth, validation, migration và OpenAPI |
| python-multipart | Nhận file và text fields trong multipart/form-data |
| python-docx + pypdf | Extract paragraphs DOCX và text từng page PDF, không OCR |
| Docker + Docker Compose v2 | Đóng gói backend và chạy cùng database |

`requirements.txt` dùng khoảng phiên bản tương thích để dễ học. Chưa có lockfile
nên hai lần cài ở thời điểm khác nhau có thể nhận bản dependency khác nhau;
khi chuẩn bị release cần chốt bộ phiên bản đã kiểm thử.

## Current architecture

```text
HTTP client -> Uvicorn -> FastAPI -> GET /health -> {"status": "ok"}
                           |
                           +-> lifespan: SELECT 1 -> PostgreSQL

POST /auth/register -> UserCreate -> auth service -> Argon2 hash -> users
POST /auth/login -> UserLogin -> verify password -> signed JWT
GET /auth/me -> HTTPBearer -> get_current_user -> verify JWT -> users
Auth endpoints -> Depends(get_db) -> Session -> Engine -> PostgreSQL
Document endpoints -> current user -> document service -> PostgreSQL metadata
                                                       -> local document storage
POST /documents/{id}/process -> extract -> normalize -> chunk -> PostgreSQL chunks
Alembic -----------------------------------------------> PostgreSQL schema
```

- Giữ `api`, `core`, `db` của Phase 1; thêm `models` cho ORM, `schemas` cho hợp
  đồng request/response và `services` cho nghiệp vụ auth/documents. Không thêm repository
  abstraction vì hiện chỉ có vài thao tác database đơn giản.
- Chọn SQLAlchemy đồng bộ để quản lý transaction đơn giản. Endpoint dùng database
  hiện là `def` để FastAPI chạy trong thread pool; không gọi truy vấn đồng
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
    auth.py
    dependencies.py
    documents.py
    document_route.py
  core/
    __init__.py
    config.py
    security.py
  db/
    __init__.py
    base.py
    session.py
  models/
    __init__.py
    user.py
    document.py
    document_chunk.py
  schemas/
    __init__.py
    user.py
    token.py
    document.py
    document_chunk.py
  services/
    __init__.py
    auth.py
    documents.py
    document_storage.py
    document_processing.py
    text_extraction.py
    text_normalization.py
    text_chunking.py
alembic/
  env.py
  script.py.mako
  versions/0001_create_users.py
  versions/0002_create_documents.py
  versions/0003_document_processing.py
tests/
  conftest.py
  test_auth.py
  test_security.py
  test_migrations.py
  test_documents.py
  test_text_processing.py
  test_document_processing.py
storage/
  .gitkeep
  documents/           # Upload local, bị Git ignore
pytest.ini
alembic.ini
Dockerfile
docker-compose.yml
docker-compose.test.yml
requirements.txt
requirements-dev.txt
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
Repo hiện publish PostgreSQL ở `localhost:5433`; container vẫn dùng cổng `5432`.
Mẫu Compose ghép URL trực tiếp, nên dùng password development chỉ có chữ, số và `_`.
Nếu dùng ký tự đặc biệt như `@`, `:`, `%`, cần percent-encode phần password trong URL
và sửa Compose để nhận URL đã encode; POSTGRES_PASSWORD vẫn là giá trị thô.

### Biến môi trường auth

| Biến | Ý nghĩa |
| --- | --- |
| `SECRET_KEY` | Secret ngẫu nhiên ít nhất 32 byte, dùng ký/verify JWT; bắt buộc |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời hạn token, mặc định 30; nhận 1–1440 |
| `ALGORITHM` | Chỉ chấp nhận `HS256`, không lấy thuật toán từ token gửi lên |

`.env.example` cố ý để `SECRET_KEY=` trống; không có secret dùng chung trong repo.
Tạo secret riêng, rồi dán vào `.env` (không chia sẻ output):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Workspace hiện tại đã được bổ sung secret local ngẫu nhiên; clone mới cần tự tạo.
Không ghi đè `.env` đang có. `SecretStr` che secret khi biểu diễn Settings, nhưng
không thay thế việc giữ an toàn file/env. Validation độ dài không chứng minh
secret có đủ entropy: luôn dùng bộ sinh ngẫu nhiên bảo mật như lệnh trên.

## Cách chạy bằng Docker

Cần Docker Desktop đang chạy Linux containers và Docker Compose v2.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Head hiện tại là `0005_conversations_and_messages`; `current` phải hiển thị revision này.
Upgrade giữ users/documents và thêm processing_error/document_chunks. Database
mới chạy cả ba migration theo thứ tự. Chạy `docker compose exec backend alembic check`
để kiểm tra model/schema có đồng bộ không.
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

## User model và auth endpoints

| Field | Thiết kế |
| --- | --- |
| `id` | UUID v4 sinh ở Python, primary key; khó đoán hơn ID tăng dần nhưng không thay thế authorization |
| `email` | VARCHAR(254), bắt buộc, unique index `ix_users_email` |
| `hashed_password` | VARCHAR(255), chỉ lưu hash Argon2id |
| `full_name` | VARCHAR(200), bắt buộc, trim khoảng trắng hai đầu |
| `is_active` | Boolean, mặc định true từ database |
| `created_at` | TIMESTAMP WITH TIME ZONE, mặc định thời gian database |
| `updated_at` | TIMESTAMP WITH TIME ZONE; cập nhật khi SQLAlchemy thực hiện UPDATE |

`updated_at` dùng `onupdate` của SQLAlchemy, không phải database trigger; SQL viết
tay phải tự cập nhật field này. PostgreSQL giữ thời điểm có timezone; API trả ISO 8601.
Email được chuẩn hóa chữ thường ở schema đăng ký/đăng nhập theo chính sách của
ứng dụng; ghi SQL trực tiếp cần tuân thủ cùng quy tắc. Unique index bảo vệ trùng
giá trị đã chuẩn hóa, kể cả hai request đồng thời. Không có email verification nên
đăng ký thành công không chứng minh user sở hữu địa chỉ email.

| Endpoint | Input / xác thực | Thành công | Lỗi chính |
| --- | --- | --- | --- |
| `POST /auth/register` | JSON email, password, full_name | 201, UserRead | 409 email trùng; 422 dữ liệu sai |
| `POST /auth/login` | JSON email, password | 200, access_token + token_type | 401 sai email/password hoặc user inactive |
| `GET /auth/me` | Header Authorization: Bearer token | 200, UserRead | 401 thiếu/sai/hết hạn token hoặc user không còn tồn tại; 403 inactive |

Password đăng ký dài 12–128 ký tự, không được toàn khoảng trắng. Không bắt buộc
mẫu chữ hoa/số/ký hiệu, để hỗ trợ passphrase dài. Password không bị trim hoặc
normalize. `UserRead` không có password/hash; handler lỗi validation cũng loại
input để password không bị trả lại trong lỗi 422. Các field ngoài schema như
`is_active` trong request đăng ký bị từ chối.

### Vì sao hash password?

Server cần kiểm tra password nhưng không cần khôi phục password gốc. Argon2id là
hash một chiều với salt ngẫu nhiên và chi phí bộ nhớ/tính toán, làm việc dò password
khi lộ database tốn kém hơn. Không dùng SHA-256 đơn thuần hoặc mã hóa có thể giải mã.
`verify_password()` để thư viện so sánh với hash; không hash lại rồi so chuỗi vì salt
là ngẫu nhiên. Login dùng cùng lỗi 401 và vẫn verify dummy hash nếu email không có,
giảm khác biệt thời gian rõ ràng giữa email tồn tại và không tồn tại.

### JWT flow và dependency injection

1. Login tra user theo email, verify Argon2 và kiểm tra `is_active`.
2. Server ký JWT bằng SECRET_KEY với `sub` là UUID user, `iat`, `exp`, `token_type=access`.
3. Client gửi `Authorization: Bearer <access_token>` khi gọi `/auth/me`.
4. `HTTPBearer` trích token; `get_current_user` dùng PyJWT kiểm tra chữ ký, thuật toán
   cho phép, thời hạn và các claim bắt buộc. Pydantic kiểm tra UUID và loại token.
5. Dependency tra user trong database, kiểm tra còn tồn tại/active, rồi cung cấp
   user cho endpoint. Token lỗi trả 401 cùng `WWW-Authenticate: Bearer`.

JWT giúp request mang chứng nhận đã đăng nhập mà server không cần lưu từng access
token. Payload chỉ được ký, **không được mã hóa**; không đặt password hay secret vào
claim. Hệ thống vẫn tra database mỗi request để khóa user inactive có hiệu lực ngay.
`Depends` tập trung logic dùng chung và cho phép override session trong test;
endpoint không lặp lại code decode token hoặc quản lý kết nối.

Chọn JSON login và `HTTPBearer` để schema rõ ràng, Swagger nhập token trực tiếp.
Không dùng `OAuth2PasswordBearer` vì nó mô tả flow lấy token bằng OAuth2 form;
project hiện không triển khai OAuth2 password grant hoặc authorization server.
Tham khảo thư viện: [FastAPI JWT/password hashing](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/),
[PyJWT verify API](https://pyjwt.readthedocs.io/en/latest/api.html).

## Cách test auth bằng Swagger

1. Chạy migration, mở `http://localhost:8000/docs`.
2. Mở `POST /auth/register` → **Try it out**, gửi:

   ```json
   {"email":"student@example.com","password":"StrongPassword123!","full_name":"Test User"}
   ```

   Nhận 201 và user không có password/hash. Gửi lại nhận 409.
3. Mở `POST /auth/login`, gửi JSON chỉ có `email` và `password` như trên.
   Nhận 200, copy giá trị `access_token`. Password sai nhận 401.
4. Bấm **Authorize**, dán **chỉ token**, không thêm chữ `Bearer`, rồi xác nhận.
5. Gọi `GET /auth/me`: nhận 200 và thông tin user. Swagger tự thêm header Bearer.
6. **Authorize → Logout**, gọi `/auth/me` lại: nhận 401. Token hỏng/hết hạn cũng 401.

Swagger Logout chỉ xóa token khỏi giao diện, không thu hồi token phía server.

## Phase 3: Document model và endpoints

| Field | Thiết kế |
| --- | --- |
| `id` | UUID v4, primary key |
| `owner_id` | UUID, FK bắt buộc tới users.id; User có nhiều Document |
| `original_filename` | Tên do client gửi, chỉ dùng hiển thị sau validation |
| `stored_filename` | UUID hex + extension, unique; không dùng tên client để ghi file |
| `file_path` | Storage key tương đối, hiện bằng stored_filename; không trả trong API |
| `file_type`, `mime_type` | Loại pdf/docx/txt và MIME chuẩn được server lựa chọn |
| `file_size` | Số byte thực tế, BIGINT với CHECK > 0 |
| `title`, `description` | Title tối đa 255 ký tự; description optional, tối đa 5000 ký tự ở API |
| `status` | VARCHAR(32), mặc định uploaded |
| `created_at`, `updated_at` | Timestamp có timezone; cùng quy tắc SQLAlchemy như User |

Status dùng chuỗi để mở rộng không phải thay PostgreSQL enum. Upload tạo
`uploaded`; endpoint process của Phase 4 chuyển processing/processed/failed.
Index `(owner_id, created_at, id)` hỗ trợ lọc theo owner và phân trang theo thời gian.
FK dùng `ON DELETE RESTRICT`: không tự cascade metadata khi file vẫn còn trên disk.
Chưa có chức năng xóa user; nếu bổ sung cần xử lý tài liệu trước.
Từ Phase 4, DocumentRead có thêm `processing_error` nullable; chỉ chứa thông báo
an toàn, không chứa traceback hoặc đường dẫn nội bộ.

Tất cả endpoint sau yêu cầu Bearer token:

| Endpoint | Hành vi / response |
| --- | --- |
| `POST /documents` | Multipart file, title?, description? → 201 DocumentRead |
| `GET /documents?skip=0&limit=20` | 200 `{items, total, skip, limit}` của current user |
| `GET /documents/{document_id}` | 200 DocumentRead hoặc 404 |
| `DELETE /documents/{document_id}` | Xóa metadata và file nếu có → 204, không có body |

`skip >= 0`, `1 <= limit <= 100`; sort `created_at DESC, id DESC` để thứ tự ổn
định khi timestamp bằng nhau. `total` chỉ đếm tài liệu của owner. Count và list
là hai truy vấn nên có thể thay đổi giữa chúng nếu có ghi đồng thời.

`owner_id` lấy từ JWT/current user, không nhận từ form. Detail/delete truy vấn
bằng **cả id và owner_id**; tài liệu không tồn tại và không thuộc user đều trả
404 để không xác nhận sự tồn tại của tài liệu người khác. UUID khó đoán không
thay thế kiểm tra ownership. DocumentRead không chứa file_path/stored_filename.
Không có public download hoặc StaticFiles mount cho storage.

### Supported file types và upload limits

| Extension | MIME chuẩn | Kiểm tra nhẹ |
| --- | --- | --- |
| `.pdf` | application/pdf | Bắt đầu bằng `%PDF-` |
| `.docx` | application/vnd.openxmlformats-officedocument.wordprocessingml.document | ZIP có `[Content_Types].xml` và `word/document.xml`; không giải nén |
| `.txt` | text/plain | UTF-8 (có thể có BOM), không chứa byte NUL |

Extension không phân biệt hoa/thường. MIME cụ thể không khớp extension bị từ chối;
nếu client không gửi MIME hoặc gửi application/octet-stream, server vẫn kiểm tra
định dạng rồi lưu MIME chuẩn. Đây chỉ là validation nhẹ, **không chứng minh tài
liệu hoàn chỉnh/an toàn, không phải antivirus, OCR hay trích xuất nội dung**.
TXT mã hóa khác UTF-8 cần được chuyển sang UTF-8 trước khi upload.

| Config | Mặc định / ý nghĩa |
| --- | --- |
| `DOCUMENT_STORAGE_PATH` | `storage/documents`, relative theo project root hoặc absolute path |
| `MAX_UPLOAD_SIZE_MB` | `20`, mỗi đơn vị = 1024 × 1024 byte; config nhận 1–100 |

Giới hạn mặc định chính xác là **20 MiB**. File rỗng trả 400; quá dung lượng trả
413; type/MIME/nội dung không phù hợp trả 415; title/description quá dài trả 422.
Không chỉ tin `Content-Length` hay `UploadFile.size`: service đếm byte khi copy
từng khối 64 KiB. DocumentRoute còn giới hạn stream request trước multipart
parser ở mức file limit + 64 KiB dành cho fields/boundaries, kể cả khi thiếu
Content-Length. Upload quá giới hạn được chặn trước khi spool vô hạn xuống disk.

### Storage architecture và xử lý lỗi

PostgreSQL lưu metadata và quan hệ; filesystem lưu binary. Cách này giữ database
nhẹ, dễ query metadata và thuận tiện chuyển binary sang object storage về sau;
đổi lại phải backup/đồng bộ cả database lẫn storage.

Tên vật lý có dạng `<uuid-hex>.pdf`, không phụ thuộc original filename. Server
từ chối tên chứa đường dẫn, dấu `:` hoặc ký tự điều khiển, kiểm tra storage key
và đường dẫn nằm trong storage root, từ chối symlink của file. Ghi bằng chế độ
exclusive để không đè file đã có. Storage root là cấu hình tin cậy của operator;
không cấp quyền ghi thư mục này cho user không tin cậy trên cùng máy.

Upload: validate → ghi file giới hạn dung lượng → tạo metadata/flush → commit.
File đang ghi được dọn nếu validation/copy lỗi; nếu thao tác database thất bại,
rollback rồi xóa file vừa tạo. API không trả SQL diagnostic hoặc đường dẫn máy.

Delete: khóa row PostgreSQL → đổi tên file thành `<uuid>.<ext>.deleting` → xóa
metadata/commit → xóa file tạm. Nếu commit lỗi, rollback và khôi phục tên file.
File đã mất thì vẫn xóa metadata bình thường. Nếu không ghi/xóa được storage,
API trả 503; nếu metadata đã commit nhưng cleanup cuối lỗi, trả 503 với detail
`Metadata deleted; file cleanup pending` và log document ID để operator xử lý.

Filesystem và PostgreSQL **không chung transaction**. Việc dọn/khôi phục trên chỉ
xử lý lỗi thông thường, không đảm bảo atomic khi process crash hoặc mất kết nối
đúng lúc commit khiến kết quả commit không xác định. Có thể còn file mồ côi,
file `.deleting` hoặc metadata thiếu file; cần đối chiếu metadata/storage trước
khi cleanup thủ công. Phase này chưa xây worker reconciliation hoặc queue.

### Docker và persistence của storage

Compose mount named volume `document_storage:/app/storage`, và đặt
`DOCUMENT_STORAGE_PATH=/app/storage/documents` trong container. Dockerfile tạo
thư mục thuộc user `app` để backend non-root có thể ghi. Rebuild/recreate hoặc
`docker compose down` không xóa volume; `down -v` xóa cả file upload và DB volume.
Giữ cùng tên Compose project để dùng lại các volume đã tạo.

Named volume tách khỏi thư mục `storage/` khi chạy Python local. Vì vậy file
upload từ Docker không tự xuất hiện trong `./storage/documents`. Nếu cần dùng
chung file khi chuyển backend Docker/local, thay mount bằng
`./storage:/app/storage` và bảo đảm user container có quyền ghi trên host; không
dùng chmod 777. Đổi kiểu mount không tự di chuyển file trong volume cũ.
Git và Docker build context bỏ qua file upload; chỉ `storage/.gitkeep` được giữ.

### Test documents bằng Swagger

1. Rebuild backend, chạy `alembic upgrade head`, mở `/docs`, đăng nhập và Authorize.
2. `POST /documents` → Try it out → chọn file PDF/DOCX/TXT. Title và description
   không bắt buộc; title trống dùng tên file bỏ extension. Execute → 201.
3. Gọi `GET /documents` với skip/limit, copy id rồi gọi detail → 200.
4. Upload lại cùng tên: có ID/tên vật lý mới; upload .exe → 415, file rỗng → 400.
5. Đăng nhập user B, thử GET/DELETE id của A → 404; list của B không chứa file A.
6. Đăng nhập lại A, DELETE id → 204; detail sau đó → 404.
7. Logout Swagger, gọi documents → 401 với request hợp lệ.

`multipart/form-data` chia body thành các phần bằng boundary: file là phần binary,
title/description là các phần text. Browser/Swagger tự tạo boundary và Content-Type;
không gửi JSON body cho endpoint upload. FastAPI dùng UploadFile để spool file thay
vì đọc toàn bộ thành bytes trong endpoint. Tham khảo
[FastAPI Forms and Files](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/).

## Phase 4: Document processing pipeline

```text
Upload
  ↓ (owner gọi POST /documents/{id}/process)
Extract
  ↓
Normalize
  ↓
Chunk
  ↓
PostgreSQL
```

Upload không tự process. Endpoint process chạy đồng bộ trong thread pool và trả
kết quả sau khi xử lý xong; chưa có queue, background worker hoặc scheduler.
Logic nằm trong services; endpoint chỉ làm xác thực, gọi service và trả response.

### Extraction architecture

`extract_text(file_path, file_type)` dispatch theo loại file; đường dẫn được lấy
từ storage key an toàn của document, không nhận path từ client.

| Type | Cách extract | Giới hạn |
| --- | --- | --- |
| TXT | Đọc utf-8-sig để hỗ trợ UTF-8/BOM | Decode lỗi → failed |
| DOCX | python-docx, đọc document.paragraphs theo thứ tự | Chưa lấy tables, headers, footers, textboxes hoặc tracked changes |
| PDF | pypdf, extract_text theo thứ tự page, nối bằng dòng trống | Không OCR; PDF encrypted bị từ chối; reading order/layout có thể không chính xác |

PDF scan thường chỉ chứa ảnh; nếu không có text layer thì parser không có ký tự
để lấy và xử lý sẽ failed. PDF scan có text layer từ OCR trước đó vẫn có thể
extract được. Đây là giới hạn của extraction, không phải lỗi authentication.
Tham khảo [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
và [python-docx paragraphs](https://python-docx.readthedocs.io/en/latest/api/document.html).

Guardrails hiện tại: tối đa khoảng 5 triệu ký tự extracted; DOCX khai báo tổng
dung lượng uncompressed tối đa 50 MiB. Đây không phải giới hạn cứng RAM/CPU của
parser: PDF nén hoặc tài liệu phức tạp vẫn có thể dùng nhiều tài nguyên. Trước
khi xử lý file không tin cậy ở quy mô production cần worker có giới hạn tài
nguyên và timeout; Phase 4 chưa triển khai worker. Không lưu page offsets hoặc
source-span của chunks, nên chưa đủ dữ liệu để tạo citation chính xác theo page.

### Normalization logic

Chuẩn hóa Unicode NFC, newline CRLF/CR/Unicode line separator, bỏ BOM đầu văn bản,
gom khoảng trắng ngang, trim từng dòng và giữ tối đa một dòng trống giữa paragraphs.
Loại NUL vì PostgreSQL TEXT không chứa được ký tự này. Giữ chữ hoa/thường, dấu câu,
Unicode tiếng Việt và số điều/khoản; không tự nối dòng hay sửa từ bị ngắt trong PDF.

Ví dụ `Điều 1.   Phạm vi   điều chỉnh` → `Điều 1. Phạm vi điều chỉnh`.
Normalize trước chunking giúp khoảng trắng dư không tiêu tốn chunk budget và
giúp boundary/char_count ổn định. Không coi normalization là sửa lỗi ngữ nghĩa.

### Chunking strategy và config

| Biến | Mặc định | Validation |
| --- | --- | --- |
| CHUNK_SIZE | 1200 ký tự | 100–20000 |
| CHUNK_OVERLAP | 200 ký tự | 0 <= overlap < size |

Service chọn điểm kết thúc tại paragraph boundary cuối cùng trong chunk budget,
gom nhiều paragraph nếu vừa. Với paragraph dài, ưu tiên newline, rồi khoảng trắng;
chỉ hard-split nếu không có boundary phù hợp. Chunk tiếp theo bắt đầu trước cuối
chunk trước một khoảng overlap. Mỗi vòng phải tiến vào text mới, không lặp vô hạn.
Trim whitespace có thể làm overlap hiển thị ngắn hơn cấu hình một chút.

Paragraph boundaries giúp giữ các câu liên quan cùng nhau tốt hơn cắt mù theo
ký tự. Overlap giữ một phần ngữ cảnh quanh ranh giới cho retrieval ở phase sau;
đổi lại làm tăng lượng text lưu và tính toán. Overlap gần bằng size tạo rất nhiều
chunks, nên giữ mặc định hoặc tỷ lệ nhỏ. Không đảm bảo toàn bộ Điều/Khoản nằm
trọn trong một chunk, nhất là paragraph quá dài.

Chunks không rỗng, chunk_index bắt đầu từ 0, liên tục; chunk cuối luôn được giữ.
`char_count = len(content)` tính Unicode code points, không phải byte UTF-8.
`token_estimate = ceil(char_count / 4)` chỉ là heuristic, có thể lệch đáng kể với
tiếng Việt và từng tokenizer; chunking vẫn dựa trên ký tự, không phải model tokens.

### Database design

`documents` thêm `processing_error VARCHAR(500) NULL`.
`document_chunks` gồm UUID id/document_id, chunk_index, content TEXT, char_count,
token_estimate và created_at có timezone. Unique `(document_id, chunk_index)`
đồng thời tạo index hỗ trợ truy vấn theo document và thứ tự chunk; không cần
thêm index trùng lặp. CHECK constraints yêu cầu index không âm, counts dương.
FK `ON DELETE CASCADE` xóa chunks khi document bị xóa.

Lưu chunks trong database giúp đọc lại mà không phải parse file mỗi request,
giữ thứ tự rõ ràng và chuẩn bị dữ liệu cho phase sau. Đây là bảng quan hệ bình
thường, không phải vector database. Migration không thay đổi hoặc xóa migration cũ.

### Processing transaction và status flow

```text
uploaded / processed / failed
              ↓
          processing
           ↙      ↘
     processed    failed
```

1. Lấy document theo id + owner_id, khóa row PostgreSQL. Nếu đang processing → 409.
2. Ghi processing, xóa processing_error cũ và commit để request khác nhìn thấy trạng thái.
3. Extract → normalize → kiểm tra text không rỗng → chunk, không giữ row lock lâu khi parse.
4. Transaction tiếp theo khóa document, DELETE chunks cũ, INSERT toàn bộ chunks mới,
   chuyển processed và commit một lần.
5. Nếu bước 3/4 lỗi: rollback transaction thay chunks, ghi failed + lỗi an toàn
   trong transaction riêng. Không để bộ chunks chỉ được insert một phần.

Reprocess thành công thay toàn bộ chunks cũ, không append hoặc duplicate.
Nếu reprocess thất bại, bộ chunks hoàn chỉnh từ lần trước được giữ lại; GET chunks
trả status failed để client biết đó không phải kết quả của lần xử lý mới nhất.
Lần xử lý đầu thất bại không có chunks. Status thể hiện trạng thái xử lý dữ liệu,
không phải trạng thái upload HTTP hoặc task queue.

DELETE document bị chặn 409 khi processing, tránh xóa file trong lúc parser đọc.
Process đồng thời cũng trả 409 sau khi thấy claim của request trước. File nguyên
gốc được giữ nguyên. Nếu process crash sau claim, trạng thái có thể kẹt processing;
chưa có tự động timeout/recovery. Operator cần xác nhận không còn request đang
chạy trước khi reset về failed bằng thao tác quản trị có kiểm soát. Không reset
chỉ vì request client timeout, vì server có thể vẫn đang xử lý.

Nếu database mất kết nối, việc ghi failed cũng có thể thất bại; API trả 503 nhưng
không đảm bảo status đã được lưu. Không thể bảo đảm transaction thành công khi
database không khả dụng hoặc mất acknowledgment của commit.

### Processing endpoints và Swagger

| Endpoint | Response |
| --- | --- |
| POST /documents/{document_id}/process | 200: document_id, status=processed, chunk_count, message |
| GET /documents/{document_id}/chunks?skip=0&limit=20 | 200: document_id, status, items, total, skip, limit |

Hai endpoint yêu cầu Bearer token và chỉ owner truy cập; thiếu token → 401,
không tồn tại/khác owner → 404. Chunks sắp theo chunk_index tăng dần; pagination
giống document list. Mỗi item gồm id, chunk_index, content, char_count,
token_estimate, created_at; không có file path. Chưa process thì items rỗng.
Count và list là hai query ở isolation mặc định; reprocess đồng thời có thể làm
thay đổi kết quả giữa hai query/trang.

Test trong Swagger:

1. Rebuild backend, chạy upgrade head; login và Authorize ở `/docs`.
2. Upload TXT có nội dung pháp luật hoặc PDF/DOCX thật, copy document id.
3. Gọi POST process (không có body), kiểm tra status processed/chunk_count.
4. Gọi GET chunks để xem thứ tự/content/counts, thử skip/limit.
5. Gọi process lần nữa; chunks được thay thế, không cộng dồn.
6. Upload PDF không có text, process → 422; GET document thấy failed và processing_error.
7. Dùng token user B process/get chunks của A → 404; bỏ token → 401.

Lỗi trả JSON `detail` an toàn: 409 file đã mất hoặc đang processing; 415 loại
không hỗ trợ; 422 file không parse được/không có text/UTF-8 sai; 503 storage hoặc
database không khả dụng; 500 lỗi processing bất ngờ. Status failed được lưu khi
có thể ghi database; không lưu hoặc trả exception text/traceback của parser.

Các file giả chỉ có `%PDF-` hay ZIP tối giản trong test upload Phase 3 không phải
tài liệu hợp lệ để test extraction. Test Phase 4 tạo DOCX thật và PDF có text bằng
thư viện, cùng PDF blank để kiểm tra nhánh không có extractable text.

## Kiểm tra và migration

```powershell
.\.venv\Scripts\python.exe -m compileall -q app alembic
.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
docker compose config --quiet
```

Import và offline migration không chứng minh đã kết nối PostgreSQL. Cần chạy
stack, online migration và kiểm tra HTTP để xác nhận tích hợp thực tế.

Test mặc định dùng SQLite tạm, chạy migration thật để tạo schema, không dùng
`create_all()`. Mỗi test rollback transaction; lifespan và dependency vẫn được
test qua FastAPI TestClient. SQLite chỉ kiểm tra logic và một phần migration,
không xác nhận đầy đủ hành vi PostgreSQL, timezone hoặc SQLSTATE unique violation.
Test nhánh concurrent duplicate chỉ chạy với PostgreSQL.
Test migration cũng chạy downgrade/upgrade trong transaction riêng và dùng
`alembic check` để phát hiện model/schema lệch nhau.

Chạy toàn bộ test bằng **Python 3.12 + PostgreSQL riêng**, không đụng volume của app:

```powershell
docker compose -p legal-ai-auth-tests -f docker-compose.test.yml config --quiet
docker compose -p legal-ai-auth-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-auth-tests -f docker-compose.test.yml down
```

Test stack dùng DB `legal_ai_test` trong tmpfs, không publish cổng. Image test có
pytest/HTTPX; image production không cài test dependency. Test tạo schema riêng,
chạy `alembic upgrade head`, kiểm tra flow rồi xóa schema đó. Ngoài Docker có thể
đặt `TEST_DATABASE_URL` trỏ tới PostgreSQL test đã tạo; database name bắt buộc kết
thúc bằng `_test`. Không trỏ test vào database chứa dữ liệu cần giữ.

Các flow test: register, duplicate email (cả khác hoa/thường), password hash,
login đúng/sai, `/me` có/không có token, token hết hạn/sai chữ ký/claim, user inactive,
validation không echo password, migration/index và Swagger/OpenAPI contract.
Phase 3 thêm upload PDF/DOCX/TXT, giới hạn kích thước/request stream, file rỗng,
MIME/type sai, path traversal, owner isolation, pagination, delete/missing file,
rollback khi DB lỗi và Swagger multipart. Test dùng storage tạm riêng từng test,
không ghi file vào storage của ứng dụng. Migration test kiểm tra cả dữ liệu User
cũ được giữ sau upgrade Phase 3. SQLite bật foreign keys để test quan hệ.

Test Phase 4 thêm extraction TXT/BOM, DOCX paragraphs, PDF pages/no-text,
normalization Unicode/newlines, paragraph chunks/overlap/index/last chunk,
process/reprocess, rollback khi insert dở, failed status, ownership, cascade,
claim conflict và OpenAPI của endpoints mới.

Chạy riêng Phase 4 sau khi cài requirements-dev:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_text_processing.py tests/test_document_processing.py tests/test_migrations.py -q
```

Chạy toàn bộ regression trên PostgreSQL test riêng:

```powershell
docker compose -p legal-ai-phase4-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-phase4-tests -f docker-compose.test.yml down
```

Khi thêm model: kế thừa Base, export model trong `app/models/__init__.py`, chạy
`alembic revision --autogenerate -m "describe change"`, review migration rồi mới
`alembic upgrade head`. Chạy tạo revision local để file nằm trong repository.

Alembic lưu lịch sử schema trong source control và database, giúp các môi trường
cùng có schema tương ứng với code. Review script trước khi chạy; autogenerate
không hiểu mọi ý định thay đổi dữ liệu. Migration không tự chạy khi API startup.

### Lịch sử kiểm chứng khi triển khai Phase 4

- Đã kiểm tra bằng Python 3.13/thư viện có sẵn: TXT UTF-8/BOM, normalization,
  chunking với nhiều tổ hợp size/overlap, paragraph/word boundaries, chunk index,
  chunk cuối và overlap. Đã kiểm tra cú pháp tương thích Python 3.12.
- Đã chạy pipeline service thật trên SQLite tạm: process, reprocess thay chunks,
  rollback sau khi insert một phần, failed status an toàn, giữ chunks cũ nguyên
  vẹn, ownership 404, processing conflict 409 và cascade khi xóa document.
  Schema smoke test tạo từ model DDL, không xác nhận migration Alembic.
- Cả Compose app và test đạt `config --quiet` (exit 0), dù có cảnh báo quyền đọc
  Docker config cá nhân. Không đồng nghĩa Docker build/start đã thành công.
- Venv hiện thiếu dependency; pypdf/python-docx cũng chưa có trong Python global.
  Sandbox không truy cập Docker daemon. Quyền tải dependency và chạy Docker test
  đã bị từ chối. Chưa chạy extraction PDF/DOCX thật, pytest đầy đủ, migration
  PostgreSQL, image Python 3.12 hoặc Swagger toàn ứng dụng Phase 4.
- Phase 1–3 đã được người dùng xác nhận test thực tế. Test regression được giữ và
  cập nhật head migration; chưa chạy lại toàn bộ trong phiên này. `.env` vẫn được
  Git ignore và không commit.

## Security notes

- Chạy HTTPS khi deploy; ai có Bearer token có thể sử dụng nó đến khi hết hạn.
- Không log request body đăng nhập/đăng ký, password, SECRET_KEY hay Authorization.
- Access token mặc định 30 phút; chưa có refresh/revoke/logout server. Hết hạn cần
  login lại. Đổi SECRET_KEY làm các token đã phát mất hiệu lực; cần kế hoạch rotation.
- Login trả lỗi chung, nhưng register trả 409 nên có thể tiết lộ email đã đăng ký;
  đây là đánh đổi theo yêu cầu UX hiện tại.
- Chưa có rate limiting/chống brute force và giới hạn request body ở gateway;
  cần bổ sung trước khi public production, nhất là vì Argon2 tiêu tốn tài nguyên.
- DB user trong Compose là development bootstrap user; production nên tách quyền
  migration và quyền runtime tối thiểu. Không dùng password development ở production.

## Phase 5: Local embeddings và semantic search

### Kiến trúc và files

```text
Document -> DocumentChunk -> EmbeddingService (CPU, passage prefix)
                                  -> chunk_embeddings VECTOR(384) -> pgvector
Query -> cùng EmbeddingService (query prefix) -> cosine search
          -> lọc owner + processed + indexed + model -> top K chunks
```

Lọc ownership nằm trong SQL trước ranking/limit, không lấy kết quả toàn hệ thống
rồi lọc bằng Python. Đây là semantic retrieval, chưa tạo câu trả lời bằng LLM.

```text
app/core/embedding_config.py       # model/dimension chuẩn của application
app/services/embeddings.py         # lazy model, batch, validate vectors
app/services/document_indexing.py  # lifecycle + atomic replacement
app/services/semantic_search.py    # ownership + cosine SQL
app/models/chunk_embedding.py      # bảng vector tách khỏi raw text
app/schemas/search.py              # request/result/index schemas
app/api/search.py                  # POST /search
app/api/documents.py               # thêm POST /documents/{id}/index
alembic/versions/0004_vector_embeddings.py
tests/test_embeddings.py
tests/test_semantic_search.py
```

`Depends(get_embedding_service)` cung cấp backend dùng chung và cho phép test
thay bằng fake service. Constructor không tải model; `load_model()` chạy lần đầu
cần inference, kiểm tra dimension thực tế rồi giữ model trong RAM. Lock ngăn hai
request cùng load và giới hạn một lần encode tại một thời điểm trong mỗi process.
Alembic/import application không tải weights. Log ghi model/dimension, bắt đầu,
số chunks, hoàn thành hoặc loại lỗi; không ghi password, JWT hay vectors.

### Model và cấu hình

Chọn **intfloat/multilingual-e5-small**, output **384 chiều**, hỗ trợ multilingual
bao gồm tiếng Việt và English. Dùng `passage: ` cho chunks, `query: ` cho query,
kể cả tiếng Việt, và `normalize_embeddings=True` theo
[model card chính thức](https://huggingface.co/intfloat/multilingual-e5-small).
Đây là model retrieval tổng quát, chưa được đánh giá chuyên biệt trên bộ luật của bạn.

```dotenv
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=16
HF_HOME=.cache/huggingface
```

Thêm các key còn thiếu vào `.env` hiện có; không chép đè secret/database settings.
Settings Phase 5 chỉ chấp nhận model và dimension này để tránh trộn không gian
vector. Dimension dùng chung từ `embedding_config.py`; migration giữ số 384 cố
định vì là snapshot lịch sử. Đổi model cần cập nhật code, re-index toàn bộ; nếu đổi
dimension cần migration mới. Hai model cùng dimension vẫn không tương thích.
Hiện lưu `model_name`, chưa pin Hugging Face revision; khi thay weights/revision
cần kiểm soát phiên bản và re-index, không trộn weights cũ/mới.

### Database và trạng thái

`chunk_embeddings`: UUID `id`, unique `chunk_id` FK cascade về `document_chunks`,
`embedding VECTOR(384)`, `model_name`, `created_at` có timezone. Unique chunk_id
đảm bảo mỗi chunk có một embedding active. Tách bảng giúp raw text và vector có
lifecycle rõ ràng; chưa cần lưu nhiều phiên bản model cùng lúc.

Document có `embedding_status`, `embedding_error`, `embedded_at`. Processing
status mô tả extract/chunk; embedding status mô tả khả năng retrieval, vì hai bước
có thể thành công/thất bại độc lập.

1. Upload/process tạo trạng thái `pending`.
2. `/index` kiểm tra owner, document `processed`, có chunks; lock và commit `indexing`.
3. Lấy chunks theo chunk_index; một encode call với batch size cấu hình.
4. Validate số vectors, chiều, giá trị hữu hạn và norm khác zero.
5. Trong một transaction: xóa embeddings cũ, insert toàn bộ mới, chuyển `indexed`, cập nhật embedded_at.
6. Nếu lỗi: rollback toàn bộ replacement, chuyển `failed`, lưu lỗi an toàn và trả 503.

Re-index không nhân bản rows. Nếu thất bại, bộ vectors cũ còn nguyên nhưng không
được search vì status là failed. `embedded_at` vẫn là lần index thành công trước.
Khi bắt đầu reprocess, reset pending/error/timestamp để không dùng vectors stale;
khi thay chunks thành công, FK cascade xóa embeddings cũ. Nếu reprocess thất bại,
chunks/vectors cũ giữ nguyên nhưng không searchable. Trong lúc indexing, các API
index/process/delete cùng document trả 409 để tránh thay chunks giữa chừng.

### API và score

`POST /documents/{document_id}/index` yêu cầu Bearer token, trả:

```json
{"document_id":"<UUID>","embedding_status":"indexed","embedded_chunks":8,"model_name":"intfloat/multilingual-e5-small"}
```

`POST /search` yêu cầu Bearer token:

```json
{"query":"Quyền của người sử dụng dữ liệu là gì?","top_k":5,"document_ids":null}
```

Query trim rồi validate 1–1000 ký tự; top_k mặc định 5, giới hạn 1–20.
document_ids null/không truyền: tất cả tài liệu hợp lệ của current user. List phải
có 1–100 UUID, duplicate được loại; `[]` trả 422. Nếu bất kỳ ID nào không tồn tại
hoặc thuộc user khác, trả 404 trước khi embed query. Không tiết lộ ID nào là của
user khác. Chỉ search tài liệu processed + indexed và đúng model_name.

Response gồm `model_name`, `results`; mỗi result có document_id, document_title,
chunk_id, chunk_index, content, score. Empty library trả results rỗng mà không load
model. SQL dùng toán tử cosine `<=>` của pgvector: `score = 1 - distance`, sắp xếp
score giảm dần, hòa điểm theo document_id/chunk_index. Score thuộc [-1, 1], càng cao
càng tương đồng; không phải xác suất, phần trăm chính xác hay kết luận pháp lý.
Không có threshold relevance: top K vẫn có thể chứa đoạn không liên quan.

Exact search chưa có HNSW/IVFFlat: đơn giản, không có recall trade-off do ANN,
phù hợp dataset portfolio nhỏ. Tham khảo [pgvector](https://github.com/pgvector/pgvector)
và [SQLAlchemy integration](https://github.com/pgvector/pgvector-python).

### Docker, backup và migration giữ dữ liệu hiện tại

Đổi image từ PostgreSQL 16 bookworm sang `pgvector/pgvector:pg16-bookworm`, giữ
service, major version, volume `postgres_data`, data directory và Compose project
hiện có. Không đổi project name khi nâng cấp app; không chạy `down -v`.
Image mới cung cấp extension binaries; migration mới bật extension và tạo schema.
Các migration 0001–0003 giữ nguyên; không dùng create_all.

Backup **trước khi thay container PostgreSQL đang chạy**. Ví dụ development user
`legal_ai_dev`; thay nếu `.env` của bạn khác. Dump bên trong container để tránh
PowerShell làm hỏng binary dump qua output redirection:

```powershell
New-Item -ItemType Directory -Force backups
docker compose exec postgres pg_dump -U legal_ai_dev -d legal_ai -Fc -f /tmp/legal_ai_before_phase5.dump
docker compose cp postgres:/tmp/legal_ai_before_phase5.dump ./backups/legal_ai_before_phase5.dump
docker compose config --quiet
docker compose pull postgres
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Head mong đợi `0005_conversations_and_messages`; users/documents/chunks hiện có được giữ,
embedding_status ban đầu pending. Backup chưa đủ: khi vận hành cần kiểm tra restore
trên database riêng. Không downgrade migration này để thử trên dữ liệu cần giữ vì
downgrade xóa bảng embeddings. Extension public được giữ khi downgrade vì có thể dùng chung.

Backend chạy non-root, `model_cache` mount tại `/app/.cache/huggingface`. Rebuild
container giữ weights trên volume; restart process vẫn phải load weights vào RAM.
Public model được tải với `token=False`, không cần Hugging Face token. Git/Docker
ignore `.cache/` và `backups/`; không đưa weights hoặc `.env` vào Git/image.

Dockerfile cài PyTorch từ CPU wheel index trước requirements để không yêu cầu CUDA.
Build cần mạng tải dependencies; lần index đầu cần mạng tải model, có thể khá lâu.
Local Python 3.12, sau khi activate venv và cấu hình DATABASE_URL localhost:

```powershell
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.6,<3.0"
python -m pip install -r requirements-dev.txt
docker compose up -d postgres
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

### Manual test model thật trong Swagger

1. Mở `http://localhost:8000/docs`, register/login và Authorize bằng access_token.
2. Upload TXT A chứa: “Người sử dụng có quyền truy cập dữ liệu trong phạm vi được cấp quyền.”
3. Upload TXT B chứa: “Doanh nghiệp kê khai và nộp thuế theo thời hạn quy định.”
4. Gọi `/documents/{id}/process` cho cả hai; kiểm tra chunks.
5. Gọi `/documents/{id}/index` cho cả hai; chờ tải model lần đầu, kiểm tra indexed/count.
6. POST /search: query “Người dùng được phép làm gì với dữ liệu?”, top_k 2.
   Kỳ vọng đoạn A đứng trên B dù khác từ; tự quan sát score và nội dung, đây chưa
   phải kết quả benchmark đã được xác nhận trong phiên triển khai.
7. Thử query tiếng Anh “What access rights does a data user have?” và filter document_ids.
8. Index lại A: số rows không tăng; process lại A: pending, không được search tới khi index lại.
9. Login user khác: không thấy A/B; truyền ID A trả 404. Xóa token: 401.

### Automated tests và mức kiểm chứng

```powershell
python -m pytest -q
python -m pytest -q tests/test_embeddings.py tests/test_semantic_search.py tests/test_migrations.py
docker compose -p legal-ai-phase5-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-phase5-tests -f docker-compose.test.yml down
```

Default dùng SQLite JSON + hàm cosine **chỉ trong test**, không thay thế pgvector
production. Test Docker dùng PostgreSQL/pgvector riêng, tmpfs, không mount volume
app. TEST_DATABASE_URL chỉ chấp nhận database kết thúc `_test`, tạo schema riêng;
search_path gồm schema đó và public cho vector extension. Cùng suite kiểm tra SQL
cosine thật khi chạy PostgreSQL. Cả hai chế độ fake embeddings và chặn model download.

Coverage đã viết: lazy loading, prefix/normalization/batching, dimension, processed
index, re-index không duplicate, rollback partial replacement, reprocess invalidation,
cascade, ownership, 401/404/409, top K/filter/status/model và query validation;
migration preservation và extension/vector dimension trên PostgreSQL; OpenAPI routes.

**Kiểm chứng phiên Phase 5:** kiểm tra cú pháp và Compose config thành công; smoke
offline bằng Python global kiểm tra Settings/import các module embedding/schema,
fake encoder load một lần, prefixes, normalization option và validation thành công.
Chưa xác nhận toàn bộ app imports, pytest, Docker build/start, migration PostgreSQL,
Swagger runtime hoặc chất lượng model thật: môi trường thiếu dependencies và quyền
cài dependency/chạy Docker test đã bị từ chối. Không coi các test đã viết là đã pass.
Phase 1–4 được người dùng xác nhận chạy thực tế trước phiên này.

### Khái niệm phỏng vấn và performance

- Embedding là dãy số biểu diễn đặc trưng ngữ nghĩa học được. Dimension là số phần
  tử của vector, không phải số từ. Cùng model cho query/document giữ cùng hệ tọa độ.
- Keyword search dựa trên từ trùng; semantic search so sánh biểu diễn đã học nên
  có thể tìm paraphrase. Khả năng này phụ thuộc model/dữ liệu, không bảo đảm đúng.
- Cosine similarity là dot product chia tích độ dài hai vectors: đo hướng thay vì
  độ lớn. Normalize đưa norm về 1; PostgreSQL TEXT thông thường không cung cấp kiểu
  vector/toán tử khoảng cách, extension bổ sung chúng ngay cạnh metadata/FK/transactions.
- Batch tận dụng tính toán ma trận, giảm overhead gọi model. Batch 16 chỉ giới hạn
  inference batch; hiện service vẫn giữ texts/vectors cả document trong RAM.
- Load mỗi request lãng phí thời gian/RAM. Singleton là mỗi process, nhiều Uvicorn
  workers vẫn nhân số bản model; bắt đầu với một worker, giảm batch nếu thiếu RAM.
- Indexing đồng bộ có thể chạm timeout HTTP khi tải model hoặc tài liệu lớn. Chưa
  có queue/job recovery. Exact search chi phí tăng theo số vectors đủ điều kiện.
- Model cắt input quá 512 tokens theo [model card](https://huggingface.co/intfloat/multilingual-e5-small); chunk size theo ký tự không đảm bảo nằm
  trong giới hạn này, nhất là tiếng Việt. Đánh giá chất lượng và điều chỉnh chunk
  size với dữ liệu thực; token-aware chunking là cải tiến sau, chưa triển khai.

### Troubleshooting Phase 5

| Hiện tượng | Kiểm tra/cách xử lý |
| --- | --- |
| vector extension unavailable | Container đang chạy đúng pgvector image; recreate PostgreSQL cùng volume rồi upgrade head |
| permission denied CREATE EXTENSION | Dùng migration account có quyền cài extension; runtime account không cần quyền đó |
| Dimension/config mismatch | Giữ E5-small/384; đổi model có kế hoạch schema + re-index, không chỉ sửa env |
| Index 409 | Process thành công trước; kiểm tra document có chunks hoặc đang indexing |
| Index/search 503 | Kiểm tra dependency, kết nối HF lần đầu, cache permissions, RAM và database; lỗi trả về được làm sạch |
| Model tải lại sau rebuild | Kiểm tra đúng Compose project, model_cache volume và HF_HOME; không xóa volume |
| Status indexing bị kẹt sau crash | Xác nhận process indexing cũ đã chết; quản trị reset failed rồi retry. Chưa có automatic recovery; không reset khi job còn chạy |
| Search rỗng | Kiểm tra owner, processed/indexed, model_name, document_ids; process xong chưa tự index |
| Search chất lượng thấp | Kiểm tra text extraction/chunks, truncation, cùng model/prefix và dữ liệu test; score không phải confidence |
| CPU/RAM quá tải | Một worker, giảm EMBEDDING_BATCH_SIZE; document lớn cần thiết kế background jobs sau |

## Phase 6: Single-turn grounded RAG

```text
Upload -> Extract -> Chunk -> Embed -> pgvector
Question -> Retrieve (Phase 5, ownership filters)
         -> similarity threshold -> Context Builder (numbered sources, char budget)
         -> LLM Provider -> validate answer/citation numbers -> Answer + Citations
```

Riêng Phase 6 không thêm schema database; tại thời điểm đó migration head là `0004_vector_embeddings`.
Không thay logic `/search`. RAG gọi trực tiếp `search_documents()` để kế thừa owner,
processed/indexed/model filters, top K và kiểm tra tất cả document_ids thuộc owner.
Không lưu hội thoại, không có streaming/tools/agents/reranker/hybrid search.

### Files và provider abstraction

```text
app/api/rag.py                  # authenticated POST /rag/ask
app/schemas/rag.py              # request, citation, response
app/services/rag.py             # orchestration, threshold, grounding checks
app/services/rag_context.py     # numbered sources and char budget
app/services/rag_prompt.py      # fixed system instructions
app/services/llm.py             # LLMProvider Protocol + OpenAI-compatible adapter
tests/test_rag.py               # API/retrieval tests with FakeLLMProvider
tests/test_llm_context.py       # offline HTTP mock and context unit tests
```

Endpoint không gọi provider API trực tiếp. `LLMProvider.generate_answer()` nhận
system prompt/question/context và trả text. Dependency injection cho phép thay
provider hoặc fake trong tests. Adapter HTTPX dùng Chat Completions JSON để không
phụ thuộc SDK riêng một vendor. Không gọi provider khi import app hoặc Alembic.

Adapter hiện gửi `messages`, `temperature`, `max_tokens` tới `/chat/completions`.
Chọn model hỗ trợ các tham số này; không phải mọi model OpenAI-compatible đều hỗ trợ
giống nhau. Ví dụ model reasoning có thể yêu cầu tham số khác. `max_tokens` là giao
diện tương thích cũ; muốn dùng model yêu cầu `max_completion_tokens` cần adapter phù
hợp, không tự retry bằng model khác. Tham khảo
[Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create).
Không chọn model mặc định để tránh phát sinh chi phí ngoài ý muốn.

### Environment variables

Thêm vào `.env` hiện có, giữ nguyên database/auth/embedding settings:

```dotenv
LLM_PROVIDER=openai-compatible
LLM_MODEL=
LLM_API_KEY=
LLM_BASE_URL=
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=800
LLM_TIMEOUT_SECONDS=60
RAG_MIN_SIMILARITY=0.45
RAG_MAX_CONTEXT_CHARS=12000
```

LLM_MODEL là ID model chính xác từ provider; chọn model chat nhỏ hỗ trợ temperature
và max_tokens, kiểm tra giá/quota tại provider trước manual test. API key là SecretStr,
không hard-code, không đưa vào prompt/logs/response. `.env` không commit.

| Provider thực tế | LLM_PROVIDER | LLM_BASE_URL | LLM_MODEL / key |
| --- | --- | --- | --- |
| OpenAI | openai-compatible | để trống, mặc định https://api.openai.com/v1 | model chat phù hợp và key của bạn |
| OpenRouter | openai-compatible | https://openrouter.ai/api/v1 | ID model và key của OpenRouter |
| Local server | openai-compatible | http://localhost:PORT/v1 | model đang serve; key local hoặc giá trị dummy nếu server bỏ qua auth |

Endpoint OpenRouter theo [tài liệu quickstart](https://openrouter.ai/docs/quickstart).

Trong Docker Desktop, server chạy trên Windows host dùng
`http://host.docker.internal:PORT/v1`. Không dùng localhost container để gọi host.
URL phải là API root, không thêm `/chat/completions`. Adapter không follow redirects;
HTTP chỉ cho localhost/loopback/host.docker.internal, hosted provider cần HTTPS.
Tự cấu hình endpoint tin cậy: các chunks được chọn và question sẽ được gửi tới nó.
Không gửi internal paths, stored filename, owner ID hay full vectors.

Thiếu key/model hoặc provider unsupported **không chặn startup**. Khi cần generation,
trả 503 với lỗi cấu hình rõ. Nếu không có context phù hợp, vẫn trả no-context 200 và
không kiểm tra key/gọi provider. Đây là ưu tiên no-context để tiết kiệm chi phí.

### Request, context và citations

```json
{"question":"Người sử dụng có quyền gì đối với dữ liệu?","document_ids":null,"top_k":5}
```

Question trim, 1–1000 ký tự; top_k 1–10, mặc định 5. document_ids giống `/search`:
null là tất cả owned indexed documents; list 1–100 UUID, deduplicate; foreign/missing
ID trả 404, [] trả 422. Tài liệu owned nhưng chưa indexed không đưa vào context.

Context builder sắp xếp score cao trước, bỏ duplicate chunk_id, giữ nguyên chunks
và đánh SOURCE 1, SOURCE 2 liên tục. Budget tính cả header và JSON-escaped content.
Chunk không vừa budget được bỏ qua để thử chunk nhỏ hơn; không cắt ngang câu/điều
luật. Nếu không chunk nào vừa, xử lý như no-context. Excerpt response tối đa 500 ký
tự; context chứa toàn bộ chunk được chọn. Metadata citation luôn lấy từ backend.

Response gồm answer, grounded, citations, model, retrieved_chunks, used_chunks.
`retrieved_chunks` là số top K trước threshold; `used_chunks` là số chunks đã gửi
trong context, không phải số citation được model sử dụng. `model=null` khi không
gọi LLM, còn lại là model cấu hình. Mỗi citation có citation_number, document_id,
document_title, chunk_id, chunk_index, score, excerpt. Chỉ trả nguồn model thực sự
viện dẫn; nếu model chỉ dùng [2], citations chỉ chứa citation_number 2.

### Prompt và grounding policy

System prompt cố định yêu cầu chỉ dựa context, không bịa điều luật/số điều, giữ sự
khác biệt giữa nguồn, trả lời theo ngôn ngữ câu hỏi, dùng [1], [2] hợp lệ và thừa
nhận thiếu thông tin. Question/context nằm trong user messages, không chèn vào system.
Tài liệu được coi là dữ liệu không tin cậy: không làm theo hướng dẫn trong tài liệu.
JSON escaping giúp phân biệt cấu trúc nguồn; đây không phải hàng rào bảo mật tuyệt đối.

| Trường hợp | Hành vi |
| --- | --- |
| Không nguồn vượt threshold/không vừa budget | Không gọi LLM, message tiếng Việt cố định, grounded false, citations [] |
| Answer rỗng/malformed/bị cắt do token limit | 503, không trả partial answer |
| Answer chứa [99] hoặc dạng numeric citation không hỗ trợ như [1, 99] | Bỏ answer, trả message thiếu thông tin, grounded false, citations [] |
| Answer có nguồn hợp lệ | Map metadata backend, grounded true nếu có ít nhất một citation |
| Answer không có citation, kể cả lời từ chối | Giữ text nhưng grounded false, citations [] |

`grounded=true` **chỉ là structural grounding**, không xác minh từng khẳng định có
được nguồn hỗ trợ. LLM vẫn có thể đưa nội dung sai kèm [1] hợp lệ. Không có factual
verifier, entailment check hoặc đảm bảo legal correctness. Client cần hiển thị trạng
thái này và cho người dùng đọc nguồn. Citation trỏ nguồn thật không chứng minh câu
trả lời suy luận đúng.

### Cost, errors và logs

Threshold mặc định 0.45 là điểm bắt đầu cần hiệu chỉnh trên câu hỏi/tài liệu thật,
không phải confidence và không đảm bảo relevance. E5 scores có thể tập trung cao;
ngưỡng quá thấp vẫn gửi nguồn yếu, quá cao bỏ sót nguồn hữu ích.

Temperature 0.1 giảm biến thiên nhưng không ngăn hallucination. Max tokens 800 giới
hạn output; context budget 12000 ký tự không phải token count/context window chính
xác. Cần chừa chỗ cho system prompt, question và output theo model chọn. Không tự
retry sau timeout/rate limit vì request trước có thể đã tiêu token.

Thiếu cấu hình, provider auth failure, 429, network/timeout, response malformed đều
trả 503 với thông báo an toàn; invalid input 422; thiếu JWT 401. Không trả provider
body/traceback. Timeout HTTPX áp dụng theo các thao tác mạng, không phải hard deadline
toàn request. LLM_MAX_TOKENS không thay thế rate limit theo user; chưa có quota server.
Log có request start, retrieved/used counts, provider/model lúc gọi, duration,
success/failure và loại lỗi. Không log question, context, JWT, password hay key.

### Chạy và test bằng Swagger

1. Điền LLM_MODEL, LLM_API_KEY và LLM_BASE_URL nếu dùng provider khác.
2. Rebuild/recreate để Compose nhận env mới (restart đơn thuần không cập nhật env):

```powershell
docker compose config --quiet
docker compose up --build -d backend
```

3. Mở http://localhost:8000/docs, login và Authorize.
4. Upload TXT: “Người sử dụng có quyền truy cập dữ liệu trong phạm vi được cấp quyền.”
5. Gọi process rồi index; có thể dùng tài liệu Phase 5 đã indexed.
6. POST /rag/ask với question “Người dùng được phép làm gì với dữ liệu?”.
7. Kỳ vọng answer dựa trên đoạn đó, có [1] và citation đúng chunk. Đây là manual
   check cần chạy với provider thật, chưa có kết quả thực tế trong phiên triển khai.
8. Thử user chưa có tài liệu: no-context, không gọi LLM. Thử foreign document_ids:404.
9. Bỏ key và recreate backend: health vẫn hoạt động; ask có relevant context trả503.

Provider thật có thể tính phí. Chỉ gửi tài liệu bạn cho phép provider đó xử lý.
Không cần migration mới; không xóa database/model volumes khi triển khai Phase 6.

### Automated tests và trạng thái kiểm chứng

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pytest -q tests/test_rag.py tests/test_llm_context.py
docker compose -p legal-ai-phase6-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-phase6-tests -f docker-compose.test.yml down
```

Tests dùng FakeLLMProvider hoặc HTTPX MockTransport, không gọi API thật. Env LLM trong
tests được ghi đè để không dùng key từ `.env`. Default SQLite tests và PostgreSQL
test stack giữ cơ chế isolation Phase 5. API tests kiểm tra auth/validation, ownership,
threshold/no-call, citations, invalid refs, timeout, config và search regression.

Có thể chạy riêng pure unit tests khi đã có HTTPX/Pydantic, không cần model/DB:

```powershell
python -m unittest discover -s tests -p test_llm_context.py -v
```

Phiên triển khai Phase 6: 6 pure unit tests đã pass, compileall và Compose config
đạt. Chưa chạy pytest suite/API runtime/PostgreSQL integration hoặc gọi provider
thật: Python/venv thiếu pytest và một số dependency; các lần cấp quyền cài đặt/chạy
Docker trước đã bị từ chối. Phase 1–5 được người dùng xác nhận chạy thực tế.

### Khái niệm phỏng vấn

- RAG kết hợp retrieval và generation: tìm nguồn riêng trước, rồi cho LLM diễn đạt
  dựa trên nguồn; không cần huấn luyện lại model khi thêm tài liệu.
- Retrieval chọn bằng chứng; generation tạo ngôn ngữ. Retrieval sai/thiếu khiến câu
  trả lời khó đúng dù model mạnh, nên cần đánh giá hai bước riêng.
- Hallucination là thông tin model tạo ra không có căn cứ hoặc sai. Grounding yêu
  cầu bám nguồn; prompt, threshold và citations giúp giảm rủi ro, không triệt tiêu.
- Backend kiểm soát citation metadata vì LLM có thể bịa UUID/tên nguồn. Model chỉ
  chọn số nguồn đã được đánh sẵn, backend kiểm tra trước khi trả metadata.
- Context window là khả năng input/output của model theo tokens; char budget là
  giới hạn đơn giản để kiểm soát độ dài/cost, chưa phải tokenizer chính xác.
- Prompt injection là tài liệu chứa chỉ dẫn như “bỏ qua system prompt”. Phân tách
  vai trò và coi context là dữ liệu là phòng vệ cơ bản, không đảm bảo tuyệt đối.
- Provider abstraction tách nghiệp vụ RAG khỏi HTTP/vendor, dễ fake test và đổi
  provider mà không sửa ownership/retrieval/context builder.

## Phase 7: Conversation and chat history

Phase 7 adds authenticated conversations, persisted user/assistant messages, saved citations, and stateful multi-turn RAG. It reuses the Phase 6 retrieval/context/grounding flow instead of embedding the whole conversation.

```text
POST /conversations -> create an empty conversation
POST /conversations/{id}/messages
  -> Transaction A: validate owner + documents, save user message, commit
  -> bounded recent history
  -> rewrite follow-up question into a standalone retrieval query when needed
  -> Phase 5 semantic retrieval + Phase 6 context builder
  -> answer-generation LLM only when document context exists
  -> Transaction B: save assistant message + citation rows, update conversation, commit
```

### Phase 7 API

All endpoints require `Authorization: Bearer <token>`.

| Endpoint | Purpose | LLM cost |
| --- | --- | --- |
| `POST /conversations` | Create conversation, default title `New conversation` if omitted | No |
| `GET /conversations?limit=20&offset=0` | List only current user's conversations, sorted by `updated_at DESC` | No |
| `GET /conversations/{conversation_id}` | Get conversation with messages and persisted citations | No |
| `PATCH /conversations/{conversation_id}` | Rename conversation | No |
| `DELETE /conversations/{conversation_id}` | Delete conversation, messages, and citations | No |
| `POST /conversations/{conversation_id}/messages` | Add a user turn and return the assistant message | Maybe |

Message request:

```json
{
  "content": "Nguoi su dung co nhung quyen gi?",
  "document_ids": null,
  "top_k": 3
}
```

`content` is trimmed and limited to 1-4000 characters. `top_k` accepts 1-10. `document_ids` is optional, deduplicated, and every ID must belong to the authenticated user; missing or foreign IDs return 404 before any LLM call.

### Database schema

Migration head is now `0005_conversations_and_messages`.

New tables:

```text
conversations(id, user_id, title, created_at, updated_at)
messages(id, conversation_id, role, content, sequence_number, grounded, retrieval_query, created_at)
message_citations(id, message_id, citation_index, document_id, chunk_id, similarity_score, created_at)
```

`messages` uses `UNIQUE(conversation_id, sequence_number)` so chat order does not depend on timestamp precision. Conversation deletion cascades to messages and citations. Documents, chunks, and embeddings remain independent; citations only reference canonical document/chunk rows and do not duplicate chunk text or metadata.

### Multi-turn behavior

The system does not embed full chat history. For the first turn, the raw user question is used as the retrieval query. For follow-up turns, the app loads only `CHAT_HISTORY_MAX_MESSAGES` recent messages, rewrites the latest question into a standalone search query, stores that query on the user message, and embeds only that standalone query.

History is used for conversational intent only. It is passed as untrusted input and is not legal evidence. The answer prompt still treats document context as the only source that can support citations.

### Environment variables

Add or keep:

```dotenv
CHAT_HISTORY_MAX_MESSAGES=6
```

Default is 6, with validation range 0-20. Setting it to 0 disables history use and makes every turn behave like a standalone question.

### Running migration

Docker:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Local:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

Expected current revision:

```text
0005_conversations_and_messages
```

### Swagger test flow

1. Register/login, then click Authorize in Swagger.
2. Upload, process, and index at least one text document.
3. Create a conversation with `POST /conversations`.
4. Send the first message with `POST /conversations/{id}/messages`.
5. Send a follow-up such as `Con nghia vu cua ho?`.
6. Open `GET /conversations/{id}` and verify:
   `user` messages have `retrieval_query`, assistant messages have `grounded`, citations are stored separately, and sequence numbers are `1, 2, 3, 4...`.

Cost behavior: conversation CRUD, auth, ownership checks, validation, and database reads do not call the LLM. First-turn RAG may call answer generation. Follow-up RAG may call query rewrite plus answer generation. Follow-up no-context may call query rewrite, but skips answer generation.

### Phase 7 test commands

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_conversations.py tests/test_rag.py tests/test_migrations.py
python -m pytest -q
```

The conversation tests use a fake LLM provider, so they do not spend API tokens. Use the PostgreSQL test compose file for a closer migration/FK/cascade check:

```powershell
docker compose -p legal-ai-phase7-tests -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -p legal-ai-phase7-tests -f docker-compose.test.yml down
```

## Phase 8A: Frontend foundation

Phase 8A adds a separate Next.js frontend in `frontend/`. It provides the visual
foundation for authentication, chat, documents, and document detail screens. All
conversation, profile, and document content shown in this phase is isolated mock UI
data; forms and controls do not call the backend yet.

Frontend stack: Next.js App Router, React, TypeScript strict mode, Tailwind CSS,
ESLint, Inter, and `lucide-react`. Server Components remain the default. The client
boundary is limited to the workspace shell and sidebar interactions.

Routes prepared in Phase 8A:

```text
/                         -> redirects to /app/chat
/login                    visual form only
/register                 visual form only
/app                      -> redirects to /app/chat
/app/chat                 chat empty state and composer shell
/app/documents            document table with temporary mock rows
/app/documents/[id]       document detail placeholder
```

Create the safe public frontend configuration and run locally:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000`. Components use the central client in
`src/lib/api/client.ts`; endpoint base URLs are not defined in page components.

Validation commands:

```powershell
npm run lint
npm run typecheck
npm run build
```

## Phase 8B: User authentication

Phase 8B connects the existing login and registration screens to FastAPI. The
frontend stores the access token through the single module
`src/lib/auth/token-storage.ts`, validates sessions with `GET /auth/me`, protects
all `/app/*` routes with a client-side guard, and clears the session on logout or
an authenticated request returning 401. Public login failures remain local form
errors and do not trigger the global expired-session handler.

For local development, configure both origins:

```dotenv
# Root .env (backend)
FRONTEND_ORIGIN=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The Phase 8B token store uses `localStorage` because the backend currently issues
only stateless access tokens. Passwords are never persisted. A later security phase
may replace this with HttpOnly cookies and refresh-token rotation after the backend
supports that flow.

Manual auth flow: create an account at `/register`, follow the redirect to
`/login?registered=1`, sign in, then refresh `/app/chat` to confirm `/auth/me`
restores the profile. Use the sidebar logout button to clear the local session.

## Phase 8C: Document workspace

Phase 8C replaces the frontend document mocks with the authenticated backend
document APIs. `/app/documents` lists the current user's documents with `skip` and
`limit` pagination, uploads one PDF/DOCX/TXT file up to 20 MB, and exposes process,
index, view, and confirmed-delete actions according to backend state. The detail
route loads document metadata and extracted chunks without exposing storage paths,
owner controls, or vectors.

The backend remains authoritative after every mutation: the frontend refetches the
list or detail rather than publishing a local pipeline state. Document requests are
centralized in `frontend/src/lib/documents/document-api.ts`; components never attach
JWT headers directly.

## Planned next phases

## Phase 8D: Conversations workspace

Phase 8D connects the workspace sidebar to the authenticated conversation API.
Users can create, list, search, select, rename, and delete their own conversations.
The detail route `/app/chat/[conversationId]` reloads persisted messages in
`sequence_number` order and displays saved citation markers. Message sending remains
disabled in this phase; conversation data and JWT headers stay centralized in the
conversation API/provider rather than page components.

The sidebar initially requests 20 conversations and uses `offset` for **Xem thêm**.
The backend remains authoritative for ownership, ordering, and stored history; date
groups and title search are presentation-only client behavior.

Phase 1–5 đã được người dùng xác nhận chạy thực tế. Phase 6 có single-turn RAG và
citations; Phase 7 thêm conversation persistence và chat history. Chưa triển khai:
streaming, frontend, agents, reranker/hybrid search.

## Troubleshooting

| Vấn đề | Cách xử lý |
| --- | --- |
| Không tìm thấy docker | Cài Docker Desktop, bật Linux containers, mở terminal mới |
| `py -3.12` không có | Cài Python 3.12 hoặc chạy toàn bộ qua Docker |
| Settings ValidationError | Kiểm tra `.env`, SECRET_KEY, ALGORITHM=HS256, TTL hợp lệ và URL psycopg |
| Connection refused | Local dùng localhost:5433, trong Compose dùng postgres:5432 |
| Password authentication failed | Đồng bộ các biến; thay `.env` không đổi password của DB đã nằm trong volume |
| Cổng 8000/5433 đã được dùng | Dừng tiến trình trùng hoặc đổi host port; local DATABASE_URL phải dùng host port mới |
| Backend chưa healthy | Xem `docker compose logs backend postgres`; `/health` không chạy trước khi startup DB check thành công |
| `alembic current` không có ID / relation users does not exist | Chạy `alembic upgrade head` trên đúng database |
| 401 khi gọi /auth/me | Kiểm tra header, thời hạn token, SECRET_KEY và đồng hồ máy; login lại |
| 403 khi gọi /auth/me | User đã bị vô hiệu hóa |
| Login nhận 422 | Gửi JSON email/password; không gửi OAuth2 form hoặc full_name |
| ModuleNotFoundError | Cài requirements trong đúng Python/venv hoặc rebuild image |
| Test PostgreSQL từ chối URL | Dùng database test có tên kết thúc bằng `_test` |
| Model mới không được autogenerate | Import model vào Alembic env trước khi so sánh metadata |
| relation documents/document_chunks/chunk_embeddings/conversations does not exist | Chạy upgrade head; revision phải là 0005_conversations_and_messages |
| Upload 413 | Giảm file size hoặc chỉnh MAX_UPLOAD_SIZE_MB rồi restart/recreate backend |
| Upload 415 | Kiểm tra extension/MIME; PDF header, DOCX container hoặc TXT UTF-8 |
| Document 404 | ID không tồn tại, đã xóa hoặc thuộc user khác |
| Document 503 | Kiểm tra DB/storage permissions và dung lượng disk; không log secrets |
| Không thấy file khi chuyển Docker/local | Hai môi trường dùng storage khác nhau; xem mục Docker/persistence |
| Metadata deleted; file cleanup pending | Đối chiếu DB với file .deleting trong storage, xử lý cleanup có kiểm soát |
| Processing 422 với PDF scan | File không có text layer; chưa hỗ trợ OCR |
| Extraction dependency unavailable | Rebuild image hoặc cài requirements có pypdf/python-docx |
| Processing 409 vì thiếu file | Kiểm tra đúng storage volume; upload tài liệu lại nếu file đã mất |
| Processing 409 / status bị kẹt | Xác nhận request cũ đã dừng trước khi operator reset trạng thái; chưa có tự động recovery |
| Chunk config ValidationError | CHUNK_SIZE 100–20000, 0 <= CHUNK_OVERLAP < CHUNK_SIZE |
| failed nhưng vẫn có chunks | Reprocess lỗi giữ bộ chunks hoàn chỉnh trước đó; kiểm tra status trước khi sử dụng |
| Chunk count quá lớn / xử lý chậm | Giảm overlap, tăng chunk size hợp lý hoặc dùng file nhỏ hơn |

Với database đã khởi tạo, đổi password bằng SQL có kiểm soát hoặc giữ cấu hình
cũ. `docker compose down -v` sẽ **xóa dữ liệu volume**; chỉ dùng khi chủ động muốn
reset toàn bộ database development.
