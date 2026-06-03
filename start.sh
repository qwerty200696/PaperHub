#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========================================="
echo "   PaperHub - Starting Server"
echo "========================================="

PORT=${PORT:-5799}

# Try python3 first, fall back to python
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "ERROR: Neither python3 nor python found"
    echo "Available commands:"
    ls /usr/bin/python* 2>/dev/null || echo "No python binaries found"
    exit 1
fi

echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"
echo "Installing dependencies..."
$PYTHON -m pip install -r backend/requirements.txt

echo ""
echo "Starting server on port $PORT..."
$PYTHON -c "
from backend.app import create_app
app = create_app('production')
app.run(host='0.0.0.0', port=$PORT)
"
