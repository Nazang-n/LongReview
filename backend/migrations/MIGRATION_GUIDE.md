# Quick Migration Guide

## Step 1: Start MySQL Server

**If using XAMPP:**
1. Open XAMPP Control Panel
2. Click "Start" next to MySQL
3. Wait for it to show "Running"

**If using standalone MySQL:**
1. Open Services (Windows + R, type `services.msc`)
2. Find "MySQL" or "MySQL80" service
3. Right-click → Start

## Step 2: Run the Migration

Once MySQL is running, choose ONE of these options:

### Option A: Using Python Script (Easiest)
```bash
cd c:\Undertaker\LongReview\backend
python migrations\add_last_review_fetch.py
```

### Option B: Using SQL File in phpMyAdmin
1. Open phpMyAdmin (usually http://localhost/phpmyadmin)
2. Click on `longreview` database
3. Click "SQL" tab
4. Copy this SQL and paste it:
```sql
ALTER TABLE game ADD COLUMN last_review_fetch DATETIME NULL AFTER steam_app_id;
```
5. Click "Go"

### Option C: Using MySQL Command Line
```bash
mysql -u root -p longreview < migrations\add_last_review_fetch.sql
```

## Step 3: Verify Migration

Run this SQL to check:
```sql
DESCRIBE game;
```

You should see `last_review_fetch` column in the list.

## Step 4: Restart Backend

After migration is complete:
```bash
cd c:\Undertaker\LongReview\backend
python -m uvicorn app.main:app --reload
```

The review scheduler will start automatically and run at 12 AM daily!

---

**That's it!** Once you complete these steps, the automated review fetching system will be active.
