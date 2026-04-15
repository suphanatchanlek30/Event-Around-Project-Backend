# คู่มือ Deploy FastAPI ไป Render (ตั้งแต่เริ่มจนใช้งานจริง)

เอกสารนี้เป็นคู่มือแบบทำตามได้จริงสำหรับโปรเจกต์นี้ ตั้งแต่การเตรียม local environment ไปจนถึง deploy production บน Render

## 1) เป้าหมายของคู่มือนี้
- รัน backend ในเครื่องได้
- ใช้ PostgreSQL local ผ่าน Docker ระหว่างพัฒนา
- push โค้ดขึ้น GitHub
- deploy FastAPI ไป Render
- ใช้ Render PostgreSQL ใน production
- ทดสอบว่า frontend เรียก API ผ่าน public URL ได้

## 2) สิ่งที่ต้องมี
- GitHub repository
- Render account
- Python 3.11+
- Docker Desktop

## 3) เตรียม Local Development

### 3.1 เปิด virtual environment และติดตั้ง dependency

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3.2 เตรียมไฟล์ environment

คัดลอกจาก `.env.example` ไปเป็น `.env`

```powershell
Copy-Item .env.example .env
```

ตรวจว่าค่าหลักใน `.env` มีครบ:
- `APP_ENV=development`
- `APP_DEBUG=true`
- `DATABASE_URL=postgresql+psycopg://...localhost...`
- `CORS_ORIGINS` เป็น URL frontend local

### 3.3 เปิดฐานข้อมูล local

```powershell
docker compose up -d db
docker compose ps
```

### 3.4 รัน migration

```powershell
alembic upgrade head
```

### 3.5 รันแอป

```powershell
uvicorn app.main:app --reload
```

ทดสอบ health:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/health`

## 4) ตรวจคุณภาพโค้ดก่อน push

```powershell
make lint
make test
```

หรือรันตรง:

```powershell
ruff check app tests alembic/env.py
black --check app tests alembic/env.py
python -m pytest -ra -W default
```

## 5) Push ขึ้น GitHub

```powershell
git add .
git commit -m "prepare deploy to render"
git push origin <branch-name>
```

เปิด Pull Request เข้า `main` และรอ CI ผ่านก่อน merge

## 6) ตั้งค่า Render PostgreSQL

1. เข้า Render Dashboard
2. เลือก New > PostgreSQL
3. ตั้งชื่อ database เช่น `event-around-postgres`
4. เลือก region ที่ใกล้ผู้ใช้งาน
5. สร้าง database และรอสถานะพร้อมใช้งาน

Render จะสร้าง connection string ให้ เช่น `postgres://...`

หมายเหตุ: โปรเจกต์นี้รองรับและจะแปลงเป็น SQLAlchemy format อัตโนมัติ

## 7) ตั้งค่า Render Web Service

มี 2 วิธี

### วิธี A: ใช้ Blueprint จากไฟล์ `render.yaml` (แนะนำ)
1. ใน Render เลือก New > Blueprint
2. เลือก repo นี้
3. Render จะอ่านไฟล์ `render.yaml`
4. ตรวจค่าที่จะถูกสร้าง (web service + database)
5. กด Create

### วิธี B: สร้าง Web Service เอง
1. New > Web Service
2. เชื่อม GitHub repo
3. Runtime: Docker
4. Branch: `main`
5. Auto Deploy: On
6. Health Check Path: `/health`

## 8) ตั้งค่า Environment Variables บน Render

ตั้งค่าที่ Web Service:
- `APP_ENV=production`
- `APP_DEBUG=false`
- `API_V1_PREFIX=/api/v1`
- `DATABASE_URL=<Render PostgreSQL connection string>`
- `JWT_SECRET_KEY=<ค่า secret จริง ห้ามใช้ค่า default>`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `REFRESH_TOKEN_EXPIRE_DAYS=7`
- `CORS_ORIGINS=<frontend-url-จริง เช่น https://my-frontend.vercel.app>`

สำคัญ:
- production secret เก็บบน Render เท่านั้น
- ห้าม commit secret ลง repo

## 9) Migration ตอน deploy

โปรเจกต์นี้กำหนด `preDeployCommand: alembic upgrade head` ใน `render.yaml` แล้ว

ผลคือทุกครั้งที่ deploy Render จะอัปเดต schema ก่อนสตาร์ตแอป

## 10) ทดสอบหลัง deploy

หลัง deploy สำเร็จ ให้ทดสอบ:
1. `GET https://<your-render-url>/health`
2. `GET https://<your-render-url>/api/v1/health`
3. ทดสอบ endpoint auth/events จาก Postman
4. ตรวจ CORS โดยเรียกจาก frontend จริง

## 11) เชื่อม frontend กับ backend production

เปลี่ยนค่า base API ของ frontend ไปเป็น:

```text
https://<your-render-url>
```

ถ้า frontend เรียก API ไม่ได้ ให้เช็ก:
- CORS_ORIGINS ครอบคลุม domain frontend หรือยัง
- frontend เรียก path ถูกต้อง เช่น `/api/v1/...`
- token ถูกส่งใน Authorization header หรือไม่

## 12) CI/CD ที่ใช้งานในโปรเจกต์นี้

- CI: GitHub Actions จากไฟล์ `.github/workflows/ci.yml`
- CD: Render auto deploy หลัง merge เข้า `main`

แนวทางที่แนะนำ:
- ใช้ branch strategy: `feature/*` -> PR -> `main`
- บังคับ required checks ก่อน merge
- protected branch ที่ `main`

## 13) แยก Local vs Production ให้ชัด

Local:
- ใช้ `.env` และ Docker PostgreSQL
- เปิด debug ได้
- CORS เป็น localhost

Production:
- ใช้ Render Environment Variables
- ใช้ Render PostgreSQL
- ปิด debug
- CORS จำกัดเฉพาะ frontend URL จริง

## 14) ปัญหาที่เจอบ่อย

1. ใช้ `localhost` ใน production
- แก้: ใช้ `DATABASE_URL` จาก Render เท่านั้น

2. deploy ผ่าน แต่ frontend เรียกไม่ได้
- แก้: ตรวจ `CORS_ORIGINS` และ base URL ของ frontend

3. migration ไม่ผ่านตอน deploy
- แก้: เปิด logs ใน Render และทดสอบ `alembic upgrade head` ใน local ให้ผ่านก่อน

4. secret หลุดเข้า repo
- แก้: ใช้ `.env.example` สำหรับตัวอย่างเท่านั้น และย้ายค่าจริงไป Render

## 15) คำสั่งสรุปแบบรวดเร็ว

เตรียม local:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

ตรวจคุณภาพก่อน merge:

```powershell
make lint
make test
```

หลัง merge main:
- Render auto deploy จะทำงานอัตโนมัติ
- ตรวจ health ที่ `/health`
- นำ URL ไปตั้งใน frontend

---

ถ้าต้องการแยก environment เพิ่ม (staging/production) ให้เพิ่มอีก 1 Render Web Service สำหรับ staging และตั้ง branch เป็น `develop` หรือ `staging` โดยใช้ตัวแปรแยกชุด
