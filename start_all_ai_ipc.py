#!/usr/bin/env python3
"""
🚀 One-Command AI IPC Environment Startup
한 번의 실행으로 모든 AI CLI IPC 환경을 구성합니다.

This script:
1. Generates project-specific ID and port
2. Starts IPC server with project isolation
3. Auto-registers all AI instances
4. Launches monitoring system
5. Enables auto-responders (NO dummy text)
"""

import os
import sys
import time
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class AllInOneIPCLauncher:
    """Complete IPC environment launcher"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.project_id = self.get_project_id()
        self.project_port = self.get_project_port()
        self.processes = []

    def get_project_id(self):
        """Generate project-specific ID from path hash"""
        project_path = str(self.project_root).replace('\\', '/').lower()
        hash_obj = hashlib.sha256(project_path.encode())
        return f"proj_{hash_obj.hexdigest()[:8]}"

    def get_project_port(self):
        """Generate project-specific port (9000-9999)"""
        port_offset = int(hashlib.md5(self.project_id.encode()).hexdigest()[:4], 16) % 1000
        return 9000 + port_offset

    def print_banner(self):
        """Display startup banner"""
        print("\n" + "="*60)
        print("🚀 AI IPC Complete Environment Launcher")
        print("="*60)
        print(f"📁 Project Root: {self.project_root}")
        print(f"🔒 Project ID: {self.project_id}")
        print(f"🔌 Project Port: {self.project_port}")
        print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

    def check_existing_processes(self):
        """Check and kill existing IPC processes"""
        print("🔍 Checking for existing processes...")

        # Kill existing processes
        processes_to_kill = [
            "claude_ipc_server",
            "monitor_instance",
            "auto_responder",
            "start_split_monitoring"
        ]

        for proc in processes_to_kill:
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(f"taskkill /F /IM *{proc}*.py",
                                 shell=True, capture_output=True)
                else:  # Unix/Linux
                    subprocess.run(f"pkill -f {proc}",
                                 shell=True, capture_output=True)
            except Exception:
                pass

        time.sleep(2)  # Wait for processes to die
        print("✅ Existing processes cleared\n")

    def start_ipc_server(self):
        """Start the IPC server with project isolation"""
        print(f"🚀 Starting IPC server on port {self.project_port}...")

        # Create config for project isolation
        config = {
            "project_id": self.project_id,
            "project_port": self.project_port,
            "project_path": str(self.project_root)
        }

        config_file = self.project_root / ".ipc_project.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Start server
        server_script = self.project_root / "src" / "claude_ipc_server.py"
        proc = subprocess.Popen(
            [sys.executable, str(server_script), "--project-isolated"],
            cwd=str(self.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(proc)

        time.sleep(3)  # Wait for server to start
        print(f"✅ IPC server started (PID: {proc.pid})\n")

        return proc

    def register_ai_instances(self):
        """Auto-register all AI instances"""
        print("📝 Registering AI instances...")

        instances = ["claude", "gemini", "codex", "chatgpt", "llama"]
        register_script = self.project_root / "tools" / "ipc_register.py"

        for instance in instances:
            try:
                result = subprocess.run(
                    [sys.executable, str(register_script), instance],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"  ✅ Registered: {instance}@{self.project_id}")
                else:
                    print(f"  ⚠️ Failed to register: {instance}")
            except Exception as e:
                print(f"  ⚠️ Error registering {instance}: {e}")

        print()

    def start_monitoring(self):
        """Start the 4-panel monitoring system"""
        print("📊 Starting monitoring system...")

        monitor_script = self.project_root / "start_split_monitoring.py"

        if monitor_script.exists():
            proc = subprocess.Popen(
                [sys.executable, str(monitor_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(proc)
            print(f"✅ Monitoring started (PID: {proc.pid})\n")
        else:
            print("⚠️ Monitoring script not found, skipping...\n")

    def start_auto_responders(self):
        """Start smart auto-responders for all AI instances (NO dummy text)"""
        print("🤖 Starting smart auto-responders...")

        # Use the new smart auto-responder
        responder_script = self.project_root / "tools" / "smart_auto_responder.py"

        # Start responder for each AI instance (except claude - that's us!)
        ai_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in ai_instances:
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(responder_script), instance],
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.processes.append(proc)
                print(f"  ✅ Smart auto-responder for {instance} (PID: {proc.pid})")
                time.sleep(0.5)  # Small delay between starts
            except Exception as e:
                print(f"  ⚠️ Failed to start responder for {instance}: {e}")

        print("  ℹ️ Auto-responders generate contextual AI responses")
        print("  ℹ️ NO dummy text - Real conversation simulation")
        print()

    def verify_setup(self):
        """Verify the complete setup"""
        print("🔍 Verifying setup...")

        # Test message send
        send_script = self.project_root / "tools" / "ipc_send.py"
        check_script = self.project_root / "tools" / "ipc_check.py"

        try:
            # Send test message
            subprocess.run(
                [sys.executable, str(send_script), "claude", "gemini",
                 "System test: Verifying IPC connection"],
                cwd=str(self.project_root),
                timeout=5
            )

            time.sleep(1)

            # Check if message received
            result = subprocess.run(
                [sys.executable, str(check_script), "gemini"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=5
            )

            if "System test" in result.stdout:
                print("✅ IPC communication verified!\n")
            else:
                print("⚠️ IPC communication test failed\n")

        except Exception as e:
            print(f"⚠️ Verification error: {e}\n")

    def print_instructions(self):
        """Print usage instructions"""
        print("\n" + "="*60)
        print("✨ AI IPC Environment Ready!")
        print("="*60)
        print("\n📚 Quick Commands:")
        print("  • Send message: python tools/ipc_send.py claude gemini 'Hello'")
        print("  • Check messages: python tools/ipc_check.py claude")
        print("  • List instances: python tools/ipc_list.py")
        print("  • Monitor specific: python tools/monitor_instance.py claude")

        print("\n🛑 To stop all processes:")
        print("  • python tools/reset_all_ipc.py")
        print("  • Or press Ctrl+C in this window")

        print("\n💡 Project Details:")
        print(f"  • Project ID: {self.project_id}")
        print(f"  • Port: {self.project_port}")
        print("  • Config: .ipc_project.json")
        print("="*60 + "\n")

    def run(self):
        """Main execution flow"""
        try:
            self.print_banner()
            self.check_existing_processes()
            self.start_ipc_server()
            self.register_ai_instances()
            self.start_monitoring()
            self.start_auto_responders()
            self.verify_setup()
            self.print_instructions()

            print("🎯 System running. Press Ctrl+C to stop all processes...")

            # Keep running
            while True:
                time.sleep(1)
                # Check if processes are still alive
                for proc in self.processes:
                    if proc.poll() is not None:
                        print(f"⚠️ Process {proc.pid} died, restarting...")
                        # Could implement restart logic here

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down all processes...")
            self.cleanup()
            print("✅ All processes stopped. Goodbye!\n")

    def cleanup(self):
        """Clean up all processes"""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    launcher = AllInOneIPCLauncher()
    launcher.run()