# Event Around Backend

โปรเจกต์ Backend ของ Event Around พัฒนาด้วย FastAPI + PostgreSQL + Docker

## มีอะไรในโปรเจกต์นี้
- โครงสร้างโปรเจกต์ FastAPI
- PostgreSQL รันผ่าน Docker
- SQLAlchemy สำหรับเชื่อมฐานข้อมูล
- Alembic สำหรับ migration
- API ตรวจสถานะระบบ (`health`)
- API สมัครสมาชิกนักศึกษา
- API ยืนยันตัวตน (Auth) ครบชุดเบื้องต้น
- API หมวดหมู่กิจกรรม (Categories) ครบชุดพื้นฐาน
- API บันทึกกิจกรรมโปรด (Saved Events)
- API นำเข้ากิจกรรมจาก CSV และ JSON
- โครงคลาส UML (Skeleton Phase) ครบชุดใน `app/domain`
- สคริปต์ seed ข้อมูลตัวอย่าง
- ชุดทดสอบเบื้องต้น

## เทคโนโลยีที่ใช้
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Docker

## วิเคราะห์โปรเจกต์ปัจจุบัน
- ตอนนี้รัน local ได้ด้วย FastAPI + Docker PostgreSQL + ไฟล์ `.env` เดิม
- โค้ดส่วน config และ database ยังถูกรวมอยู่ใน `app/core` เป็นหลัก
- ยังไม่มีชั้นสำหรับ Render โดยตรง เช่น CORS, port จาก environment, และ blueprint สำหรับ deploy
- ยังไม่มี CI/CD workflow ที่แยกหน้าที่ชัดเจนระหว่างตรวจโค้ดกับ deploy

## โครงสร้างเป้าหมาย
- `app/core/settings.py` เก็บ config จาก environment และคำนวณ `DATABASE_URL` ให้ถูกทั้ง local และ production
- `app/db/` เก็บ `Base`, `engine`, `SessionLocal`, และ `get_db`
- `app/main.py` เป็นจุดเริ่ม app, ใส่ CORS, และ health endpoint สำหรับตรวจสถานะ
- `alembic/env.py` ใช้ `DATABASE_URL` จาก environment โดยตรง
- `.github/workflows/ci.yml` ใช้ตรวจ lint, format, test, และ migration validation
- `render.yaml` ใช้เป็น Render Blueprint สำหรับ web service + PostgreSQL

## CI/CD Architecture
- **CI** ใช้ GitHub Actions เท่านั้น
	- รันตอน `pull_request` และ `push` เข้า `main`
	- ตรวจ dependencies, lint, format check, test, และ migration validation
- **CD** ใช้ Render auto deploy หลัง merge เข้า `main`
	- Render จะ build จาก `Dockerfile`
	- ใช้ Render PostgreSQL ใน production
	- รัน `alembic upgrade head` ก่อนเริ่ม service เพื่อให้ schema ตรงกับโค้ด
- **Secrets**
	- ฝั่ง GitHub เก็บเฉพาะ secrets ที่ workflow ต้องใช้จริง
	- ฝั่ง Render เก็บ production secrets เช่น `JWT_SECRET_KEY` และ `CORS_ORIGINS`

## ไฟล์สำคัญที่เพิ่ม/แก้
- `app/core/settings.py` สำหรับอ่านค่าจาก environment และสร้าง `DATABASE_URL`
- `app/db/base.py` และ `app/db/session.py` สำหรับ SQLAlchemy engine/session
- `app/main.py` สำหรับ CORS และ health endpoint
- `render.yaml` สำหรับ Render Blueprint
- `.github/workflows/ci.yml` สำหรับ CI บน GitHub Actions
- `pyproject.toml` และ `pytest.ini` สำหรับกติกา lint/test
- `requirements-dev.txt` สำหรับเครื่องมือ dev เช่น `ruff` และ `black`
- `.env.example` สำหรับตัวอย่าง config ที่ไม่ใช่ secret

## วิธี deploy บน Render แบบสั้น
1. Push code ขึ้น GitHub
2. สร้าง Render PostgreSQL
3. สร้าง Web Service จาก repo นี้ หรือใช้ `render.yaml`
4. ตั้งค่า environment variables บน Render
5. เปิด Auto Deploy ให้ merge เข้า `main` แล้ว deploy อัตโนมัติ
6. ตรวจ health endpoint ที่ `/health`
7. นำ base URL ของ Render ไปให้ frontend เรียกใช้งาน

