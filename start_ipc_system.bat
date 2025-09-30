@echo off
setlocal ENABLEDELAYEDEXPANSION
REM ================================================================
REM  UNIFIED IPC SYSTEM LAUNCHER
REM  모든 인스턴스 등록 + 자동응답 실행
REM ================================================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║     UNIFIED IPC SYSTEM WITH AUTO-RESPONDERS             ║
echo ║                                                          ║
echo ║  Starting all instances with auto-responders...         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Change to repo root based on this script's folder
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Prefer the local venv Python if available; otherwise use system Python
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

REM Start the unified system (correct script name)
"%PYTHON_EXE%" start_all_ai_ipc.py

REM If error occurred
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error occurred while running the IPC system
    echo.
    pause
    exit /b %ERRORLEVEL%
)

REM Keep window open
pause