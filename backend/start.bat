@echo off
REM PaperHub Backend Startup Script (Windows)

cd /d "%~dp0"

echo =========================================
echo    PaperHub - Backend Server
echo =========================================
echo.

REM 使用指定的 Python 解释器
set PYTHON=C:\opt\anaconda3\envs\py38\python.exe

echo Using Python: %PYTHON%
echo.

echo Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt

echo.
echo Starting server...
echo Access: http://localhost:5799
echo.
"%PYTHON%" app.py 5799