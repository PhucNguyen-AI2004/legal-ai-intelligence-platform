# Legal AI Intelligence Platform

## Project overview

Dự án portfolio hướng tới vị trí Fresher/Junior AI Engineer hoặc Data Engineer.
Mục tiêu dài hạn là xử lý tài liệu pháp luật và trả lời câu hỏi có dẫn nguồn.
**Phase 4 bổ sung document processing pipeline**: extract text → normalize →
chunk → lưu PostgreSQL, trên nền backend/auth/documents hiện có.

## Current phase

Đã có FastAPI, cấu hình môi trường, SQLAlchemy, PostgreSQL, Alembic, Docker,
bảng users, đăng ký, đăng nhập bằng JWT, upload/lưu metadata, list/detail/delete
tài liệu thuộc user hiện tại, xử lý tài liệu và xem chunks. Phase 1–3 đã được
người dùng xác nhận test thực tế.
Chưa có OCR, LLM, RAG, embedding, vector database, frontend, social login,
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

Phase 4 có head `0003_document_processing`; `current` phải hiển thị revision này.
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
tiếng Việt và từng tokenizer; chưa có tokenizer LLM hay embedding.

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

### Trạng thái kiểm chứng Phase 4

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

## Planned next phases

Phase 1 (backend), Phase 2 (User/Auth), Phase 3 (Documents) và Phase 4 (Processing)
đã có mã nguồn. Các bước dự kiến sau: embedding
và retrieval; RAG/citation/hội thoại; deploy, monitoring và hardening.
Chưa triển khai Phase 5, embedding, vector database, RAG hoặc LLM.

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
| relation documents/document_chunks does not exist | Chạy upgrade head; revision phải là 0003_document_processing |
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
