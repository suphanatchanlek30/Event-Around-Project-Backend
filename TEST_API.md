# TEST API Guide

คู่มือนี้รวมวิธีรัน API และวิธีทดสอบ endpoint ที่สำคัญของโปรเจกต์

## สถานะโปรเจกต์ตอนนี้ (Phase)

- ปัจจุบันอยู่ใน **UML Skeleton Phase** สำหรับโครงสร้าง OOP
- คลาสตาม UML ถูกสร้างไว้ครบชุดที่ `app/domain` แล้ว
- เมธอดในคลาส domain ส่วนใหญ่ยังเป็น `NotImplementedError` เพื่อรอเติม logic ตอนทำ API รอบถัดไป
- API ที่ทดสอบได้ตอนนี้เน้นกลุ่ม Auth และ Health ตามรายการด้านล่าง
- API ที่ทดสอบได้ตอนนี้เน้นกลุ่ม Auth, Health และ Categories ตามรายการด้านล่าง
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

## 2) ทดสอบด้วย Postman

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

#### **🔟 Categories: List (Active Only by default)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/categories`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงหมวดหมู่สำเร็จ",
  "data": [
    {
      "categoryId": 1,
      "name": "Academic",
      "description": "กิจกรรมเชิงวิชาการ",
      "isActive": true
    }
  ]
}
```

ต้องการดึงทุกหมวดรวม inactive:

`GET /api/v1/categories?includeInactive=true`

---

#### **1️⃣1️⃣ Categories: Create (ADMIN / ORGANIZER)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/categories`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Content-Type:** application/json  
**Body:**

```json
{
  "name": "Hackathon",
  "description": "กิจกรรมการแข่งขันพัฒนาโปรแกรม"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "สร้างหมวดหมู่สำเร็จ",
  "data": {
    "categoryId": 7,
    "name": "Hackathon",
    "description": "กิจกรรมการแข่งขันพัฒนาโปรแกรม",
    "isActive": true
  }
}
```

---

#### **1️⃣2️⃣ Categories: Get Detail**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/categories/1`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงรายละเอียดหมวดหมู่สำเร็จ",
  "data": {
    "categoryId": 1,
    "name": "Academic",
    "description": "กิจกรรมเชิงวิชาการ",
    "isActive": true
  }
}
```

---

#### **1️⃣3️⃣ Categories: Update (ADMIN / ORGANIZER)**

**Method:** PATCH  
**URL:** `http://127.0.0.1:8000/api/v1/categories/1`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Content-Type:** application/json  
**Body:**

```json
{
  "name": "Workshop Updated",
  "description": "กิจกรรมฝึกปฏิบัติแบบลงมือทำ"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "แก้ไขหมวดหมู่สำเร็จ",
  "data": {
    "categoryId": 1,
    "name": "Workshop Updated",
    "description": "กิจกรรมฝึกปฏิบัติแบบลงมือทำ",
    "isActive": true
  }
}
```

---

#### **1️⃣4️⃣ Categories: Deactivate (Soft Delete)**

