#!/usr/bin/env python3
"""
Gemini 설치된 TOML 파일 검증 스크립트

설치 위치의 TOML 파일들을 검증합니다.
"""

import sys
from pathlib import Path

def validate_installed_commands():
    """설치된 Gemini commands 검증"""

    # 설치 경로
    gemini_dir = Path.home() / ".gemini" / "commands" / "ipc"

    if not gemini_dir.exists():
        print(f"❌ Gemini commands 디렉토리가 없습니다: {gemini_dir}")
        print(f"   먼저 Gemini CLI를 설치하고 commands를 복사하세요.")
        return False

    toml_files = list(gemini_dir.glob("*.toml"))

    if not toml_files:
        print(f"❌ TOML 파일이 없습니다: {gemini_dir}")
        return False

    print(f"\n🔍 검증 중: {len(toml_files)}개 파일 ({gemini_dir})\n")

    errors = []
    warnings = []

    for toml_file in sorted(toml_files):
        file_errors = []
        file_warnings = []

        try:
            with open(toml_file, 'rb') as f:
                content = f.read()

            # 백슬래시 경로 검사 (Windows 경로 이스케이프 문제)
            text = content.decode('utf-8')
            if 'D:\\claude-ipc-mcp' in text or 'D:\\tools' in text:
                file_errors.append("Windows 백슬래시 경로 사용 (TOML 파싱 에러 발생)")
                file_errors.append("  → 슬래시로 변경 필요: D:/claude-ipc-mcp")

            # 필수 요소 확인
            if 'prompt' not in text:
                file_errors.append("'prompt' 필드 누락")
            elif '!{' not in text:
                file_warnings.append("명령 실행 구문 (!{...}) 없음")

            if 'description' not in text:
                file_warnings.append("'description' 필드 누락")

            # 옛날 변수명 검사
            old_vars = ['{target}', '{message}', '{timeout}', '{instance_id}', '{old_name}', '{new_name}']
            for old_var in old_vars:
                if old_var in text:
                    file_errors.append(f"옛날 변수명 사용: {old_var}")
                    file_errors.append("  → {args[N]} 형식으로 변경 필요")

            # 이중 중괄호 검사
            if '{{args' in text:
                file_errors.append("이중 중괄호 사용: {{args[N]}}")
                file_errors.append("  → 단일 중괄호로 변경: {args[N]}")

        except Exception as e:
            file_errors.append(f"파일 읽기 실패: {e}")

        # 결과 출력
        if file_errors:
            print(f"❌ {toml_file.name}")
            for error in file_errors:
                print(f"   {error}")
            errors.append((toml_file.name, file_errors))
        elif file_warnings:
            print(f"⚠️  {toml_file.name}")
            for warning in file_warnings:
                print(f"   {warning}")
            warnings.append((toml_file.name, file_warnings))
        else:
            print(f"✅ {toml_file.name}")

    print()
    print("=" * 60)

    if errors:
        print(f"\n❌ {len(errors)}개 파일에 오류 발견:")
        for filename, error_list in errors:
            print(f"\n  {filename}:")
            for error in error_list:
                print(f"    - {error}")
        print(f"\n🔧 해결 방법:")
        print(f"   1. scripts/update-gemini-commands.bat 실행")
        print(f"   2. 최신 TOML 파일로 자동 교체됩니다")
        return False

    if warnings:
        print(f"\n⚠️  {len(warnings)}개 파일에 경고:")
        for filename, warning_list in warnings:
            print(f"\n  {filename}:")
            for warning in warning_list:
                print(f"    - {warning}")

    print(f"\n✨ 검증 완료!")
    if not errors and not warnings:
        print(f"   모든 파일이 정상입니다.")

    return len(errors) == 0

if __name__ == "__main__":
    success = validate_installed_commands()
    sys.exit(0 if success else 1)
