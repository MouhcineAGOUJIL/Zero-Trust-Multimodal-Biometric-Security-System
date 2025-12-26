
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal, engine
from backend import models

def check_db():
    print(f"Checking DB at: {os.path.abspath('biosec.db')}")
    if not os.path.exists('biosec.db'):
        print("ERROR: biosec.db file does not exist!")
        return

    session = SessionLocal()
    try:
        users = session.query(models.User).all()
        print(f"Found {len(users)} users.")
        for u in users:
            print(f" - ID: {u.id}, Username: {u.username}")
            
        templates = session.query(models.BiometricTemplate).all()
        print(f"Found {len(templates)} templates.")
        for t in templates:
            print(f" - Tpl ID: {t.id}, User ID: {t.user_id}")
            if t.fingerprint_vault: print(f"   Finger Vault: Yes ({len(t.fingerprint_vault)} bytes)")
            if t.palm_vault: print(f"   Palm Vault: Yes ({len(t.palm_vault)} bytes)")
            
    except Exception as e:
        print(f"Query failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_db()
