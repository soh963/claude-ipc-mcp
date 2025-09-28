#!/usr/bin/env python3
"""
Fixed AI-Powered Auto Responder
메시지 라우팅 버그 수정 버전
각 인스턴스가 자신에게 온 메시지만 정확히 처리
"""

import asyncio
import sqlite3
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import requests
from typing import Dict, List, Optional, Set
import hashlib

# 환경 변수 설정
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class OllamaProvider:
    """Ollama 로컬 LLM 제공자"""

    def __init__(self, model: str = "llama3.2"):
        self.name = "Ollama"
        self.model = model
        self.api_url = f"{OLLAMA_API_URL}/api/generate"

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Ollama를 사용한 응답 생성"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 300
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Failed to generate response')
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print("❌ Ollama not running. Using fallback responses.")
            return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None


class FixedAIResponder:
    """수정된 AI 기반 자동응답 시스템"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.running = False

        # AI 제공자 설정
        self.ai_provider = self.auto_select_provider()

        # 메시지 추적
        self.processed_message_ids = set()  # rowid 추적
        self.conversation_history = {}
        self.last_check_time = 0

        # 인스턴스별 페르소나
        self.personas = {
            'claude': "You are Claude, the master coordinator of the IPC system. You help manage communication between AI instances and provide intelligent analysis.",
            'gemini': "You are Gemini, a creative multi-modal AI assistant. You excel at creative thinking and can help with various tasks including code analysis.",
            'codex': "You are Codex, a code specialist. You help with programming tasks, code review, and software development.",
            'lm': "You are LM, a language model expert in documentation and technical writing.",
        }

        self.persona = self.personas.get(instance_id, f"You are {instance_id}, an AI assistant.")

    def auto_select_provider(self):
        """사용 가능한 AI 제공자 자동 선택"""
        # Ollama 확인
        try:
            response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    model_name = models[0]['name']
                    print(f"✅ Using Ollama with model: {model_name}")
                    return OllamaProvider(model_name)
                else:
                    print("⚠️ Ollama running but no models. Using llama3.2")
                    return OllamaProvider("llama3.2")
        except:
            pass

        print("⚠️ No AI provider available. Using fallback responses.")
        return None

    async def start(self):
        """AI 응답기 시작"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🤖 Fixed AI Responder for [{self.instance_id}]")
        print(f"{'='*60}")
        print(f"✅ Instance: {self.instance_id}")
        print(f"✅ AI Provider: {self.ai_provider.name if self.ai_provider else 'Fallback'}")
        print(f"✅ Database: {self.db_path}")
        print(f"{'='*60}\n")

        # 시작시 모든 기존 메시지를 읽음 처리
        self.mark_existing_as_read()

        while self.running:
            try:
                # 새 메시지 확인 - to_id가 정확히 자신인 것만
                new_messages = await self.check_new_messages()

                if new_messages:
                    print(f"\n🔍 [{self.instance_id}] Found {len(new_messages)} new messages FOR ME")
                    for msg in new_messages:
                        print(f"   📨 From: {msg['from_id']} -> To: {msg['to_id']} (Me)")

                for msg in new_messages:
                    # 자신에게 온 메시지만 처리
                    if msg['to_id'] == self.instance_id:
                        await self.process_message(msg)
                    else:
                        print(f"   ⚠️ Wrong recipient! {msg['to_id']} != {self.instance_id}")

                await asyncio.sleep(3)

                # 주기적으로 처리 기록 정리
                if len(self.processed_message_ids) > 100:
                    self.processed_message_ids = set(list(self.processed_message_ids)[-50:])

            except Exception as e:
                print(f"❌ [{self.instance_id}] Error: {e}")
                await asyncio.sleep(5)

    def mark_existing_as_read(self):
        """시작시 기존 메시지 읽음 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 자신에게 온 메시지만 읽음 처리
            cursor.execute("""
                UPDATE messages
                SET read_flag = 1
                WHERE to_id = ? AND read_flag = 0
            """, (self.instance_id,))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            if affected > 0:
                print(f"✅ Marked {affected} existing messages as read")

        except Exception as e:
            print(f"⚠️ Could not mark messages as read: {e}")

    async def check_new_messages(self):
        """새 메시지 확인 - to_id가 정확히 자신인 것만"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # to_id가 정확히 자신이고 read_flag가 0인 메시지만
            cursor.execute("""
                SELECT rowid, from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND read_flag = 0
                ORDER BY timestamp ASC
                LIMIT 5
            """, (self.instance_id,))

            messages = []
            for row in cursor.fetchall():
                # Double check - to_id가 정확히 자신인지 확인
                if row[2] == self.instance_id:
                    messages.append({
                        'id': row[0],
                        'from_id': row[1],
                        'to_id': row[2],
                        'content': row[3],
                        'timestamp': row[4]
                    })

            conn.close()
            return messages

        except Exception as e:
            print(f"❌ DB Error: {e}")
            return []

    async def process_message(self, msg):
        """메시지 처리"""
        # 중복 처리 방지
        if msg['id'] in self.processed_message_ids:
            print(f"   ⏭️ Already processed message {msg['id']}")
            return

        # 자기 자신의 메시지는 무시
        if msg['from_id'] == self.instance_id:
            self.mark_as_read(msg['id'])
            return

        # 처리 기록
        self.processed_message_ids.add(msg['id'])
        self.mark_as_read(msg['id'])

        from_id = msg['from_id']
        content = msg['content']

        print(f"\n📨 [{self.instance_id}] Processing message from {from_id}")
        print(f"   Content: {content[:100]}...")

        # AI 응답 생성
        response = await self.generate_ai_response(from_id, content)

        if response:
            # 응답 전송
            if await self.send_response(from_id, response):
                print(f"   ✅ Response sent to {from_id}")
                print(f"   📤 {response[:100]}...")

                # 대화 기록 업데이트
                self.update_conversation_history(from_id, content, response)

    async def generate_ai_response(self, from_id: str, message: str) -> str:
        """AI를 사용한 응답 생성"""

        # 특수 명령어 처리
        if "파일 리스트" in message or "file list" in message.lower():
            return await self.handle_file_list_request(from_id)

        if "상태" in message or "status" in message.lower():
            return self.get_status_response()

        # AI 응답 생성
        if self.ai_provider:
            context = f"""
{self.persona}

You are communicating with {from_id} through the IPC system.
Previous context: {self.get_conversation_context(from_id)}

Respond naturally and helpfully. Keep responses concise (2-3 sentences).
If asked about technical details, provide specific information.
"""

            response = await self.ai_provider.generate_response(message, context)

            if response:
                return f"[{self.instance_id}] {response}"

        # Fallback 응답
        return self.generate_fallback_response(from_id, message)

    async def handle_file_list_request(self, from_id: str) -> str:
        """파일 리스트 요청 처리"""
        if self.instance_id == "gemini":
            return f"""[{self.instance_id}] Claude IPC MCP 프로젝트 주요 파일:

📁 Core Files:
- ai_powered_responder.py (AI 응답 시스템)
- safe_autoresponder.py (안전 응답 시스템)
- fixed_ai_responder.py (수정된 AI 응답)

📁 Tools:
- tools/ipc_register.py (인스턴스 등록)
- tools/ipc_send.py (메시지 전송)
- tools/ipc_check.py (메시지 확인)

📁 Scripts:
- start_ai_ipc_system.bat (AI 시스템 시작)
- start_safe_ipc_system.bat (안전 시스템)

총 70+ 파일이 프로젝트에 있습니다."""

        return f"[{self.instance_id}] 파일 리스트는 gemini에게 문의하세요."

    def get_status_response(self) -> str:
        """상태 응답 생성"""
        return f"""[{self.instance_id}] 시스템 상태:
✅ Instance: {self.instance_id} (Active)
✅ AI Provider: {self.ai_provider.name if self.ai_provider else 'Fallback'}
✅ Messages Processed: {len(self.processed_message_ids)}
✅ Status: Operational"""

    def generate_fallback_response(self, from_id: str, message: str) -> str:
        """Fallback 응답"""
        if "안녕" in message or "hello" in message.lower():
            return f"[{self.instance_id}] 안녕하세요 {from_id}! 무엇을 도와드릴까요?"

        if "?" in message:
            return f"[{self.instance_id}] 질문을 받았습니다. 처리 중입니다..."

        return f"[{self.instance_id}] 메시지를 받았습니다: '{message[:50]}...'"

    def get_conversation_context(self, from_id: str) -> str:
        """대화 컨텍스트 가져오기"""
        if from_id not in self.conversation_history:
            return "No previous conversation"

        history = self.conversation_history[from_id]
        recent = history[-2:] if len(history) > 2 else history

        context_lines = []
        for h in recent:
            context_lines.append(f"{from_id}: {h['user'][:50]}")
            context_lines.append(f"Me: {h['assistant'][:50]}")

        return " | ".join(context_lines)

    def update_conversation_history(self, from_id: str, user_msg: str, ai_response: str):
        """대화 기록 업데이트"""
        if from_id not in self.conversation_history:
            self.conversation_history[from_id] = []

        self.conversation_history[from_id].append({
            'user': user_msg,
            'assistant': ai_response,
            'timestamp': time.time()
        })

        # 5개 이상이면 오래된 것 삭제
        if len(self.conversation_history[from_id]) > 5:
            self.conversation_history[from_id] = self.conversation_history[from_id][-5:]

    def mark_as_read(self, message_id):
        """메시지를 읽음 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET read_flag = 1
                WHERE rowid = ?
            """, (message_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Failed to mark as read: {e}")

    async def send_response(self, to_id: str, content: str):
        """응답 전송 - from_id와 to_id를 정확히 설정"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # from_id는 자신, to_id는 메시지 보낸 사람
            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
                VALUES (?, ?, ?, datetime('now'), 0)
            """, (self.instance_id, to_id, content))

            conn.commit()
            conn.close()

            print(f"   📮 Sent: {self.instance_id} -> {to_id}")
            return True

        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def stop(self):
        """중지"""
        self.running = False
        print(f"🛑 [{self.instance_id}] AI Responder stopped")


async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python fixed_ai_responder.py <instance_id>")
        print("Example: python fixed_ai_responder.py claude")
        sys.exit(1)

    instance_id = sys.argv[1]
    responder = FixedAIResponder(instance_id)

    try:
        await responder.start()
    except KeyboardInterrupt:
        print("\n✋ Stopped by user")
        responder.stop()


if __name__ == "__main__":
    asyncio.run(main())