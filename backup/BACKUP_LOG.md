# 백업 로그
백업 날짜: 2025-09-25

## 백업된 파일 목록

### tools/ 디렉토리에서 이동된 파일

#### 초기 테스트 및 개발 파일
- `simple_auto_responder.py` - 초기 단순 자동응답기 (현재 smart_auto_responder.py로 대체)
- `realtime_notifier.py` - 실시간 알림기 (현재 proactive_auto_responder.py로 통합)
- `realtime_notifier_multi.py` - 멀티 인스턴스 알림기 (현재 proactive_auto_responder.py로 통합)
- `multi_instance_responder.py` - 멀티 인스턴스 응답기 (현재 proactive_auto_responder.py로 통합)

#### 테스트 스크립트
- `interactive_test.py` - 대화형 테스트 스크립트
- `test_bidirectional.py` - 양방향 통신 테스트

#### Windows 배치 파일
- `add_to_startup.bat` - 시작프로그램 추가 배치파일
- `install_as_service.bat` - 서비스 설치 배치파일
- `setup_auto_check.bat` - 자동 확인 설정 배치파일

### 루트 디렉토리에서 이동된 파일

#### 테스트 및 임시 파일
- `message_to_lm.txt` - 테스트 메시지 파일
- `registration.txt` - 테스트 등록 파일
- `NUL` - 빈 파일

#### 초기 실행 스크립트
- `run_message.py` - 메시지 전송 실행 스크립트
- `run_register.py` - 인스턴스 등록 실행 스크립트
- `start_all.py` - 전체 시작 스크립트 (현재 start_proactive_all.py로 대체)

## 현재 활성 파일

### 핵심 도구 (tools/)
- `proactive_auto_responder.py` - 능동적 자동응답기 (모든 인스턴스가 자동으로 메시지 송수신)
- `smart_auto_responder.py` - 스마트 자동응답기 (무한 루프 방지 기능)
- `ipc_manager.py` - 통합 관리 유틸리티
- `ipc_check.py`, `ipc_list.py`, `ipc_register.py`, `ipc_rename.py`, `ipc_send.py` - IPC 개별 도구
- `ipc_auto_check_manager.py` - 자동 확인 관리자
- `fix_database.py` - 데이터베이스 수정 도구

### 실행 스크립트 (루트)
- `start_proactive_all.py` - 모든 인스턴스를 능동적 모드로 시작

## 백업 이유
- 기능이 통합되어 더 이상 필요하지 않은 초기 구현체들
- 테스트 목적으로만 사용되었던 스크립트들
- 현재 시스템에서 활발히 사용되지 않는 보조 도구들

## 복원 방법
필요시 backup 폴더에서 원래 위치로 파일을 복사하면 됩니다:
```bash
# 예: realtime_notifier.py 복원
cp backup/tools/realtime_notifier.py tools/
```