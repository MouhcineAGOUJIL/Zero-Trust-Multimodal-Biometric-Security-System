import sys
import os

# Add current directory to path so we can import 'backend'
sys.path.append(os.getcwd())

try:
    from backend.database import engine
    from backend import models
    
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Schema Created Successfully in biosec.db")
except Exception as e:
    print(f"Error: {e}")