## ความสัมพันธ์กับ UML
- โปรเจกต์มีโครง UML แยกใน `app/domain` เพื่อเตรียม OOP เต็มรูปแบบ
- ในเฟสนี้ คลาสใน `app/domain` เป็น skeleton (method signatures ครบ แต่ยังไม่ลง business logic ลึก)
- API ปัจจุบันยังทำงานผ่าน service/repository เดิม และจะค่อย map เข้ากับ domain classes ในรอบถัดไป

### UML Skeleton Classes ที่สร้างแล้ว
- `User` (abstract)
- `Student`
- `Organizer`
- `EventCategory`
- `Event`
- `EventManager`
- `LocationService`
- `AuthManager`
- `EventAroundSystem`

## วิธีติดตั้งและรัน (Setup)

### สิ่งที่ต้องมีในเครื่อง
- Python 3.11 ขึ้นไป
- Docker Desktop (รองรับ Docker Compose)

### 1) สร้างและเปิด virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 3) สร้างไฟล์ `.env`

สร้างไฟล์ `.env` ที่ root ของโปรเจกต์ แล้วใส่ค่าตัวอย่างนี้:

```env
APP_NAME=Event Around API
APP_ENV=development
APP_DEBUG=true
API_V1_PREFIX=/api/v1
APP_TIMEZONE=Asia/Bangkok

POSTGRES_USER=event_user
POSTGRES_PASSWORD=event_pass
POSTGRES_DB=event_around_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435

DATABASE_URL=postgresql+psycopg://event_user:event_pass@localhost:5435/event_around_db

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Timezone Policy

- `APP_TIMEZONE` ใช้กำหนด timezone สำหรับเวลาที่ส่งออกทาง API โดยค่า default คือ `Asia/Bangkok`
- ระบบเก็บค่า `datetime` ในฐานข้อมูลเป็น UTC เพื่อให้ deploy บน server timezone อะไรก็ให้ผลลัพธ์เหมือนกัน
- เวลาที่ตอบกลับไปยัง frontend จะถูกแปลงเป็นเวลาไทยเสมอและส่งในรูปแบบ ISO 8601 ที่มี offset เช่น `2026-04-30T15:20:00+07:00`
- input ที่ส่งมาเป็น `datetime` แบบไม่มี timezone จะถูกตีความเป็นเวลา `Asia/Bangkok` ก่อนแปลงไปเก็บเป็น UTC
- ข้อมูลเก่าที่เป็น naive datetime ในคอลัมน์ legacy จะถูกอ่านเป็น UTC และ migration `0008_convert_legacy_datetimes_to_timestamptz.py` ใช้แปลง schema ฝั่ง PostgreSQL ให้เป็น `TIMESTAMP WITH TIME ZONE`
- access token และ refresh token ยังคำนวณอายุจาก UTC เพื่อให้การหมดอายุคงที่ในทุก environment แต่เมื่อ response มี field เวลา จะส่งออกเป็น Bangkok time

ตัวอย่าง response:

```json
{
	"success": true,
	"message": "ดึงรายละเอียดกิจกรรมสำเร็จ",
	"data": {
		"eventId": 101,
		"startTime": "2026-04-30T15:20:00+07:00",
		"endTime": "2026-04-30T18:20:00+07:00",
		"createdAt": "2026-04-25T09:00:00+07:00"
	}
}
```

### 4) เปิดฐานข้อมูล PostgreSQL

```bash
docker compose up -d db
docker compose ps
```

### 5) รัน migration

```bash
alembic upgrade head
```

ถ้าเจอ error ลักษณะ `relation "users" already exists` แปลว่าเคยสร้างตารางไว้ก่อนหน้า ให้รีเซ็ตฐานข้อมูลแล้วรันใหม่:

```bash
docker compose down -v
docker compose up -d db
alembic upgrade head
```

### 6) รัน API

```bash
uvicorn app.main:app --reload
```

API จะรันที่ `http://127.0.0.1:8000`

### 7) ทดสอบว่า API ทำงาน

```bash
curl http://127.0.0.1:8000/api/v1/health
```

ผลลัพธ์ที่คาดหวัง:

