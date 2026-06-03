#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========================================="
echo "   PaperHub - Starting Server"
echo "========================================="

PYTHON=${PYTHON:-python3}
PORT=${PORT:-5799}

echo "Installing dependencies..."
$PYTHON -m pip install -r backend/requirements.txt

echo "Starting server on port $PORT..."
$PYTHON -c "
from backend.app import create_app
app = create_app('production')
app.run(host='0.0.0.0', port=$PORT)
"
