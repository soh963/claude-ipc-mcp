@echo off
REM ================================================================
REM  AI-POWERED IPC SYSTEM
REM  실제 AI를 사용한 자동응답 시스템
REM ================================================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║         AI-POWERED IPC SYSTEM WITH REAL AI              ║
echo ║                                                          ║
echo ║  Starting all instances with AI responders...           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d D:\claude-ipc-mcp

REM Check if Ollama is running
echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama is running
    echo.

    REM Check available models
    echo Available Ollama models:
    curl -s http://localhost:11434/api/tags | python -c "import sys, json; models = json.load(sys.stdin).get('models', []); [print(f'  - {m[\"name\"]}') for m in models] if models else print('  No models found. Run: ollama pull llama3.2')"
) else (
    echo ⚠️ Ollama not running. Starting Ollama...
    start /B ollama serve
    timeout /t 3 /nobreak > nul

    echo.
    echo 📦 Pulling default model (llama3.2)...
    ollama pull llama3.2
)

echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM Register all instances
echo 📝 Registering instances...
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm

echo.
echo 🤖 Starting AI-powered responders...
echo.

REM Start AI responders with different models if available
start "Claude AI Responder" cmd /k python ai_powered_responder.py claude
timeout /t 1 /nobreak > nul

start "Gemini AI Responder" cmd /k python ai_powered_responder.py gemini
timeout /t 1 /nobreak > nul

start "Codex AI Responder" cmd /k python ai_powered_responder.py codex
timeout /t 1 /nobreak > nul

start "LM AI Responder" cmd /k python ai_powered_responder.py lm

echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo ✅ AI-Powered IPC System Started!
echo.
echo 📌 Features:
echo    - Real AI responses using Ollama/OpenAI/Gemini
echo    - Conversation context awareness
echo    - Instance-specific personas
echo    - Intelligent message processing
echo.
echo 💡 To send a message:
echo    python tools/ipc_send.py claude gemini "Your message"
echo.
echo 🔧 To check Ollama models:
echo    ollama list
echo.
echo 📥 To pull new models:
echo    ollama pull llama3.2
echo    ollama pull mistral
echo    ollama pull codellama
echo.
pause