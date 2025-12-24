from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zero Trust Biometric API",
    description="Backend API for Multimodal BioHashing System",
    version="1.0"
)

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"status": "System Operational", "mode": "Zero Trust Active"}
