@echo off
title PyCk Installer
echo.
echo ========================================================
echo             PyCk Windows Global Installer
echo ========================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python and try again.
    pause
    exit /b 1
)

python setup.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] PyCk has been successfully installed globally on Windows!
echo.
pause
