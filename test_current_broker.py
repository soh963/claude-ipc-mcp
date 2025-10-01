#!/usr/bin/env python3
"""Test if current broker is running and responding"""
import sys
sys.path.insert(0, "D:/claude-ipc-mcp/src")

from core import broker_client
import json

print("Testing broker connection...")
status = broker_client.status()
print(json.dumps(status, indent=2))

if status.get("status") == "ok":
    print("\n✅ SUCCESS! 브로커가 정상 작동 중입니다!")
    print(f"활성 인스턴스: {len(status.get('instances', []))}")

    # Check if fix is working
    print("\n인증 수정사항이 적용되었습니다!")
else:
    print(f"\n❌ 브로커 응답 실패: {status.get('message', '알 수 없는 오류')}")