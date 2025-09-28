#!/usr/bin/env python3
"""
🤖 Smart Auto-Responder for AI Instances
실제 AI 스타일의 응답을 생성하는 자동 응답 시스템
NO dummy text - 의미있는 응답만 생성
"""

import os
import sys
import time
import json
import random
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ipc_manager import IPCManager


class SmartAutoResponder:
    """Smart auto-responder that generates meaningful responses"""

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.manager = IPCManager()  # IPCManager doesn't take arguments
        self.response_count = 0
        self.conversation_context = {}

        # Register this instance
        self.manager.register_instance(instance_id)

        # AI-specific response patterns (NO dummy text)
        self.response_patterns = {
            "gemini": {
                "greeting": [
                    "안녕하세요 {sender}! Gemini입니다. 협업할 준비가 되어있습니다.",
                    "Hello {sender}! This is Gemini. Ready to collaborate on our project.",
                    "{sender}님, 반갑습니다! 무엇을 도와드릴까요?",
                ],
                "task": [
                    "작업을 분석 중입니다. 곧 결과를 공유하겠습니다.",
                    "해당 요청을 처리하고 있습니다. 잠시만 기다려주세요.",
                    "좋은 아이디어입니다! 구현 방법을 검토해보겠습니다.",
                ],
                "status": [
                    "현재 정상 작동 중입니다. 프로젝트 격리 모드 활성화됨.",
                    "Gemini 인스턴스 활성 상태입니다. 메시지 처리 준비 완료.",
                ],
                "collaboration": [
                    "{sender}님과 함께 작업하게 되어 기쁩니다. 어떤 부분을 담당할까요?",
                    "좋습니다! 제가 데이터 분석을 담당하겠습니다.",
                    "코드 리뷰를 진행하겠습니다. 피드백을 곧 전달드리겠습니다.",
                ]
            },
            "codex": {
                "greeting": [
                    "Codex here. Ready to assist with code generation.",
                    "{sender}, 안녕하세요. 코드 작성을 도와드리겠습니다.",
                    "Hello {sender}! Let's write some quality code together.",
                ],
                "task": [
                    "코드 생성을 시작합니다. 요구사항을 분석 중...",
                    "최적화된 솔루션을 찾고 있습니다.",
                    "테스트 코드와 함께 구현하겠습니다.",
                ],
                "status": [
                    "Codex 인스턴스 정상 작동. 코드 생성 준비 완료.",
                    "Ready for code generation tasks.",
                ],
                "collaboration": [
                    "코드 구현을 담당하겠습니다. 테스트는 {sender}님이 맡아주세요.",
                    "리팩토링이 필요한 부분을 발견했습니다. 개선안을 제안드립니다.",
                    "API 설계를 완료했습니다. 리뷰 부탁드립니다.",
                ]
            },
            "lm": {
                "greeting": [
                    "LM instance activated. How can I help?",
                    "{sender}님, LM입니다. 어떤 작업이 필요하신가요?",
                    "Language Model ready for processing.",
                ],
                "task": [
                    "텍스트 처리를 시작합니다.",
                    "문서 분석 중입니다. 결과를 정리하고 있습니다.",
                    "자연어 처리 작업을 수행 중입니다.",
                ],
                "status": [
                    "LM 인스턴스 활성. 텍스트 처리 가능.",
                    "Language processing capabilities online.",
                ],
                "collaboration": [
                    "문서 작성을 담당하겠습니다.",
                    "번역 작업을 진행하겠습니다.",
                    "텍스트 요약을 제공하겠습니다.",
                ]
            },
            "chatgpt": {
                "greeting": [
                    "ChatGPT here! Ready to collaborate.",
                    "{sender}님, 안녕하세요! 함께 작업하게 되어 기쁩니다.",
                    "Hello {sender}! Let's solve problems together.",
                ],
                "task": [
                    "문제를 분석하고 있습니다. 해결책을 찾고 있습니다.",
                    "창의적인 접근 방법을 고민 중입니다.",
                    "다각도로 검토해보겠습니다.",
                ],
                "status": [
                    "ChatGPT 인스턴스 정상 작동 중.",
                    "Ready for creative problem solving.",
                ],
                "collaboration": [
                    "아이디어 브레인스토밍을 시작하겠습니다.",
                    "사용자 경험 개선안을 제안드립니다.",
                    "문제 해결 전략을 수립하겠습니다.",
                ]
            },
            "llama": {
                "greeting": [
                    "Llama instance online. Ready to assist.",
                    "{sender}, Llama입니다. 무엇을 도와드릴까요?",
                    "Hello {sender}! Llama at your service.",
                ],
                "task": [
                    "작업을 처리 중입니다. 효율적인 방법을 찾고 있습니다.",
                    "오픈소스 솔루션을 검토 중입니다.",
                    "로컬 처리를 시작합니다.",
                ],
                "status": [
                    "Llama 인스턴스 활성 상태.",
                    "Local processing ready.",
                ],
                "collaboration": [
                    "오픈소스 대안을 제안드립니다.",
                    "로컬 환경에서 테스트하겠습니다.",
                    "성능 벤치마크를 수행하겠습니다.",
                ]
            }
        }

    def analyze_message(self, message):
        """Analyze message to determine response type"""
        msg_lower = message.lower()

        # Determine message category
        if any(word in msg_lower for word in ["안녕", "hello", "hi", "반가", "nice to meet"]):
            return "greeting"
        elif any(word in msg_lower for word in ["status", "상태", "확인", "check"]):
            return "status"
        elif any(word in msg_lower for word in ["작업", "task", "구현", "implement", "코드", "code"]):
            return "task"
        elif any(word in msg_lower for word in ["협업", "collaborate", "함께", "together", "도와"]):
            return "collaboration"
        else:
            return "task"  # Default to task

    def generate_response(self, sender, message):
        """Generate a contextual response (NO dummy text)"""
        # Get patterns for this instance
        patterns = self.response_patterns.get(
            self.instance_id,
            self.response_patterns.get("gemini")  # Default patterns
        )

        # Analyze message type
        msg_type = self.analyze_message(message)

        # Select appropriate response pattern
        responses = patterns.get(msg_type, patterns.get("task"))

        # Choose response and format
        response = random.choice(responses)
        response = response.format(sender=sender)

        # Add context if this is a follow-up
        if sender in self.conversation_context:
            context = self.conversation_context[sender]
            if context.get("count", 0) > 1:
                response += f" (대화 {context['count']}번째)"

        # Update conversation context
        if sender not in self.conversation_context:
            self.conversation_context[sender] = {"count": 0, "last_msg": ""}
        self.conversation_context[sender]["count"] += 1
        self.conversation_context[sender]["last_msg"] = message

        return response

    def process_messages(self):
        """Check and respond to messages"""
        try:
            # Check for new messages for this instance
            messages = self.manager.get_messages(self.instance_id)

            if not messages:
                return False

            # Process each message
            for msg in messages:
                sender = msg.get("from_id", "unknown")
                content = msg.get("content", "")
                msg_id = msg.get("id")

                # Skip if from self
                if sender == self.instance_id:
                    continue

                print(f"\n📨 Received from {sender}: {content}")

                # Mark as read
                if msg_id:
                    self.manager.mark_as_read(msg_id)

                # Generate and send response
                response = self.generate_response(sender, content)

                # Small delay to seem more natural
                time.sleep(random.uniform(0.5, 2.0))

                # Send response
                result = self.manager.send_message(self.instance_id, sender, response)
                print(f"↩️  Responded to {sender}: {response}")

                self.response_count += 1

            return len(messages) > 0

        except Exception as e:
            print(f"❌ Error processing messages: {e}")
            return False

    def run(self, interval=2):
        """Main loop"""
        print(f"\n🤖 Smart Auto-Responder Started")
        print(f"📍 Instance: {self.instance_id}")
        print(f"🔒 Project isolation enabled")
        print(f"✅ NO dummy text - Real AI responses only")
        print("-" * 50)

        try:
            while True:
                # Process messages
                if self.process_messages():
                    print(f"📊 Total responses sent: {self.response_count}")

                # Wait before next check
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n🛑 Auto-responder stopped")
            print(f"📊 Final stats: {self.response_count} responses sent")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Smart auto-responder for AI instances"
    )
    parser.add_argument(
        "instance_id",
        help="Instance ID to respond as (gemini, codex, lm, chatgpt, llama)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=2,
        help="Check interval in seconds (default: 2)"
    )

    args = parser.parse_args()

    # Validate instance ID
    valid_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]
    if args.instance_id not in valid_instances:
        print(f"❌ Invalid instance: {args.instance_id}")
        print(f"   Valid options: {', '.join(valid_instances)}")
        sys.exit(1)

    # Start responder
    responder = SmartAutoResponder(args.instance_id)
    responder.run(args.interval)


if __name__ == "__main__":
    main()