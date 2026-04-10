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
- สคริปต์ seed ข้อมูลตัวอย่าง
- ชุดทดสอบเบื้องต้น

## เทคโนโลยีที่ใช้
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Docker

## ความสัมพันธ์กับ UML
- `User` คือ entity หลัก
- `Student` แทนด้วย `User(role="STUDENT")`
- `AuthManager` แทนด้วย `AuthService`

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

หรือรันตรง:

```bash
python -m pytest -q
```

seed ข้อมูลตัวอย่าง:

```bash
make seed
```

## คู่มือทดสอบ API แยกไฟล์

ดูวิธีรันและทดสอบ API แบบละเอียดที่ไฟล์ `TEST_API.md`

## Auth APIs ที่ทำแล้ว

- POST /api/v1/auth/register/student
- POST /api/v1/auth/register/organizer
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- PATCH /api/v1/auth/me
- POST /api/v1/auth/change-password

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