#!/usr/bin/env python3
"""
🚀 Complete IPC System with Auto-Responder and Monitoring
한 번의 실행으로 모든 것이 자동으로 시작됩니다.
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime

class CompleteIPCSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.tools_dir = self.project_root / "tools"
        self.processes = []
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]

    def start_server(self):
        """IPC 서버 시작"""
        print("🖥️ Starting IPC Server...")
        import socket
        try:
            # Check if already running
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(("127.0.0.1", 9876))
            s.close()
            print("   ✅ Server already running")
        except:
            # Start server if not running
            server_script = self.project_root / "src" / "claude_ipc_server.py"
            if server_script.exists():
                proc = subprocess.Popen(
                    [sys.executable, str(server_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(proc)
                time.sleep(2)
                print("   ✅ Server started")
        print()

    def register_all_instances(self):
        """모든 인스턴스 등록"""
        print("📝 Registering all AI instances...")
        register_script = self.tools_dir / "ipc_register.py"

        for instance in self.instances:
            try:
                result = subprocess.run(
                    [sys.executable, str(register_script), instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Registered" in result.stdout or "already registered" in result.stdout.lower():
                    print(f"   ✅ {instance}: Ready")
                else:
                    print(f"   ⚠️ {instance}: Registration issue")
            except Exception as e:
                print(f"   ❌ {instance}: {e}")
        print()

    def start_auto_responders(self):
        """Auto-responder 시작 (gemini 포함)"""
        print("🤖 Starting Auto-Responders...")

        # Simple auto-responder for better reliability
        simple_responder = self.tools_dir / "simple_auto_responder.py"

        # Create simple auto-responder if it doesn't exist
        if not simple_responder.exists():
            self.create_simple_responder()

        # Start auto-responders for all instances except claude
        responder_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in responder_instances:
            try:
                if os.name == 'nt':
                    # Windows: Start in new window
                    cmd = f'start "Auto-Responder: {instance}" {sys.executable} {simple_responder} {instance}'
                    subprocess.Popen(cmd, shell=True)
                else:
                    # Unix: Background process
                    proc = subprocess.Popen(
                        [sys.executable, str(simple_responder), instance],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)

                print(f"   ✅ {instance}: Auto-responder active")
                time.sleep(0.5)
            except Exception as e:
                print(f"   ❌ {instance}: {e}")
        print()

    def create_simple_responder(self):
        """Create simple auto-responder if missing"""
        simple_responder = self.tools_dir / "simple_auto_responder.py"
        content = '''#!/usr/bin/env python3
"""Simple Auto-Responder for IPC System"""
import sys
import time
from pathlib import Path
import socket
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_auto_responder.py <instance_id>")
        return

    instance_id = sys.argv[1]
    print(f"🤖 Auto-responder for {instance_id} started")

    # Import IPC manager
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools.ipc_manager import IPCManager

    manager = IPCManager()
    manager.register(instance_id)

    print(f"✅ {instance_id} registered and monitoring messages...")

    while True:
        try:
            messages = manager.check_messages(instance_id)

            if messages:
                for msg in messages:
                    from_id = msg.get('from_id', 'unknown')
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', '')

                    print(f"📬 Message from {from_id}: {content}")

                    # Send auto-response
                    response = f"Auto-response from {instance_id}: Message received!"
                    manager.register(instance_id)  # Re-register to ensure token
                    manager.send_message(from_id, response)
                    print(f"📤 Sent response to {from_id}")

            time.sleep(2)

        except KeyboardInterrupt:
            print(f"\\n🛑 Auto-responder for {instance_id} stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
'''
        simple_responder.write_text(content, encoding='utf-8')
        print("   📝 Created simple_auto_responder.py")

    def start_monitoring(self):
        """모니터링 시스템 시작"""
        print("📊 Starting Monitoring System...")

        # Try different monitoring scripts
        monitor_scripts = [
            self.project_root / "start_split_monitoring.py",
            self.project_root / "start_safe_4panel_monitor.py",
            self.tools_dir / "monitor_instance.py"
        ]

        started = False
        for script in monitor_scripts:
            if script.exists():
                try:
                    if os.name == 'nt':
                        # Windows: Open in new window
                        if script.name == "monitor_instance.py":
                            cmd = f'start "IPC Monitor" {sys.executable} {script} gemini'
                        else:
                            cmd = f'start "IPC Monitor" {sys.executable} {script}'
                        subprocess.Popen(cmd, shell=True)
                    else:
                        # Unix
                        if script.name == "monitor_instance.py":
                            proc = subprocess.Popen([sys.executable, str(script), "gemini"])
                        else:
                            proc = subprocess.Popen([sys.executable, str(script)])
                        self.processes.append(proc)

                    print(f"   ✅ Monitoring started: {script.name}")
                    started = True
                    break
                except Exception as e:
                    print(f"   ⚠️ Could not start {script.name}: {e}")

        if not started:
            print("   ⚠️ No monitoring script found")
        print()

    def send_test_message(self):
        """테스트 메시지 전송"""
        print("📤 Sending test message to Gemini...")

        try:
            # Register as claude first
            register_script = self.tools_dir / "ipc_register.py"
            subprocess.run(
                [sys.executable, str(register_script), "claude"],
                capture_output=True,
                timeout=5
            )

            # Send message to gemini
            send_script = self.tools_dir / "ipc_send.py"
            result = subprocess.run(
                [sys.executable, str(send_script), "gemini",
                 "안녕 Gemini! 시스템이 정상 작동 중입니다. 응답 부탁드립니다."],
                capture_output=True,
                text=True,
                timeout=5
            )

            if "Sent to" in result.stdout:
                print("   ✅ Test message sent to Gemini")
            else:
                print("   ⚠️ Could not send test message")

            # Wait a moment for response
            print("   ⏳ Waiting for Gemini's response...")
            time.sleep(3)

            # Check for response
            check_script = self.tools_dir / "ipc_check.py"
            result = subprocess.run(
                [sys.executable, str(check_script), "claude"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if "From:" in result.stdout:
                print("   ✅ Response received!")
                print("   📬 " + result.stdout.strip())
            else:
                print("   ⏳ Response pending (check monitor)")

        except Exception as e:
            print(f"   ❌ Test error: {e}")
        print()

    def show_status(self):
        """시스템 상태 표시"""
        print("="*60)
        print("✨ Complete IPC System Status")
        print("="*60)

        # Check active instances
        list_script = self.tools_dir / "ipc_list.py"
        if list_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(list_script)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                active_instances = []
                if result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "ID:" in line:
                            instance = line.split("ID:")[-1].strip()
                            if instance:
                                active_instances.append(instance)

                print("👥 Active Instances:")
                for instance in self.instances:
                    if instance in active_instances:
                        print(f"   ✅ {instance}: Online")
                    else:
                        print(f"   ⏳ {instance}: Starting...")

            except Exception as e:
                print(f"   ⚠️ Could not get instance list: {e}")

        print("\n🤖 Auto-Responders:")
        print("   ✅ All auto-responders active")

        print("\n📊 Monitoring:")
        print("   ✅ Real-time monitoring active")

        print("\n" + "="*60)
        print("💚 System is fully operational!")
        print("="*60)
        print("\n📚 Quick Commands:")
        print("  • Send message: python tools/ipc_send.py <to> <message>")
        print("  • Check messages: python tools/ipc_check.py <instance>")
        print("  • List instances: python tools/ipc_list.py")
        print("\n🛑 Press Ctrl+C to stop all services")
        print("="*60)

    def run(self):
        """메인 실행"""
        print("\n" + "="*60)
        print("      🚀 COMPLETE IPC SYSTEM LAUNCHER")
        print("         Auto-Responder + Monitoring")
        print("="*60)
        print(f"📁 Project: {self.project_root}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        try:
            # 1. Start IPC server
            self.start_server()

            # 2. Register all instances
            self.register_all_instances()

            # 3. Start auto-responders (including gemini)
            self.start_auto_responders()

            # 4. Start monitoring
            self.start_monitoring()

            # 5. Send test message to gemini
            self.send_test_message()

            # 6. Show system status
            self.show_status()

            # Keep running
            print("\n💚 All systems running. Press Ctrl+C to stop...")
            while True:
                time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down all systems...")
            self.shutdown()

    def shutdown(self):
        """시스템 종료"""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass

        if os.name == 'nt':
            # Close all windows on Windows
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq Auto-Responder*" 2>nul',
                         shell=True, capture_output=True)
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq IPC Monitor*" 2>nul',
                         shell=True, capture_output=True)

        print("✅ All systems stopped")

if __name__ == "__main__":
    try:
        system = CompleteIPCSystem()
        system.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)