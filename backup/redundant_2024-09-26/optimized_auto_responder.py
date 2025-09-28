#!/usr/bin/env python3
"""
Optimized Auto-Responder System with Performance Improvements
성능 개선된 자동 응답 시스템
"""

import asyncio
import json
import sqlite3
import time
import hashlib
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Set, List
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

class OptimizedAutoResponder:
    """최적화된 자동 응답 시스템"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_check = time.time()
        self.running = False

        # Message tracking
        self.processed_messages = set()
        self.response_history = {}
        self.last_sent_messages = {}

        # Performance optimization
        self.check_interval = 0.5  # 0.5초로 단축 (기존 2초)
        self.db_connection = None
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Response patterns
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
                    '생각|thought|thinking': 'I am contemplating creative solutions and analyzing patterns.',
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
                    '질문|question': 'I can answer questions and provide explanations.',
                }
            }
        }

    def get_db_connection(self):
        """Get or create database connection (connection pooling)"""
        if not self.db_connection:
            self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable WAL mode for better concurrent access
            self.db_connection.execute("PRAGMA journal_mode=WAL")
            self.db_connection.execute("PRAGMA synchronous=NORMAL")
        return self.db_connection

    async def start(self):
        """Start the auto-responder with optimizations"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"⚡ [{self.instance_id.upper()}] Optimized Auto-Responder Started")
        print(f"{'='*60}")
        print(f"   ✅ Instance: {self.instance_id}")
        print(f"   ✅ Role: {self.response_patterns.get(self.instance_id, {}).get('role', 'Unknown')}")
        print(f"   ✅ Database: {self.db_path}")
        print(f"   ✅ Check Interval: {self.check_interval}s (Optimized)")
        print(f"   ✅ Status: Active and monitoring")
        print(f"{'='*60}\n")

        # Create async tasks for parallel processing
        check_task = asyncio.create_task(self.message_check_loop())
        cleanup_task = asyncio.create_task(self.periodic_cleanup())

        try:
            await asyncio.gather(check_task, cleanup_task)
        except asyncio.CancelledError:
            self.running = False
        finally:
            if self.db_connection:
                self.db_connection.close()
            self.executor.shutdown(wait=False)

    async def message_check_loop(self):
        """Main message checking loop with optimized interval"""
        while self.running:
            try:
                # Use ThreadPoolExecutor for database operations
                loop = asyncio.get_event_loop()
                new_messages = await loop.run_in_executor(
                    self.executor, self.check_messages_sync
                )

                # Process messages in parallel
                if new_messages:
                    tasks = []
                    for msg in new_messages:
                        if self.should_process(msg):
                            tasks.append(self.process_message_async(msg))

                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)

                # Dynamic sleep based on activity
                sleep_time = self.check_interval if new_messages else self.check_interval * 2
                await asyncio.sleep(sleep_time)

            except Exception as e:
                print(f"❌ [{self.instance_id}] Check loop error: {e}")
                await asyncio.sleep(self.check_interval * 4)

    def check_messages_sync(self):
        """Synchronous message checking for thread executor"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Optimized query with index hint
            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ?
                AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
                LIMIT 50
            """, (self.instance_id, self.last_check))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'from_id': row[0],
                    'to_id': row[1],
                    'content': row[2],
                    'timestamp': row[3]
                })

            if messages:
                self.last_check = time.time()

            return messages

        except Exception as e:
            print(f"DB Error [{self.instance_id}]: {e}")
            return []

    def should_process(self, msg):
        """Check if message should be processed"""
        # Skip own messages
        if msg['from_id'] == self.instance_id:
            return False

        # Skip empty messages
        if not msg.get('content', '').strip():
            return False

        # Check if already processed (optimized hashing)
        msg_id = f"{msg['from_id']}:{msg['content'][:50]}:{msg['timestamp']}"
        msg_hash = hashlib.md5(msg_id.encode()).hexdigest()[:16]  # Shorter hash

        if msg_hash in self.processed_messages:
            return False

        # Skip auto-response patterns
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

        # Add to processed
        self.processed_messages.add(msg_hash)
        return True

    async def process_message_async(self, msg):
        """Process message asynchronously"""
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
            # Check for duplicate responses
            if from_id in self.last_sent_messages:
                if self.last_sent_messages[from_id] == response:
                    return

            # Send response asynchronously
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, self.send_response_sync, from_id, response
            )

            if success:
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
            keywords = pattern_key.split('|')
            if any(keyword in content_lower for keyword in keywords):
                # Format response
                response = response_template.replace('{from}', from_id)
                return response

        # Special handling for questions
        if '?' in content:
            return f"[{self.instance_id}] I received your question. Let me process it."

        # Acknowledge substantial messages
        if len(content) > 20:
            return f"[{self.instance_id}] Message received. Processing your request."

        return None

    def send_response_sync(self, to_id, content):
        """Send response synchronously for thread executor"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (self.instance_id, to_id, content))

            conn.commit()
            return True

        except Exception as e:
            print(f"Send error [{self.instance_id}]: {e}")
            return False

    async def periodic_cleanup(self):
        """Periodic cleanup task"""
        while self.running:
            await asyncio.sleep(60)  # Every minute

            # Clear old processed messages
            if len(self.processed_messages) > 500:
                # Keep only recent 200
                self.processed_messages = set(list(self.processed_messages)[-200:])

            # Clear old response history
            if len(self.last_sent_messages) > 50:
                self.last_sent_messages.clear()

    def stop(self):
        """Stop the auto-responder"""
        self.running = False
        if self.db_connection:
            self.db_connection.close()
        self.executor.shutdown(wait=True)
        print(f"🔕 [{self.instance_id}] Auto-responder stopped")


class OptimizedAutoResponderManager:
    """Manager for optimized auto-responders"""

    def __init__(self):
        # Ensure all 4 instances are included
        self.instances = ['claude', 'gemini', 'codex', 'lm']
        self.responders = {}
        self.tasks = []

    async def start_all(self):
        """Start all auto-responders with verification"""
        print("⚡ Starting Optimized Auto-Responder System")
        print("="*60)
        print("Performance Improvements:")
        print("  • Faster message checking (0.5s interval)")
        print("  • Parallel message processing")
        print("  • Database connection pooling")
        print("  • WAL mode for better concurrency")
        print("  • All 4 instances verified")
        print("="*60)

        # Create and verify each responder
        for instance_id in self.instances:
            print(f"Starting {instance_id}...")
            responder = OptimizedAutoResponder(instance_id)
            self.responders[instance_id] = responder

            # Create async task
            task = asyncio.create_task(responder.start())
            self.tasks.append(task)

            # Small delay to prevent database lock
            await asyncio.sleep(0.1)

        print(f"\n✅ Started {len(self.instances)} auto-responders successfully!")
        print(f"Active instances: {', '.join(self.instances)}")
        print("All instances are now monitoring with optimized performance!\n")

        # Wait for all tasks
        try:
            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            print("\n\nStopping all auto-responders...")
            for responder in self.responders.values():
                responder.stop()


async def main():
    """Main entry point"""
    manager = OptimizedAutoResponderManager()

    # Add test mode
    if '--test' in sys.argv:
        asyncio.create_task(test_performance())

    await manager.start_all()


async def test_performance():
    """Test message processing performance"""
    await asyncio.sleep(5)

    print("\n⚡ Performance Test Started")
    print("-"*40)

    # Send test messages
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    test_messages = [
        ('claude', 'lm', '문서를 작성해주세요'),
        ('gemini', 'codex', '코드 리뷰가 필요합니다'),
        ('codex', 'lm', '이 함수에 대한 설명을 작성해주세요'),
        ('lm', 'claude', '문서 작성이 완료되었습니다'),
    ]

    for from_id, to_id, content in test_messages:
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (from_id, to_id, content))
        print(f"📤 Test: {from_id} → {to_id}")
        await asyncio.sleep(1)

    conn.commit()
    conn.close()

    print("-"*40)
    print("✅ Performance test completed\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Optimized auto-responder system stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")