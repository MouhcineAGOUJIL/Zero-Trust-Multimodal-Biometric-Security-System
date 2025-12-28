#!/bin/bash

echo "🔄 Resetting Biometric Security Database..."

# 1. Stop Backend (Optional, but good practice if running in background)
# fuser -k 8000/tcp 2>/dev/null

# 2. Remove SQLite Database Files
if [ -f "biosec.db" ]; then
    rm biosec.db
    echo "✅ Deleted biosec.db (Root)"
fi

if [ -f "backend/biosec.db" ]; then
    rm backend/biosec.db
    echo "✅ Deleted backend/biosec.db"
fi

# 3. Clear any temporary image stores if they exist (based on previous exploration)
if [ -d "backend/biometric_store" ]; then
    rm -rf backend/biometric_store
    echo "✅ Cleared biometric_store"
fi

echo "✨ Database Reset Successfully."
echo "   The backend will recreate a fresh database on the next startup."
echo "   Please restart the backend now: ./start_backend.sh"
