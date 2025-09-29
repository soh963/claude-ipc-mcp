#!/usr/bin/env python3
"""
데이터베이스 스키마 검증 도구
서버 시작 시 스키마 호환성을 자동으로 검증하고 문제를 보고
"""

import sqlite3
import sys
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

class SchemaValidator:
    """데이터베이스 스키마 검증기"""

    # 예상되는 스키마 정의 (실제 데이터베이스 구조에 맞춤)
    EXPECTED_SCHEMA = {
        'instances': {
            'columns': {
                'instance_id': 'TEXT PRIMARY KEY',
                'last_seen': 'TEXT'
            },
            'required': ['instance_id', 'last_seen']
        },
        'sessions': {
            'columns': {
                'session_token_hash': 'TEXT PRIMARY KEY',
                'instance_id': 'TEXT',
                'created_at': 'TEXT',
                'expires_at': 'TEXT'
            },
            'required': ['session_token_hash', 'instance_id', 'created_at', 'expires_at']
        },
        'messages': {
            'columns': {
                'id': 'INTEGER PRIMARY KEY',
                'from_id': 'TEXT',
                'to_id': 'TEXT',
                'content': 'TEXT',
                'timestamp': 'TEXT',
                'read_flag': 'INTEGER',
                'is_read': 'INTEGER',
                'data': 'TEXT',
                'summary': 'TEXT',
                'large_file_path': 'TEXT'
            },
            'required': ['id', 'from_id', 'to_id', 'content', 'timestamp', 'read_flag']
        },
        'name_history': {
            'columns': {
                'old_name': 'TEXT PRIMARY KEY',
                'new_name': 'TEXT',
                'changed_at': 'TEXT'
            },
            'required': ['old_name', 'new_name', 'changed_at']
        }
    }

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path.home() / '.claude-ipc-data' / 'messages.db'
        else:
            self.db_path = Path(db_path)

        self.issues = []
        self.warnings = []
        self.info = []

    def connect(self) -> sqlite3.Connection:
        """데이터베이스 연결"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_actual_schema(self) -> Dict:
        """실제 데이터베이스 스키마 조회"""
        conn = self.connect()
        cursor = conn.cursor()

        actual_schema = {}

        # 모든 테이블 목록 가져오기
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table_row in tables:
            table_name = table_row[0]

            # 테이블 정보 가져오기
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            actual_schema[table_name] = {
                'columns': {},
                'column_list': []
            }

            for col in columns:
                col_name = col[1]
                col_type = col[2]
                col_notnull = col[3]
                col_default = col[4]
                col_pk = col[5]

                actual_schema[table_name]['columns'][col_name] = {
                    'type': col_type,
                    'notnull': col_notnull,
                    'default': col_default,
                    'pk': col_pk
                }
                actual_schema[table_name]['column_list'].append(col_name)

        conn.close()
        return actual_schema

    def validate_table(self, table_name: str, expected: Dict, actual: Dict) -> bool:
        """단일 테이블 검증"""
        is_valid = True

        if table_name not in actual:
            self.issues.append(f"❌ Table '{table_name}' is missing")
            return False

        actual_table = actual[table_name]
        expected_columns = expected['required']
        actual_columns = actual_table['column_list']

        # 필수 컬럼 확인
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            self.issues.append(f"❌ Table '{table_name}' missing required columns: {missing_columns}")
            is_valid = False

        # 추가 컬럼 확인 (경고만)
        extra_columns = set(actual_columns) - set(expected_columns)
        if extra_columns:
            self.warnings.append(f"⚠️ Table '{table_name}' has extra columns: {extra_columns}")

        # 컬럼 타입 확인 (정보만)
        for col_name in expected_columns:
            if col_name in actual_columns:
                actual_col = actual_table['columns'][col_name]
                self.info.append(f"ℹ️ {table_name}.{col_name}: {actual_col['type']} (PK: {actual_col['pk']})")

        return is_valid

    def validate(self) -> bool:
        """전체 스키마 검증"""
        print("🔍 Database Schema Validator")
        print("=" * 60)
        print(f"Database: {self.db_path}")
        print()

        try:
            # 데이터베이스 존재 확인
            if not self.db_path.exists():
                self.issues.append(f"❌ Database file not found: {self.db_path}")
                return False

            # 실제 스키마 가져오기
            actual_schema = self.get_actual_schema()

            print("📊 Validating schema...")
            print("-" * 60)

            # 각 테이블 검증
            all_valid = True
            for table_name, expected in self.EXPECTED_SCHEMA.items():
                is_valid = self.validate_table(table_name, expected, actual_schema)
                if not is_valid:
                    all_valid = False

            # 결과 출력
            self.print_results()

            return all_valid

        except Exception as e:
            self.issues.append(f"❌ Validation error: {e}")
            return False

    def print_results(self):
        """검증 결과 출력"""
        # 심각한 문제
        if self.issues:
            print("\n🚨 CRITICAL ISSUES (Must Fix):")
            for issue in self.issues:
                print(f"  {issue}")

        # 경고
        if self.warnings:
            print("\n⚠️ WARNINGS (Should Review):")
            for warning in self.warnings:
                print(f"  {warning}")

        # 정보
        if self.info and '--verbose' in sys.argv:
            print("\nℹ️ SCHEMA DETAILS:")
            for info in self.info:
                print(f"  {info}")

        # 최종 상태
        print("\n" + "=" * 60)
        if not self.issues:
            print("✅ Schema validation PASSED!")
            print("All required tables and columns are present.")
        else:
            print("❌ Schema validation FAILED!")
            print(f"Found {len(self.issues)} critical issue(s) that must be fixed.")

    def generate_fix_script(self) -> Optional[str]:
        """문제를 수정하는 SQL 스크립트 생성"""
        if not self.issues:
            return None

        fix_script = []
        fix_script.append("-- Auto-generated schema fix script")
        fix_script.append(f"-- Generated at: {datetime.now().isoformat()}")
        fix_script.append("")

        for issue in self.issues:
            if "missing required columns" in issue:
                # 컬럼 추가 스크립트 생성
                table_match = re.search(r"Table '(\w+)'", issue)
                columns_match = re.search(r"columns: {([^}]+)}", issue)

                if table_match and columns_match:
                    table = table_match.group(1)
                    columns = columns_match.group(1).replace("'", "").split(", ")

                    for col in columns:
                        col = col.strip()
                        if table in self.EXPECTED_SCHEMA and col in self.EXPECTED_SCHEMA[table]['columns']:
                            col_type = self.EXPECTED_SCHEMA[table]['columns'][col]
                            fix_script.append(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")

            elif "Table" in issue and "is missing" in issue:
                # 테이블 생성 스크립트 생성
                table_match = re.search(r"Table '(\w+)'", issue)
                if table_match:
                    table = table_match.group(1)
                    if table in self.EXPECTED_SCHEMA:
                        columns = self.EXPECTED_SCHEMA[table]['columns']
                        col_defs = [f"{col} {type_}" for col, type_ in columns.items()]
                        create_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n  " + ",\n  ".join(col_defs) + "\n);"
                        fix_script.append(create_sql)

        return "\n".join(fix_script) if len(fix_script) > 2 else None

    def auto_fix(self) -> bool:
        """검증 실패 시 자동 수정 시도"""
        if not self.issues:
            return True

        print("\n🔧 Attempting auto-fix...")

        fix_script = self.generate_fix_script()
        if not fix_script:
            print("❌ Could not generate fix script")
            return False

        print("\n📝 Generated fix script:")
        print("-" * 40)
        print(fix_script)
        print("-" * 40)

        # 사용자 확인
        response = input("\nApply these fixes? (y/N): ")
        if response.lower() != 'y':
            print("❌ Auto-fix cancelled")
            return False

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.executescript(fix_script)
            conn.commit()
            conn.close()

            print("✅ Fixes applied successfully!")

            # 재검증
            self.issues = []
            self.warnings = []
            self.info = []
            return self.validate()

        except Exception as e:
            print(f"❌ Failed to apply fixes: {e}")
            return False

    def export_report(self, filename: Optional[str] = None) -> str:
        """검증 리포트를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"schema_validation_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'database': str(self.db_path),
            'status': 'PASS' if not self.issues else 'FAIL',
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info,
            'actual_schema': self.get_actual_schema() if self.db_path.exists() else None
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Report saved to: {filename}")
        return filename


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Database Schema Validator for IPC System')
    parser.add_argument('--db', type=str, help='Path to database file')
    parser.add_argument('--verbose', action='store_true', help='Show detailed schema information')
    parser.add_argument('--auto-fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--export', type=str, help='Export report to file')

    args = parser.parse_args()

    # 검증기 생성
    validator = SchemaValidator(args.db)

    # 검증 실행
    is_valid = validator.validate()

    # 자동 수정
    if not is_valid and args.auto_fix:
        is_valid = validator.auto_fix()

    # 리포트 저장
    if args.export:
        validator.export_report(args.export)

    # 종료 코드
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()