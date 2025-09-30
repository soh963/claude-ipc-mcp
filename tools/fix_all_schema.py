#!/usr/bin/env python3
"""
모든 파일의 스키마 불일치를 자동으로 수정하는 도구
프로젝트 전체의 SQL 쿼리를 스캔하고 수정
"""

import re
import sys
from pathlib import Path
from typing import Dict
import shutil
from datetime import datetime


class SchemaFixer:
    """SQL 스키마 불일치를 자동으로 수정하는 클래스"""

    def __init__(self, backup: bool = True):
        self.backup = backup
        self.fixed_files = []
        self.error_files = []
        self.changes_made = {}

        # SQL 쿼리 패턴과 대체 규칙 정의
        self.replacements = {
            # instances 테이블 - 'id' -> 'instance_id'
            r"\bWHERE\s+id\s*=": "WHERE instance_id =",
            r"\bWHERE\s+id\s+IN": "WHERE instance_id IN",
            r"\bAND\s+id\s*=": "AND instance_id =",
            r"\bOR\s+id\s*=": "OR instance_id =",
            r"SELECT\s+id\s+FROM\s+instances": "SELECT instance_id FROM instances",
            r"SELECT\s+id,": "SELECT instance_id,",
            r"SELECT\s+\*\s+FROM\s+instances\s+WHERE\s+id": "SELECT * FROM instances WHERE instance_id",
            r"DELETE\s+FROM\s+instances\s+WHERE\s+id": "DELETE FROM instances WHERE instance_id",
            r"UPDATE\s+instances\s+SET\s+(.*?)\s+WHERE\s+id": r"UPDATE instances SET \1 WHERE instance_id",
            r"INSERT\s+INTO\s+instances\s*\(\s*id,": "INSERT INTO instances (instance_id,",
            r"INSERT\s+OR\s+REPLACE\s+INTO\s+instances\s*\(\s*id,": "INSERT OR REPLACE INTO instances (instance_id,",
            r"instances\s*\(\s*id\s*\)": "instances (instance_id)",
            r'"id"\s*=\s*\?': '"instance_id" = ?',
            r"'id'\s*=\s*\?": "'instance_id' = ?",
            # sessions 테이블 - 'token_hash' -> 'session_token_hash'
            r"\btoken_hash\b": "session_token_hash",
            r'"token_hash"': '"session_token_hash"',
            r"'token_hash'": "'session_token_hash'",
            # name_history 테이블
            r"\bold_id\b": "old_instance_id",
            r"\bnew_id\b": "new_instance_id",
            r'"old_id"': '"old_instance_id"',
            r'"new_id"': '"new_instance_id"',
        }

        # 특별한 컨텍스트가 필요한 패턴들
        self.context_patterns = [
            # cursor.execute 내부의 쿼리만 수정
            (r'(cursor\.execute\s*\(\s*["\'])(.*?)(["\'])', self.fix_query_in_execute),
            (r'(cursor\.executemany\s*\(\s*["\'])(.*?)(["\'])', self.fix_query_in_execute),
            (r'(conn\.execute\s*\(\s*["\'])(.*?)(["\'])', self.fix_query_in_execute),
        ]

    def fix_query_in_execute(self, match):
        """cursor.execute 내부의 쿼리를 수정"""
        prefix = match.group(1)
        query = match.group(2)
        suffix = match.group(3)

        # 쿼리 내용 수정
        for pattern, replacement in self.replacements.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)

        return prefix + query + suffix

    def backup_file(self, filepath: Path):
        """파일 백업 생성"""
        if not self.backup:
            return

        backup_dir = filepath.parent / "backup"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"

        shutil.copy2(filepath, backup_path)
        print(f"  📁 Backup created: {backup_path.name}")

    def fix_file(self, filepath: Path) -> bool:
        """단일 파일의 SQL 쿼리 수정"""
        try:
            # 파일 읽기
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            changes = []

            # 컨텍스트 패턴 적용
            for pattern, handler in self.context_patterns:
                new_content = re.sub(pattern, handler, content, flags=re.MULTILINE | re.DOTALL)
                if new_content != content:
                    changes.append(f"Applied context pattern: {pattern}")
                    content = new_content

            # 일반 패턴 적용
            for pattern, replacement in self.replacements.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    changes.append(f"Replaced {len(matches)} occurrences of '{pattern}'")

            # 변경사항이 있으면 파일 저장
            if content != original_content:
                # 백업 생성
                self.backup_file(filepath)

                # 수정된 내용 저장
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                self.fixed_files.append(filepath)
                self.changes_made[filepath] = changes
                return True

            return False

        except Exception as e:
            print(f"  ❌ Error processing {filepath}: {e}")
            self.error_files.append((filepath, str(e)))
            return False

    def fix_all_files(self, root_dir: Path = None) -> Dict:
        """프로젝트의 모든 Python 파일 수정"""
        if root_dir is None:
            root_dir = Path.cwd()

        print(f"🔍 Scanning for Python files in: {root_dir}")
        print("=" * 60)

        # Python 파일 찾기
        py_files = []
        for filepath in root_dir.rglob("*.py"):
            # 제외할 디렉토리
            if any(skip in str(filepath) for skip in ["venv", "__pycache__", "backup", ".git"]):
                continue
            py_files.append(filepath)

        print(f"📋 Found {len(py_files)} Python files to check")
        print("-" * 60)

        # 각 파일 처리
        for filepath in py_files:
            relative_path = filepath.relative_to(root_dir)
            print(f"Checking: {relative_path}")

            if self.fix_file(filepath):
                print(f"  ✅ Fixed: {relative_path}")
                for change in self.changes_made[filepath]:
                    print(f"    - {change}")
            else:
                print("  ⏭️  No changes needed")

        return self.generate_report()

    def generate_report(self) -> Dict:
        """수정 결과 리포트 생성"""
        report = {
            "total_files_checked": len(self.fixed_files) + len(self.error_files),
            "files_fixed": len(self.fixed_files),
            "files_with_errors": len(self.error_files),
            "fixed_files": self.fixed_files,
            "error_files": self.error_files,
            "changes": self.changes_made,
        }

        print("\n" + "=" * 60)
        print("📊 SCHEMA FIX REPORT")
        print("=" * 60)
        print(f"Total files checked: {report['total_files_checked']}")
        print(f"Files fixed: {report['files_fixed']}")
        print(f"Files with errors: {report['files_with_errors']}")

        if self.fixed_files:
            print("\n✅ Successfully fixed files:")
            for filepath in self.fixed_files:
                print(f"  - {filepath.name}")

        if self.error_files:
            print("\n❌ Files with errors:")
            for filepath, error in self.error_files:
                print(f"  - {filepath.name}: {error}")

        return report

    def verify_fixes(self) -> bool:
        """수정 후 검증"""
        print("\n🔍 Verifying fixes...")

        # 수정된 파일들에서 문제가 되는 패턴이 남아있는지 확인
        issues = []
        problem_patterns = [
            r"DELETE\s+FROM\s+instances\s+WHERE\s+id\s*=",
            r"UPDATE\s+instances.*WHERE\s+id\s*=",
            r"SELECT\s+id\s+FROM\s+instances",
            r"\btoken_hash\b(?!\s*:)",  # token_hash (딕셔너리 키가 아닌 경우)
        ]

        for filepath in self.fixed_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in problem_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append((filepath, pattern))

        if issues:
            print("⚠️ Some patterns may still need attention:")
            for filepath, pattern in issues:
                print(f"  - {filepath.name}: Pattern '{pattern}' found")
            return False

        print("✅ All fixes verified successfully!")
        return True


def main():
    """메인 실행 함수"""
    print("🔧 SQL Schema Fixer Tool")
    print("This tool will automatically fix SQL query column mismatches")
    print("=" * 60)

    # 명령줄 인수 처리
    backup = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-backup":
        backup = False
        print("⚠️ Running without backup (--no-backup flag)")
    else:
        print("📁 Backup will be created for modified files")

    print()

    # 사용자 확인
    response = input("Do you want to proceed? (y/N): ")
    if response.lower() != "y":
        print("❌ Operation cancelled")
        return

    # 스키마 수정 실행
    fixer = SchemaFixer(backup=backup)
    report = fixer.fix_all_files()

    # 검증 실행
    if report["files_fixed"] > 0:
        fixer.verify_fixes()

    print("\n✨ Schema fix complete!")

    # 추가 권장사항
    if report["files_fixed"] > 0:
        print("\n📌 Next steps:")
        print("1. Test the IPC system: python tools/ipc_test.py")
        print("2. Run the schema validator: python tools/schema_validator.py")
        print("3. Check auto-responders: python tools/simple_auto_responder.py")


if __name__ == "__main__":
    main()
