# Steam API Integration

ผมได้เพิ่ม Steam API integration ให้แล้วครับ! ตอนนี้คุณสามารถดึงข้อมูลจาก Steam ได้เลย

## ติดตั้ง requests library:

```powershell
cd c:\Project GameWeb\backend
.\venv\Scripts\activate
pip install requests
```

## Restart Backend Server:

กด Ctrl+C ใน terminal ที่รัน backend แล้วรันใหม่:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

## API Endpoints ใหม่:

### 1. ดึงรีวิวจาก Steam (ไม่บันทึก database)
```
GET /api/steam/reviews/570?language=thai&max_reviews=10
```

### 2. ดึงข้อมูลเกมจาก Steam
```
GET /api/steam/app/570
```

### 3. Import เกมจาก Steam เข้า Database
```
POST /api/steam/import/game/570
```

### 4. Import รีวิวจาก Steam เข้า Database
```
POST /api/steam/import/reviews/570?game_id=1&max_reviews=50
```

## ทดสอบ:

1. เปิด http://localhost:8000/docs
2. ลองใช้ endpoint `/api/steam/reviews/570` 
3. จะได้รีวิวภาษาไทยของ Dota 2 จาก Steam

**App ID ตัวอย่าง:**
- 570 = Dota 2
- 730 = CS:GO
- 1172470 = Apex Legends