```json
{"success":true,"message":"Event Around API is running","data":null}
```

## คำสั่งที่ใช้บ่อย

รันแอป:

```bash
make run
```

รันเทสต์ทั้งหมด:

```bash
make test
```

ตรวจ lint:

```bash
make lint
```

จัด format โค้ด:

```bash
make format
```

หรือรันตรง:

```bash
python -m pytest -q
```

seed ข้อมูลตัวอย่าง:

```bash
make seed
```

## การทดสอบโปรเจกต์

โปรเจกต์นี้ใช้ `pytest` เป็นหลักในการรันทดสอบอัตโนมัติ และใช้ `FastAPI TestClient` สำหรับยิง API แบบไม่ต้องเปิด browser หรือเรียกผ่าน Postman ทุกครั้ง

เครื่องมือที่ใช้:
- `pytest` สำหรับรันทดสอบและสรุปผลว่า `passed / failed / warnings` เท่าไหร่
- `FastAPI TestClient` สำหรับทดสอบ API แบบเร็วและแยกจากการรันเซิร์ฟเวอร์จริง
- SQLite in-memory + `StaticPool` ในชุดทดสอบ เพื่อให้เทสเร็วและไม่กระทบฐานข้อมูลจริง

ทำไมวิธีนี้ดี:
- รันเร็ว และเห็นผลทันที
- เทสแยกจากข้อมูลจริง ลดความเสี่ยงทำข้อมูลใน DB พัง
- เขียน assert ได้ชัดเจน ทำให้จับ bug ได้ง่าย

คำสั่งรันเทสต์ทั้งโปรเจกต์:

```bash
python -m pytest -ra -q
```

ถ้าต้องการให้แสดง warning ด้วย:

```bash
python -m pytest -ra -W default
```

บัญชีตัวอย่างที่ได้จากการ seed:

- ADMIN
	- email: `admin@example.com`
	- password: `Password123!`
- ORGANIZER
	- email: `organizer@example.com`
	- password: `Password123!`

หมายเหตุ:
- สคริปต์ seed จะตรวจ email ซ้ำก่อน insert (รันซ้ำแล้วไม่เพิ่มข้อมูลซ้ำ)
- ควรเปลี่ยนรหัสผ่านเริ่มต้นทันทีหลังล็อกอินครั้งแรก

## คู่มือทดสอบ API แยกไฟล์

ดูวิธีรันและทดสอบ API แบบละเอียดที่ไฟล์ **[TEST_API.md](TEST_API.md)**

## คู่มือ Deploy แยกไฟล์

ดูวิธี deploy ตั้งแต่ local จนขึ้น Render จริงที่ไฟล์ **[DEPLOY_RENDER.md](DEPLOY_RENDER.md)**

## Auth APIs ที่ทำแล้ว

- POST /api/v1/auth/register/student
- POST /api/v1/auth/register/organizer
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- PATCH /api/v1/auth/me
- POST /api/v1/auth/change-password

## Category APIs ที่ทำแล้ว

- GET /api/v1/categories
	- Public
	- query: `includeInactive=true|false` (default เป็น `false`)
- POST /api/v1/categories
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
- GET /api/v1/categories/{categoryId}
	- Public
- PATCH /api/v1/categories/{categoryId}
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
- DELETE /api/v1/categories/{categoryId}
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
	- เป็น soft delete (`isActive = false`)

## Event APIs ที่ทำแล้ว

- GET /api/v1/events
	- Public
	- query: `page`, `pageSize`, `search`, `categoryId`, `status`, `startFrom`, `endTo`, `sortBy`, `sortOrder`
	- Default แสดงเฉพาะ `PUBLISHED`
- POST /api/v1/events
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
	- Organizer สร้างได้เป็น `DRAFT`
	- Admin สามารถสร้างได้ทั้ง `DRAFT` หรือ `PUBLISHED`
- PATCH /api/v1/events/{eventId}
	- ต้องเป็นเจ้าของกิจกรรม (`ORGANIZER` ที่เป็น organizer ของ event)
- DELETE /api/v1/events/{eventId}
	- ต้องเป็นเจ้าของกิจกรรม (`ORGANIZER` ที่เป็น organizer ของ event)
