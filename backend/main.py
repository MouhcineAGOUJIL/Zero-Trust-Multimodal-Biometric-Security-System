from fastapi import FastAPI
from .database import engine, Base
from .routers import auth

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zero Trust Biometric API",
    description="Backend API for Multimodal BioHashing System",
    version="1.0"
)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"status": "System Operational", "mode": "Zero Trust Active"}
