@echo off
REM PaperHub Backend Startup Script (Windows)

cd /d "%~dp0"

echo =========================================
echo    PaperHub - Backend Server
echo =========================================
echo.

REM 使用 python3
set PYTHON=python

echo Using Python: %PYTHON%
echo.

echo Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt

echo.
echo Starting server...
echo Access: http://localhost:5799
echo.
"%PYTHON%" app.py 5799