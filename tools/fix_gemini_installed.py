#!/usr/bin/env python3
"""
설치된 Gemini TOML 파일 자동 수정 스크립트

설치 경로의 모든 TOML 파일 오류 수정
"""

import re
from pathlib import Path
from datetime import datetime

def fix_toml_content(content: str, filename: str) -> tuple[str, list[str]]:
    """TOML 내용 수정 및 변경사항 반환"""
    changes = []
    original = content

    # 1. Windows 백슬래시 경로 수정: 모든 백슬래시를 슬래시로
    # D:\claude-ipc-mcp\tools\file.py → D:/claude-ipc-mcp/tools/file.py
    # D:/claude-ipc-mcp\tools\file.py → D:/claude-ipc-mcp/tools/file.py (혼합 경로도 수정)

    # 정규식으로 모든 백슬래시를 슬래시로 변경
    # D:로 시작하는 경로에서 백슬래시를 모두 찾아서 슬래시로 변경
    import re
    backslash_pattern = re.compile(r'(D:[/\\][^\s"\']+)')

    def replace_backslashes(match):
        path = match.group(1)
        fixed_path = path.replace('\\', '/')
        return fixed_path

    new_content = backslash_pattern.sub(replace_backslashes, content)

    if new_content != content:
        # 변경된 경로들 추출
        old_paths = backslash_pattern.findall(content)
        new_paths = backslash_pattern.findall(new_content)
        unique_changes = set(zip(old_paths, new_paths))

        for old, new in unique_changes:
            if old != new:
                changes.append(f"경로 수정: {old} → {new}")

        content = new_content

    # 2. 옛날 변수명 수정
    old_to_new_vars = {
        '{target}': '{args[0]}',
        '{message}': '{args[1]}',
        '{timeout}': '{args[2]:-30}',
        '{name}': '{args[0]}',
        '{instance}': '{args[0]}',
        '{instance_id}': '{args[0]}',
        '{old_name}': '{args[0]}',
        '{new_name}': '{args[1]}',
        '{policy}': '{args[1]:-smart}',
    }

    for old_var, new_var in old_to_new_vars.items():
        if old_var in content:
            content = content.replace(old_var, new_var)
            changes.append(f"변수명 변경: {old_var} → {new_var}")

    # 3. 이중 중괄호 수정: {{args[0]}} → {args[0]}
    double_brace_pattern = r'\{\{(args\[\d+\](?::-[^}]+)?)\}\}'
    if re.search(double_brace_pattern, content):
        content = re.sub(double_brace_pattern, r'{\1}', content)
        changes.append("이중 중괄호 → 단일 중괄호")

    # 4. 추가 닫는 중괄호 제거
    extra_brace_pattern = r'(\{args\[\d+\](?::-[^}]+)?\})\}+'
    if re.search(extra_brace_pattern, content):
        content = re.sub(extra_brace_pattern, r'\1', content)
        changes.append("추가 닫는 중괄호 제거")

    # 5. 중첩 인용부호 수정: "{{args[0]}}" → '{args[0]}'
    nested_quote_pattern = r'"(\{args\[\d+\](?::-[^}]+)?\})"'
    if re.search(nested_quote_pattern, content):
        content = re.sub(nested_quote_pattern, r"'\1'", content)
        changes.append("중첩 인용부호 수정")

    return content, changes

def fix_all_installed_files():
    """설치된 모든 TOML 파일 수정"""

    # 설치 경로
    gemini_dir = Path.home() / ".gemini" / "commands" / "ipc"

    if not gemini_dir.exists():
        print(f"❌ Gemini commands 디렉토리가 없습니다: {gemini_dir}")
        return False

    toml_files = sorted(gemini_dir.glob("*.toml"))

    if not toml_files:
        print(f"❌ TOML 파일이 없습니다: {gemini_dir}")
        return False

    print(f"\n🔧 Gemini TOML 파일 자동 수정")
    print(f"📁 위치: {gemini_dir}")
    print(f"📦 파일 개수: {len(toml_files)}")
    print("=" * 70)
    print()

    # 백업 디렉토리 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = gemini_dir / f".backup_{timestamp}"
    backup_dir.mkdir(exist_ok=True)

    print(f"💾 백업 생성: {backup_dir.name}\n")

    fixed_count = 0
    unchanged_count = 0
    error_count = 0

    for toml_file in toml_files:
        try:
            # 원본 파일 읽기
            original_content = toml_file.read_text(encoding='utf-8')

            # 백업
            backup_file = backup_dir / toml_file.name
            backup_file.write_text(original_content, encoding='utf-8')

            # 수정
            fixed_content, changes = fix_toml_content(original_content, toml_file.name)

            if changes:
                # 수정된 내용 저장
                toml_file.write_text(fixed_content, encoding='utf-8')

                print(f"✅ {toml_file.name}")
                for change in changes:
                    print(f"   - {change}")
                print()

                fixed_count += 1
            else:
                print(f"⚪ {toml_file.name} (변경 없음)")
                unchanged_count += 1

        except Exception as e:
            print(f"❌ {toml_file.name}: {e}")
            error_count += 1

    print()
    print("=" * 70)
    print("\n📊 수정 결과:")
    print(f"  ✅ 수정 완료: {fixed_count} 개")
    print(f"  ⚪ 변경 없음: {unchanged_count} 개")
    if error_count > 0:
        print(f"  ❌ 오류 발생: {error_count} 개")

    print(f"\n💾 백업 위치: {backup_dir}")
    print(f"\n🎯 다음 단계:")
    print(f"  1. Gemini CLI 재시작")
    print(f"  2. /ipc/ping 명령으로 테스트")
    print(f"  3. 문제 발생 시 백업 폴더에서 복원")

    print("\n✨ 수정 완료!")

    return error_count == 0

if __name__ == "__main__":
    import sys
    success = fix_all_installed_files()
    sys.exit(0 if success else 1)
