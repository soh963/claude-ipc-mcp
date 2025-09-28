#!/usr/bin/env python3
"""
데이터베이스 스키마 호환성 래퍼
코드와 실제 DB 스키마 간의 차이를 자동으로 처리
"""

import sqlite3
import re
from typing import Optional, Any, List, Tuple

class DBCompat:
    """데이터베이스 스키마 호환성 래퍼"""

    # 컬럼명 매핑 테이블
    COLUMN_MAPPINGS = {
        # instances 테이블
        'id': 'instance_id',
        'token_hash': 'session_token_hash',
    }

    # SQL 쿼리 패턴 매핑
    QUERY_MAPPINGS = {
        # instances 테이블 관련
        r'\bWHERE\s+id\s*=': 'WHERE instance_id =',
        r'\bWHERE\s+id\s+IN': 'WHERE instance_id IN',
        r'\bSELECT\s+id\b': 'SELECT instance_id',
        r'\bSELECT\s+id,': 'SELECT instance_id,',
        r'\bDELETE\s+FROM\s+instances\s+WHERE\s+id\b': 'DELETE FROM instances WHERE instance_id',
        r'\bUPDATE\s+instances\s+SET\s+.*\s+WHERE\s+id\b': lambda m: m.group(0).replace('WHERE id', 'WHERE instance_id'),
        r'\bINSERT\s+INTO\s+instances\s*\(\s*id\b': 'INSERT INTO instances (instance_id',
        r'\bINSERT\s+OR\s+REPLACE\s+INTO\s+instances\s*\(\s*id\b': 'INSERT OR REPLACE INTO instances (instance_id',

        # sessions 테이블 관련
        r'\btoken_hash\b': 'session_token_hash',

        # name_history 테이블 관련
        r'\bold_id\b': 'old_instance_id',
        r'\bnew_id\b': 'new_instance_id',
    }

    @classmethod
    def fix_query(cls, query: str) -> str:
        """SQL 쿼리의 컬럼명을 자동으로 수정"""
        fixed_query = query

        # 정규 표현식을 사용한 패턴 매칭 및 교체
        for pattern, replacement in cls.QUERY_MAPPINGS.items():
            if callable(replacement):
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
            else:
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)

        return fixed_query

    @classmethod
    def safe_execute(cls, cursor: sqlite3.Cursor, query: str,
                     params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """스키마 차이를 자동으로 처리하는 안전한 쿼리 실행"""
        fixed_query = cls.fix_query(query)

        try:
            if params:
                return cursor.execute(fixed_query, params)
            return cursor.execute(fixed_query)
        except sqlite3.OperationalError as e:
            # 스키마 관련 오류를 더 명확하게 로깅
            error_msg = str(e)
            print(f"[DB_COMPAT] Schema error: {error_msg}")
            print(f"[DB_COMPAT] Original query: {query}")
            print(f"[DB_COMPAT] Fixed query: {fixed_query}")

            # 더 구체적인 오류 메시지 제공
            if "no column" in error_msg.lower():
                column_match = re.search(r'no column named (\w+)', error_msg, re.IGNORECASE)
                if column_match:
                    bad_column = column_match.group(1)
                    print(f"[DB_COMPAT] Column '{bad_column}' not found. Check schema with: sqlite3 ~/.claude-ipc-data/messages.db '.schema'")

            raise

    @classmethod
    def safe_executemany(cls, cursor: sqlite3.Cursor, query: str,
                         params_list: List[Tuple]) -> sqlite3.Cursor:
        """여러 파라미터를 사용한 배치 실행"""
        fixed_query = cls.fix_query(query)

        try:
            return cursor.executemany(fixed_query, params_list)
        except sqlite3.OperationalError as e:
            print(f"[DB_COMPAT] Batch execution error: {e}")
            print(f"[DB_COMPAT] Query: {fixed_query}")
            raise

    @classmethod
    def safe_fetchone(cls, cursor: sqlite3.Cursor, query: str,
                     params: Optional[Tuple] = None) -> Optional[Tuple]:
        """단일 결과 조회"""
        cls.safe_execute(cursor, query, params)
        return cursor.fetchone()

    @classmethod
    def safe_fetchall(cls, cursor: sqlite3.Cursor, query: str,
                     params: Optional[Tuple] = None) -> List[Tuple]:
        """모든 결과 조회"""
        cls.safe_execute(cursor, query, params)
        return cursor.fetchall()

    @classmethod
    def get_schema_info(cls, db_path: str) -> dict:
        """데이터베이스 스키마 정보 조회"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        schema_info = {}

        # 모든 테이블 목록 가져오기
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema_info[table_name] = [col[1] for col in columns]  # 컬럼명만 저장

        conn.close()
        return schema_info

    @classmethod
    def validate_compatibility(cls, db_path: str) -> bool:
        """현재 코드와 DB 스키마의 호환성 검증"""
        schema = cls.get_schema_info(db_path)

        # 필수 테이블과 컬럼 확인
        required = {
            'instances': ['instance_id', 'last_seen'],
            'sessions': ['session_token_hash', 'instance_id', 'created_at', 'expires_at'],
            'messages': ['message_id', 'from_id', 'to_id', 'content', 'timestamp', 'read_flag'],
            'name_history': ['old_instance_id', 'new_instance_id', 'changed_at']
        }

        issues = []
        for table, required_columns in required.items():
            if table not in schema:
                issues.append(f"Missing table: {table}")
                continue

            actual_columns = schema[table]
            missing = set(required_columns) - set(actual_columns)
            if missing:
                issues.append(f"Table {table} missing columns: {missing}")

        if issues:
            print("⚠️ Schema compatibility issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("✅ Schema compatibility check passed")
        return True


# 기존 코드와의 호환성을 위한 헬퍼 함수들
def safe_query(cursor: sqlite3.Cursor, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
    """기존 코드에서 쉽게 사용할 수 있는 헬퍼 함수"""
    return DBCompat.safe_execute(cursor, query, params)


def fix_query(query: str) -> str:
    """쿼리만 수정하는 헬퍼 함수"""
    return DBCompat.fix_query(query)


if __name__ == "__main__":
    # 테스트 및 데모
    print("Database Compatibility Wrapper Test")
    print("=" * 40)

    # 테스트 쿼리들
    test_queries = [
        "SELECT id FROM instances WHERE id = ?",
        "DELETE FROM instances WHERE id = ?",
        "UPDATE instances SET last_seen = ? WHERE id = ?",
        "INSERT INTO instances (id, last_seen) VALUES (?, ?)",
        "SELECT token_hash FROM sessions WHERE token_hash = ?",
        "SELECT * FROM name_history WHERE old_id = ? AND new_id = ?",
    ]

    print("\nQuery transformation examples:")
    for query in test_queries:
        fixed = fix_query(query)
        print(f"\nOriginal: {query}")
        print(f"Fixed:    {fixed}")

    # 실제 DB 스키마 검증 (DB가 존재하는 경우)
    from pathlib import Path
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if db_path.exists():
        print("\n" + "=" * 40)
        print("Checking actual database schema...")
        DBCompat.validate_compatibility(str(db_path))

        print("\nActual schema:")
        schema = DBCompat.get_schema_info(str(db_path))
        for table, columns in schema.items():
            print(f"  {table}: {columns}")