#!/usr/bin/env python3
"""
Local IPC Broker - Unix Socket/Named Pipe based

절대 규칙 준수:
- .ipc/broker/ 에서만 실행
- Unix socket (Linux/Mac) 또는 Named Pipe (Windows) 사용
- TCP 포트 사용 금지
- 프로젝트별 완전 격리
"""

import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
import platform

# Windows Named Pipe 지원
if platform.system() == "Windows":
    import win32pipe
    import win32file
    import pywintypes
else:
    import socket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LocalBroker:
    """
    로컬 IPC 브로커 - .ipc/broker/ 전용

    절대 규칙:
    1. .ipc/broker/ 에서만 실행
    2. Unix socket 또는 Named Pipe 사용
    3. 프로젝트별 완전 격리
    4. TCP 포트 사용 금지
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ipc_root = project_root / ".ipc"
        self.broker_dir = self.ipc_root / "broker"
        self.state_dir = self.ipc_root / "state"

        # 필수 디렉토리 생성
        self.broker_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # 플랫폼별 통신 설정
        self.platform = platform.system()
        if self.platform == "Windows":
            self.pipe_name = f"\\\\.\\pipe\\ipc_{project_root.name}"
            self.socket_path = None
        else:
            self.socket_path = self.broker_dir / "broker.sock"
            self.pipe_name = None

        # 데이터베이스 경로 (절대 규칙: .ipc/state/messages.db)
        self.db_path = self.state_dir / "messages.db"

        # PID 파일 경로
        self.pid_file = self.broker_dir / "broker.pid"

        # 로그 파일
        self.log_file = self.broker_dir / "broker.log"

        # 인스턴스 및 세션 저장소
        self.instances: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, str] = {}  # session_token -> instance_id

        # DB 초기화
        self._init_database()

        logger.info(f"Local broker initialized for project: {project_root}")
        logger.info(f"Database: {self.db_path}")
        if self.platform == "Windows":
            logger.info(f"Named Pipe: {self.pipe_name}")
        else:
            logger.info(f"Unix Socket: {self.socket_path}")

    def _init_database(self):
        """데이터베이스 초기화 (절대 규칙: .ipc/state/messages.db)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 인스턴스 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY,
                session_token_hash TEXT,
                last_seen TEXT,
                metadata TEXT
            )
        """)

        # 메시지 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                read INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized: {self.db_path}")

    def start(self):
        """브로커 시작 (Unix socket 또는 Named Pipe)"""
        # PID 파일 저장
        self.pid_file.write_text(str(os.getpid()))

        logger.info("Starting local broker...")

        if self.platform == "Windows":
            self._start_named_pipe()
        else:
            self._start_unix_socket()

    def _start_unix_socket(self):
        """Unix Socket 기반 브로커 시작"""
        # 기존 소켓 파일 제거
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Unix socket 생성
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(self.socket_path))
        sock.listen(5)

        # 권한 설정 (소유자만 접근)
        os.chmod(self.socket_path, 0o600)

        logger.info(f"Broker listening on: {self.socket_path}")

        try:
            while True:
                client_socket, _ = sock.accept()
                self._handle_client(client_socket)
        except KeyboardInterrupt:
            logger.info("Broker shutting down...")
        finally:
            sock.close()
            if self.socket_path.exists():
                self.socket_path.unlink()

    def _start_named_pipe(self):
        """Windows Named Pipe 기반 브로커 시작"""
        logger.info(f"Broker listening on: {self.pipe_name}")

        try:
            while True:
                # Named Pipe 생성
                pipe = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    65536,
                    65536,
                    0,
                    None
                )

                # 클라이언트 연결 대기
                win32pipe.ConnectNamedPipe(pipe, None)

                try:
                    # 요청 읽기
                    data = win32file.ReadFile(pipe, 65536)[1]

                    # 요청 처리
                    request = json.loads(data.decode("utf-8"))
                    response = self._process_request(request)

                    # 응답 전송
                    win32file.WriteFile(pipe, json.dumps(response).encode("utf-8"))

                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    error_response = {"status": "error", "message": str(e)}
                    win32file.WriteFile(pipe, json.dumps(error_response).encode("utf-8"))

                finally:
                    # 연결 종료
                    win32pipe.DisconnectNamedPipe(pipe)
                    win32file.CloseHandle(pipe)

        except KeyboardInterrupt:
            logger.info("Broker shutting down...")

    def _handle_client(self, client_socket):
        """클라이언트 요청 처리 (Unix socket)"""
        try:
            data = client_socket.recv(65536)
            if not data:
                return

            request = json.loads(data.decode("utf-8"))
            response = self._process_request(request)

            client_socket.send(json.dumps(response).encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            error_response = {"status": "error", "message": str(e)}
            client_socket.send(json.dumps(error_response).encode("utf-8"))
        finally:
            client_socket.close()

    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """요청 처리"""
        action = request.get("action")

        if action == "register":
            return self._handle_register(request)
        elif action == "send":
            return self._handle_send(request)
        elif action == "check":
            return self._handle_check(request)
        elif action == "list":
            return self._handle_list(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_register(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """인스턴스 등록"""
        instance_id = request.get("instance_id")
        if not instance_id:
            return {"status": "error", "message": "Missing instance_id"}

        # 세션 토큰 생성
        import hashlib
        import secrets

        session_token = secrets.token_hex(16)
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()

        # 인스턴스 저장
        self.instances[instance_id] = {
            "session_token_hash": token_hash,
            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        self.sessions[session_token] = instance_id

        # DB에 저장
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO instances (id, session_token_hash, last_seen) VALUES (?, ?, ?)",
            (instance_id, token_hash, self.instances[instance_id]["last_seen"])
        )
        conn.commit()
        conn.close()

        logger.info(f"Registered instance: {instance_id}")

        return {
            "status": "ok",
            "instance_id": instance_id,
            "session_token": session_token,
        }

    def _handle_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 전송"""
        session_token = request.get("session_token")
        from_id = request.get("from_id")
        to_id = request.get("to_id")
        message = request.get("message", {})
        content = message.get("content", "")

        # 세션 검증
        if session_token not in self.sessions:
            return {"status": "error", "message": "Invalid session token"}

        # DB에 메시지 저장
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (from_id, to_id, content, timestamp) VALUES (?, ?, ?, ?)",
            (from_id, to_id, content, time.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        conn.commit()
        conn.close()

        logger.info(f"Message sent: {from_id} -> {to_id}")

        return {"status": "ok"}

    def _handle_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 확인"""
        session_token = request.get("session_token")
        instance_id = request.get("instance_id")

        # 세션 검증
        if session_token not in self.sessions:
            return {"status": "error", "message": "Invalid session token"}

        # DB에서 메시지 조회
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, from_id, to_id, content, timestamp FROM messages WHERE to_id = ? AND read = 0",
            (instance_id,)
        )

        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "from": row[1],
                "to": row[2],
                "content": row[3],
                "timestamp": row[4],
            })

        # 메시지를 읽음으로 표시
        cursor.execute("UPDATE messages SET read = 1 WHERE to_id = ? AND read = 0", (instance_id,))
        conn.commit()
        conn.close()

        return {"status": "ok", "messages": messages}

    def _handle_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """인스턴스 목록 조회 (현재 프로젝트만)"""
        # DB에서 인스턴스 조회
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, session_token_hash, last_seen FROM instances")

        instances = []
        for row in cursor.fetchall():
            instances.append({
                "id": row[0],
                "session_token_hash": row[1],
                "last_seen": row[2],
            })

        conn.close()

        return {"status": "ok", "instances": instances}


def main():
    """메인 진입점"""
    # 프로젝트 루트 감지 (절대 규칙)
    project_root = os.getenv("IPC_PROJECT_ROOT")
    if not project_root:
        logger.error("IPC_PROJECT_ROOT environment variable not set")
        sys.exit(1)

    project_root = Path(project_root)

    # 로컬 브로커 시작
    broker = LocalBroker(project_root)
    broker.start()


if __name__ == "__main__":
    main()
