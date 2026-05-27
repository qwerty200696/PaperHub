#!/bin/bash
# PaperHub Backend Startup Script

cd "$(dirname "$0")"

echo "========================================="
echo "   PaperHub - Backend Server"
echo "========================================="
echo ""

# 使用 python3
PYTHON="/opt/anaconda3/envs/py38/bin/python"

echo "Using Python: $PYTHON"
echo ""

echo "Installing dependencies..."
$PYTHON -m pip install -r requirements.txt

echo ""
echo "Starting server..."
echo "Access: http://localhost:5799"
echo ""
$PYTHON app.py 5799