- POST /api/v1/events/{eventId}/publish
	- ต้องเป็น `ADMIN`
	- ตรวจสอบข้อมูลครบก่อนเปลี่ยนเป็น `PUBLISHED`
- POST /api/v1/events/{eventId}/cancel
	- ต้องเป็น `ADMIN` หรือเจ้าของกิจกรรม
	- บันทึกเหตุผลการยกเลิก
- GET /api/v1/events/{eventId}
	- Public
	- ถ้า `event` อยู่ในสถานะอื่นที่ไม่ใช่ `PUBLISHED` จะต้องเป็น `ADMIN` หรือ `ORGANIZER` เท่านั้น
	- `isSaved` จะคืนค่าเฉพาะสำหรับผู้ใช้ที่ล็อกอินเป็น `STUDENT`
- GET /api/v1/events/my-events
	- ต้องเป็น `ORGANIZER`
	- query: `page`, `pageSize`, `status`, `search`, `sortBy`, `sortOrder`
	- แสดงเฉพาะกิจกรรมที่ organizer ปัจจุบันเป็นเจ้าของ

## Nearby / Map APIs ที่ทำแล้ว

- GET /api/v1/events/nearby
	- Public
	- query: `latitude`, `longitude`, `radiusKm`, `search`, `categoryId`, `page`, `pageSize`, `sortBy`, `sortOrder`
	- ดึงกิจกรรมที่อยู่ในรัศมีเทียบกับตำแหน่งผู้ใช้
- GET /api/v1/events/map
	- Public
	- query: `latitude`, `longitude`, `radiusKm`, `search`, `categoryId`
	- คืนข้อมูลเบาๆ สำหรับ marker บนแผนที่
- GET /api/v1/events/upcoming
	- Public
	- query: `page`, `pageSize`, `categoryId`, `sortBy`, `sortOrder`
	- แสดงกิจกรรมที่กำลังจะมาถึง (start_time > now และ status = PUBLISHED)
- GET /api/v1/events/active
	- Public
	- query: `page`, `pageSize`, `categoryId`, `sortBy`, `sortOrder`
	- แสดงกิจกรรมที่ยัง active (status = PUBLISHED และ end_time > now)

## Organizer APIs ที่ทำแล้ว

- GET /api/v1/organizer/dashboard
	- ต้องเป็น `ORGANIZER`
	- แสดงสรุปข้อมูล dashboard ของ organizer
	- คืนจำนวน event ทั้งหมด, DRAFT, PUBLISHED, CANCELLED และยอด saved รวม
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `ORGANIZER` จะตอบ `403`
- GET /api/v1/organizer/events/{eventId}/stats
	- ต้องเป็น `ORGANIZER` และเป็นเจ้าของกิจกรรม
	- ดูสถิติราย event เช่น savedCount, status, start/end time
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `ORGANIZER` หรือไม่ใช่เจ้าของกิจกรรม จะตอบ `403`
		- ถ้าไม่พบกิจกรรม จะตอบ `404`

## Import APIs ที่ทำแล้ว

- POST /api/v1/import/events/csv
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
	- รับไฟล์ `CSV` ผ่าน `form-data`
	- รองรับ `defaultStatus` เป็น `DRAFT` หรือ `PUBLISHED`
	- ถ้า `categoryId` ไม่ตรงกับข้อมูลจริง ระบบจะนับแถวนั้นเป็น failed
	- ถ้า `ORGANIZER` ใส่ `status=PUBLISHED` ใน row นั้น จะถูกปฏิเสธ
	- ถ้าโครงสร้าง CSV ผิด จะตอบ `400 bad csv format`
- POST /api/v1/import/events/json
	- ต้องเป็น `ADMIN` หรือ `ORGANIZER`
	- รับ `application/json`
	- ใช้โครงสร้าง `events` เป็น array ของข้อมูลกิจกรรม
	- ถ้า `categoryId` ไม่ตรงกับข้อมูลจริง ระบบจะนับแถวนั้นเป็น failed
	- ถ้าค่าใน row ไม่ถูกต้อง ระบบจะคืนรายละเอียด error ตาม field

## SavedEvent APIs ที่ทำแล้ว

