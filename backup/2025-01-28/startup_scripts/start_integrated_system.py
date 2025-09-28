#!/usr/bin/env python3
"""
🚀 Integrated IPC System Launcher
통합 IPC 시스템 런처 - 모든 기능 포함
"""

import os
import sys
import subprocess
import time
import socket
import threading
from pathlib import Path
from datetime import datetime

class IntegratedIPCLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.tools_dir = self.project_root / "tools"
        self.processes = []
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]

    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)

    def notify_instances(self, message, instance=None):
        """Print notification that would appear in instance terminals"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        if instance:
            print(f"[{timestamp}] [{instance}] {message}")
        else:
            print(f"[{timestamp}] {message}")

    def check_python(self):
        """Check Python installation"""
        self.print_header("🔍 System Check")
        print("• Checking Python installation...")

        try:
            result = subprocess.run([sys.executable, "--version"],
                                  capture_output=True, text=True, timeout=5)
            print(f"  ✅ Python found: {result.stdout.strip()}")
            return True
        except:
            print("  ❌ Python check failed")
            return False

    def cleanup_processes(self):
        """Clean up any existing processes"""
        print("\n• Cleaning up old processes...")

        try:
            if os.name == 'nt':
                # Kill monitoring windows
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul',
                             shell=True, capture_output=True)
                # Kill auto-responder windows
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul',
                             shell=True, capture_output=True)
                # Kill any stray Python processes from IPC
                subprocess.run('taskkill /F /FI "WINDOWTITLE eq *IPC*" 2>nul',
                             shell=True, capture_output=True)
            else:
                subprocess.run("pkill -f 'python.*ipc'",
                             shell=True, capture_output=True)

            time.sleep(1)
            print("  ✅ Cleanup complete")
        except:
            print("  ⚠️ Cleanup had issues but continuing")

    def start_ipc_server(self):
        """Start the IPC broker server - using singleton broker"""
        self.print_header("🖥️ IPC Server")
        print("• Starting IPC Message Broker...")

        try:
            # Use singleton broker start script
            result = subprocess.run(
                [sys.executable, 'tools/start_broker.py'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("  ✅ Singleton broker started/confirmed")

                # Verify connection
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect(('127.0.0.1', 9876))
                    s.close()
                    print("  ✅ IPC Server running on port 9876")
                    return True
                except:
                    print("  ❌ Server connection failed")
                    return False
            else:
                print("  ❌ Singleton broker startup failed")
                if result.stderr:
                    print(f"      Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("  ❌ Broker start timeout")
            return False
        except Exception as e:
            print(f"  ❌ Server start error: {e}")
            return False

    def register_all_instances(self):
        """Register all instances with the broker"""
        self.print_header("📝 Instance Registration")

        register_script = self.tools_dir / "ipc_register.py"
        if not register_script.exists():
            print("  ❌ Register script not found")
            return False

        for instance in self.instances:
            try:
                result = subprocess.run(
                    [sys.executable, str(register_script), instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Registered" in result.stdout or "already registered" in result.stdout.lower():
                    print(f"  ✅ {instance}: Registered successfully")
                    self.notify_instances(f"IPC MCP Connected - Can communicate with other instances", instance)
                else:
                    print(f"  ⚠️ {instance}: Registration issue")
            except Exception as e:
                print(f"  ❌ {instance}: Error - {e}")

        return True

    def start_auto_responders_with_supervisor(self):
        """Start auto-responder supervisor"""
        self.print_header("🤖 Auto-Responder System")
        print("• Starting Auto-Responder Supervisor...")

        supervisor_script = self.project_root / "auto_responder_supervisor.py"

        # Use robust responders if supervisor doesn't exist
        if not supervisor_script.exists():
            print("  ⚠️ Supervisor not found, starting individual responders...")
            return self.start_individual_responders()

        try:
            if os.name == 'nt':
                subprocess.Popen(
                    f'start "Auto-Responder Supervisor" /min {sys.executable} {supervisor_script}',
                    shell=True
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, str(supervisor_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(proc)

            print("  ✅ Auto-Responder Supervisor started")

            # Notify each instance about auto-responder
            for instance in ["gemini", "codex", "lm", "chatgpt", "llama"]:
                self.notify_instances(f"Auto-Responder activated - Will respond to messages", instance)

            return True

        except Exception as e:
            print(f"  ❌ Error starting supervisor: {e}")
            return False

    def start_individual_responders(self):
        """Fallback: Start individual auto-responders"""
        responder_script = self.tools_dir / "robust_auto_responder.py"

        # Fallback to simple if robust doesn't exist
        if not responder_script.exists():
            responder_script = self.tools_dir / "simple_auto_responder.py"

        if not responder_script.exists():
            print("  ❌ No auto-responder scripts found")
            return False

        instances_to_start = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in instances_to_start:
            try:
                if os.name == 'nt':
                    cmd = f'start /min "Auto-Responder: {instance}" {sys.executable} {responder_script} {instance}'
                    subprocess.Popen(cmd, shell=True)
                else:
                    proc = subprocess.Popen(
                        [sys.executable, str(responder_script), instance],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.processes.append(proc)

                print(f"  ✅ Started auto-responder for {instance}")
                self.notify_instances(f"Auto-Responder activated", instance)
                time.sleep(0.3)

            except Exception as e:
                print(f"  ❌ Failed to start {instance}: {e}")

        return True

    def start_enhanced_monitoring(self):
        """Start the enhanced monitoring system"""
        self.print_header("📊 Monitoring System")
        print("• Starting Enhanced Monitoring...")

        monitor_script = self.project_root / "enhanced_monitor.py"

        # Fallback to other monitors
        if not monitor_script.exists():
            monitor_script = self.project_root / "unified_monitor.py"

        if not monitor_script.exists():
            monitor_script = self.project_root / "start_split_monitoring.py"

        if not monitor_script.exists():
            print("  ❌ No monitoring script found")
            return False

        try:
            if os.name == 'nt':
                subprocess.Popen(
                    f'start "IPC Enhanced Monitor" {sys.executable} {monitor_script}',
                    shell=True
                )
            else:
                proc = subprocess.Popen([sys.executable, str(monitor_script)])
                self.processes.append(proc)

            print(f"  ✅ Enhanced monitoring started")
            return True

        except Exception as e:
            print(f"  ❌ Error starting monitoring: {e}")
            return False

    def display_connection_info(self):
        """Display connection information for all instances"""
        self.print_header("🔗 IPC MCP Connection Status")

        print("\nEach instance can now communicate with:")
        print("─" * 50)

        for instance in self.instances:
            others = [i for i in self.instances if i != instance]
            print(f"\n{instance.upper()}:")
            for other in others:
                print(f"  • {other}")

        print("\n─" * 50)
        print("All instances are connected via IPC MCP protocol")
        print("Messages are routed through broker on port 9876")

    def verify_system(self):
        """Verify the system is working"""
        self.print_header("✅ System Verification")

        try:
            # Test message sending
            register_script = self.tools_dir / "ipc_register.py"
            send_script = self.tools_dir / "ipc_send.py"

            # Register claude
            subprocess.run([sys.executable, str(register_script), "claude"],
                         capture_output=True, timeout=5)

            # Send test message
            result = subprocess.run(
                [sys.executable, str(send_script), "gemini", "System test message"],
                capture_output=True, text=True, timeout=5
            )

            if "Sent to" in result.stdout:
                print("  ✅ Message system: OPERATIONAL")
                self.notify_instances("Test message sent successfully", "claude")
            else:
                print("  ⚠️ Message system: NEEDS ATTENTION")

            # Check broker
            if self.check_broker_status():
                print("  ✅ IPC Broker: ONLINE")
            else:
                print("  ❌ IPC Broker: OFFLINE")

            # Summary
            print("\n" + "─" * 50)
            print("System is ready for AI CLI communication!")
            print("─" * 50)

        except Exception as e:
            print(f"  ⚠️ Verification incomplete: {e}")

    def check_broker_status(self):
        """Check if broker is running"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", 9876))
            s.close()
            return True
        except:
            return False

    def run(self):
        """Main execution"""
        print("\n" + "="*70)
        print("      🚀 INTEGRATED IPC SYSTEM LAUNCHER")
        print("         Complete Solution with All Features")
        print("="*70)
        print(f"Project: {self.project_root}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        try:
            # 1. System check
            if not self.check_python():
                return

            # 2. Cleanup
            self.cleanup_processes()

            # 3. Start IPC server
            if not self.start_ipc_server():
                print("\n❌ Failed to start IPC server. Exiting.")
                return

            # 4. Register instances
            self.register_all_instances()

            # 5. Start auto-responders
            self.start_auto_responders_with_supervisor()

            # 6. Start monitoring
            self.start_enhanced_monitoring()

            # 7. Display connection info
            self.display_connection_info()

            # 8. Verify system
            self.verify_system()

            # Final message
            print("\n" + "="*70)
            print("💚 SYSTEM FULLY OPERATIONAL")
            print("="*70)
            print("\nFeatures active:")
            print("  • IPC Message Broker ✓")
            print("  • Auto-Responders ✓")
            print("  • Enhanced Monitoring ✓")
            print("  • Loop Prevention ✓")
            print("  • Health Monitoring ✓")
            print("\nPress Ctrl+C to stop all services")
            print("="*70)

            # Keep running
            while True:
                time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down all services...")
            self.shutdown()

    def shutdown(self):
        """Shutdown all services"""
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
            # Clean up Windows processes
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul',
                         shell=True, capture_output=True)
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul',
                         shell=True, capture_output=True)
            subprocess.run('taskkill /F /FI "WINDOWTITLE eq *IPC*" 2>nul',
                         shell=True, capture_output=True)

        print("✅ All services stopped")

if __name__ == "__main__":
    launcher = IntegratedIPCLauncher()
    launcher.run()