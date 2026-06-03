#!/bin/bash
# PaperHub Backend Startup Script

cd "$(dirname "$0")"

echo "========================================="
echo "   PaperHub - Backend Server"
echo "========================================="
echo ""

# Use python3 from PATH (works on Railway and local envs)
PYTHON="$(command -v python3)"

echo "Using Python: $PYTHON"
echo ""

echo "Installing dependencies..."
$PYTHON -m pip install -r requirements.txt

echo ""
# Railway sets PORT env var; fall back to 5799
PORT="${PORT:-5799}"
echo "Starting server on port $PORT..."
echo ""
$PYTHON app.py $PORT
