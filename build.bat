@echo off
chcp 65001 > nul
echo ============================================
echo   Timer Reminder - Build Script
echo ============================================
echo.

REM Check Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/3] Building exe with PyInstaller...
pyinstaller --onefile --windowed --name "TimerReminder" --version-file version_info.txt --add-data "config.json;." --hidden-import pystray --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo [3/3] Build complete!
echo.
echo Output: dist\TimerReminder.exe
echo.
echo You can now run the exe or move it to your Startup folder:
echo   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
echo.

REM Clean up build artifacts
rmdir /s /q build 2> nul
del /q TimerReminder.spec 2> nul

echo Done!
pause
