#!/usr/bin/env python3
"""
Codex CLI IPC Initialization
Codex CLI에서 IPC 시스템에 자동 등록하는 초기화 스크립트
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

class CodexIPCHandler:
    def __init__(self):
        self.instance_name = "codex"
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
                print(f"✅ Codex registered with IPC system")
                print(f"   Instance: {self.instance_name}")
                print(f"   Specialization: Code generation & review")

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

        # Codex-specific responses
        if "코드" in content or "code" in content_lower:
            if "생성" in content or "generate" in content_lower:
                return "💻 Codex: Ready to generate code. Please specify language and requirements."
            elif "리뷰" in content or "review" in content_lower:
                return "🔍 Codex: Ready to review code. Please share the code to review."
            else:
                return "📝 Codex: Code assistance ready. How can I help?"
        elif "버그" in content or "bug" in content_lower or "fix" in content_lower:
            return "🐛 Codex: Bug fixing mode activated. Share the problematic code."
        elif "테스트" in content or "test" in content_lower:
            return "🧪 Codex: Test generation mode ready. Specify the function to test."
        elif "ping" in content_lower:
            return "🏓 Codex pong! Code generation AI ready."
        elif "status" in content_lower or "상태" in content:
            return "✅ Codex is active - Specialized in code generation, review, and debugging"

        # Handle code sharing
        if data and data.get('type') == 'code':
            language = data.get('language', 'unknown')
            return f"📂 Codex: Received {language} code. Analyzing..."

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

    def send_code(self, to_instance, code, language="python", description=""):
        """Send code snippet to another instance"""
        data = {
            "type": "code",
            "language": language,
            "code": code,
            "description": description
        }
        message = f"📝 Code snippet ({language}): {description[:50]}..."
        return self.send_message(to_instance, message, data)

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
_codex_ipc = None

def initialize_ipc():
    """Initialize IPC for Codex"""
    global _codex_ipc
    if not _codex_ipc and IPC_AVAILABLE:
        _codex_ipc = CodexIPCHandler()
    return _codex_ipc

def send_to(instance, message, data=None):
    """Convenience function to send messages"""
    if _codex_ipc:
        return _codex_ipc.send_message(instance, message, data)
    return False

def send_code_to(instance, code, language="python", description=""):
    """Convenience function to send code"""
    if _codex_ipc:
        return _codex_ipc.send_code(instance, code, language, description)
    return False

def check_ipc():
    """Convenience function to check messages"""
    if _codex_ipc:
        messages = _codex_ipc.check_messages()
        for msg in messages:
            _codex_ipc.process_message(msg)
        return messages
    return []

def broadcast_message(message, data=None):
    """Convenience function to broadcast"""
    if _codex_ipc:
        return _codex_ipc.broadcast(message, data)
    return False

# Auto-initialize when imported
if __name__ != "__main__":
    initialize_ipc()

# For testing
if __name__ == "__main__":
    print("🚀 Codex IPC Initialization Test")
    print("=" * 40)

    handler = initialize_ipc()
    if handler:
        print("\n📊 Testing IPC functions:")

        # Test send
        print("1. Sending test message...")
        if send_to("claude", "Hello from Codex! Ready for code tasks."):
            print("   ✅ Message sent")

        # Test code send
        print("2. Sending code snippet...")
        sample_code = """
def hello_world():
    print("Hello from Codex!")
    return True
"""
        if send_code_to("claude", sample_code, "python", "Sample hello world function"):
            print("   ✅ Code sent")

        # Test check
        print("3. Checking messages...")
        messages = check_ipc()
        print(f"   📬 Found {len(messages)} message(s)")

        # Test broadcast
        print("4. Broadcasting...")
        if broadcast_message("Codex is online - Code assistance available"):
            print("   ✅ Broadcast sent")

        print("\n✅ IPC initialization complete!")
        print("Monitoring for messages... (Press Ctrl+C to stop)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopped")