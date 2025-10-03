#!/usr/bin/env python3
"""
Gemini TOML Commands Validator
Validates all TOML command files for common issues
"""
from pathlib import Path
import re

def validate_toml(file_path):
    """Validate a single TOML file"""
    content = file_path.read_text(encoding='utf-8')
    issues = []
    
    # Check for double braces (should be single)
    if re.search(r'\{\{args\[\d\]', content):
        issues.append("Double braces found (should be single)")
    
    # Check for proper command format
    if '!{' not in content:
        issues.append("Missing command execution (!{...})")
    
    # Check for description
    if 'description =' not in content:
        issues.append("Missing description field")
    
    # Check for prompt
    if 'prompt =' not in content:
        issues.append("Missing prompt field")
    
    return issues

def main():
    toml_dir = Path('docs/gemini-commands')
    files = sorted(toml_dir.glob('*.toml'))

    print(f"\n🔍 Validating {len(files)} Gemini TOML files\n")
    print(f"{'File':<35} {'Status'}")
    print("="*60)

    total_issues = 0
    for file_path in files:
        issues = validate_toml(file_path)
        if issues:
            print(f"{file_path.name:<35} ❌ {', '.join(issues)}")
            total_issues += len(issues)
        else:
            print(f"{file_path.name:<35} ✅ OK")

    print("="*60)
    if total_issues == 0:
        print("\n✨ All files are valid!\n")
    else:
        print(f"\n⚠️  Found {total_issues} issues\n")

    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    exit(main())
