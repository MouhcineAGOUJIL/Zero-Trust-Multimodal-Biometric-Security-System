import sys
import os
from sqlalchemy import create_engine, text

# Force absolute path to avoid confusion
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "biosec.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

print(f"[Diagnose] Expected DB Path: {DB_PATH}")

if os.path.exists(DB_PATH):
    print(f"[Diagnose] File exists. Permissions: {oct(os.stat(DB_PATH).st_mode)}")
else:
    print("[Diagnose] File does NOT exist. Attempting creation...")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("[Diagnose] Connection successful.")
        conn.execute(text("CREATE TABLE IF NOT EXISTS test (id int)"))
        conn.execute(text("INSERT INTO test VALUES (1)"))
        conn.commit()
        print("[Diagnose] Write successful.")
except Exception as e:
    print(f"[Diagnose] FAILED: {e}")

# Check directory permissions
print(f"[Diagnose] Directory '{BASE_DIR}' Writable: {os.access(BASE_DIR, os.W_OK)}")
