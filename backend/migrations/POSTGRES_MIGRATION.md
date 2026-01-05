# PostgreSQL Migration - Simple Instructions

## You're using PostgreSQL! Here's the easiest way:

### Option 1: Using pgAdmin (Recommended - Easiest!)

1. Open **pgAdmin**
2. Connect to your PostgreSQL server
3. Navigate to: **Databases → longreview → Schemas → public → Tables → game**
4. Right-click on **game** table → **Query Tool**
5. Paste this SQL and click **Execute** (F5):

```sql
ALTER TABLE game ADD COLUMN last_review_fetch TIMESTAMP NULL;
```

6. Done! ✓

---

### Option 2: Using psql Command Line

```bash
psql -U postgres -d longreview -c "ALTER TABLE game ADD COLUMN last_review_fetch TIMESTAMP NULL;"
```

---

### Option 3: Update Python Script with Your Password

Edit `migrations/add_last_review_fetch.py` line 11:
```python
password="YOUR_POSTGRES_PASSWORD_HERE",
```

Then run:
```bash
python migrations\add_last_review_fetch.py
```

---

## After Migration

Just restart your backend:
```bash
cd c:\Undertaker\LongReview\backend
python -m uvicorn app.main:app --reload
```

The review scheduler will start automatically! 🎉
