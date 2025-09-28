@echo off
title Auto-Responders for IPC
echo Starting auto-responders...
echo.

REM Start responders for each instance
start /min cmd /k python simple_responder.py gemini
start /min cmd /k python simple_responder.py codex
start /min cmd /k python simple_responder.py lm

echo Auto-responders started!
echo.
echo Press any key to stop them...
pause > nul

taskkill /F /FI "WINDOWTITLE eq *simple_responder*" 2>nul
echo Stopped.