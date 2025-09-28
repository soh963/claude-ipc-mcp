@echo off
chcp 65001 >nul
title AI CLI Integration System
cls

echo ====================================================
echo     AI CLI Integration System v1.0
echo     Unified Environment for Claude, Gemini, Codex
echo ====================================================
echo.

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Set working directory
cd /d "%~dp0"

:: Run setup if needed
if not exist "D:\.ai-cli-ipc" (
    echo First time setup detected...
    echo Running environment configuration...
    call powershell -ExecutionPolicy Bypass -File setup-ai-cli-env.ps1
    echo.
)

:: Main menu
:menu
echo.
echo Select an option:
echo ================
echo 1. Start IPC Server
echo 2. Launch Claude CLI
echo 3. Launch Gemini CLI
echo 4. Launch Codex CLI
echo 5. Interactive Chat Mode
echo 6. Test Connections
echo 7. Setup Environment
echo 8. Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto claude
if "%choice%"=="3" goto gemini
if "%choice%"=="4" goto codex
if "%choice%"=="5" goto chat
if "%choice%"=="6" goto test
if "%choice%"=="7" goto setup
if "%choice%"=="8" goto end

echo Invalid choice. Please try again.
goto menu

:start_server
echo.
echo Starting IPC Server...
start "IPC Server" node ipc-server.js
timeout /t 2 >nul
echo Server started in new window
goto menu

:claude
echo.
echo Launching Claude CLI...
start "Claude CLI" node ai-cli-client.js claude
goto menu

:gemini
echo.
echo Launching Gemini CLI...
start "Gemini CLI" node ai-cli-client.js gemini
goto menu

:codex
echo.
echo Launching Codex CLI...
start "Codex CLI" node ai-cli-client.js codex
goto menu

:chat
echo.
echo Starting Interactive Chat Mode...
node ai-cli.js chat
goto menu

:test
echo.
echo Running Connection Tests...
node test-connection.js
pause
goto menu

:setup
echo.
echo Running Environment Setup...
call powershell -ExecutionPolicy Bypass -File setup-ai-cli-env.ps1
pause
goto menu

:end
echo.
echo Thank you for using AI CLI Integration System!
echo Goodbye!
timeout /t 2 >nul
exit /b 0