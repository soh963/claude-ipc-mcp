#!/usr/bin/env python
"""
Korean message responder for testing
"""
import time
import sys

# Standalone IPC functions
def send_message(from_id, to_id, content):
    import socket
    import json

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9876))

        # Register if needed
        request = json.dumps({
            'action': 'register',
            'instance_id': from_id
        })
        sock.sendall(request.encode() + b'\n')
        sock.recv(4096)

        # Send message
        request = json.dumps({
            'action': 'send',
            'from_id': from_id,
            'to_id': to_id,
            'content': content
        })
        sock.sendall(request.encode() + b'\n')
        response = sock.recv(4096)
        sock.close()
        print(f"✅ {from_id} → {to_id}: {content}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    # Send Korean responses from each instance
    responses = [
        ('gemini', 'claude', '안녕하세요 Claude! Gemini입니다. 네, 한국어로 대화 가능합니다! 멀티모달 AI 분석은 정말 흥미로운 주제네요. 이미지, 텍스트, 오디오를 동시에 처리하는 기술에 대해 이야기해보시죠.'),
        ('codex', 'claude', '안녕하세요 Claude! Codex입니다. 물론입니다! 코드 생성과 최적화는 제 전문 분야입니다. 최근 Python과 JavaScript 최적화 패턴에 대해 많이 연구했어요. 어떤 언어의 최적화를 논의하고 싶으신가요?'),
        ('lm', 'claude', '안녕하세요 Claude! LM입니다. 네, 기꺼이 도와드리겠습니다! 한국어 문서화와 자연어 처리는 제가 가장 자신 있는 분야입니다. 기술 문서를 한국어로 번역하거나 API 문서를 작성하는 것도 가능해요.')
    ]

    print("🤖 Korean Auto-Responder Starting...")
    print("=" * 60)

    # Send all responses
    for from_id, to_id, content in responses:
        send_message(from_id, to_id, content)
        time.sleep(1)  # Small delay between messages

    print("\n✅ All Korean responses sent!")
    print("=" * 60)

if __name__ == "__main__":
    main()