@echo off
echo ========================================
echo   Platform Detektor Plagiarisme Launcher
echo ========================================

echo 1. Starting Flask App...
start "Flask App" cmd /k "call venv\Scripts\activate & python app.py"

echo Waiting for Flask to start...
timeout /t 5

echo.
echo ========================================
echo   Aplikasi Berjalan!
echo   1. Akses Browser: http://127.0.0.1:5000
echo   2. JANGAN TUTUP window Flask (Window hitam)
echo ========================================
pause
