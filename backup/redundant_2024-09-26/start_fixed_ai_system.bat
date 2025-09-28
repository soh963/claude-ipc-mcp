@echo off
REM ================================================================
REM  FIXED AI IPC SYSTEM - 메시지 라우팅 버그 수정
REM ================================================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║      FIXED AI IPC SYSTEM (Routing Bug Fixed)            ║
echo ║                                                          ║
echo ║  Each instance processes ONLY its own messages          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d D:\claude-ipc-mcp

REM Check Ollama
echo 🔍 Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Ollama not running. Please start with: ollama serve
    echo.
    pause
    exit /b 1
)

echo ✅ Ollama is running
echo.

REM Register all instances
echo 📝 Registering instances...
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm
echo.

REM Clear any stuck messages
echo 🧹 Clearing stuck messages...
python -c "import sqlite3; from pathlib import Path; conn = sqlite3.connect(Path.home() / '.claude-ipc-data' / 'messages.db'); conn.execute('UPDATE messages SET read_flag = 1 WHERE read_flag = 0'); conn.commit(); print('Cleared old unread messages')"
echo.

REM Start fixed AI responders
echo 🤖 Starting FIXED AI responders...
echo.

start "Claude AI" cmd /k "python fixed_ai_responder.py claude"
timeout /t 1 /nobreak > nul

start "Gemini AI" cmd /k "python fixed_ai_responder.py gemini"
timeout /t 1 /nobreak > nul

start "Codex AI" cmd /k "python fixed_ai_responder.py codex"
timeout /t 1 /nobreak > nul

start "LM AI" cmd /k "python fixed_ai_responder.py lm"

echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo ✅ Fixed AI System Started!
echo.
echo 📌 What's Fixed:
echo    - Each instance processes ONLY messages sent TO them
echo    - No message routing confusion
echo    - Proper from/to handling
echo    - AI-powered intelligent responses
echo.
echo 🧪 Test it:
echo    python tools/ipc_send.py claude gemini "Hello Gemini!"
echo    python tools/ipc_send.py gemini claude "Hello Claude!"
echo.
pause