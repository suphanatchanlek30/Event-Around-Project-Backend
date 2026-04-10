# TEST API Guide

คู่มือนี้รวมวิธีรัน API และวิธีทดสอบ endpoint ที่สำคัญของโปรเจกต์

## สถานะโปรเจกต์ตอนนี้ (Phase)

- ปัจจุบันอยู่ใน **UML Skeleton Phase** สำหรับโครงสร้าง OOP
- คลาสตาม UML ถูกสร้างไว้ครบชุดที่ `app/domain` แล้ว
- เมธอดในคลาส domain ส่วนใหญ่ยังเป็น `NotImplementedError` เพื่อรอเติม logic ตอนทำ API รอบถัดไป
- API ที่ทดสอบได้ตอนนี้เน้นกลุ่ม Auth และ Health ตามรายการด้านล่าง
- Auth ผ่านรอบ refactor ให้สอดคล้อง UML มากขึ้น โดยไม่เปลี่ยน request/response contract

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

## 4) ทดสอบด้วย Postman (วิธีง่ายๆ ก๊อปไปลงตรง Body)

### ขั้นตอนการตั้งค่า Postman

1. **สร้าง Collection** ชื่อ `Event Around API`
2. **สร้าง Environment Variable** ชื่อ `accessToken` และ `refreshToken` (ไว้เก็บค่าจากการ login)
3. **Base URL**: `http://127.0.0.1:8000`

### ขั้นตอนการใช้งาน (ทดสอบลำดับนี้)

---

#### **1️⃣ Health Check**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/health`  
**Body:** None (ไม่ต้องใส่ข้อมูล)

**Expected Response:**
```json
{
  "success": true,
  "message": "Event Around API is running",
  "data": null
}
```

---

#### **2️⃣ Register Student**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/register/student`  
**Content-Type:** application/json  
**Body:** (ก๊อปตรงนี้ไปลงใน Postman Body tab)

```json
{
  "fullName": "Somying Student",
  "email": "somying@student.com",
  "password": "Password123!",
  "confirmPassword": "Password123!"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Student registered successfully",
  "data": {
    "userId": 1,
    "fullName": "Somying Student",
    "email": "somying@student.com",
    "role": "STUDENT"
  }
}
```

---

#### **3️⃣ Register Organizer (Optional)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/register/organizer`  
**Content-Type:** application/json  
**Body:**

```json
{
  "fullName": "UBU Computer Club",
  "email": "club@ubu.ac.th",
  "password": "Password123!",
  "confirmPassword": "Password123!"
}
```

---

#### **4️⃣ Login**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/login`  
**Content-Type:** application/json  
**Body:**

```json
{
  "email": "somying@student.com",
  "password": "Password123!"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "userId": 1,
    "fullName": "Somying Student",
    "email": "somying@student.com",
    "role": "STUDENT",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**⚠️ สำคัญ:** คัดลอก `accessToken` และ `refreshToken` ไปไว้ใน Postman Environment Variables ด้วย

---

#### **5️⃣ Get My Profile (Get Me)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/auth/me`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "data": {
    "userId": 1,
    "fullName": "Somying Student",
    "email": "somying@student.com",
    "role": "STUDENT",
    "profileImageUrl": null,
    "createdAt": "2026-04-10T10:00:00",
    "updatedAt": "2026-04-10T10:00:00"
  }
}
```

---

#### **6️⃣ Update My Profile**

**Method:** PATCH  
**URL:** `http://127.0.0.1:8000/api/v1/auth/me`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Content-Type:** application/json  
**Body:**

```json
{
  "fullName": "Somying Updated",
  "profileImageUrl": "https://example.com/avatar.jpg"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "userId": 1,
    "fullName": "Somying Updated",
    "email": "somying@student.com",
    "role": "STUDENT",
    "profileImageUrl": "https://example.com/avatar.jpg",
    "createdAt": "2026-04-10T10:00:00",
    "updatedAt": "2026-04-10T10:05:00"
  }
}
```

---

#### **7️⃣ Change Password**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/change-password`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Content-Type:** application/json  
**Body:**

```json
{
  "oldPassword": "Password123!",
  "newPassword": "NewSecurePassword123!",
  "confirmNewPassword": "NewSecurePassword123!"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

#### **8️⃣ Refresh Token**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/refresh`  
**Content-Type:** application/json  
**Body:**

```json
{
  "refreshToken": "{{refreshToken}}"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

#### **9️⃣ Logout**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/auth/logout`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Content-Type:** application/json  
**Body:**

```json
{
  "refreshToken": "{{refreshToken}}"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

### 💡 เคล็ดลับ Postman

1. **ตั้ง Environment Variables:**
   - ไปที่ **Environments** → **Create new > Event Around**
   - สร้าง Variables: `accessToken` คำเดียว
   - หลังจาก Login ให้ **Tests** tab เพิ่มโค้ดนี้เก็บ token:
   ```javascript
   let response = pm.response.json();
   pm.environment.set("accessToken", response.data.accessToken);
   pm.environment.set("refreshToken", response.data.refreshToken);
   ```
   - ครั้งต่อไป ใช้ `{{accessToken}}` และ `{{refreshToken}}` ได้เลย

2. **ทดสอบตามลำดับ:**
   - Health → Register → Login → Get Me → Update Me → Change Password → Refresh → Logout

3. **Postman Collection (Optional):**
   - จัดเก็บ request ทีละชุด เพื่อรัน automation test ได้

---

## 5) รันชุดทดสอบอัตโนมัติ (pytest)

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

## 6) คำสั่งปิดระบบ

ปิดเฉพาะ container:

```bash
docker compose down
```

ปิดและลบ volume (รีเซ็ตฐานข้อมูลทั้งหมด):

```bash
docker compose down -v
```
