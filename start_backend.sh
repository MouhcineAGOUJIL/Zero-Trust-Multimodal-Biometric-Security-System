#!/bin/bash
# Stop any existing backend process on port 8000
fuser -k 8000/tcp 2>/dev/null

# Activate virtual environment and run uvicorn
echo "🚀 Starting Backend Server (Zero Trust Biometric System)..."
source venv/bin/activate
./venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
