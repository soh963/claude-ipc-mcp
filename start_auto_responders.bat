@echo off
echo Starting Auto-Responders for All AI Instances...
echo ================================================

REM Start auto-responders in separate windows
start /min cmd /c "python tools\simple_auto_responder.py gemini"
timeout /t 1 /nobreak >nul
start /min cmd /c "python tools\simple_auto_responder.py codex"
timeout /t 1 /nobreak >nul
start /min cmd /c "python tools\simple_auto_responder.py lm"
timeout /t 1 /nobreak >nul
start /min cmd /c "python tools\simple_auto_responder.py chatgpt"
timeout /t 1 /nobreak >nul
start /min cmd /c "python tools\simple_auto_responder.py llama"

echo.
echo ✅ Auto-responders started for all instances!
echo.
echo To stop them, close the minimized windows or run:
echo   taskkill /F /IM python.exe
echo.
pause