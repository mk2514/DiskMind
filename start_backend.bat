@echo off
echo ============================================================
echo  DiskMind - Backend Startup
echo ============================================================

set PYTHON_SCRIPTS=C:\Users\sange\AppData\Local\Programs\Python\Python313\Scripts
set PYTHON_DIR=C:\Users\sange\AppData\Local\Programs\Python\Python313

REM Check what packages are available
echo.
echo Checking packages...
"%PYTHON_DIR%\Lib\site-packages\pip" list 2>nul

REM Install missing packages
echo.
echo Installing missing packages (if any)...
"%PYTHON_SCRIPTS%\pip.exe" install aiosqlite psutil scikit-learn joblib 2>nul

REM Generate demo data
echo.
echo Generating demo data...
cd /d "%~dp0"
"%PYTHON_SCRIPTS%\uvicorn.exe" --version

REM Start backend
echo.
echo Starting DiskMind backend on http://localhost:8000
echo Press Ctrl+C to stop
echo.
"%PYTHON_SCRIPTS%\uvicorn.exe" backend.main:app --reload --host 0.0.0.0 --port 8000
