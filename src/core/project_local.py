#!/usr/bin/env python3
"""
Project-Local IPC System
모든 IPC 데이터를 프로젝트 루트의 .ipc/ 폴더에 저장
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def detect_project_root(start_path: Path = None) -> Path:
    """
    프로젝트 루트 디렉토리 감지

    .git, .ipc, pyproject.toml, package.json 등의 마커 파일로 루트 찾기
    """
    current = start_path or Path.cwd()

    # 프로젝트 루트 마커들
    markers = [
        ".git",
        ".ipc",
        "pyproject.toml",
        "package.json",
        "setup.py",
        "Cargo.toml",
        "go.mod"
    ]

    # 최대 10단계까지 상위 디렉토리 검색
    for _ in range(10):
        if current == current.parent:
            # 루트 디렉토리까지 도달
            break

        # 마커 파일 존재 확인
        if any((current / marker).exists() for marker in markers):
            logger.info(f"Detected project root: {current}")
            return current

        current = current.parent

    # 마커를 찾지 못하면 현재 디렉토리 사용
    fallback = start_path or Path.cwd()
    logger.warning(f"No project markers found, using current directory: {fallback}")
    return fallback


def init_ipc_directory(project_root: Path) -> Path:
    """
    .ipc 디렉토리 구조 초기화

    Returns:
        Path: .ipc 디렉토리 경로
    """
    ipc_dir = project_root / ".ipc"

    # 서브디렉토리 생성
    subdirs = ["config", "data", "logs", "state", "secret"]
    for subdir in subdirs:
        (ipc_dir / subdir).mkdir(parents=True, exist_ok=True)

    # .gitignore 생성 (IPC 데이터는 버전 관리 제외)
    gitignore_path = ipc_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# IPC runtime data - do not commit
data/*.db
data/*.db-journal
data/*.db-wal
logs/*.log
state/*.pid
state/*.lock
state/*.json
secret/*

# Keep directory structure
!.gitignore
!config/
!data/.gitkeep
!logs/.gitkeep
!state/.gitkeep
!secret/.gitkeep
"""
        gitignore_path.write_text(gitignore_content)

    # .gitkeep 파일로 빈 디렉토리 유지
    for subdir in subdirs:
        gitkeep = ipc_dir / subdir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    logger.info(f"Initialized IPC directory: {ipc_dir}")
    return ipc_dir


def init_project_database(db_path: Path) -> None:
    """
    프로젝트 로컬 데이터베이스 초기화

    단일 데이터베이스에 모든 테이블 통합
    """
    with sqlite3.connect(db_path) as conn:
        # 인스턴스 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS instances (
                instance_id TEXT PRIMARY KEY,
                project_root TEXT NOT NULL,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME NOT NULL
            )
        """)

        # 세션 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_token_hash TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
            )
        """)

        # 메시지 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                delivered INTEGER DEFAULT 0,
                read_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 이름 변경 이력
        conn.execute("""
            CREATE TABLE IF NOT EXISTS name_history (
                old_name TEXT PRIMARY KEY,
                new_name TEXT NOT NULL,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 인덱스 생성
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_to_id
            ON messages(to_id, delivered)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_instance
            ON sessions(instance_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_instances_project
            ON instances(project_root)
        """)

        conn.commit()

    logger.info(f"Initialized project database: {db_path}")


