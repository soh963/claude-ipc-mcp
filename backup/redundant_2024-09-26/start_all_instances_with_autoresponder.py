#!/usr/bin/env python3
"""
통합 IPC 시스템 시작 스크립트
모든 인스턴스를 등록하고 자동응답까지 실행
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path
import threading
import json
import sqlite3
import hashlib
import random
from typing import Dict, List, Optional
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))


class IPCInstance:
    """IPC 인스턴스 관리 클래스"""

    def __init__(self, instance_id: str, role: str):
        self.instance_id = instance_id
        self.role = role
        self.session_token = None
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.registered = False

    def register(self):
        """인스턴스 등록"""
        try:
            # ipc_register.py 실행
            result = subprocess.run(
                ['python', 'tools/ipc_register.py', self.instance_id],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.registered = True
                print(f"✅ [{self.instance_id}] Registered successfully")
                return True
            else:
                print(f"❌ [{self.instance_id}] Registration failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ [{self.instance_id}] Error during registration: {e}")
            return False


class UnifiedAutoResponder:
    """통합 자동 응답 시스템"""

    def __init__(self, instance: IPCInstance):
        self.instance = instance
        self.running = False
        self.last_check = time.time()
        self.processed_messages = set()
        self.response_patterns = self.load_response_patterns()

    def load_response_patterns(self):
        """인스턴스별 응답 패턴 로드"""
        patterns = {
            'claude': {
                'role': 'Master Coordinator & Assistant',
                'patterns': {
                    '안녕|hello|hi': f'Hello! I am Claude, the master coordinator. How can I help you today?',
                    '도움|help|assist': 'I can help with coordination, analysis, and task distribution.',
                    '상태|status': 'Claude IPC system is operational. All instances are active.',
                    '코드|code': 'For code tasks, I will coordinate with Codex for implementation.',
                    '분석|analyze': 'I can perform analysis or coordinate with Gemini for deeper insights.',
                }
            },
            'gemini': {
                'role': 'Multi-modal Assistant & Analyzer',
                'patterns': {
                    '안녕|hello|hi': 'Gemini here! Ready for multi-modal analysis and creative thinking.',
                    '이미지|image|visual': 'I specialize in visual analysis and creative tasks.',
                    '창의|creative': 'Let me generate creative ideas for your request.',
                    '분석|analyze': 'Starting multi-modal analysis now.',
                }
            },
            'codex': {
                'role': 'Code Specialist & Developer',
                'patterns': {
                    '안녕|hello|hi': 'Codex ready for code generation and review!',
                    '코드|code|program': 'I can help with code generation, review, and optimization.',
                    '버그|bug|fix': 'Bug fixing mode activated. Share the problematic code.',
                    '테스트|test': 'Test generation ready. Specify the function to test.',
                }
            },
            'lm': {
                'role': 'Language Model & Documentation',
                'patterns': {
                    '안녕|hello|hi': 'LM ready for documentation and language tasks!',
                    '문서|document|docs': 'Documentation mode activated. What needs documenting?',
                    '번역|translate': 'Translation services ready.',
                    '설명|explain': 'I can provide detailed explanations.',
                }
            },
            'testuser': {
                'role': 'Test Instance',
                'patterns': {
                    '안녕|hello|hi': 'Test instance responding!',
                    'test': 'Test successful!',
                }
            },
            'test1': {
                'role': 'Test Instance 1',
                'patterns': {
                    '안녕|hello|hi': 'Test1 instance active!',
                    'test': 'Test1 confirmation received!',
                }
            },
            'agent-test-1': {
                'role': 'Agent Test Instance',
                'patterns': {
                    '안녕|hello|hi': 'Agent test instance operational!',
                    'test': 'Agent test confirmed!',
                }
            }
        }

        # Return patterns for this instance, or default
        return patterns.get(self.instance.instance_id, {
            'role': 'Generic Instance',
            'patterns': {
                '안녕|hello|hi': f'{self.instance.instance_id} responding!',
                'help': f'{self.instance.instance_id} ready to help!',
            }
        })

    async def start(self):
        """자동 응답기 시작"""
        self.running = True
        print(f"🤖 [{self.instance.instance_id}] Auto-responder started - {self.response_patterns['role']}")

        while self.running:
            try:
                # Check for new messages
                new_messages = await self.check_messages()

                for msg in new_messages:
                    if self.should_process(msg):
                        await self.process_message(msg)

                await asyncio.sleep(2)

                # Cleanup old records
                if len(self.processed_messages) > 1000:
                    self.processed_messages.clear()

            except Exception as e:
                print(f"❌ [{self.instance.instance_id}] Error: {e}")
                await asyncio.sleep(5)

    async def check_messages(self):
        """새 메시지 확인"""
        try:
            conn = sqlite3.connect(self.instance.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
            """, (self.instance.instance_id, self.last_check))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'from_id': row[0],
                    'to_id': row[1],
                    'content': row[2],
                    'timestamp': row[3]
                })

            conn.close()

            if messages:
                self.last_check = time.time()

            return messages

        except Exception as e:
            return []

    def should_process(self, msg):
        """메시지 처리 여부 결정"""
        # Skip own messages
        if msg['from_id'] == self.instance.instance_id:
            return False

        # Skip empty messages
        if not msg['content'].strip():
            return False

        # Check if already processed
        msg_hash = hashlib.md5(f"{msg['from_id']}:{msg['content']}:{msg['timestamp']}".encode()).hexdigest()
        if msg_hash in self.processed_messages:
            return False

        # Skip auto-response patterns to prevent loops
        auto_patterns = [
            "요청을 확인했습니다",
            "처리 중입니다",
            "메시지 받았습니다",
            "received your message",
            "processing request",
            "responding!"
        ]

        content_lower = msg['content'].lower()
        if any(pattern in content_lower for pattern in auto_patterns):
            return False

        self.processed_messages.add(msg_hash)
        return True

    async def process_message(self, msg):
        """메시지 처리 및 응답"""
        from_id = msg['from_id']
        content = msg['content']

        print(f"📨 [{self.instance.instance_id}] Message from {from_id}: {content[:50]}...")

        # Generate response
        response = self.generate_response(from_id, content)

        if response:
            if await self.send_response(from_id, response):
                print(f"   ↩️ Replied to {from_id}")

    def generate_response(self, from_id, content):
        """응답 생성"""
        patterns = self.response_patterns.get('patterns', {})
        content_lower = content.lower()

        # Check each pattern
        for pattern_key, response_template in patterns.items():
            keywords = pattern_key.split('|')
            if any(keyword in content_lower for keyword in keywords):
                return f"[{self.instance.instance_id}] {response_template}"

        # For questions
        if '?' in content:
            return f"[{self.instance.instance_id}] I received your question. Processing..."

        return None

    async def send_response(self, to_id, content):
        """응답 전송"""
        try:
            conn = sqlite3.connect(self.instance.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
                VALUES (?, ?, ?, datetime('now'), 0)
            """, (self.instance.instance_id, to_id, content))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def stop(self):
        """자동 응답기 중지"""
        self.running = False


class UnifiedIPCManager:
    """통합 IPC 시스템 매니저"""

    def __init__(self):
        # Define all instances with their roles
        self.instance_configs = [
            ('claude', 'Master Coordinator'),
            ('gemini', 'Multi-modal Analyzer'),
            ('codex', 'Code Specialist'),
            ('lm', 'Documentation Expert'),
            ('testuser', 'Test Instance'),
            ('test1', 'Test Instance 1'),
            ('agent-test-1', 'Agent Test'),
        ]

        self.instances = {}
        self.responders = {}
        self.tasks = []

    async def initialize_all(self):
        """모든 인스턴스 초기화 및 등록"""
        print("\n" + "="*60)
        print("🚀 UNIFIED IPC SYSTEM STARTUP")
        print("="*60)
        print(f"Initializing {len(self.instance_configs)} instances...")
        print("-"*60)

        # Create and register instances
        for instance_id, role in self.instance_configs:
            instance = IPCInstance(instance_id, role)
            self.instances[instance_id] = instance

            # Register instance
            if instance.register():
                # Create auto-responder
                responder = UnifiedAutoResponder(instance)
                self.responders[instance_id] = responder
            else:
                print(f"⚠️ Skipping auto-responder for {instance_id} due to registration failure")

        print("-"*60)
        print(f"✅ {len(self.responders)} instances ready with auto-responders")
        print("="*60 + "\n")

    async def start_all_responders(self):
        """모든 자동응답기 시작"""
        print("🤖 Starting all auto-responders...")
        print("-"*60)

        for instance_id, responder in self.responders.items():
            task = asyncio.create_task(responder.start())
            self.tasks.append(task)

        print(f"✅ {len(self.tasks)} auto-responders running")
        print("-"*60)

    async def send_welcome_messages(self):
        """웰컴 메시지 전송"""
        await asyncio.sleep(2)

        print("\n📢 Sending welcome messages...")

        # Send broadcast from claude
        if 'claude' in self.instances:
            try:
                conn = sqlite3.connect(Path.home() / ".claude-ipc-data" / "messages.db")
                cursor = conn.cursor()

                # Broadcast message
                message = "🎉 Unified IPC System is now active! All instances are registered and auto-responders are running. Let's collaborate!"

                for instance_id in self.instances:
                    if instance_id != 'claude':
                        cursor.execute("""
                            INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
                            VALUES (?, ?, ?, datetime('now'), 0)
                        """, ('claude', instance_id, message))

                conn.commit()
                conn.close()

                print("✅ Welcome messages sent!")

            except Exception as e:
                print(f"❌ Error sending welcome messages: {e}")

    async def monitor_status(self):
        """시스템 상태 모니터링"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            active_count = sum(1 for r in self.responders.values() if r.running)
            if active_count < len(self.responders):
                print(f"⚠️ Only {active_count}/{len(self.responders)} responders active")

    async def run(self):
        """전체 시스템 실행"""
        # Initialize all instances
        await self.initialize_all()

        # Start all auto-responders
        await self.start_all_responders()

        # Send welcome messages
        await self.send_welcome_messages()

        # Start monitoring
        monitor_task = asyncio.create_task(self.monitor_status())

        try:
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all instances...")
            for responder in self.responders.values():
                responder.stop()
            print("✅ All instances stopped")


async def main():
    """메인 실행 함수"""
    manager = UnifiedIPCManager()
    await manager.run()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║     UNIFIED IPC SYSTEM WITH AUTO-RESPONDERS             ║
║                                                          ║
║  This script will:                                      ║
║  1. Register all IPC instances                          ║
║  2. Start auto-responders for each instance             ║
║  3. Enable inter-instance communication                 ║
║  4. Monitor system status                               ║
╚══════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✋ System stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")