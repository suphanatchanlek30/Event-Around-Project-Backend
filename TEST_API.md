# TEST API Guide

คู่มือนี้รวมวิธีรัน API และวิธีทดสอบ endpoint ที่สำคัญของโปรเจกต์

## 1) รัน API

### 1.1 เปิด virtual environment

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 1.2 เปิดฐานข้อมูล PostgreSQL

```bash
docker compose up -d db
docker compose ps
```

### 1.3 รัน migration

```bash
alembic upgrade head
```

ถ้าเจอ `relation "users" already exists` ให้รีเซ็ตฐานข้อมูลแล้วลองใหม่:

```bash
docker compose down -v
docker compose up -d db
alembic upgrade head
```

### 1.4 รันเซิร์ฟเวอร์

```bash
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

## 2) ทดสอบ Health API

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected response:

```json
{"success":true,"message":"Event Around API is running","data":null}
```

## 3) ทดสอบ Register Student API

Endpoint: `POST /api/v1/auth/register/student`

ตัวอย่าง request body:

```json
{
  "fullName": "Test User",
  "email": "test1@example.com",
  "password": "Password123!",
  "confirmPassword": "Password123!"
}
```

ตัวอย่างคำสั่ง PowerShell:

```powershell
$body = @{
  fullName = 'Test User'
  email = 'test1@example.com'
  password = 'Password123!'
  confirmPassword = 'Password123!'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/register/student' -Method Post -ContentType 'application/json' -Body $body
```

## 3.1) ทดสอบ Register Organizer API

Endpoint: POST /api/v1/auth/register/organizer

```powershell
$body = @{
  fullName = 'Computer Science Club'
  email = 'organizer@ubu.ac.th'
  password = 'Password123!'
  confirmPassword = 'Password123!'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/register/organizer' -Method Post -ContentType 'application/json' -Body $body
```

## 3.2) ทดสอบ Login API

Endpoint: POST /api/v1/auth/login

```powershell
$loginBody = @{
  email = 'student@ubu.ac.th'
  password = 'Password123!'
} | ConvertTo-Json

$login = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/login' -Method Post -ContentType 'application/json' -Body $loginBody
$accessToken = $login.data.accessToken
$refreshToken = $login.data.refreshToken
```

## 3.3) ทดสอบ Me API

Endpoint: GET /api/v1/auth/me

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/me' -Method Get -Headers @{ Authorization = "Bearer $accessToken" }
```

## 3.4) ทดสอบ Update Me API

Endpoint: PATCH /api/v1/auth/me

```powershell
$patchBody = @{
  fullName = 'Somying Updated'
  profileImageUrl = 'https://example.com/profile.jpg'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/me' -Method Patch -ContentType 'application/json' -Headers @{ Authorization = "Bearer $accessToken" } -Body $patchBody
```

## 3.5) ทดสอบ Change Password API

Endpoint: POST /api/v1/auth/change-password

```powershell
$changePassBody = @{
  oldPassword = 'Password123!'
  newPassword = 'NewPassword123!'
  confirmNewPassword = 'NewPassword123!'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/change-password' -Method Post -ContentType 'application/json' -Headers @{ Authorization = "Bearer $accessToken" } -Body $changePassBody
```

## 3.6) ทดสอบ Refresh API

Endpoint: POST /api/v1/auth/refresh

```powershell
$refreshBody = @{ refreshToken = $refreshToken } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/refresh' -Method Post -ContentType 'application/json' -Body $refreshBody
```

## 3.7) ทดสอบ Logout API

Endpoint: POST /api/v1/auth/logout

```powershell
$logoutBody = @{ refreshToken = $refreshToken } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/logout' -Method Post -ContentType 'application/json' -Headers @{ Authorization = "Bearer $accessToken" } -Body $logoutBody
```

## 4) รันชุดทดสอบอัตโนมัติ (pytest)

รันทั้งหมด:

```bash
python -m pytest -q
```

รันเฉพาะไฟล์ทดสอบ auth:

```bash
python -m pytest tests/test_auth.py -q
```

ไฟล์ทดสอบหลัก:
- `tests/test_health.py`
- `tests/test_auth.py`

## 5) คำสั่งปิดระบบ

ปิดเฉพาะ container:

```bash
docker compose down
```

ปิดและลบ volume (รีเซ็ตฐานข้อมูลทั้งหมด):

```bash
docker compose down -v
```