**Method:** DELETE  
**URL:** `http://127.0.0.1:8000/api/v1/categories/1`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ปิดใช้งานหมวดหมู่สำเร็จ",
  "data": {
    "categoryId": 1,
    "isActive": false
  }
}
```

---

#### **1️⃣5️⃣ Events: List (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงรายการกิจกรรมสำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "locationName": "SCI Building Room 501",
      "startTime": "2026-04-10T09:00:00+00:00",
      "endTime": "2026-04-10T12:00:00+00:00",
      "status": "PUBLISHED",
      "category": {
        "categoryId": 3,
        "name": "Workshop"
      },
      "organizer": {
        "userId": 20,
        "fullName": "Computer Science Club"
      }
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

ต้องการกรอง/ค้นหา/จัดเรียงให้ใส่ query string เช่น:
`GET /api/v1/events?search=python&categoryId=3&status=PUBLISHED&startFrom=2026-04-01T00:00:00Z&endTo=2026-04-30T23:59:59Z&sortBy=startTime&sortOrder=asc`

---

#### **1️⃣6️⃣ Events: Create (ORGANIZER / ADMIN)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/events`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
Content-Type: application/json
```
**Body:**
```json
{
  "title": "Python Workshop",
  "description": "เวิร์กชอป Python เบื้องต้น",
  "shortDescription": "ลงมือทำจริง",
  "locationName": "SCI Building Room 501",
  "latitude": 15.120245,
  "longitude": 104.906928,
  "startTime": "2026-04-10T09:00:00+07:00",
  "endTime": "2026-04-10T12:00:00+07:00",
  "categoryId": 3,
  "coverImageUrl": "https://example.com/python.jpg",
  "status": "DRAFT"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "สร้างกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "title": "Python Workshop",
    "status": "DRAFT",
    "categoryId": 3,
    "organizerId": 20
  }
}
```

---

#### **1️⃣7️⃣ Events: Update (Organizer Owner)**

**Method:** PATCH  
**URL:** `http://127.0.0.1:8000/api/v1/events/1001`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
Content-Type: application/json
```
**Body:**
```json
{
  "title": "Python Workshop Updated",
  "locationName": "SCI Building Room 502",
  "latitude": 15.120300,
  "longitude": 104.907000,
  "startTime": "2026-04-10T10:00:00+07:00",
  "endTime": "2026-04-10T13:00:00+07:00"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "แก้ไขกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "title": "Python Workshop Updated",
    "locationName": "SCI Building Room 502",
    "status": "DRAFT"
  }
}
```

---

#### **1️⃣8️⃣ Events: Delete (Organizer Owner)**

**Method:** DELETE  
**URL:** `http://127.0.0.1:8000/api/v1/events/1001`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ลบกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "deleted": true
  }
}
```

---

#### **1️⃣9️⃣ Events: Publish (ADMIN only)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/events/1001/publish`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "เผยแพร่กิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "status": "PUBLISHED"
  }
}
```

---

#### **2️⃣0️⃣ Events: Cancel (ADMIN or Organizer Owner)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/events/1001/cancel`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
Content-Type: application/json
```
**Body:**
```json
{
  "reason": "เลื่อนสถานที่จัดงาน"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "ยกเลิกกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "status": "CANCELLED",
    "reason": "เลื่อนสถานที่จัดงาน"
  }
}
```

---

#### **2️⃣1️⃣ Events: Detail (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/1001`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงรายละเอียดกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "title": "Python Workshop",
    "description": "A hands-on workshop",
    "shortDescription": "เรียนรู้ Python",
    "locationName": "SCI Building Room 501",
    "latitude": 14.87,
    "longitude": 102.01,
    "startTime": "2026-04-10T09:00:00+00:00",
    "endTime": "2026-04-10T12:00:00+00:00",
    "status": "PUBLISHED",
    "coverImageUrl": "https://example.com/workshop.jpg",
    "category": {
      "categoryId": 3,
      "name": "Workshop"
    },
    "organizer": {
      "userId": 20,
      "fullName": "Computer Science Club"
    },
    "savedCount": 12,
    "isSaved": true
  }
}
```

---

#### **2️⃣2️⃣ Events: My Events (Organizer Only)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/my-events?page=1&pageSize=10&status=PUBLISHED&search=python&sortBy=createdAt&sortOrder=desc`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงรายการกิจกรรมของผู้จัดสำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "status": "PUBLISHED",
      "savedCount": 17,
      "startTime": "2026-04-10T09:00:00+07:00",
      "endTime": "2026-04-10T12:00:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

---

#### **2️⃣3️⃣ Events: Nearby (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/nearby?latitude=15.120100&longitude=104.905800&radiusKm=5&categoryId=3&search=python&sortBy=distance&sortOrder=asc&page=1&pageSize=20`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงกิจกรรมใกล้ตัวสำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "locationName": "SCI Building Room 501",
      "latitude": 15.120245,
      "longitude": 104.906928,
      "distanceKm": 0.41,
      "startTime": "2026-04-10T09:00:00+07:00",
      "endTime": "2026-04-10T12:00:00+07:00",
      "category": {
        "categoryId": 3,
        "name": "Workshop"
      }
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

---

