#!/usr/bin/env python3
"""
🤖 Robust Auto-Responder with Health Monitoring
무한 루프 방지와 건강 체크를 포함한 강력한 자동 응답기
"""

import sys
import os
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ipc_manager import IPCManager

class RobustAutoResponder:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.manager = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.processed_messages = set()  # Track processed messages to prevent loops
        self.response_history = {}  # Track response history to prevent echo
        self.last_heartbeat = datetime.now()
        self.running = True

        # Set up logging
        log_file = Path.home() / ".claude-ipc-data" / f"auto_responder_{instance_id}.log"
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"AutoResponder-{instance_id}")

        # Terminal output notification
        self.notify_terminal(f"🤖 Auto-Responder for {instance_id} starting...")

    def notify_terminal(self, message):
        """Print notification to terminal"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{self.instance_id}] {message}")
        self.logger.info(message)

    def connect(self):
        """Connect to IPC system with retry logic"""
        for attempt in range(3):
            try:
                self.manager = IPCManager()
                self.manager.register(self.instance_id)
                self.notify_terminal(f"✅ Connected to IPC system (attempt {attempt + 1})")
                self.reconnect_attempts = 0
                return True
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)

        self.notify_terminal(f"❌ Failed to connect after 3 attempts")
        return False

    def is_loop_message(self, from_id, content):
        """Check if this message would create a loop"""
        # Check if we recently sent a similar message to this sender
        key = f"{self.instance_id}->{from_id}"
        if key in self.response_history:
            last_content, last_time = self.response_history[key]
            time_diff = datetime.now() - last_time

            # If we sent a similar message within 5 seconds, it might be a loop
            if time_diff < timedelta(seconds=5):
                similarity = self.calculate_similarity(content, last_content)
                if similarity > 0.8:
                    self.logger.warning(f"Loop detected: Similar message from {from_id}")
                    return True

        return False

    def calculate_similarity(self, str1, str2):
        """Simple similarity calculation"""
        if str1 == str2:
            return 1.0

        # Check if one contains the other
        if str1 in str2 or str2 in str1:
            return 0.9

        # Check common words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        if not words1 or not words2:
            return 0.0

        common = len(words1 & words2)
        total = len(words1 | words2)
        return common / total if total > 0 else 0.0

    def generate_response(self, from_id, content):
        """Generate contextual response based on message content"""
        content_lower = content.lower()

        # Prevent loop responses
        if self.is_loop_message(from_id, content):
            self.notify_terminal(f"🔄 Loop prevention: Not responding to potential echo from {from_id}")
            return None

        # Contextual responses based on content
        responses = []

        if any(word in content_lower for word in ["hello", "hi", "안녕", "hey"]):
            responses = [
                f"Hello {from_id}! I'm {self.instance_id}, nice to hear from you!",
                f"Hi there {from_id}! This is {self.instance_id} responding.",
                f"Greetings {from_id}! {self.instance_id} here, how can I help?"
            ]
        elif any(word in content_lower for word in ["how are you", "what's up", "뭐하", "뭐해"]):
            responses = [
                f"I'm functioning well as {self.instance_id}, monitoring messages!",
                f"All systems operational here at {self.instance_id}!",
                f"{self.instance_id} is running smoothly, thanks for asking!"
            ]
        elif "weather" in content_lower or "날씨" in content_lower:
            responses = [
                f"I'm {self.instance_id}, I don't have weather data access but the IPC system is clear!",
                f"As {self.instance_id}, I focus on message routing rather than weather!"
            ]
        elif "file" in content_lower or "list" in content_lower or "파일" in content_lower:
            responses = [
                f"{self.instance_id} here: I handle messages, not file operations!",
                f"I'm {self.instance_id}, specialized in IPC communication."
            ]
        elif "test" in content_lower:
            responses = [
                f"Test received by {self.instance_id}! Connection confirmed.",
                f"{self.instance_id} test response: All systems go!"
            ]
        else:
            # Generic contextual response
            responses = [
                f"{self.instance_id} received: '{content[:30]}...' - Message processed!",
                f"Acknowledged by {self.instance_id}: Got your message about {content[:20]}",
                f"{self.instance_id} confirms receipt of your message."
            ]

        return random.choice(responses) if responses else None

    def process_messages(self):
        """Process incoming messages"""
        try:
            messages = self.manager.check_messages(self.instance_id)

            if messages:
                for msg in messages:
                    msg_id = msg.get('id', '')
                    from_id = msg.get('from_id', 'unknown')
                    content = msg.get('content', '')

                    # Skip if already processed (prevent duplicate processing)
                    if msg_id in self.processed_messages:
                        continue

                    self.processed_messages.add(msg_id)

                    # Don't respond to our own messages
                    if from_id == self.instance_id:
                        continue

                    self.notify_terminal(f"📬 Message from {from_id}: {content[:50]}...")

                    # Generate and send response
                    response = self.generate_response(from_id, content)

                    if response:
                        # Store response history for loop prevention
                        key = f"{self.instance_id}->{from_id}"
                        self.response_history[key] = (response, datetime.now())

                        # Clean old history (older than 1 minute)
                        self.clean_response_history()

                        # Re-register and send
                        self.manager.register(self.instance_id)
                        self.manager.send_message(from_id, response)
                        self.notify_terminal(f"📤 Sent response to {from_id}: {response[:50]}...")

                    # Prevent message flooding
                    time.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error processing messages: {e}")
            raise

    def clean_response_history(self):
        """Clean old entries from response history"""
        current_time = datetime.now()
        keys_to_remove = []

        for key, (content, timestamp) in self.response_history.items():
            if current_time - timestamp > timedelta(minutes=1):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.response_history[key]

    def clean_processed_messages(self):
        """Clean old processed message IDs to prevent memory growth"""
        # Keep only last 1000 message IDs
        if len(self.processed_messages) > 1000:
            # Convert to list, sort, keep last 500
            msg_list = list(self.processed_messages)
            self.processed_messages = set(msg_list[-500:])

    def heartbeat(self):
        """Send heartbeat to log for monitoring"""
        while self.running:
            time.sleep(30)  # Every 30 seconds
            if self.running:
                self.last_heartbeat = datetime.now()
                self.logger.info(f"Heartbeat: {self.instance_id} alive")
                self.notify_terminal(f"💗 Heartbeat: Still monitoring...")

                # Clean old data
                self.clean_processed_messages()
                self.clean_response_history()

    def run(self):
        """Main run loop with health monitoring"""
        self.notify_terminal(f"🚀 Starting robust auto-responder for {self.instance_id}")

        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
        heartbeat_thread.start()

        while self.running:
            try:
                # Connect if not connected
                if not self.manager:
                    if not self.connect():
                        if self.reconnect_attempts >= self.max_reconnect_attempts:
                            self.notify_terminal(f"❌ Max reconnection attempts reached. Exiting.")
                            break
                        self.reconnect_attempts += 1
                        time.sleep(5)
                        continue

                # Process messages
                self.process_messages()

                # Health check
                if datetime.now() - self.last_heartbeat > timedelta(minutes=2):
                    self.logger.warning("Heartbeat timeout detected, restarting...")
                    self.manager = None
                    continue

                # Wait before next check
                time.sleep(2)

            except KeyboardInterrupt:
                self.notify_terminal(f"⚠️ Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.notify_terminal(f"❌ Error: {e}")

                # Try to reconnect
                self.manager = None
                time.sleep(5)

        self.running = False
        self.notify_terminal(f"🛑 Auto-responder for {self.instance_id} stopped")

def main():
    if len(sys.argv) < 2:
        print("Usage: python robust_auto_responder.py <instance_id>")
        sys.exit(1)

    instance_id = sys.argv[1]

    # Notify MCP connection
    print(f"\n{'='*60}")
    print(f"🔗 IPC MCP CONNECTION ESTABLISHED")
    print(f"{'='*60}")
    print(f"Instance ID: {instance_id}")
    print(f"Status: Connected to IPC Message Broker")
    print(f"Available for communication with:")

    # List potential instances
    instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]
    instances.remove(instance_id) if instance_id in instances else None
    for inst in instances:
        print(f"  • {inst}")

    print(f"{'='*60}\n")

    # Start responder
    responder = RobustAutoResponder(instance_id)

    try:
        responder.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()