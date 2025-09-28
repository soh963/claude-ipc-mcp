#!/usr/bin/env python3
"""
Global Auto-Registration System for AI CLI Instances
자동으로 모든 AI CLI 인스턴스를 등록하고 메시지를 모니터링합니다.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import threading

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

class GlobalIPCRegistrar:
    def __init__(self):
        self.config_file = Path.home() / '.claude-ipc' / 'instances.json'
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.ipc = IPCManager()
        self.registered_instances = {}
        self.running = True
        self.load_config()

    def load_config(self):
        """Load instance configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.instances = json.load(f)
        else:
            # Default configuration for various AI CLI tools
            self.instances = {
                "claude": {
                    "auto_register": True,
                    "startup_check": "claude --version",
                    "enabled": True,
                    "response_patterns": {
                        "파일 리스트": "self.list_files",
                        "상태 확인": "self.check_status",
                        "도움말": "self.show_help"
                    }
                },
                "gemini": {
                    "auto_register": True,
                    "startup_check": "gemini --version",
                    "enabled": True,
                    "response_patterns": {
                        "이미지 분석": "self.analyze_image",
                        "창의적": "self.creative_response"
                    }
                },
                "codex": {
                    "auto_register": True,
                    "startup_check": "codex --version",
                    "enabled": True,
                    "response_patterns": {
                        "코드 생성": "self.generate_code",
                        "코드 리뷰": "self.review_code"
                    }
                },
                "cursor": {
                    "auto_register": True,
                    "startup_check": "cursor --version",
                    "enabled": True,
                    "response_patterns": {}
                },
                "windsurf": {
                    "auto_register": True,
                    "startup_check": "windsurf --version",
                    "enabled": True,
                    "response_patterns": {}
                },
                "lm": {
                    "auto_register": True,
                    "startup_check": "lm --version",
                    "enabled": True,
                    "response_patterns": {
                        "문서 작성": "self.write_document",
                        "번역": "self.translate"
                    }
                }
            }
            self.save_config()

    def save_config(self):
        """Save instance configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.instances, f, indent=2)
        print(f"✅ Configuration saved to {self.config_file}")

    def register_all(self):
        """Register all enabled instances"""
        print(f"\n🔄 Registering {len(self.instances)} AI instances...")
        success_count = 0

        for name, config in self.instances.items():
            if config.get('enabled') and config.get('auto_register'):
                try:
                    result = self.ipc.register(name)
                    if result.get('status') == 'ok':
                        self.registered_instances[name] = {
                            'session_token': result.get('session_token'),
                            'registered_at': datetime.now().isoformat()
                        }
                        print(f"  ✅ {name}: Registered successfully")
                        success_count += 1
                    else:
                        print(f"  ⚠️ {name}: {result.get('message', 'Unknown error')}")
                except Exception as e:
                    print(f"  ❌ {name}: Registration failed - {e}")

        print(f"\n📊 Registration complete: {success_count}/{len(self.instances)} instances registered")
        return success_count > 0

    def monitor_and_respond(self):
        """Monitor messages for all instances"""
        print("\n🎯 Starting message monitoring...")

        while self.running:
            for name in self.registered_instances:
                if self.instances[name].get('enabled'):
                    try:
                        messages = self.ipc.check(name)
                        if messages and messages.get('messages'):
                            self.process_messages(name, messages['messages'])
                    except Exception as e:
                        # Silent fail to avoid spam
                        pass

            time.sleep(1)  # Check every second

    def process_messages(self, instance_name, messages):
        """Process received messages with smart responses"""
        for msg in messages:
            sender = msg.get('from')
            content = msg.get('message', {}).get('content', '')
            timestamp = msg.get('timestamp', '')

            print(f"\n📨 {instance_name} received from {sender}:")
            print(f"   Time: {timestamp}")
            print(f"   Message: {content[:100]}{'...' if len(content) > 100 else ''}")

            # Auto-respond logic based on patterns
            response = self.generate_response(instance_name, sender, content)
            if response:
                try:
                    self.ipc.send(instance_name, sender, response)
                    print(f"   ↩️ Replied: {response[:50]}...")
                except Exception as e:
                    print(f"   ❌ Reply failed: {e}")

    def generate_response(self, instance_name, sender, content):
        """Generate smart response based on content"""
        content_lower = content.lower()

        # Universal responses
        if "ping" in content_lower:
            return f"🏓 pong from {instance_name} - I'm alive and responding!"
        elif "status" in content_lower or "상태" in content_lower:
            return f"✅ {instance_name} is active and monitoring messages"
        elif "help" in content_lower or "도움말" in content_lower:
            return f"💡 {instance_name} available commands: ping, status, list, test"
        elif "list" in content_lower or "목록" in content_lower:
            active = list(self.registered_instances.keys())
            return f"📋 Active instances: {', '.join(active)}"
        elif "test" in content_lower or "테스트" in content_lower:
            return f"🧪 Test successful! {instance_name} received your message"

        # Instance-specific patterns
        patterns = self.instances[instance_name].get('response_patterns', {})
        for pattern, response_func in patterns.items():
            if pattern in content_lower:
                # Here you could call specific functions
                return f"🤖 {instance_name}: Processing '{pattern}' request..."

        # Default response for unknown commands
        if "?" in content or "어떻게" in content or "how" in content_lower:
            return f"🤔 {instance_name}: I received your question. Try 'help' for available commands."

        return None  # No response for general messages

    def health_check(self):
        """Periodic health check and re-registration"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds

            # Re-register any lost instances
            for name in list(self.instances.keys()):
                if name not in self.registered_instances and self.instances[name].get('enabled'):
                    try:
                        result = self.ipc.register(name)
                        if result.get('status') == 'ok':
                            self.registered_instances[name] = {
                                'session_token': result.get('session_token'),
                                'registered_at': datetime.now().isoformat()
                            }
                            print(f"🔄 Re-registered {name}")
                    except:
                        pass

    def start(self):
        """Start all monitoring threads"""
        # Start health check thread
        health_thread = threading.Thread(target=self.health_check, daemon=True)
        health_thread.start()

        # Main monitoring loop
        try:
            self.monitor_and_respond()
        except KeyboardInterrupt:
            print("\n⏹️ Stopping global IPC monitor...")
            self.running = False

def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║   🌐 Global IPC Auto-Registration System  ║
    ║   Connecting all AI CLI instances         ║
    ╚══════════════════════════════════════════╝
    """)

    registrar = GlobalIPCRegistrar()

    # Try to register all instances
    if registrar.register_all():
        # Start monitoring
        print("\n🚀 Starting global IPC monitor...")
        print("Press Ctrl+C to stop\n")
        registrar.start()
    else:
        print("\n❌ Failed to register any instances. Check if IPC server is running.")
        print("Run: python src/claude_ipc_server.py")
        sys.exit(1)

if __name__ == "__main__":
    main()