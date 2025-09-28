#!/usr/bin/env python3
"""
AI-Powered Auto Responder
실제 AI를 사용하여 메시지에 응답하는 시스템
Ollama, OpenAI API, Google Gemini API 등 지원
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


class AIProvider:
    """AI 제공자 추상 클래스"""

    def __init__(self, name: str):
        self.name = name

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """AI 응답 생성"""
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama 로컬 LLM 제공자"""

    def __init__(self, model: str = "llama3.2"):
        super().__init__("Ollama")
        self.model = model
        self.api_url = f"{OLLAMA_API_URL}/api/generate"

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Ollama를 사용한 응답 생성"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            # Ollama API 호출
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Failed to generate response')
            else:
                print(f"Ollama API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print("❌ Ollama not running. Start with: ollama serve")
            return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None


class GeminiProvider(AIProvider):
    """Google Gemini API 제공자"""

    def __init__(self):
        super().__init__("Gemini")
        self.api_key = GEMINI_API_KEY

        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not set")

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Gemini API를 사용한 응답 생성"""
        if not self.api_key:
            return None

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')

            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            response = model.generate_content(full_prompt)

            return response.text

        except ImportError:
            print("❌ google-generativeai not installed. Run: pip install google-generativeai")
            return None
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None


class OpenAIProvider(AIProvider):
    """OpenAI API 제공자"""

    def __init__(self):
        super().__init__("OpenAI")
        self.api_key = OPENAI_API_KEY

        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not set")

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """OpenAI API를 사용한 응답 생성"""
        if not self.api_key:
            return None

        try:
            import openai

            openai.api_key = self.api_key

            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})

            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except ImportError:
            print("❌ openai not installed. Run: pip install openai")
            return None
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None


class AIResponder:
    """AI 기반 자동응답 시스템"""

    def __init__(self, instance_id: str, ai_provider: AIProvider = None):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.running = False

        # AI 제공자 설정
        self.ai_provider = ai_provider or self.auto_select_provider()

        # 메시지 추적
        self.processed_messages = set()
        self.conversation_history = {}  # 대화 기록 저장
        self.response_cooldown = {}

        # 인스턴스별 페르소나 설정
        self.personas = {
            'claude': "You are Claude, an intelligent assistant focused on coordination and analysis.",
            'gemini': "You are Gemini, a multi-modal AI assistant specializing in creative thinking and visual analysis.",
            'codex': "You are Codex, a code specialist focused on programming and software development.",
            'lm': "You are LM, a language model expert in documentation and technical writing.",
        }

        self.persona = self.personas.get(instance_id, f"You are {instance_id}, an AI assistant.")

    def auto_select_provider(self) -> AIProvider:
        """사용 가능한 AI 제공자 자동 선택"""

        # 1. Ollama 확인 (로컬 우선)
        try:
            response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"✅ Using Ollama (local LLM)")
                models = response.json().get('models', [])
                if models:
                    model_name = models[0]['name']
                    print(f"   Model: {model_name}")
                    return OllamaProvider(model_name)
                else:
                    print("   ⚠️ No models found. Run: ollama pull llama3.2")
                    return OllamaProvider()
        except:
            pass

        # 2. Gemini API 확인
        if GEMINI_API_KEY:
            print(f"✅ Using Gemini API")
            return GeminiProvider()

        # 3. OpenAI API 확인
        if OPENAI_API_KEY:
            print(f"✅ Using OpenAI API")
            return OpenAIProvider()

        print("⚠️ No AI provider available. Using fallback responses.")
        return None

    async def start(self):
        """AI 응답기 시작"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🤖 AI-Powered Responder for [{self.instance_id}]")
        print(f"{'='*60}")
        print(f"✅ Instance: {self.instance_id}")
        print(f"✅ AI Provider: {self.ai_provider.name if self.ai_provider else 'None (Fallback)'}")
        print(f"✅ Persona: {self.persona[:50]}...")
        print(f"{'='*60}\n")

        # 시작시 기존 메시지 읽음 처리
        self.mark_all_as_read()

        while self.running:
            try:
                # 새 메시지 확인
                new_messages = await self.check_new_messages()

                if new_messages:
                    print(f"\n🔍 Found {len(new_messages)} new messages")

                for msg in new_messages:
                    if self.should_respond(msg):
                        await self.process_message(msg)
                    else:
                        self.mark_as_read(msg['id'])

                await asyncio.sleep(2)  # 2초마다 확인

            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)

    def mark_all_as_read(self):
        """시작시 모든 메시지를 읽음 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET read_flag = 1
                WHERE to_id = ?
            """, (self.instance_id,))

            conn.commit()
            conn.close()

            print(f"✅ Marked all existing messages as read")

        except Exception as e:
            print(f"⚠️ Could not mark messages as read: {e}")

    async def check_new_messages(self):
        """새 메시지 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT rowid, from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND read_flag = 0
                ORDER BY timestamp ASC
                LIMIT 5
            """, (self.instance_id,))

            messages = []
            for row in cursor.fetchall():
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
            print(f"DB Error: {e}")
            return []

    def should_respond(self, msg):
        """응답 여부 결정"""
        # 자기 자신의 메시지는 무시
        if msg['from_id'] == self.instance_id:
            return False

        # 이미 처리한 메시지
        if msg['id'] in self.processed_messages:
            return False

        # 5초 쿨다운
        if msg['from_id'] in self.response_cooldown:
            if time.time() - self.response_cooldown[msg['from_id']] < 5:
                return False

        return True

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
            print(f"Failed to mark as read: {e}")

    async def process_message(self, msg):
        """AI를 사용한 메시지 처리"""
        self.processed_messages.add(msg['id'])
        self.mark_as_read(msg['id'])

        from_id = msg['from_id']
        content = msg['content']

        print(f"\n📨 [{self.instance_id}] From {from_id}:")
        print(f"   {content[:100]}...")

        # 대화 컨텍스트 가져오기
        context = self.get_conversation_context(from_id)

        # AI 응답 생성
        if self.ai_provider:
            print(f"   🤔 Generating AI response...")
            response = await self.generate_ai_response(content, context)
        else:
            response = self.generate_fallback_response(content)

        if response:
            # 응답 전송
            if await self.send_response(from_id, response):
                print(f"   ✅ AI Response sent!")
                print(f"   📤 {response[:100]}...")

                # 대화 기록 업데이트
                self.update_conversation_history(from_id, content, response)

                # 쿨다운 설정
                self.response_cooldown[from_id] = time.time()

    async def generate_ai_response(self, message: str, context: str) -> str:
        """AI를 사용한 응답 생성"""

        # 프롬프트 구성
        system_prompt = f"""
{self.persona}

You are participating in an IPC (Inter-Process Communication) system where different AI instances communicate with each other.
Respond naturally and helpfully to the message. Keep responses concise but informative.
If asked about files or code, provide helpful guidance even if you don't have direct access.
"""

        # 대화 컨텍스트 포함
        if context:
            system_prompt += f"\n\nPrevious conversation context:\n{context}"

        # AI 응답 생성
        response = await self.ai_provider.generate_response(message, system_prompt)

        if response:
            # 인스턴스 ID 태그 추가
            return f"[{self.instance_id} AI] {response}"
        else:
            return self.generate_fallback_response(message)

    def generate_fallback_response(self, message: str) -> str:
        """AI 사용 불가시 폴백 응답"""
        if '?' in message:
            return f"[{self.instance_id}] I received your question but AI is not available. Please check AI provider setup."
        else:
            return f"[{self.instance_id}] Message received. AI provider not configured."

    def get_conversation_context(self, from_id: str) -> str:
        """대화 컨텍스트 가져오기"""
        if from_id not in self.conversation_history:
            return ""

        history = self.conversation_history[from_id]
        # 최근 3개 대화만 컨텍스트로 사용
        recent = history[-3:] if len(history) > 3 else history

        context_lines = []
        for h in recent:
            context_lines.append(f"User: {h['user']}")
            context_lines.append(f"Assistant: {h['assistant']}")

        return "\n".join(context_lines)

    def update_conversation_history(self, from_id: str, user_msg: str, ai_response: str):
        """대화 기록 업데이트"""
        if from_id not in self.conversation_history:
            self.conversation_history[from_id] = []

        self.conversation_history[from_id].append({
            'user': user_msg,
            'assistant': ai_response,
            'timestamp': time.time()
        })

        # 10개 이상이면 오래된 것 삭제
        if len(self.conversation_history[from_id]) > 10:
            self.conversation_history[from_id] = self.conversation_history[from_id][-10:]

    async def send_response(self, to_id: str, content: str):
        """응답 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
                VALUES (?, ?, ?, datetime('now'), 0)
            """, (self.instance_id, to_id, content))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def stop(self):
        """중지"""
        self.running = False
        print(f"🛑 [{self.instance_id}] AI Responder stopped")


async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python ai_powered_responder.py <instance_id> [model]")
        print("Example: python ai_powered_responder.py gemini")
        print("         python ai_powered_responder.py claude llama3.2")
        sys.exit(1)

    instance_id = sys.argv[1]

    # AI 제공자 설정
    if len(sys.argv) > 2:
        model = sys.argv[2]
        provider = OllamaProvider(model)
    else:
        provider = None  # 자동 선택

    responder = AIResponder(instance_id, provider)

    try:
        await responder.start()
    except KeyboardInterrupt:
        print("\n✋ Stopped by user")
        responder.stop()


if __name__ == "__main__":
    asyncio.run(main())