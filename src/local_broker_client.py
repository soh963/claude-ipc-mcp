#!/usr/bin/env python3
"""
Local IPC Broker Client - Unix Socket/Named Pipe based

절대 규칙 준수:
- 프로젝트 루트 자동 감지
- .ipc 폴더 우선 참조
- Unix socket/Named Pipe 통신
- TCP 포트 사용 금지
"""

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

if platform.system() == "Windows":
    import win32file
    import win32pipe
    import pywintypes
else:
    import socket


def detect_project_root() -> Path:
    """
    프로젝트 루트 감지 (절대 규칙)

    우선순위:
    1. .ipc 폴더 검색
    2. .git 리포지토리 검색
    3. 프로젝트 마커 검색 (pyproject.toml, package.json 등)
    4. 현재 디렉토리 (기본값)
    """
    current = Path.cwd()

    # 1. .ipc 폴더 우선 검색
    for parent in [current, *current.parents]:
        if (parent / ".ipc").exists():
            return parent

    # 2. Git 리포지토리 검색
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent

    # 3. 프로젝트 마커 검색
    markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod"]
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent

    # 4. 현재 디렉토리 반환 (기본값)
    return current


def ensure_ipc_structure(project_root: Path) -> None:
    """
    .ipc 구조 자동 생성 (절대 규칙)

    생성 디렉토리:
    - .ipc/broker/   (브로커 실행 및 상태)
    - .ipc/state/    (데이터베이스)
    - .ipc/config/   (설정 파일)
    - .ipc/logs/     (로그)
    - .ipc/secret/   (인증 토큰)
    """
    ipc_root = project_root / ".ipc"

    directories = [
        ipc_root / "broker",
        ipc_root / "state",
        ipc_root / "config",
        ipc_root / "logs",
        ipc_root / "secret",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # 권한 설정 (소유자만 접근)
        os.chmod(directory, 0o700)

    # .gitignore 생성
    gitignore = ipc_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# IPC runtime files\n"
            "broker/\n"
            "state/\n"
            "logs/\n"
            "secret/\n"
            "!config/\n"
        )


def is_broker_running(project_root: Path) -> bool:
    """브로커 실행 중인지 확인"""
    pid_file = project_root / ".ipc" / "broker" / "broker.pid"

    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text())

        # 프로세스 존재 확인
        if platform.system() == "Windows":
            import psutil
            return psutil.pid_exists(pid)
        else:
            os.kill(pid, 0)
            return True
    except (ValueError, OSError, ProcessLookupError):
        return False


