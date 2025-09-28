#!/usr/bin/env python3
"""
Gemini CLI IPC Initialization
Gemini CLI에서 IPC 시스템에 자동 등록하는 초기화 스크립트
"""

import sys
import os
import json
import threading
import time

# Add IPC tools to path
ipc_home = os.environ.get('CLAUDE_IPC_HOME', 'D:/claude-ipc-mcp')
sys.path.append(os.path.join(ipc_home, 'tools'))

try:
    from ipc_manager import IPCManager
    IPC_AVAILABLE = True
except ImportError:
    IPC_AVAILABLE = False
    print("⚠️ IPC system not available. Install claude-ipc-mcp first.")

class GeminiIPCHandler:
    def __init__(self):
        self.instance_name = "gemini"
        self.ipc = None
        self.monitoring = False
        self.session_token = None

        if IPC_AVAILABLE:
            self.ipc = IPCManager()
            self.register()

    def register(self):
        """Register with IPC system"""
        try:
            result = self.ipc.register(self.instance_name)
            if result.get('status') == 'ok':
                self.session_token = result.get('session_token')
                print(f"✅ Gemini registered with IPC system")
                print(f"   Instance: {self.instance_name}")

                # Start monitoring thread
                self.start_monitoring()
                return True
            else:
                print(f"⚠️ IPC registration failed: {result.get('message')}")
                return False
        except Exception as e:
            print(f"❌ Could not connect to IPC: {e}")
            return False

    def start_monitoring(self):
        """Start background message monitoring"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_messages, daemon=True)
        monitor_thread.start()

    def _monitor_messages(self):
        """Background thread to check for messages"""
        while self.monitoring:
            try:
                messages = self.check_messages()
                if messages:
                    for msg in messages:
                        self.process_message(msg)
            except:
                pass
            time.sleep(2)  # Check every 2 seconds

    def check_messages(self):
        """Check for new messages"""
        if not self.ipc:
            return []

        try:
            result = self.ipc.check(self.instance_name)
            if result.get('status') == 'ok':
                return result.get('messages', [])
        except:
            pass
        return []

    def process_message(self, message):
        """Process incoming IPC message"""
        sender = message.get('from', 'unknown')
        content = message.get('message', {}).get('content', '')
        data = message.get('message', {}).get('data', {})
        timestamp = message.get('timestamp', '')

        print(f"\n📨 IPC Message from {sender}:")
        print(f"   Time: {timestamp}")
        print(f"   Content: {content}")

        # Auto-respond based on content
        response = self.generate_response(sender, content, data)
        if response:
            self.send_message(sender, response)

    def generate_response(self, sender, content, data):
        """Generate response based on message content"""
        content_lower = content.lower()

        # Gemini-specific responses
        if "이미지" in content or "image" in content_lower:
            return "🎨 Gemini: 이미지 분석 기능을 준비 중입니다."
        elif "창의적" in content or "creative" in content_lower:
            return "✨ Gemini: 창의적인 아이디어를 생성하겠습니다."
        elif "분석" in content or "analyze" in content_lower:
            return "🔍 Gemini: 멀티모달 분석을 시작합니다."
        elif "ping" in content_lower:
            return "🏓 Gemini pong! Multi-modal AI ready."
        elif "status" in content_lower or "상태" in content:
            return "✅ Gemini is active with vision and language capabilities"

        return None

    def send_message(self, to_instance, content, data=None):
        """Send message to another instance"""
        if not self.ipc:
            print("❌ IPC not available")
            return False

        try:
            result = self.ipc.send(self.instance_name, to_instance, content, data)
            if result.get('status') == 'ok':
                print(f"↩️ Sent reply to {to_instance}")
                return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
        return False

    def broadcast(self, content, data=None):
        """Broadcast message to all instances"""
        if not self.ipc:
            return False

        try:
            result = self.ipc.broadcast(self.instance_name, content, data)
            return result.get('status') == 'ok'
        except:
            return False

# Global IPC handler
_gemini_ipc = None

def initialize_ipc():
    """Initialize IPC for Gemini"""
    global _gemini_ipc
    if not _gemini_ipc and IPC_AVAILABLE:
        _gemini_ipc = GeminiIPCHandler()
    return _gemini_ipc

def send_to(instance, message, data=None):
    """Convenience function to send messages"""
    if _gemini_ipc:
        return _gemini_ipc.send_message(instance, message, data)
    return False

def check_ipc():
    """Convenience function to check messages"""
    if _gemini_ipc:
        messages = _gemini_ipc.check_messages()
        for msg in messages:
            _gemini_ipc.process_message(msg)
        return messages
    return []

def broadcast_message(message, data=None):
    """Convenience function to broadcast"""
    if _gemini_ipc:
        return _gemini_ipc.broadcast(message, data)
    return False

# Auto-initialize when imported
if __name__ != "__main__":
    initialize_ipc()

# For testing
if __name__ == "__main__":
    print("🚀 Gemini IPC Initialization Test")
    print("=" * 40)

    handler = initialize_ipc()
    if handler:
        print("\n📊 Testing IPC functions:")

        # Test send
        print("1. Sending test message...")
        if send_to("claude", "Hello from Gemini!"):
            print("   ✅ Message sent")

        # Test check
        print("2. Checking messages...")
        messages = check_ipc()
        print(f"   📬 Found {len(messages)} message(s)")

        # Test broadcast
        print("3. Broadcasting...")
        if broadcast_message("Gemini is online"):
            print("   ✅ Broadcast sent")

        print("\n✅ IPC initialization complete!")
        print("Monitoring for messages... (Press Ctrl+C to stop)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopped")