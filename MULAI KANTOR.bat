@echo off
title Kantor Marketing AI
echo ============================================
echo   KANTOR MARKETING AI - Mulai Semua
echo ============================================
echo.

:: Cek Python
where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan! Install Python dulu.
    pause
    exit /b
)

echo [+] Menjalankan Kantor Marketing + Otak Luar...
echo     Tutup jendela ini untuk menghentikan semua.
echo.
py "%~dp0mulai_kantor.py"

pause

