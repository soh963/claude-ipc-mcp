@echo off
REM ================================================================
REM  SAFE IPC SYSTEM - 무한루프 방지 버전
REM ================================================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║           SAFE IPC SYSTEM (Loop Prevention)             ║
echo ║                                                          ║
echo ║  Starting all instances with safe auto-responders...    ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d D:\claude-ipc-mcp

REM Register all instances first
echo Registering instances...
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm

echo.
echo Starting safe auto-responders in separate windows...

REM Start each responder in its own window
start "Claude Auto-Responder" cmd /k python safe_autoresponder.py claude
timeout /t 1 /nobreak > nul

start "Gemini Auto-Responder" cmd /k python safe_autoresponder.py gemini
timeout /t 1 /nobreak > nul

start "Codex Auto-Responder" cmd /k python safe_autoresponder.py codex
timeout /t 1 /nobreak > nul

start "LM Auto-Responder" cmd /k python safe_autoresponder.py lm

echo.
echo ✅ All instances started with safe auto-responders!
echo.
echo 📌 Features:
echo    - Infinite loop prevention
echo    - Duplicate message prevention
echo    - 5-second cooldown between responses
echo    - Auto-response pattern detection
echo.
echo Close this window to keep responders running.
pause