- POST /api/v1/saved-events
	- ต้องเป็น `STUDENT`
	- Body: `eventId`
	- บันทึกกิจกรรมลงรายการโปรดของผู้ใช้
	- response จะคืน `eventId` และ `saved = true`
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `STUDENT` จะตอบ `403`
		- ถ้าไม่พบกิจกรรม จะตอบ `404`
		- ถ้าบันทึกกิจกรรมซ้ำ จะตอบ `409`
		- ถ้า `eventId` ไม่ถูกต้อง จะตอบ `422`
- GET /api/v1/saved-events
	- ต้องเป็น `STUDENT`
	- query: `page`, `pageSize`, `status`, `sortBy`, `sortOrder`
	- ดึงรายการกิจกรรมที่ student บันทึกไว้ทั้งหมด พร้อม pagination
	- `sortBy` รองรับ `savedAt`, `startTime`, `endTime`
	- response แต่ละ item มี `savedAt` เพื่อแสดงเวลาที่บันทึก
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `STUDENT` จะตอบ `403`
		- ถ้า `status` ไม่ถูกต้อง จะตอบ `400`
- DELETE /api/v1/saved-events/{eventId}
	- ต้องเป็น `STUDENT`
	- Path param: `eventId` 
	- ยกเลิกบันทึกกิจกรรมออกจากรายการโปรดของผู้ใช้
	- response จะคืน `eventId` และ `saved = false`
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `STUDENT` จะตอบ `403`
		- ถ้าไม่พบกิจกรรมในรายการบันทึก จะตอบ `404`
- GET /api/v1/saved-events/check/{eventId}
	- ต้องเป็น `STUDENT`
	- Path param: `eventId` 
	- ใช้เช็กว่า event นี้ถูกบันทึกโดยนักศึกษาปัจจุบันแล้วหรือยัง เพื่อเอาไปแสดงปุ่ม save/unsave บน frontend
	- response จะคืน `eventId` และ `isSaved = true|false`
	- กรณีผิดเงื่อนไข:
		- ถ้าไม่ส่ง token จะตอบ `401`
		- ถ้า role ไม่ใช่ `STUDENT` จะตอบ `403`
		- ถ้าไม่พบกิจกรรม จะตอบ `404`

### แนวคิดการทำงานของ Event APIs
- ผู้ใช้ `ORGANIZER` สร้างกิจกรรมใหม่ในสถานะ `DRAFT` ได้
- `ADMIN` สามารถสร้างกิจกรรมเป็น `PUBLISHED` ได้โดยตรง หรืออนุมัติกิจกรรม `DRAFT` ให้เป็น `PUBLISHED`
- เจ้าของกิจกรรม (Organizer) สามารถแก้ไขหรือลบกิจกรรมของตัวเองได้
- `ADMIN` และเจ้าของกิจกรรมสามารถยกเลิกกิจกรรม พร้อมบันทึกเหตุผลการยกเลิก
- กิจกรรมที่ยังเป็น `DRAFT` จะไม่แสดงในรายการสาธารณะจนกว่าจะถูกเผยแพร่

หมายเหตุ:
- ชื่อหมวดหมู่ห้ามซ้ำ (ตรวจแบบไม่สนตัวพิมพ์เล็ก/ใหญ่)
- ถ้า query `includeInactive` ไม่ถูกต้อง จะตอบ `400`
- ถ้าไม่มีสิทธิ์ จะตอบ `403`
- ถ้าไม่พบหมวดหมู่ จะตอบ `404`

- `AuthService` เริ่ม delegate บาง business flow ไปที่ `app/domain/AuthManager` แล้ว
- `register_student` และ `register_organizer` ใช้ `AuthManager.register_student()` / `AuthManager.register_organizer()` เพื่อกำหนด role จาก domain
- `is_email_unique` ใช้ `AuthManager.is_email_unique()` ใน flow ตรวจสอบอีเมลซ้ำ
- `login` ใช้ `AuthManager.login()` ในชั้น domain ก่อนออก token
- `User` domain มี `verify_password()` และ getter/setter หลัก เพื่อ map กับพฤติกรรมตาม UML
- **API contract ไม่เปลี่ยน** จากสเปกเดิม

## Troubleshooting

- ถ้า `pytest` import `app` ไม่ได้ ให้ใช้:

```bash
python -m pytest -q
```

- ปิดเฉพาะ container:

```bash
docker compose down
```

- ปิดและลบ volume (รีเซ็ตฐานข้อมูลทั้งหมด):

```bash
docker compose down -v
```