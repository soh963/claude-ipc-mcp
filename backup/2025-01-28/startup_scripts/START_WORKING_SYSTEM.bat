@echo off
echo === Starting Working IPC System ===
echo.

echo [Step 1] Starting IPC Server...
start "IPC Server" /MIN python src\claude_ipc_server.py
timeout /t 3 /nobreak >nul

echo [Step 2] Registering instances...
python tools\ipc_register.py claude
python tools\ipc_register.py gemini
python tools\ipc_register.py codex
python tools\ipc_register.py lm
python tools\ipc_register.py chatgpt
python tools\ipc_register.py llama

echo [Step 3] Starting auto-responders...
start "Auto-Responder: gemini" /MIN python tools\simple_auto_responder.py gemini
start "Auto-Responder: codex" /MIN python tools\simple_auto_responder.py codex
start "Auto-Responder: lm" /MIN python tools\simple_auto_responder.py lm
start "Auto-Responder: chatgpt" /MIN python tools\simple_auto_responder.py chatgpt
start "Auto-Responder: llama" /MIN python tools\simple_auto_responder.py llama
timeout /t 2 /nobreak >nul

echo [Step 4] Starting monitor...
start "IPC Monitor" python enhanced_monitor.py

echo.
echo === System Started Successfully ===
echo.
echo Test the system:
echo   python tools\ipc_send.py claude gemini "Hello!"
echo   python tools\ipc_check.py
echo.
pause