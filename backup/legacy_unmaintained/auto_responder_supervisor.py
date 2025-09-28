#!/usr/bin/env python3
"""
🎯 Auto-Responder Supervisor Process
자동 응답기 감독 프로세스 - 모든 auto-responder 관리
"""

import os
import sys
import subprocess
import time
import threading
import json
from pathlib import Path
from datetime import datetime
import psutil

class AutoResponderSupervisor:
    def __init__(self):
        self.responders = {}
        self.instances = ["gemini", "codex", "lm", "chatgpt", "llama"]
        self.health_check_interval = 30  # seconds
        self.max_restart_attempts = 3
        self.restart_counts = {}
        self.running = True
        self.log_file = Path.home() / ".claude-ipc-data" / "supervisor.log"
        self.log_file.parent.mkdir(exist_ok=True)

    def log(self, message):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def start_responder(self, instance_id):
        """Start an auto-responder for a specific instance"""
        try:
            # Use the robust auto-responder
            responder_script = Path(__file__).parent / "tools" / "robust_auto_responder.py"

            # Fallback to simple if robust doesn't exist
            if not responder_script.exists():
                responder_script = Path(__file__).parent / "tools" / "simple_auto_responder.py"

            if not responder_script.exists():
                self.log(f"❌ Auto-responder script not found for {instance_id}")
                return None

            # Start the process
            if os.name == 'nt':
                # Windows: Create new window for each responder
                process = subprocess.Popen(
                    f'start "Auto-Responder: {instance_id}" /min {sys.executable} {responder_script} {instance_id}',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Unix: Background process
                process = subprocess.Popen(
                    [sys.executable, str(responder_script), instance_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # Store process info
            self.responders[instance_id] = {
                'process': process,
                'pid': process.pid,
                'last_heartbeat': datetime.now(),
                'restart_count': self.restart_counts.get(instance_id, 0),
                'status': 'running'
            }

            self.log(f"✅ Started auto-responder for {instance_id} (PID: {process.pid})")
            return process

        except Exception as e:
            self.log(f"❌ Failed to start responder for {instance_id}: {e}")
            return None

    def check_process_health(self, instance_id):
        """Check if a responder process is still running"""
        if instance_id not in self.responders:
            return False

        info = self.responders[instance_id]
        process = info['process']

        # Check if process is still running
        if process.poll() is not None:
            # Process has terminated
            return False

        # Additional check using psutil if available
        try:
            if psutil.pid_exists(info['pid']):
                # Check if process is responsive (not zombie)
                proc = psutil.Process(info['pid'])
                if proc.status() == psutil.STATUS_ZOMBIE:
                    return False
                return True
        except:
            # Fallback to basic check
            return process.poll() is None

        return True

    def restart_responder(self, instance_id):
        """Restart a failed responder"""
        self.log(f"🔄 Restarting auto-responder for {instance_id}")

        # Increment restart count
        self.restart_counts[instance_id] = self.restart_counts.get(instance_id, 0) + 1

        if self.restart_counts[instance_id] > self.max_restart_attempts:
            self.log(f"❌ Max restart attempts reached for {instance_id}. Giving up.")
            if instance_id in self.responders:
                self.responders[instance_id]['status'] = 'failed'
            return False

        # Kill existing process if still lingering
        if instance_id in self.responders:
            try:
                process = self.responders[instance_id]['process']
                if process.poll() is None:
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
            except:
                pass

        # Wait a moment before restarting
        time.sleep(2)

        # Start new process
        if self.start_responder(instance_id):
            self.log(f"✅ Successfully restarted {instance_id}")
            return True
        else:
            self.log(f"❌ Failed to restart {instance_id}")
            return False

    def health_check_loop(self):
        """Continuous health check for all responders"""
        while self.running:
            time.sleep(self.health_check_interval)

            if not self.running:
                break

            self.log("🔍 Performing health check...")

            for instance_id in self.instances:
                if not self.check_process_health(instance_id):
                    self.log(f"⚠️ {instance_id} responder is not healthy")

                    # Check if we should attempt restart
                    if instance_id in self.responders:
                        status = self.responders[instance_id].get('status', 'unknown')
                        if status != 'failed':
                            self.restart_responder(instance_id)
                    else:
                        # Not started yet, start it
                        self.start_responder(instance_id)

            # Reset restart counts every hour
            current_time = datetime.now()
            if current_time.minute == 0 and current_time.second < 30:
                self.restart_counts = {}
                self.log("📊 Reset restart counts")

    def start_all(self):
        """Start all auto-responders"""
        self.log("🚀 Starting all auto-responders...")

        for instance_id in self.instances:
            self.start_responder(instance_id)
            time.sleep(0.5)  # Small delay between starts

    def stop_all(self):
        """Stop all auto-responders"""
        self.log("🛑 Stopping all auto-responders...")

        for instance_id, info in self.responders.items():
            try:
                process = info['process']
                if process.poll() is None:
                    process.terminate()
                    self.log(f"  Stopped {instance_id}")
            except Exception as e:
                self.log(f"  Error stopping {instance_id}: {e}")

    def status_report(self):
        """Generate status report"""
        report = []
        report.append("\n" + "="*60)
        report.append("📊 AUTO-RESPONDER STATUS REPORT")
        report.append("="*60)

        for instance_id in self.instances:
            if instance_id in self.responders:
                info = self.responders[instance_id]
                health = "✅ HEALTHY" if self.check_process_health(instance_id) else "❌ UNHEALTHY"
                restarts = self.restart_counts.get(instance_id, 0)
                status = info.get('status', 'unknown')
                report.append(f"{instance_id:10} | {health:12} | Restarts: {restarts} | Status: {status}")
            else:
                report.append(f"{instance_id:10} | ⚫ NOT STARTED")

        report.append("="*60 + "\n")
        return "\n".join(report)

    def run(self):
        """Main supervisor loop"""
        print("\n" + "="*60)
        print("🎯 AUTO-RESPONDER SUPERVISOR")
        print("="*60)
        print("Managing auto-responders for:", ", ".join(self.instances))
        print("Health check interval:", self.health_check_interval, "seconds")
        print("Max restart attempts:", self.max_restart_attempts)
        print("="*60 + "\n")

        try:
            # Start all responders
            self.start_all()

            # Start health check thread
            health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
            health_thread.start()

            # Main loop for status reporting
            last_report_time = datetime.now()

            while self.running:
                try:
                    # Print status report every minute
                    if (datetime.now() - last_report_time).seconds >= 60:
                        print(self.status_report())
                        last_report_time = datetime.now()

                    time.sleep(5)

                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            self.log("\n⚠️ Keyboard interrupt received")

        finally:
            self.running = False
            self.stop_all()
            self.log("👋 Supervisor stopped")

def main():
    supervisor = AutoResponderSupervisor()

    try:
        supervisor.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Try to import psutil for better process management
    try:
        import psutil
    except ImportError:
        print("Warning: psutil not installed. Process management may be limited.")
        print("Install with: pip install psutil")

    main()