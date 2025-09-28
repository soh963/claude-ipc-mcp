#!/usr/bin/env python3
"""
Unified Auto-Responder System for All AI CLI Instances
모든 AI CLI 인스턴스를 위한 통합 자동 응답 시스템
Solves: 메시지 보내기는 되지만 메시지를 캐치하고 답변하는것이 안되는 상황
"""

import asyncio
import json
import sqlite3
import time
import hashlib
import random
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Set, List
from datetime import datetime, timedelta
import subprocess
import threading

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

class UnifiedAutoResponder:
    """통합 자동 응답 시스템 - 모든 인스턴스의 메시지를 처리"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_check = time.time()
        self.running = False

        # Message tracking to prevent loops
        self.processed_messages = set()
        self.response_history = {}
        self.last_sent_messages = {}
        self.message_cooldown = {}

        # Instance-specific response patterns
        self.response_patterns = self.load_response_patterns()

    def load_response_patterns(self):
        """Load intelligent response patterns for each instance"""
        return {
            'claude': {
                'role': 'Master Coordinator & Assistant',
                'patterns': {
                    '안녕|hello|hi': 'Hello {from}! I am Claude, the master coordinator. How can I help you today?',
                    '생각|thought|thinking': 'I am currently analyzing the IPC system and coordinating between instances.',
                    '도움|help|assist': 'I can help with coordination, analysis, and task distribution. What do you need?',
                    '상태|status': 'Claude IPC system is operational. All instances are active.',
                    '프로젝트|project': 'I can help coordinate project tasks across all instances.',
                    '코드|code': 'For code tasks, I will coordinate with Codex for implementation.',
                    '분석|analyze': 'I can perform analysis or coordinate with Gemini for deeper insights.',
                }
            },
            'gemini': {
                'role': 'Multi-modal Assistant & Analyzer',
                'patterns': {
                    '안녕|hello|hi': 'Hello {from}! Gemini here, ready for multi-modal analysis.',
                    '생각|thought|thinking': 'I am contemplating creative solutions and analyzing patterns in our communication.',
                    '이미지|image|visual': 'I can help with visual analysis and creative tasks.',
                    '창의|creative': 'Let me generate creative ideas for your request.',
                    '분석|analyze': 'Starting multi-modal analysis now.',
                    '도움|help': 'I specialize in creative thinking and visual analysis.',
                }
            },
            'codex': {
                'role': 'Code Specialist & Developer',
                'patterns': {
                    '안녕|hello|hi': 'Hello {from}! Codex ready for code generation and review.',
                    '코드|code|program': 'I can help with code generation, review, and optimization.',
                    '버그|bug|fix': 'Bug fixing mode activated. Share the problematic code.',
                    '테스트|test': 'Test generation ready. Specify the function to test.',
                    '리뷰|review': 'Code review mode activated. Please share the code.',
                    '생성|generate|create': 'Ready to generate code. Specify language and requirements.',
                }
            },
            'lm': {
                'role': 'Language Model & Documentation',
                'patterns': {
                    '안녕|hello|hi': 'Hello {from}! LM ready for documentation and language tasks.',
                    '문서|document|docs': 'Documentation mode activated. What needs documenting?',
                    '번역|translate': 'Translation services ready. Specify source and target languages.',
                    '설명|explain': 'I can provide detailed explanations and documentation.',
                    '가이드|guide': 'Ready to create guides and tutorials.',
                }
            }
        }

    async def start(self):
        """Start the auto-responder"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🚀 [{self.instance_id.upper()}] Auto-Responder Started")
        print(f"{'='*60}")
        print(f"   ✅ Instance: {self.instance_id}")
        print(f"   ✅ Role: {self.response_patterns[self.instance_id]['role']}")
        print(f"   ✅ Database: {self.db_path}")
        print(f"   ✅ Status: Active and monitoring")
        print(f"{'='*60}\n")

        while self.running:
            try:
                # Check for new messages
                new_messages = await self.check_messages()

                for msg in new_messages:
                    if self.should_process(msg):
                        await self.process_message(msg)

                await asyncio.sleep(2)

                # Cleanup old records periodically
                if len(self.processed_messages) > 1000:
                    self.processed_messages.clear()

            except Exception as e:
                print(f"❌ [{self.instance_id}] Error: {e}")
                await asyncio.sleep(5)

    async def check_messages(self):
        """Check for new messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get messages for this instance since last check
            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
            """, (self.instance_id, self.last_check))

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
            print(f"DB Error: {e}")
            return []

    def should_process(self, msg):
        """Check if message should be processed"""
        # Skip own messages
        if msg['from_id'] == self.instance_id:
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
            "processing request"
        ]

        content_lower = msg['content'].lower()
        if any(pattern in content_lower for pattern in auto_patterns):
            return False

        # Mark as processed
        self.processed_messages.add(msg_hash)
        return True

    async def process_message(self, msg):
        """Process incoming message and generate response"""
        from_id = msg['from_id']
        content = msg['content']

        # Display received message
        print(f"\n📨 [{self.instance_id.upper()}] Received Message")
        print(f"   From: {from_id}")
        print(f"   Content: {content}")
        print(f"   Time: {msg['timestamp']}")

        # Generate response
        response = self.generate_response(from_id, content)

        if response:
            # Check if same as last message (prevent loops)
            if from_id in self.last_sent_messages:
                if self.last_sent_messages[from_id] == response:
                    return

            # Send response
            if await self.send_response(from_id, response):
                print(f"   ↩️ Reply: {response}")
                self.last_sent_messages[from_id] = response

    def generate_response(self, from_id, content):
        """Generate intelligent response based on patterns"""
        if self.instance_id not in self.response_patterns:
            return None

        patterns = self.response_patterns[self.instance_id]['patterns']
        content_lower = content.lower()

        # Check each pattern
        for pattern_key, response_template in patterns.items():
            # Split pattern by | for multiple keywords
            keywords = pattern_key.split('|')
            if any(keyword in content_lower for keyword in keywords):
                # Format response with sender info
                response = response_template.replace('{from}', from_id)
                return response

        # Special handling for questions
        if '?' in content:
            return f"[{self.instance_id}] I received your question. Let me think about it and get back to you."

        # For important messages that don't match patterns, acknowledge
        if len(content) > 20:  # Substantial message
            return f"[{self.instance_id}] Message received. Processing your request."

        return None

    async def send_response(self, to_id, content):
        """Send response message to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (self.instance_id, to_id, content))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def stop(self):
        """Stop the auto-responder"""
        self.running = False
        print(f"🔕 [{self.instance_id}] Auto-responder stopped")


class AutoResponderManager:
    """Manager to run auto-responders for all instances"""

    def __init__(self):
        self.instances = ['claude', 'gemini', 'codex', 'lm']
        self.responders = {}
        self.tasks = []

    async def start_all(self):
        """Start auto-responders for all instances"""
        print("🌐 Starting Unified Auto-Responder System")
        print("="*60)
        print("This solves: 메시지 보내기는 되지만 메시지를 캐치하고 답변하는것이 안되는 상황")
        print("="*60)

        # Create responders for each instance
        for instance_id in self.instances:
            responder = UnifiedAutoResponder(instance_id)
            self.responders[instance_id] = responder

            # Create async task for each responder
            task = asyncio.create_task(responder.start())
            self.tasks.append(task)

        print(f"\n✅ Started {len(self.instances)} auto-responders")
        print("All instances are now monitoring and responding to messages!\n")

        # Wait for all tasks
        try:
            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            print("\n\nStopping all auto-responders...")
            for responder in self.responders.values():
                responder.stop()

    async def test_communication(self):
        """Send test messages between instances"""
        await asyncio.sleep(3)  # Wait for responders to start

        print("\n🧪 Testing Communication Between Instances")
        print("-"*40)

        # Test messages
        test_pairs = [
            ('claude', 'gemini', 'Hello Gemini! How are you today?'),
            ('gemini', 'codex', 'Can you help with code review?'),
            ('codex', 'lm', 'Need documentation for this function'),
            ('lm', 'claude', 'Documentation complete. Please review.')
        ]

        for from_id, to_id, message in test_pairs:
            try:
                conn = sqlite3.connect(Path.home() / ".claude-ipc-data" / "messages.db")
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO messages (from_id, to_id, content, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                """, (from_id, to_id, message))

                conn.commit()
                conn.close()

                print(f"📤 Test: {from_id} → {to_id}: {message}")
                await asyncio.sleep(2)

            except Exception as e:
                print(f"Test error: {e}")


async def main():
    """Main entry point"""
    manager = AutoResponderManager()

    # Start test task if requested
    if '--test' in sys.argv:
        asyncio.create_task(manager.test_communication())

    # Start all responders
    await manager.start_all()


if __name__ == "__main__":
    try:
        # Check if running individually or all
        if len(sys.argv) > 1 and sys.argv[1] != '--test':
            # Run single instance
            instance_id = sys.argv[1]
            responder = UnifiedAutoResponder(instance_id)
            asyncio.run(responder.start())
        else:
            # Run all instances
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n\n✋ Auto-responder system stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")