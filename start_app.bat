@echo off
echo ========================================
echo   Platform Detektor Plagiarisme Launcher
echo ========================================

echo 1. Starting Flask App...
start "Flask App" cmd /k "python app.py"

echo Waiting for Flask to start...
timeout /t 5

echo 2. Starting Ngrok...
echo    (Pastikan Anda sudah login ngrok di terminal ini sebelumnya)
start "Ngrok Tunnel" cmd /k "ngrok http 5000"

echo.
echo ========================================
echo   Aplikasi Berjalan!
echo   1. Flask Local: http://127.0.0.1:5000
echo   2. Cek window Ngrok untuk Public URL
echo   3. JANGAN TUTUP window Flask atau Ngrok
echo ========================================
pause
