# 프로젝트 정리 분석 - 2024-09-26

## 핵심 파일 (유지)

### 1. 코어 시스템
- `src/claude_ipc_server.py` - MCP 서버 (핵심)
- `tools/ipc_*.py` - 기본 IPC 도구들
- `pyproject.toml` - 프로젝트 설정
- `README.md` - 프로젝트 문서

### 2. 필수 도구 (tools/)
- `tools/auto_responder.py` - 기본 자동 응답기
- `tools/monitor_instance.py` - 인스턴스 모니터링

## 중복/테스트 파일 (백업 필요)

### 1. Responder 중복 (19개 파일!)
**문제**: 같은 기능을 하는 responder가 너무 많음
- `ai_powered_responder.py`
- `fixed_ai_responder.py`
- `safe_autoresponder.py`
- `optimized_auto_responder.py`
- `korean_responder.py`
- `simple_responder.py`
- `simple_test_responder.py`
- `standalone_responder.py`
→ **해결**: `tools/auto_responder.py` 하나만 유지

### 2. Monitor 중복
- `clean_monitor.py`
- `monitor_with_responders.py`
- `start_monitoring.py`
- `start_split_monitoring.py`
- `start_safe_4panel_monitor.py`
→ **해결**: `tools/monitor_instance.py` 하나만 유지

### 3. Startup 스크립트 과다 (21개!)
**문제**: 너무 많은 시작 스크립트
- `start_4monitors.bat`
- `start_4panel_fixed.bat`
- `start_4panel_monitor.bat`
- `start_4split.ps1`
- `start_4split_fixed.bat`
- `start_4windows.bat`
- `start_ai_ipc_system.bat`
- `start_auto_responders.bat`
- `start_clean_monitor.bat`
- `start_fixed_ai_system.bat`
- `start_global_ipc.bat`
- `start_ipc_system.bat`
- `start_safe_auto_responders.bat`
- `start_safe_ipc_system.bat`
- `start_simple_responders.bat`
→ **해결**: `start_ipc_system.bat` 하나만 유지

### 4. 잘못된 파일명
- `D:claude-ipc-mcpstart_4panel_monitor.bat` (경로 문제)
- `D:claude-ipc-mcptoolsmonitor_instance.py` (경로 문제)
- `nul` (더미 파일)

### 5. 테스트/개발 파일
- `test_*.py` (테스트용)
- `check_response_issue.py`
- `send_and_check.py`
- `fresh_start.py`
- `clear_messages.py`

### 6. 중복 설정 파일
- `.mcp.json.backup`
- `instances.json`
- `messages.json`
- `ipc_messages.db` (빈 파일)

## 정리 계획

1. **백업 폴더 생성**: `backup/redundant_2024-09-26/`
2. **중복 파일 이동**: 위 리스트의 파일들을 백업 폴더로
3. **핵심 파일 유지**:
   - MCP 서버 (`src/`)
   - 기본 도구 (`tools/ipc_*.py`)
   - 하나의 자동 응답기
   - 하나의 모니터
   - 하나의 시작 스크립트
4. **문서 정리**: 불필요한 가이드 통합

## 예상 결과

**Before**: 100+ 파일 (중복과 혼란)
**After**: ~20개 핵심 파일 (명확한 구조)

## 핵심 기능 확인
- ✅ AI 간 메시지 전송/수신
- ✅ 자동 응답
- ✅ 메시지 영속성
- ✅ 세션 관리