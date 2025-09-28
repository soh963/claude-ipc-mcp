#!/usr/bin/env python3
"""
완전히 새로운 IPC 시스템 시작 스크립트
모든 기능이 실제로 작동하도록 보장
"""
import os
import sys
import subprocess
import time
import socket
import json
from pathlib import Path

class FreshIPCSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]

    def cleanup_old_processes(self):
        """기존 프로세스 정리 - Windows 전용"""
        print("🧹 Cleaning up old processes...")

        # Kill Python processes related to IPC
        commands = [
            'taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul',
            'taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul',
            'taskkill /F /FI "WINDOWTITLE eq *IPC*" 2>nul',
            'taskkill /F /FI "WINDOWTITLE eq IPC Server" 2>nul'
        ]

        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)

        time.sleep(2)
        print("   ✅ Cleanup complete")

    def start_ipc_server(self):
        """IPC 서버 시작 - 싱글톤 브로커 사용"""
        print("🖥️ Starting IPC Server...")

        try:
            # 싱글톤 브로커 시작 스크립트 사용
            result = subprocess.run(
                ['python', 'tools/start_broker.py'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("   ✅ Singleton broker started/confirmed")

                # 연결 확인
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect(('127.0.0.1', 9876))
                    s.close()
                    print("   ✅ IPC Server running on port 9876")
                    return True
                except:
                    print("   ❌ Server connection failed")
                    return False
            else:
                print("   ❌ Singleton broker startup failed")
                if result.stderr:
                    print(f"      Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("   ❌ Broker start timeout")
            return False
        except Exception as e:
            print(f"   ❌ Server start error: {e}")
            return False

    def register_instance(self, instance_id):
        """인스턴스 등록"""
        try:
            # Connect to broker
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(('127.0.0.1', 9876))

            # Send registration
            request = {
                'action': 'register',
                'instance_id': instance_id
            }
            sock.send(json.dumps(request).encode() + b'\n')

            # Get response
            response_data = sock.recv(4096).decode()
            response = json.loads(response_data)
            sock.close()

            if response.get('status') == 'ok':
                return True, response.get('session_token')
            return False, None

        except Exception as e:
            print(f"   Error registering {instance_id}: {e}")
            return False, None

    def register_all_instances(self):
        """모든 인스턴스 등록"""
        print("📝 Registering all instances...")

        for instance in self.instances:
            success, token = self.register_instance(instance)
            if success:
                print(f"   ✅ {instance}: Registered")

                # Save session for claude
                if instance == "claude":
                    session_file = Path.home() / '.ipc-session'
                    session_data = {
                        "instance_id": "claude",
                        "session_token": token
                    }
                    with open(session_file, 'w') as f:
                        json.dump(session_data, f)
                    print(f"   📁 Claude session saved to ~/.ipc-session")
            else:
                print(f"   ❌ {instance}: Failed to register")

    def start_auto_responders(self):
        """자동 응답기 시작 - claude 제외"""
        print("🤖 Starting Auto-Responders...")

        responder_script = self.project_root / "tools" / "simple_auto_responder.py"
        if not responder_script.exists():
            # Create it if it doesn't exist
            self.create_simple_responder()
            responder_script = self.project_root / "tools" / "simple_auto_responder.py"

        responder_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in responder_instances:
            cmd = f'start "Auto-Responder: {instance}" /MIN python "{responder_script}" {instance}'
            subprocess.Popen(cmd, shell=True)
            print(f"   ✅ {instance}: Auto-responder started")
            time.sleep(0.5)

    def create_simple_responder(self):
        """Simple auto-responder 생성"""
        responder_path = self.project_root / "tools" / "simple_auto_responder.py"
        content = '''#!/usr/bin/env python3
"""Simple Auto-Responder for IPC System"""
import sys
import time
import json
import socket

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_auto_responder.py <instance_id>")
        return

    instance_id = sys.argv[1]
    print(f"🤖 Auto-responder for {instance_id} started")

    # Register first
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(('127.0.0.1', 9876))

        request = {
            'action': 'register',
            'instance_id': instance_id
        }
        sock.send(json.dumps(request).encode() + b'\\n')

        response_data = sock.recv(4096).decode()
        response = json.loads(response_data)
        sock.close()

        if response.get('status') != 'ok':
            print(f"Failed to register: {response}")
            return

        session_token = response.get('session_token')
        print(f"✅ {instance_id} registered successfully")

    except Exception as e:
        print(f"Registration error: {e}")
        return

    # Main loop
    while True:
        try:
            # Check messages
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(('127.0.0.1', 9876))

            request = {
                'action': 'check',
                'instance_id': instance_id,
                'session_token': session_token
            }
            sock.send(json.dumps(request).encode() + b'\\n')

            response_data = sock.recv(8192).decode()
            response = json.loads(response_data)
            sock.close()

            if response.get('status') == 'ok':
                messages = response.get('messages', [])

                for msg in messages:
                    from_id = msg.get('from_id', 'unknown')
                    content = msg.get('content', '')
                    print(f"📬 {instance_id} received from {from_id}: {content[:50]}...")

                    # Send auto-response
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5.0)
                    sock.connect(('127.0.0.1', 9876))

                    response_msg = f"Auto-response from {instance_id}: Received '{content[:30]}...'"

                    request = {
                        'action': 'send',
                        'instance_id': instance_id,
                        'session_token': session_token,
                        'to_id': from_id,
                        'message': response_msg
                    }
                    sock.send(json.dumps(request).encode() + b'\\n')

                    response_data = sock.recv(4096).decode()
                    sock.close()

                    print(f"📤 {instance_id} sent response to {from_id}")

            time.sleep(2)

        except KeyboardInterrupt:
            print(f"\\n🛑 Auto-responder for {instance_id} stopped")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
'''
        responder_path.write_text(content, encoding='utf-8')
        print("   📝 Created simple_auto_responder.py")

    def start_monitoring(self):
        """모니터링 시작"""
        print("📊 Starting Monitoring...")

        # Try enhanced monitor first
        monitor_script = self.project_root / "enhanced_monitor.py"
        if monitor_script.exists():
            cmd = f'start "IPC Monitor" python "{monitor_script}"'
            subprocess.Popen(cmd, shell=True)
            print("   ✅ Enhanced monitor started")
        else:
            # Alternative monitor
            alt_monitor = self.project_root / "tools" / "monitor_instance.py"
            if alt_monitor.exists():
                cmd = f'start "IPC Monitor" python "{alt_monitor}" claude'
                subprocess.Popen(cmd, shell=True)
                print("   ✅ Instance monitor started")

    def test_system(self):
        """시스템 테스트"""
        print("\n🔍 Testing System...")

        # Test message from claude to gemini
        try:
            # Load claude session
            session_file = Path.home() / '.ipc-session'
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)
                    session_token = session_data['session_token']

                # Send test message
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect(('127.0.0.1', 9876))

                request = {
                    'action': 'send',
                    'instance_id': 'claude',
                    'session_token': session_token,
                    'to_id': 'gemini',
                    'message': 'System test message'
                }
                sock.send(json.dumps(request).encode() + b'\n')

                response_data = sock.recv(4096).decode()
                response = json.loads(response_data)
                sock.close()

                if response.get('status') == 'ok':
                    print("   ✅ Test message sent successfully")
                else:
                    print(f"   ❌ Test failed: {response.get('message')}")
            else:
                print("   ⚠️ Claude session not found")

        except Exception as e:
            print(f"   ❌ Test error: {e}")

    def run(self):
        """메인 실행"""
        print("\n" + "="*60)
        print("      🚀 FRESH IPC SYSTEM LAUNCHER")
        print("         Clean Start with Working Components")
        print("="*60 + "\n")

        # Step by step
        self.cleanup_old_processes()

        if not self.start_ipc_server():
            print("\n❌ Failed to start server. Exiting.")
            return

        self.register_all_instances()
        self.start_auto_responders()
        self.start_monitoring()

        time.sleep(2)
        self.test_system()

        print("\n" + "="*60)
        print("💚 System is running!")
        print("="*60)
        print("\nPress Ctrl+C to stop...")

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")

if __name__ == "__main__":
    system = FreshIPCSystem()
    system.run()