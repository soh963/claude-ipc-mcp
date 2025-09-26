#!/usr/bin/env python3
"""
🤖 Simple Auto-Responder for AI Instances
각 AI 인스턴스가 메시지를 받으면 자동으로 응답
"""
from __future__ import annotations

import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

from session_utils import load_session

# Broker connection details
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876
CHECK_INTERVAL_SECONDS = 3
COOLDOWN_SECONDS = 8


class SimpleAutoResponder:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.project_root = Path(__file__).parent.parent
        self.last_received: Dict[str, str] = {}
        self.last_replied: Dict[str, str] = {}
        self.response_count = 0

        self.responses: Dict[str, List[str]] = {
            "gemini": [
                "Gemini입니다. 메시지 확인했습니다. 협업 준비 완료!",
                "알겠습니다. 작업을 진행하겠습니다.",
                "좋은 아이디어입니다! 구현해보겠습니다.",
                "Gemini가 분석 중입니다. 곧 결과를 공유하겠습니다.",
            ],
            "codex": [
                "Codex here. Code generation ready.",
                "코드 구현을 시작하겠습니다.",
                "최적화된 솔루션을 찾았습니다.",
                "테스트 코드와 함께 작성하겠습니다.",
            ],
            "lm": [
                "LM instance processing your request.",
                "텍스트 처리를 진행하겠습니다.",
                "문서 분석 완료했습니다.",
                "Language Model ready for collaboration.",
            ],
            "chatgpt": [
                "ChatGPT입니다. 함께 문제를 해결해봅시다!",
                "창의적인 접근을 시도해보겠습니다.",
                "분석 결과를 공유드립니다.",
                "좋은 협업이 될 것 같습니다!",
            ],
            "llama": [
                "Llama here. Processing locally.",
                "오픈소스 솔루션을 검토했습니다.",
                "로컬 환경에서 테스트 완료했습니다.",
                "효율적인 방법을 찾았습니다.",
            ],
        }

    # ------------------------------------------------------------------
    # Session-aware helper wrappers
    # ------------------------------------------------------------------
    def _run_tool(self, tool_path: Path, *args: str) -> subprocess.CompletedProcess:
        """Run one of the CLI tools with the current instance session."""
        session = load_session(self.instance_id)
        command = [
            sys.executable,
            str(tool_path),
            "--instance",
            session.instance_id,
            *args,
        ]
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=10,
        )

    def check_messages(self) -> List[Dict[str, str]]:
        """Return list of incoming messages."""
        result = self._run_tool(self.project_root / "tools" / "ipc_check.py")
        output = result.stdout.strip()
        if not output or "No new messages" in output:
            return []

        messages: List[Dict[str, str]] = []
        sender = None
        for line in output.splitlines():
            if line.startswith("From:"):
                sender = line.split(":", 1)[1].strip()
            elif line.startswith("Content:") and sender:
                content = line.split(":", 1)[1].strip()
                messages.append({"from": sender, "content": content})
                sender = None
        return messages

    def send_response(self, to_id: str, message: str) -> bool:
        """Send a response message via ipc_send."""
        result = self._run_tool(
            self.project_root / "tools" / "ipc_send.py",
            to_id,
            message,
        )
        if result.returncode != 0:
            print(f"Error sending response: {result.stderr or result.stdout}")
            return False
        return True

    # ------------------------------------------------------------------
    # Response selection / loop prevention
    # ------------------------------------------------------------------
    def get_response(self) -> str:
        pool = self.responses.get(self.instance_id.lower())
        if not pool:
            pool = [
                f"{self.instance_id}가 요청을 확인했습니다.",
                f"{self.instance_id}가 작업을 진행합니다.",
                f"{self.instance_id}가 메시지를 처리했습니다.",
            ]
        # Avoid repeating the same response twice in a row by shuffling until different
        candidate = random.choice(pool)
        attempts = 0
        while attempts < 5 and any(candidate == last for last in self.last_replied.values()):
            candidate = random.choice(pool)
            attempts += 1
        return candidate

    def should_ignore(self, sender: str, content: str) -> bool:
        if sender == self.instance_id:
            return True
        # Skip if message identical to the most recent one from this sender
        if self.last_received.get(sender) == content:
            return True
        # Skip if we already replied the exact same phrase recently
        last_reply = self.last_replied.get(sender)
        if last_reply and content.strip() == last_reply.strip():
            return True
        return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        print(f"🤖 Auto-Responder for {self.instance_id} started")
        print("📡 Checking messages every 3 seconds...")
        print("-" * 40)

        try:
            while True:
                for message in self.check_messages():
                    sender = message["from"]
                    content = message["content"]

                    if self.should_ignore(sender, content):
                        continue

                    print(f"\n📨 Message from {sender}: {content}")
                    self.last_received[sender] = content

                    response = self.get_response()
                    time.sleep(random.uniform(0.5, 1.5))

                    if self.send_response(sender, response):
                        print(f"↩️  Sent to {sender}: {response}")
                        self.response_count += 1
                        self.last_replied[sender] = response

                time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopped. Sent {self.response_count} responses.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python tools/simple_auto_responder.py <instance_id>")
        sys.exit(1)
    responder = SimpleAutoResponder(sys.argv[1])
    responder.run()


if __name__ == "__main__":
    main()