def init_project_config(ipc_dir: Path, project_root: Path) -> Dict[str, Any]:
    """
    프로젝트 설정 파일 초기화
    """
    config_path = ipc_dir / "config" / "project.json"

    if config_path.exists():
        # 기존 설정 로드
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        # 프로젝트별 고유 포트 할당
        from core.project_port import get_or_create_project_port, get_project_id

        project_id = get_project_id(project_root)
        broker_port = get_or_create_project_port(project_root)

        # 새 설정 생성
        config = {
            "project_root": str(project_root),
            "project_name": project_root.name,
            "project_id": project_id,
            "broker_host": os.getenv("IPC_HOST", "127.0.0.1"),
            "broker_port": broker_port,
            "created_at": datetime.now().isoformat(),
            "version": "2.0.0"
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Created project config: {config_path} (ID: {project_id}, Port: {broker_port})")

    return config


def get_project_ipc_dir(project_root: Path = None) -> Path:
    """
    프로젝트 IPC 디렉토리 가져오기 (없으면 생성)

    Args:
        project_root: 프로젝트 루트 (None이면 자동 감지)

    Returns:
        Path: .ipc 디렉토리 경로
    """
    if project_root is None:
        project_root = detect_project_root()

    ipc_dir = project_root / ".ipc"

    # .ipc 디렉토리가 없으면 초기화
    if not ipc_dir.exists():
        init_ipc_directory(project_root)

        # 데이터베이스 초기화
        db_path = ipc_dir / "data" / "ipc.db"
        init_project_database(db_path)

        # 설정 초기화
        init_project_config(ipc_dir, project_root)

    return ipc_dir


def get_project_database() -> Path:
    """현재 프로젝트의 데이터베이스 경로 반환"""
    ipc_dir = get_project_ipc_dir()
    db_path = ipc_dir / "data" / "ipc.db"

    # 데이터베이스가 없으면 초기화
    if not db_path.exists():
        init_project_database(db_path)

    return db_path


def get_project_config() -> Dict[str, Any]:
    """현재 프로젝트 설정 반환"""
    ipc_dir = get_project_ipc_dir()
    config_path = ipc_dir / "config" / "project.json"

    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)

    # 설정이 없으면 생성
    project_root = ipc_dir.parent
    return init_project_config(ipc_dir, project_root)


def migrate_global_to_project(project_root: Path = None) -> bool:
    """
    전역 데이터를 프로젝트 로컬로 마이그레이션

    Returns:
        bool: 마이그레이션 성공 여부
    """
    if project_root is None:
        project_root = detect_project_root()

    # 전역 데이터베이스 경로
    global_db = Path.home() / ".claude-ipc-data" / "messages.db"

    if not global_db.exists():
        logger.info("No global database to migrate")
        return True

    # 프로젝트 로컬 준비
    ipc_dir = get_project_ipc_dir(project_root)
    project_db = ipc_dir / "data" / "ipc.db"

    try:
        with sqlite3.connect(project_db) as conn:
            # 전역 DB 연결
            conn.execute(f"ATTACH DATABASE '{global_db}' AS global")

            # 인스턴스 마이그레이션
            conn.execute("""
                INSERT OR REPLACE INTO instances (instance_id, project_root, registered_at, last_seen)
                SELECT instance_id, ?, registered_at, last_seen
                FROM global.instances
                WHERE instance_id NOT IN (SELECT instance_id FROM instances)
            """, (str(project_root),))

            # 메시지 마이그레이션 (중복 방지)
            conn.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp, delivered, created_at)
                SELECT from_id, to_id, content, timestamp, delivered, created_at
                FROM global.messages
                WHERE id NOT IN (
                    SELECT id FROM messages WHERE id IN (SELECT id FROM global.messages)
                )
            """)

            # 이름 이력 마이그레이션
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO name_history
                    SELECT * FROM global.name_history
                """)
            except sqlite3.OperationalError:
                # 전역 DB에 name_history 테이블이 없을 수 있음
                pass

            conn.execute("DETACH DATABASE global")
            conn.commit()

        logger.info(f"Successfully migrated global data to {project_db}")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== Project Local IPC Initialization ===")

    # 프로젝트 루트 감지
    root = detect_project_root()
    print(f"Project root: {root}")

    # IPC 디렉토리 초기화
    ipc_dir = get_project_ipc_dir(root)
    print(f"IPC directory: {ipc_dir}")

    # 데이터베이스 경로
    db = get_project_database()
    print(f"Database: {db}")

    # 설정 확인
    config = get_project_config()
    print(f"Config: {json.dumps(config, indent=2)}")
