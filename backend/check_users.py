import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
import models

db = SessionLocal()
try:
    users = db.query(models.User).all()

    if not users:
        print("NO USERS FOUND in the database! Please run 'python seed.py' again.")
    else:
        print(f"FOUND {len(users)} users in the database:")
        for u in users:
            print(f" - {u.email} (Role: {u.role})")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    db.close()
