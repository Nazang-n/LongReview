from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def list_users():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Role: {u.user_role}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
