#!/usr/bin/env python3
"""Test broadcast message to all instances"""

from core import broker_client
import time

# gemini-test 세션으로 브로드캐스트
session_token = "mtzXmFudW4nwsiBTwn3cMnee23Xb0EFc8WhRZw0UKio"
instance_id = "gemini-test"

print(f"📢 Sending broadcast message from {instance_id}...")

# 브로드캐스트 메시지 전송
response = broker_client.send(
    session_token,
    instance_id,
    "*",  # 모든 인스턴스에게
    "안녕하세요! 모든 인스턴스 여러분! 브로드캐스트 테스트입니다. 반갑습니다! 👋"
)

print(f"✅ Broadcast sent: {response}")

print("\n⏳ Waiting 5 seconds for responses...")
time.sleep(5)

# 응답 확인
print("\n📬 Checking for responses...")
check_response = broker_client._send_request({
    "action": "check",
    "instance_id": instance_id,
    "session_token": session_token
})

messages = check_response.get("messages", [])
print(f"\n✉️ Received {len(messages)} response(s):\n")

for msg in messages:
    print(f"  From: {msg['from']}")
    print(f"  Content: {msg['message']['content']}")
    print(f"  Time: {msg['timestamp']}")
    print()

if not messages:
    print("  ❌ No responses received")
