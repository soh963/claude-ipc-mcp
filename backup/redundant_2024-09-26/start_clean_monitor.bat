@echo off
title Clean IPC Monitor
echo ========================================
echo    🧹 IPC 클린 모니터 시작
echo ========================================
echo.
echo 1. 데이터베이스 초기화 중...
python clear_messages.py < nul
echo.
echo 2. 초기 인사 메시지 전송...
python fresh_start.py
echo.
echo 3. 4분할 모니터 시작...
echo.
timeout /t 2 /nobreak > nul
start start_4panel_monitor.bat
echo.
echo ✅ 깨끗한 상태로 시작되었습니다!
echo.
pause