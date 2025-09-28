#!/usr/bin/env python3
"""
🚀 All-in-One IPC System Launcher
한 번의 실행으로 모든 IPC 기능을 시작하고 테스트합니다.
"""

import os
import sys
import subprocess
import time
import sqlite3
from pathlib import Path
from datetime import datetime
import threading

class IPCSystemManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.tools_dir = self.project_root / "tools"
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.processes = []
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]

    def cleanup_processes(self):
        """기존 Python 프로세스 정리"""
        print("🧹 Cleaning up existing processes...")
        try:
            if os.name == 'nt':
                # Windows: Use full command path
                result = subprocess.run("taskkill /F /IM python.exe", shell=True, capture_output=True, text=True)
                if "SUCCESS" in result.stdout or "프로세스" in result.stdout:
                    print("   ✅ Cleaned up existing processes")
                else:
                    print("   ℹ️ No processes to clean up")
            else:
                subprocess.run("pkill -f python", shell=True, capture_output=True)
                print("   ✅ Cleanup complete")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
        time.sleep(2)
        print()

    def start_ipc_server(self):
        """IPC 서버 시작 (필요한 경우)"""
        print("🖥️ Checking IPC server...")
        # Check if server is running by attempting to connect
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(("127.0.0.1", 9876))
            s.close()
            print("   ✅ IPC server already running\n")
        except:
            print("   ⚡ Starting IPC server...")
            server_script = self.project_root / "src" / "claude_ipc_server.py"
            if server_script.exists():
                proc = subprocess.Popen(
                    [sys.executable, str(server_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(proc)
                time.sleep(3)
                print("   ✅ IPC server started\n")
            else:
                print("   ⚠️ Server script not found\n")

    def register_instances(self):
        """모든 AI 인스턴스 등록"""
        print("📝 Registering AI instances...")
        register_script = self.tools_dir / "ipc_register.py"

        for instance in self.instances:
            try:
                result = subprocess.run(
                    [sys.executable, str(register_script), instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Registered" in result.stdout:
                    queued = result.stdout.count("queued")
                    if queued:
                        print(f"   ✅ {instance}: Registered with queued messages")
                    else:
                        print(f"   ✅ {instance}: Registered")
                else:
                    print(f"   ⚠️ {instance}: Registration failed")
            except Exception as e:
                print(f"   ❌ {instance}: Error - {e}")
        print()

    def test_communication(self):
        """통신 테스트"""
        print("🧪 Testing communication...")

        # Test messages
        test_pairs = [
            ("claude", "gemini", "안녕 Gemini! 테스트 메시지입니다."),
            ("gemini", "claude", "Claude님, 메시지 받았습니다!"),
            ("claude", "codex", "Codex, 준비되셨나요?"),
            ("codex", "claude", "네, 준비 완료!"),
        ]

        send_script = self.tools_dir / "ipc_send.py"
        check_script = self.tools_dir / "ipc_check.py"
        register_script = self.tools_dir / "ipc_register.py"

        # Send test messages
        for from_id, to_id, message in test_pairs:
            try:
                # Register as sender
                subprocess.run(
                    [sys.executable, str(register_script), from_id],
                    capture_output=True,
                    timeout=5
                )
                # Send message
                result = subprocess.run(
                    [sys.executable, str(send_script), to_id, message],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Sent to" in result.stdout:
                    print(f"   ✅ {from_id} → {to_id}")
                else:
                    print(f"   ❌ {from_id} → {to_id}: Failed")
            except Exception as e:
                print(f"   ❌ {from_id} → {to_id}: Error - {e}")

        print()

        # Check received messages
        print("📬 Checking messages...")
        for instance in ["claude", "gemini", "codex", "lm"]:
            try:
                # Register and check
                subprocess.run(
                    [sys.executable, str(register_script), instance],
                    capture_output=True,
                    timeout=5
                )
                result = subprocess.run(
                    [sys.executable, str(check_script), instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if "No new messages" in result.stdout:
                    print(f"   📭 {instance}: No new messages")
                elif "From:" in result.stdout:
                    msg_count = result.stdout.count("From:")
                    print(f"   📬 {instance}: {msg_count} message(s)")
                else:
                    print(f"   ⚠️ {instance}: Check failed")
            except Exception as e:
                print(f"   ❌ {instance}: Error - {e}")
        print()

    def start_auto_responders(self):
        """Auto-responder 시작"""
        print("🤖 Starting auto-responders...")
        responder_script = self.tools_dir / "simple_auto_responder.py"

        # Skip claude (that's us)
        responder_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in responder_instances:
            try:
                if os.name == 'nt':
                    # Windows: Start in minimized window
                    subprocess.Popen(
                        f'start /min "Responder-{instance}" {sys.executable} {responder_script} {instance}',
                        shell=True
                    )
                else:
                    # Unix: Start in background
                    proc = subprocess.Popen(
                        [sys.executable, str(responder_script), instance],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)
                print(f"   ✅ {instance} responder started")
                time.sleep(0.3)
            except Exception as e:
                print(f"   ❌ {instance}: Error - {e}")
        print()

    def start_monitoring(self):
        """모니터링 시작"""
        print("📊 Starting monitoring...")
        monitor_script = self.project_root / "start_split_monitoring.py"

        if monitor_script.exists():
            try:
                if os.name == 'nt':
                    subprocess.Popen(
                        f'start "IPC Monitor" {sys.executable} {monitor_script}',
                        shell=True
                    )
                else:
                    proc = subprocess.Popen(
                        [sys.executable, str(monitor_script)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)
                print("   ✅ Monitoring started\n")
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        else:
            print("   ⚠️ Monitoring script not found\n")

    def show_database_stats(self):
        """데이터베이스 통계 표시"""
        print("📈 Database statistics:")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]

            # Unread messages
            cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
            unread = cursor.fetchone()[0]

            # Messages by instance
            cursor.execute("""
                SELECT to_id, COUNT(*) as count
                FROM messages
                WHERE read_flag = 0
                GROUP BY to_id
                ORDER BY count DESC
                LIMIT 5
            """)
            unread_by_instance = cursor.fetchall()

            conn.close()

            print(f"   📊 Total messages: {total}")
            print(f"   📬 Unread messages: {unread}")
            if unread_by_instance:
                print("   📨 Unread by instance:")
                for instance, count in unread_by_instance:
                    print(f"      • {instance}: {count}")
            print()

        except Exception as e:
            print(f"   ⚠️ Could not read database: {e}\n")

    def show_active_instances(self):
        """활성 인스턴스 표시"""
        print("👥 Active instances:")
        list_script = self.tools_dir / "ipc_list.py"

        try:
            result = subprocess.run(
                [sys.executable, str(list_script)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "ID:" in line:
                        parts = line.split("ID:")
                        if len(parts) > 1:
                            instance_id = parts[1].strip()
                            if instance_id in self.instances:
                                print(f"   ✅ {instance_id}")
                            else:
                                print(f"   • {instance_id}")
            print()
        except Exception as e:
            print(f"   ⚠️ Error: {e}\n")

    def print_usage_guide(self):
        """사용 가이드 출력"""
        print("="*70)
        print("✨ IPC System Ready!")
        print("="*70)
        print("\n📚 Quick Commands:")
        print("  • Send message:    python tools/ipc_send.py <to> <message>")
        print("  • Check messages:  python tools/ipc_check.py <instance>")
        print("  • List instances:  python tools/ipc_list.py")
        print("  • Run full test:   python test_ipc_communication.py")
        print("\n🛠️ Management:")
        print("  • Reset all:       python tools/reset_all_ipc.py")
        print("  • Clear messages:  python tools/clear_project_messages.py")
        print("  • Monitor:         python tools/monitor_instance.py <instance>")
        print("\n🛑 To stop all: Press Ctrl+C or close this window")
        print("="*70)

    def run(self):
        """메인 실행"""
        print("\n" + "="*70)
        print("      🚀 All-in-One IPC System Launcher")
        print("="*70)
        print(f"📁 Project: {self.project_root}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        try:
            # 1. Cleanup
            self.cleanup_processes()

            # 2. Start server
            self.start_ipc_server()

            # 3. Register instances
            self.register_instances()

            # 4. Test communication
            self.test_communication()

            # 5. Show database stats
            self.show_database_stats()

            # 6. Show active instances
            self.show_active_instances()

            # 7. Start auto-responders
            self.start_auto_responders()

            # 8. Start monitoring
            self.start_monitoring()

            # 9. Show usage guide
            self.print_usage_guide()

            # Keep running
            print("\n💚 System is running. Press Ctrl+C to stop...")
            while True:
                time.sleep(60)
                print(f"💚 Heartbeat at {datetime.now().strftime('%H:%M:%S')}")

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            self.shutdown()

    def shutdown(self):
        """시스템 종료"""
        # Kill all processes
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass

        # Kill all Python processes on Windows
        if os.name == 'nt':
            subprocess.run("taskkill /F /IM python.exe 2>nul", shell=True, capture_output=True)

        print("✅ Shutdown complete")

if __name__ == "__main__":
    try:
        manager = IPCSystemManager()
        manager.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)