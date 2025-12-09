# LongReview Backend API

Backend API สำหรับ LongReview - แพลตฟอร์มรีวิวเกม

## เทคโนโลยีที่ใช้

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM สำหรับจัดการ database
- **PostgreSQL** - Database
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

## การติดตั้ง

### 1. สร้าง Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment Variables

แก้ไขไฟล์ `.env` ตามความต้องการ:

```env
DATABASE_URL=postgresql://postgres:17082546@localhost:5432/LongReview
CORS_ORIGINS=http://localhost:4200
HOST=0.0.0.0
PORT=8000
```

## การรัน Server

```bash
# รันด้วย uvicorn (แนะนำ)
uvicorn app.main:app --reload --port 8000

# หรือรันด้วย Python
python -m app.main
```

Server จะรันที่: `http://localhost:8000`

## API Documentation

เมื่อ server รันแล้ว สามารถเข้าถึง API documentation ได้ที่:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Games

- `GET /api/games/` - ดึงรายการเกมทั้งหมด
- `GET /api/games/{id}` - ดึงข้อมูลเกมตาม ID
- `POST /api/games/` - สร้างเกมใหม่
- `PUT /api/games/{id}` - อัพเดทข้อมูลเกม
- `DELETE /api/games/{id}` - ลบเกม
- `GET /api/games/search/?query={text}` - ค้นหาเกม

### Reviews

- `GET /api/reviews/` - ดึงรายการรีวิวทั้งหมด
- `GET /api/reviews/{id}` - ดึงข้อมูลรีวิวตาม ID
- `GET /api/reviews/game/{game_id}` - ดึงรีวิวของเกมที่ระบุ
- `POST /api/reviews/` - สร้างรีวิวใหม่
- `PUT /api/reviews/{id}` - อัพเดทรีวิว
- `DELETE /api/reviews/{id}` - ลบรีวิว

### Health Check

- `GET /` - Root endpoint
- `GET /health` - Health check

## โครงสร้างโปรเจกต์

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── database.py       # Database configuration
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       ├── games.py      # Game endpoints
│       └── reviews.py    # Review endpoints
├── .env                  # Environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Database Models

### User
- id, username, email, password_hash
- created_at, updated_at, is_active

### Game
- id, title, description, genre, rating
- image_url, release_date, developer, publisher
- created_at, updated_at

### Review
- id, game_id, user_id, title, content, rating
- created_at, updated_at

## การพัฒนา

### ติดตั้ง Dependencies เพิ่มเติม

```bash
pip install <package-name>
pip freeze > requirements.txt
```

### Database Migrations

SQLAlchemy จะสร้าง tables อัตโนมัติเมื่อรัน server ครั้งแรก

หากต้องการใช้ Alembic สำหรับ migrations:

```bash
pip install alembic
alembic init alembic
```

## Production

สำหรับ production แนะนำให้:

1. ปิด `echo=True` ใน `database.py`
2. ใช้ environment variables ที่ปลอดภัย
3. ตั้งค่า CORS ให้เฉพาะเจาะจง
4. ใช้ HTTPS
5. เพิ่ม rate limiting และ authentication
