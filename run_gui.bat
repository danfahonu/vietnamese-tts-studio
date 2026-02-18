@echo off
chcp 65001 >nul 2>&1
REM Vietnamese TTS Studio — Trình khởi chạy
REM ═══════════════════════════════════════

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║    Vietnamese TTS Studio v2.0             ║
echo   ║    Chuyển văn bản thành giọng nói         ║
echo   ╚══════════════════════════════════════════╝
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   [LỖI] Chưa cài đặt Python!
    echo   Vui lòng tải Python tại: https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo   [OK] Đã tìm thấy Python
echo.

REM Kiểm tra và cài đặt thư viện
echo   Đang kiểm tra thư viện cần thiết...
pip show customtkinter >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Đang cài đặt các thư viện cần thiết...
    pip install -r requirements_gui.txt
    echo.
)

echo.
echo   Đang khởi động ứng dụng...
echo.

REM Chạy ứng dụng
python tts_gui.py

REM Kiểm tra lỗi
if errorlevel 1 (
    echo.
    echo   [LỖI] Ứng dụng gặp sự cố!
    echo.
)

pause