def start_local_broker(project_root: Path) -> bool:
    """
    로컬 브로커 시작 (절대 규칙)

    실행 위치: .ipc/broker/
    통신 방식: Unix socket (Linux/Mac) 또는 Named Pipe (Windows)
    """
    if is_broker_running(project_root):
        return True

    broker_dir = project_root / ".ipc" / "broker"
    broker_script = Path(__file__).parent / "local_broker.py"

    if not broker_script.exists():
        raise FileNotFoundError(f"Broker script not found: {broker_script}")

    # 환경변수 설정
    env = os.environ.copy()
    env["IPC_PROJECT_ROOT"] = str(project_root)

    # 브로커 시작
    if platform.system() == "Windows":
        # Windows: CREATE_NO_WINDOW 플래그로 백그라운드 실행
        creationflags = 0x08000000
    else:
        creationflags = 0

    subprocess.Popen(
        [sys.executable, str(broker_script)],
        cwd=str(broker_dir),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    # 브로커 시작 대기
    for _ in range(50):  # 최대 5초 대기
        time.sleep(0.1)
        if is_broker_running(project_root):
            return True

    return False


def send_request(project_root: Path, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    브로커에 요청 전송

    통신 방식:
    - Linux/Mac: Unix socket
    - Windows: Named Pipe
    """
    platform_name = platform.system()

    if platform_name == "Windows":
        return _send_request_windows(project_root, request)
    else:
        return _send_request_unix(project_root, request)


def _send_request_unix(project_root: Path, request: Dict[str, Any]) -> Dict[str, Any]:
    """Unix Socket으로 요청 전송 (improved error handling)"""
    socket_path = project_root / ".ipc" / "broker" / "broker.sock"

    if not socket_path.exists():
        return {"status": "error", "message": "Broker not running"}

    sock = None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(30.0)
        sock.connect(str(socket_path))

        # 요청 전송
        request_data = json.dumps(request).encode("utf-8")
        sock.send(request_data)

        # 응답 수신 (improved: larger buffer and better error handling)
        response_data = sock.recv(1048576)  # 1MB buffer for large responses

        if not response_data:
            return {"status": "error", "message": "Empty response from broker"}

        # Decode with error handling
        try:
            decoded_data = response_data.decode("utf-8")
        except UnicodeDecodeError as e:
            return {"status": "error", "message": f"Response decode error: {e}"}

        # Parse JSON with error handling
        try:
            return json.loads(decoded_data)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {e}, data: {decoded_data[:100]}"}

    except socket.timeout:
        return {"status": "error", "message": "Request timeout (30s)"}
    except ConnectionRefusedError:
        return {"status": "error", "message": "Broker not accepting connections"}
    except Exception as e:
        return {"status": "error", "message": f"Communication error: {str(e)}"}
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def _send_request_windows(project_root: Path, request: Dict[str, Any]) -> Dict[str, Any]:
    """Windows Named Pipe로 요청 전송 (improved error handling)"""
    pipe_name = f"\\\\.\\pipe\\ipc_{project_root.name}"

    handle = None
    try:
        # Named Pipe 연결
        handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        # 요청 전송
        request_data = json.dumps(request).encode("utf-8")
        win32file.WriteFile(handle, request_data)

        # 응답 수신 (improved: larger buffer and better error handling)
        result, data = win32file.ReadFile(handle, 1048576)  # 1MB buffer for large responses

        if not data:
            return {"status": "error", "message": "Empty response from broker"}

        # Decode with error handling
        try:
            decoded_data = data.decode("utf-8")
        except UnicodeDecodeError as e:
            return {"status": "error", "message": f"Response decode error: {e}"}

        # Parse JSON with error handling
        try:
            return json.loads(decoded_data)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {e}, data: {decoded_data[:100]}"}

    except pywintypes.error as e:
        error_code = e.args[0] if e.args else "unknown"
        if error_code == 2:  # ERROR_FILE_NOT_FOUND
            return {"status": "error", "message": "Broker not running (pipe not found)"}
        elif error_code == 231:  # ERROR_PIPE_BUSY
            return {"status": "error", "message": "Broker busy, please retry"}
        else:
            return {"status": "error", "message": f"Named pipe error ({error_code}): {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Communication error: {str(e)}"}
    finally:
        if handle:
            try:
                win32file.CloseHandle(handle)
            except Exception:
                pass


# 공개 API 함수들

def register(instance_id: str) -> Dict[str, Any]:
    """인스턴스 등록"""
    project_root = detect_project_root()
    ensure_ipc_structure(project_root)
    start_local_broker(project_root)

    request = {
        "action": "register",
        "instance_id": instance_id,
    }

    return send_request(project_root, request)


def send_message(session_token: str, from_id: str, to_id: str, content: str) -> Dict[str, Any]:
    """메시지 전송"""
    project_root = detect_project_root()

    request = {
        "action": "send",
        "session_token": session_token,
        "from_id": from_id,
        "to_id": to_id,
        "message": {"content": content},
    }

    return send_request(project_root, request)


def check_messages(session_token: str, instance_id: str) -> Dict[str, Any]:
    """메시지 확인"""
    project_root = detect_project_root()

    request = {
        "action": "check",
        "session_token": session_token,
        "instance_id": instance_id,
    }

    return send_request(project_root, request)


def list_instances() -> Dict[str, Any]:
    """인스턴스 목록 조회 (현재 프로젝트만)"""
    project_root = detect_project_root()

    # Auto-start broker if not running
    start_local_broker(project_root)

    request = {"action": "list"}

    return send_request(project_root, request)


def get_project_info() -> Dict[str, str]:
    """현재 프로젝트 정보 반환"""
    project_root = detect_project_root()

    return {
        "project_root": str(project_root),
        "ipc_dir": str(project_root / ".ipc"),
        "broker_running": str(is_broker_running(project_root)),
    }


# =============================================================================
# API Compatibility Wrappers (for CLI migration)
# =============================================================================

def send(session_token: str, from_id: str, to_id: str, content: str, **kwargs) -> Dict[str, Any]:
    """
    API compatibility wrapper for send_message()

    Matches old broker_client.send() signature for seamless CLI migration
    """
    return send_message(session_token, from_id, to_id, content)


def check(session_token: str, instance_id: str, **kwargs) -> Dict[str, Any]:
    """
    API compatibility wrapper for check_messages()

    Matches old broker_client.check() signature
    """
    return check_messages(session_token, instance_id)


def status(**kwargs) -> Dict[str, Any]:
    """
    Check local broker status

    Returns broker status following absolute rules (project-local broker)
    """
    project_root = detect_project_root()

    if is_broker_running(project_root):
        return {
            "status": "ok",
            "project_root": str(project_root),
            "broker_location": str(project_root / ".ipc" / "broker"),
        }
    else:
        return {
            "status": "error",
            "message": "Local broker not running",
            "project_root": str(project_root),
        }
