#!/usr/bin/env python3
"""
AI-Powered Auto-responder for IPC instances
Responds using actual AI CLI tools (Gemini, ChatGPT, Ollama, etc.)

Usage:
    python tools/auto_responder_ai.py gemini        # Use Gemini AI
    python tools/auto_responder_ai.py ollama        # Use Ollama
    python tools/auto_responder_ai.py chatgpt       # Use ChatGPT
"""

import sqlite3
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import json
from ai_cli_adapter import AICliAdapter


class AIAutoResponder:
    def __init__(self, instance_id="gemini", ai_type="ollama"):
        """
        Initialize AI-powered auto-responder

        Args:
            instance_id: IPC instance ID
            ai_type: Type of AI to use ('gemini', 'ollama', 'chatgpt', etc.)
        """
        self.instance_id = instance_id
        self.ai_type = ai_type
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_message_id = 0

        # Initialize AI adapter
        try:
            self.ai_adapter = AICliAdapter(ai_type)
            print(f"✅ AI adapter initialized: {ai_type}", flush=True)
        except ValueError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)

        # Status metadata
        try:
            self.status_dir = Path(os.path.expandvars(r"%USERPROFILE%\.claude-ipc-data")) / "responders"
        except Exception:
            self.status_dir = Path.home() / ".claude-ipc-data" / "responders"
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.status_path = self.status_dir / f"{self.instance_id}.json"
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.last_check_at = None
        self.last_response_at = None

        self.init_db()
        self._write_status(last_check=True)

    def init_db(self):
        """Initialize database connection"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=2.0)
            cursor = conn.cursor()

            # Best-effort pragmas
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA busy_timeout=2000;")
            except Exception:
                pass

            # Get last message ID
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_message_id = result[0]
                print(f"📊 Last message ID = {self.last_message_id}", flush=True)
            else:
                print("📊 No messages, starting from ID = 0", flush=True)

            # Create indexes
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_to_id ON messages(to_id, id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id, id)")
                conn.commit()
            except Exception:
                pass

        except sqlite3.OperationalError as e:
            print(f"⏳ Waiting for DB initialization: {e}", flush=True)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def check_for_requests(self):
        """Check for new incoming messages"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get new messages
            cursor.execute(
                """
                SELECT id, from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND id > ?
                ORDER BY id ASC
            """,
                (self.instance_id, self.last_message_id),
            )

            messages = cursor.fetchall()

            if messages:
                print(f"\n🔍 Found {len(messages)} new message(s)", flush=True)

            import re
            for msg_id, from_id, content, timestamp in messages:
                self.last_message_id = msg_id

                # Ignore self-messages
                if from_id == self.instance_id:
                    continue

                print(f"\n📥 Message from [{from_id}]: {content}", flush=True)

                # Extract correlation token
                corr = None
                try:
                    m = re.search(r"\[corr=([^\]]+)\]", content or "")
                    if m:
                        corr = m.group(1)
                        # Remove correlation token from content
                        content = re.sub(r"\[corr=[^\]]+\]", "", content).strip()
                except Exception:
                    corr = None

                # Generate AI response
                response = self.generate_ai_response(content, from_id)

                if response:
                    # Add correlation token back
                    if corr and f"[corr={corr}]" not in response:
                        response = f"{response} [corr={corr}]"

                    self.send_response(from_id, response)
                    print("✅ AI response sent!", flush=True)
                else:
                    print("❌ Failed to generate AI response", flush=True)

        except sqlite3.OperationalError as e:
            print(f"⏳ DB not ready: {e}", flush=True)
        finally:
            try:
                conn.close()
            except Exception:
                pass

            # Update last check time
            try:
                self.last_check_at = datetime.now().isoformat(timespec="seconds")
                self._write_status()
            except Exception:
                pass

    def generate_ai_response(self, content, from_id):
        """
        Generate response using actual AI CLI

        Args:
            content: User message
            from_id: Sender instance ID

        Returns:
            AI-generated response or None
        """
        # Build context-aware prompt
        prompt = f"""You are {self.instance_id}, an AI assistant in an inter-AI communication system.
You received a message from {from_id}: "{content}"

Please provide a helpful, concise response. Keep it under 200 words."""

        try:
            # Get AI response
            ai_response = self.ai_adapter.send_message(prompt, timeout=30)

            if ai_response:
                # Clean and format response
                response = ai_response.strip()

                # Add AI signature
                response = f"{response}\n\n— {self.ai_type.capitalize()} via {self.instance_id}"

                return response
            else:
                return None

        except Exception as e:
            print(f"❌ AI error: {e}", flush=True)
            return None

    def send_response(self, to_id, message):
        """Send response message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (self.instance_id, to_id, message, timestamp),
        )

        conn.commit()
        conn.close()

        print(f"📤 Response sent to [{to_id}]: {message[:100]}...")

        # Update status
        try:
            self.last_response_at = datetime.now().isoformat(timespec="seconds")
            self._write_status()
        except Exception:
            pass

    def run(self):
        """Run AI auto-responder"""
        print("=" * 70, flush=True)
        print(f"🤖 AI-Powered Auto-Responder Started", flush=True)
        print(f"   Instance: {self.instance_id}", flush=True)
        print(f"   AI Type: {self.ai_type}", flush=True)
        print(f"   Database: {self.db_path}", flush=True)
        print("=" * 70, flush=True)
        print("Running... (Press Ctrl+C to stop)", flush=True)
        print("=" * 70, flush=True)

        try:
            check_count = 0
            while True:
                check_count += 1
                if check_count % 30 == 0:  # Status every minute
                    print(f"⏰ Status: Running... (checks: {check_count})", flush=True)

                self.check_for_requests()
                time.sleep(2)  # Check every 2 seconds

        except KeyboardInterrupt:
            print("\n\n👋 AI Auto-Responder Stopped", flush=True)

    def _write_status(self, last_check: bool = False):
        """Write status file for monitoring"""
        payload = {
            "instance_id": self.instance_id,
            "ai_type": self.ai_type,
            "policy": "ai-powered",
            "started_at": self.started_at,
            "last_check_at": self.last_check_at,
            "last_response_at": self.last_response_at,
        }

        if last_check:
            payload["last_check_at"] = datetime.now().isoformat(timespec="seconds")
            self.last_check_at = payload["last_check_at"]

        try:
            self.status_path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/auto_responder_ai.py <ai_type> [instance_id]")
        print("AI types: gemini, ollama, chatgpt, aider")
        print("\nExample:")
        print("  python tools/auto_responder_ai.py ollama")
        print("  python tools/auto_responder_ai.py gemini gemini-assistant")
        sys.exit(1)

    ai_type = sys.argv[1].lower()
    instance_id = sys.argv[2] if len(sys.argv) > 2 else ai_type

    print(f"🚀 Starting AI Auto-Responder")
    print(f"   Instance: {instance_id}")
    print(f"   AI Type: {ai_type}\n")

    responder = AIAutoResponder(instance_id=instance_id, ai_type=ai_type)
    responder.run()