#### **2️⃣4️⃣ Events: Map (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/map?latitude=15.120100&longitude=104.905800&radiusKm=5&categoryId=3&search=python`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงข้อมูลแผนที่สำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "latitude": 15.120245,
      "longitude": 104.906928,
      "locationName": "SCI Building Room 501",
      "distanceKm": 0.41,
      "startTime": "2026-04-10T09:00:00+07:00"
    }
  ]
}
```

---

#### **2️⃣5️⃣ Events: Upcoming (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/upcoming?page=1&pageSize=10&categoryId=3&sortBy=startTime&sortOrder=asc`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงกิจกรรมที่กำลังจะมาถึงสำเร็จ",
  "data": [
    {
      "eventId": 1002,
      "title": "Hackathon Intro",
      "startTime": "2026-05-01T09:00:00+07:00",
      "endTime": "2026-05-01T12:00:00+07:00",
      "status": "PUBLISHED"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

---

#### **2️⃣6️⃣ Events: Active (Public)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/events/active?page=1&pageSize=10&categoryId=3&sortBy=startTime&sortOrder=asc`  
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงกิจกรรมที่ยัง active สำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "status": "PUBLISHED",
      "startTime": "2026-04-10T09:00:00+07:00",
      "endTime": "2026-04-10T12:00:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 1,
    "totalPages": 1
  }
}
```

---

#### **2️⃣7️⃣ Saved Events: Save Event (Student Only)**

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/v1/saved-events`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
Content-Type: application/json
```
**Body:**
```json
{
  "eventId": 1001
}
```

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "บันทึกกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "saved": true
  }
}
```

#### **2️⃣8️⃣ Saved Events: Get My Saved Events (Student Only)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/saved-events`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None

**Expected Response:**
```json
{
  "success": true,
  "message": "ดึงรายการกิจกรรมที่บันทึกไว้สำเร็จ",
  "data": [
    {
      "eventId": 1001,
      "title": "Python Workshop",
      "locationName": "SCI Building Room 501",
      "startTime": "2026-04-10T09:00:00+07:00",
      "endTime": "2026-04-10T12:00:00+07:00",
      "status": "PUBLISHED",
      "savedAt": "2026-03-27T12:30:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 1,
    "totalPages": 1
  }
}
```
ดึงรายการกิจกรรมที่บันทึกไว้ทั้งหมดพร้อม pagination
`GET /api/v1/saved-events?page=1&pageSize=10&status=PUBLISHED&sortBy=savedAt&sortOrder=desc`

---

#### **2️⃣9️⃣ Saved Events: Unsave Event (Student Only)**

**Method:** DELETE  
**URL:** `http://127.0.0.1:8000/api/v1/saved-events/{eventId}`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None  
**Path Param:** `eventId` — ID ของกิจกรรมที่ต้องการยกเลิกบันทึก

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "ยกเลิกบันทึกกิจกรรมสำเร็จ",
  "data": {
    "eventId": 1001,
    "saved": false
  }
}

```
---

#### **3️⃣0️⃣ Saved Events: Check Save Status (Student Only)**

**Method:** GET  
**URL:** `http://127.0.0.1:8000/api/v1/saved-events/check/{eventId}`  
**Headers:**
```
Authorization: Bearer {{accessToken}}
```
**Body:** None  
**Path Param:** `eventId` — ID ของกิจกรรมที่ต้องการตรวจสอบ

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "ตรวจสอบสถานะการบันทึกสำเร็จ",
  "data": {
    "eventId": 1001,
    "isSaved": true
  }
}
```

`isSaved` จะเป็น `false` ถ้านักศึกษายังไม่เคยบันทึก event นี้

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
  - Categories List → Create → Get Detail → Update → Deactivate
  - Events List → Detail → My Events / Nearby / Map / Upcoming / Active → Saved Events (POST) → Saved Events (GET) → Saved Events (DELETE) → Saved Events (Check)

3. **Postman Collection (Optional):**
   - จัดเก็บ request ทีละชุด เพื่อรัน automation test ได้

---

## 3) รันชุดทดสอบอัตโนมัติ (pytest)

รันทั้งหมด:

```bash
python -m pytest -q
```

รันเฉพาะไฟล์ทดสอบ auth:

```bash
python -m pytest tests/test_auth.py -q
```

รันเฉพาะไฟล์ทดสอบ categories:

```bash
python -m pytest tests/test_categories.py -q
```

รันเฉพาะไฟล์ทดสอบ saved events:

```bash
python -m pytest tests/test_savedEvent.py -q
```

ไฟล์ทดสอบหลัก:
- `tests/test_health.py`
- `tests/test_auth.py`
- `tests/test_categories.py`
- `tests/test_events.py`
- `tests/test_savedEvent.py`

## 4) คำสั่งปิดระบบ

ปิดเฉพาะ container:

```bash
docker compose down
```

ปิดและลบ volume (รีเซ็ตฐานข้อมูลทั้งหมด):

```bash
docker compose down -v
```
