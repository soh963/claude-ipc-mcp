#!/usr/bin/env python3
"""
🚀 Ultimate IPC System - One-Click Complete Solution
원클릭으로 모든 기능이 활성화되는 완벽한 시스템
"""

import os
import sys
import subprocess
import time
import threading
import socket
from pathlib import Path
from datetime import datetime

class UltimateIPCSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.tools_dir = self.project_root / "tools"
        self.processes = []
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]
        self.success_count = 0
        self.error_log = []

    def log_error(self, error_msg):
        """에러를 로그에 기록"""
        self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')}: {error_msg}")

    def check_python(self):
        """Python 설치 확인"""
        print("🔍 Checking Python installation...")
        try:
            result = subprocess.run([sys.executable, "--version"],
                                  capture_output=True, text=True, timeout=5)
            print(f"   ✅ Python found: {result.stdout.strip()}")
            return True
        except Exception as e:
            self.log_error(f"Python check failed: {e}")
            print(f"   ❌ Python check failed")
            return False

    def cleanup_old_processes(self):
        """기존 프로세스 정리"""
        print("🧹 Cleaning up old processes...")
        try:
            if os.name == 'nt':
                # Windows: Kill only IPC-related processes, not ALL Python
                # Kill any monitoring windows
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul',
                             shell=True, capture_output=True)
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul',
                             shell=True, capture_output=True)
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *IPC*" 2>nul',
                             shell=True, capture_output=True)
                # Kill specific IPC processes
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq IPC Server" 2>nul',
                             shell=True, capture_output=True)
            else:
                subprocess.run("pkill -f 'python.*ipc'",
                             shell=True, capture_output=True)

            time.sleep(1)
            print("   ✅ Cleanup complete")
        except Exception as e:
            self.log_error(f"Cleanup failed: {e}")
            print("   ⚠️ Cleanup had issues but continuing")

    def start_ipc_server(self):
        """IPC 서버 시작"""
        print("🖥️ Starting IPC Server...")
        try:
            # Check if server is already running
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            try:
                s.connect(("127.0.0.1", 9876))
                s.close()
                print("   ✅ Server already running")
                self.success_count += 1
                return True
            except:
                pass

            # Start server
            server_script = self.project_root / "src" / "claude_ipc_server.py"
            if server_script.exists():
                if os.name == 'nt':
                    subprocess.Popen(
                        f'start /min "IPC Server" {sys.executable} {server_script}',
                        shell=True
                    )
                else:
                    proc = subprocess.Popen(
                        [sys.executable, str(server_script)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)

                time.sleep(2)

                # Verify server started
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                try:
                    s.connect(("127.0.0.1", 9876))
                    s.close()
                    print("   ✅ Server started successfully")
                    self.success_count += 1
                    return True
                except:
                    self.log_error("Server failed to start")
                    print("   ❌ Server failed to start")
                    return False
            else:
                self.log_error("Server script not found")
                print("   ❌ Server script not found")
                return False
        except Exception as e:
            self.log_error(f"Server start error: {e}")
            print(f"   ❌ Error: {e}")
            return False

    def register_all_instances(self):
        """모든 인스턴스 등록"""
        print("📝 Registering all AI instances...")
        register_script = self.tools_dir / "ipc_register.py"

        if not register_script.exists():
            self.log_error("Register script not found")
            print("   ❌ Register script not found")
            return False

        success_count = 0
        for instance in self.instances:
            try:
                result = subprocess.run(
                    [sys.executable, str(register_script), instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Registered" in result.stdout or "already registered" in result.stdout.lower():
                    print(f"   ✅ {instance}: Registered")
                    success_count += 1
                else:
                    print(f"   ⚠️ {instance}: Registration issue")
                    self.log_error(f"{instance} registration failed")
            except Exception as e:
                self.log_error(f"{instance} registration error: {e}")
                print(f"   ❌ {instance}: Error")

        self.success_count += success_count
        return success_count > 0

    def create_auto_responders(self):
        """Auto-responder 생성 및 시작"""
        print("🤖 Starting Auto-Responders...")

        # Create simple auto-responder if needed
        simple_responder = self.tools_dir / "simple_auto_responder.py"
        if not simple_responder.exists():
            self.create_simple_responder_file()

        responder_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]
        success_count = 0

        for instance in responder_instances:
            try:
                if os.name == 'nt':
                    # Windows: Start in minimized window
                    cmd = f'start /min "Auto-Responder: {instance}" {sys.executable} {simple_responder} {instance}'
                    subprocess.Popen(cmd, shell=True)
                else:
                    proc = subprocess.Popen(
                        [sys.executable, str(simple_responder), instance],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)

                print(f"   ✅ {instance}: Auto-responder started")
                success_count += 1
                time.sleep(0.3)
            except Exception as e:
                self.log_error(f"{instance} auto-responder error: {e}")
                print(f"   ❌ {instance}: Failed")

        self.success_count += success_count
        return success_count > 0

    def create_simple_responder_file(self):
        """Simple auto-responder 파일 생성"""
        simple_responder = self.tools_dir / "simple_auto_responder.py"
        content = '''#!/usr/bin/env python3
"""Simple Auto-Responder for IPC System"""
import sys
import time
import json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_auto_responder.py <instance_id>")
        return

    instance_id = sys.argv[1]
    print(f"🤖 Auto-responder for {instance_id} started")

    # Import IPC manager
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from tools.ipc_manager import IPCManager
    except ImportError:
        # Fallback to direct import
        sys.path.insert(0, str(Path(__file__).parent))
        from ipc_manager import IPCManager

    manager = IPCManager()
    manager.register(instance_id)

    print(f"✅ {instance_id} registered and monitoring...")

    while True:
        try:
            messages = manager.check_messages(instance_id)
            if messages:
                for msg in messages:
                    from_id = msg.get('from_id', 'unknown')
                    content = msg.get('content', '')
                    print(f"📬 Message from {from_id}: {content}")

                    # Send response
                    response = f"Auto-response from {instance_id}: Received '{content[:30]}...'"
                    manager.register(instance_id)
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

    def start_unified_monitoring(self):
        """통합 모니터링 시작"""
        print("📊 Starting Unified Monitoring...")

        monitor_script = self.project_root / "unified_monitor.py"

        if monitor_script.exists():
            try:
                if os.name == 'nt':
                    # Windows: Open in new window
                    cmd = f'start "Unified IPC Monitor" {sys.executable} {monitor_script}'
                    subprocess.Popen(cmd, shell=True)
                else:
                    proc = subprocess.Popen([sys.executable, str(monitor_script)])
                    self.processes.append(proc)

                print("   ✅ Unified monitoring started")
                self.success_count += 1
                return True
            except Exception as e:
                self.log_error(f"Monitoring start error: {e}")
                print(f"   ❌ Error: {e}")
                return False
        else:
            self.log_error("Monitor script not found")
            print("   ⚠️ Monitor script not found, using alternative")
            return self.start_alternative_monitoring()

    def start_alternative_monitoring(self):
        """대체 모니터링 시작"""
        alternatives = [
            self.project_root / "start_split_monitoring.py",
            self.tools_dir / "monitor_instance.py"
        ]

        for script in alternatives:
            if script.exists():
                try:
                    if os.name == 'nt':
                        if script.name == "monitor_instance.py":
                            cmd = f'start "IPC Monitor" {sys.executable} {script} gemini'
                        else:
                            cmd = f'start "IPC Monitor" {sys.executable} {script}'
                        subprocess.Popen(cmd, shell=True)
                    else:
                        if script.name == "monitor_instance.py":
                            proc = subprocess.Popen([sys.executable, str(script), "gemini"])
                        else:
                            proc = subprocess.Popen([sys.executable, str(script)])
                        self.processes.append(proc)

                    print(f"   ✅ Alternative monitoring started: {script.name}")
                    self.success_count += 1
                    return True
                except:
                    continue

        print("   ❌ No monitoring available")
        return False

    def verify_system(self):
        """시스템 검증"""
        print("\n🔍 Verifying System...")

        # Test message sending
        try:
            register_script = self.tools_dir / "ipc_register.py"
            send_script = self.tools_dir / "ipc_send.py"

            # Register as claude
            subprocess.run([sys.executable, str(register_script), "claude"],
                         capture_output=True, timeout=5)

            # Send test message
            result = subprocess.run(
                [sys.executable, str(send_script), "gemini",
                 "System verification test"],
                capture_output=True, text=True, timeout=5
            )

            if "Sent to" in result.stdout:
                print("   ✅ Message system working")
                self.success_count += 1
            else:
                print("   ⚠️ Message system needs attention")

        except Exception as e:
            self.log_error(f"Verification error: {e}")
            print("   ⚠️ Verification incomplete")

    def save_error_report(self):
        """에러 리포트 저장"""
        if self.error_log:
            error_file = self.project_root / "ERROR_REPORT.md"
            with error_file.open('a', encoding='utf-8') as f:
                f.write(f"\n\n## Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for error in self.error_log:
                    f.write(f"- {error}\n")
            print(f"\n📝 Error report saved to ERROR_REPORT.md")

    def show_final_status(self):
        """최종 상태 표시"""
        print("\n" + "="*60)
        print("✨ ULTIMATE IPC SYSTEM STATUS")
        print("="*60)

        success_rate = (self.success_count / 8) * 100 if self.success_count > 0 else 0

        print(f"\n🎯 Success Rate: {success_rate:.0f}%")
        print(f"   ✅ Successful operations: {self.success_count}/8")

        if self.error_log:
            print(f"   ⚠️ Errors encountered: {len(self.error_log)}")
            print("\n   Recent errors:")
            for error in self.error_log[-3:]:
                print(f"      • {error}")

        print("\n📚 Quick Commands:")
        print("  • Send message: python tools/ipc_send.py <to> <message>")
        print("  • Check messages: python tools/ipc_check.py <instance>")
        print("  • List instances: python tools/ipc_list.py")

        print("\n💡 Tips:")
        print("  • Monitor window shows real-time messages")
        print("  • Auto-responders reply automatically")
        print("  • Press Ctrl+C to stop all services")

        print("\n" + "="*60)
        if success_rate >= 75:
            print("💚 System is operational!")
        elif success_rate >= 50:
            print("🟡 System partially operational")
        else:
            print("🔴 System needs attention")
        print("="*60)

    def run(self):
        """메인 실행"""
        print("\n" + "="*60)
        print("      🚀 ULTIMATE IPC SYSTEM LAUNCHER")
        print("         One-Click Complete Solution")
        print("="*60)
        print(f"📁 Project: {self.project_root}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        try:
            # 1. Check Python
            if not self.check_python():
                return

            # 2. Cleanup old processes
            self.cleanup_old_processes()

            # 3. Start IPC server
            self.start_ipc_server()

            # 4. Register instances
            self.register_all_instances()

            # 5. Start auto-responders
            self.create_auto_responders()

            # 6. Start unified monitoring
            self.start_unified_monitoring()

            # 7. Verify system
            self.verify_system()

            # 8. Save error report if needed
            if self.error_log:
                self.save_error_report()

            # 9. Show final status
            self.show_final_status()

            # Keep running
            print("\n💚 Press Ctrl+C to stop all services...")
            while True:
                time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
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
            # Close all related windows
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul',
                         shell=True, capture_output=True)
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul',
                         shell=True, capture_output=True)
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *IPC*" 2>nul',
                         shell=True, capture_output=True)

        print("✅ All services stopped")

if __name__ == "__main__":
    try:
        system = UltimateIPCSystem()
        system.run()
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)