#!/usr/bin/env python3
"""
Service Manager for Broker Daemon
Handles broker lifecycle management, health checks, and auto-start
"""

import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manages the broker daemon lifecycle
    - Checks if broker is running
    - Starts broker if needed
    - Stops broker gracefully
    - Provides health checks
    """

    def __init__(self, host: str = None, port: int = None):
        """Initialize service manager"""
        self.host = host or os.getenv("IPC_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("IPC_GLOBAL_PORT",
                                os.getenv("IPC_PORT", "9876")))

        # Paths - Use project-local .ipc directory
        from core.project_local import get_project_ipc_dir
        self.data_dir = get_project_ipc_dir() / "state"
        self.pid_file = self.data_dir / "broker.pid"
        self.log_file = get_project_ipc_dir() / "logs" / "broker.log"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def is_broker_running(self) -> bool:
        """Check if broker is running and responsive"""
        # First, try to connect to the broker
        if self._test_connection():
            # Verify it's actually our broker by trying a status request
            if self._test_broker_status():
                return True

        # Check PID file as fallback
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                if self._is_process_running(pid):
                    # Process exists, but not responding - might be starting up
                    return self._wait_for_broker(timeout=2)
            except (ValueError, OSError):
                pass

        return False

    def start_broker(self, timeout: int = 30) -> bool:
        """Start the broker daemon if not running"""
        # Check if already running
        if self.is_broker_running():
            logger.info("Broker is already running")
            return True

        logger.info(f"Starting broker daemon on {self.host}:{self.port}")

        # Clean up any stale PID file
        if self.pid_file.exists():
            try:
                old_pid = int(self.pid_file.read_text().strip())
                if not self._is_process_running(old_pid):
                    self.pid_file.unlink()
                    logger.info(f"Removed stale PID file for process {old_pid}")
            except:
                self.pid_file.unlink()

        # Find Python executable
        python_exe = sys.executable

        # Find broker daemon script
        broker_daemon_path = Path(__file__).parent / "daemon.py"
        if not broker_daemon_path.exists():
            logger.error(f"Broker daemon script not found: {broker_daemon_path}")
            return False

        # Prepare environment
        env = os.environ.copy()
        env["IPC_HOST"] = self.host
        env["IPC_GLOBAL_PORT"] = str(self.port)

        # Start broker process
        try:
            if platform.system() == "Windows":
                # Windows: Use CREATE_NO_WINDOW to run in background
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                # Use CREATE_NO_WINDOW flag
                CREATE_NO_WINDOW = 0x08000000

                process = subprocess.Popen(
                    [python_exe, str(broker_daemon_path)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
                )
            else:
                # Unix/Linux: Use nohup and setsid for proper daemonization
                process = subprocess.Popen(
                    [python_exe, str(broker_daemon_path)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid  # Create new session
                )

            logger.info(f"Started broker process with PID {process.pid}")

            # Wait for broker to be ready
            if self._wait_for_broker(timeout=timeout):
                logger.info("Broker daemon started successfully")
                return True
            else:
                logger.error("Broker daemon failed to start (timeout)")
                # Try to kill the process if it's still running
                try:
                    if platform.system() == "Windows":
                        subprocess.run(f"taskkill /F /PID {process.pid}",
                                     shell=True, capture_output=True)
                    else:
                        os.kill(process.pid, 9)
                except:
                    pass
                return False

        except Exception as e:
            logger.error(f"Failed to start broker daemon: {e}")
            return False

    def stop_broker(self, force: bool = False) -> bool:
        """Stop the broker daemon"""
        if not self.pid_file.exists():
            logger.info("No PID file found, broker may not be running")
            return True

        try:
            pid = int(self.pid_file.read_text().strip())
        except (ValueError, OSError) as e:
            logger.error(f"Could not read PID file: {e}")
            return False

        if not self._is_process_running(pid):
            logger.info(f"Process {pid} is not running")
            self.pid_file.unlink()
            return True

        logger.info(f"Stopping broker daemon (PID {pid})")

        try:
            if platform.system() == "Windows":
                # Windows: Use taskkill
                if force:
                    cmd = f"taskkill /F /PID {pid}"
                else:
                    cmd = f"taskkill /PID {pid}"
                result = subprocess.run(cmd, shell=True, capture_output=True)
                success = result.returncode == 0
            else:
                # Unix/Linux: Use kill signals
                if force:
                    os.kill(pid, 9)  # SIGKILL
                else:
                    os.kill(pid, 15)  # SIGTERM
                success = True

            if success:
                # Wait for process to terminate
                for _ in range(10):
                    if not self._is_process_running(pid):
                        break
                    time.sleep(0.5)

                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()

                logger.info("Broker daemon stopped")
                return True
            else:
                logger.error("Failed to stop broker daemon")
                return False

        except Exception as e:
            logger.error(f"Error stopping broker: {e}")
            return False

    def restart_broker(self, timeout: int = 30) -> bool:
        """Restart the broker daemon"""
        logger.info("Restarting broker daemon...")

        # Stop if running
        if self.is_broker_running():
            if not self.stop_broker():
                logger.warning("Failed to stop broker cleanly, forcing stop")
                self.stop_broker(force=True)

        # Wait a moment for port to be released
        time.sleep(2)

        # Start broker
        return self.start_broker(timeout=timeout)

    def get_broker_status(self) -> Dict[str, Any]:
        """Get detailed broker status"""
        status = {
            "running": False,
            "pid": None,
            "host": self.host,
            "port": self.port,
            "responsive": False,
            "version": None
        }

        # Check if running
        if self.is_broker_running():
            status["running"] = True
            status["responsive"] = True

            # Get PID
            if self.pid_file.exists():
                try:
                    status["pid"] = int(self.pid_file.read_text().strip())
                except:
                    pass

            # Get broker info via status request
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.host, self.port))

                request = json.dumps({"action": "status"})
                sock.send(request.encode())

                response_data = sock.recv(4096).decode()
                response = json.loads(response_data)

                if response.get("status") == "ok":
                    status["version"] = response.get("version")
                    status["instances"] = response.get("instances", [])
                    status["total_queued"] = response.get("total_queued", 0)
                    status["uptime"] = response.get("uptime")

                sock.close()
            except Exception as e:
                logger.debug(f"Could not get broker details: {e}")

        return status

    def ensure_broker_running(self) -> bool:
        """Ensure broker is running, start if needed"""
        if self.is_broker_running():
            return True

        logger.info("Broker is not running, starting...")
        return self.start_broker()

    def health_check(self) -> Tuple[bool, str]:
        """Perform health check on broker"""
        # Check if running
        if not self.is_broker_running():
            return False, "Broker is not running"

        # Try to register a test instance
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))

            # Test registration
            test_id = f"health_check_{int(time.time())}"
            request = json.dumps({"action": "register", "instance_id": test_id})
            sock.send(request.encode())

            response_data = sock.recv(4096).decode()
            response = json.loads(response_data)

            sock.close()

            if response.get("status") == "ok" and response.get("session_token"):
                return True, "Broker is healthy and accepting connections"
            else:
                return False, f"Broker responded but registration failed: {response}"

        except Exception as e:
            return False, f"Health check failed: {e}"

    def _test_connection(self) -> bool:
        """Test if broker is accepting connections"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except:
            return False

    def _test_broker_status(self) -> bool:
        """Test if broker responds to status request"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((self.host, self.port))

            request = json.dumps({"action": "status"})
            sock.send(request.encode())

            response_data = sock.recv(4096).decode()
            response = json.loads(response_data)

            sock.close()

            return response.get("status") == "ok"
        except:
            return False

    def _wait_for_broker(self, timeout: int = 30) -> bool:
        """Wait for broker to become responsive"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._test_connection():
                # Connection established, now test if it's actually responding
                if self._test_broker_status():
                    return True
            time.sleep(0.5)

        return False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        if platform.system() == "Windows":
            # Windows: Use tasklist
            try:
                result = subprocess.run(
                    f'tasklist /FI "PID eq {pid}"',
                    shell=True, capture_output=True, text=True
                )
                return str(pid) in result.stdout
            except:
                return False
        else:
            # Unix/Linux: Use kill signal 0
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def cleanup_stale_processes(self):
        """Clean up any stale broker processes"""
        # This is primarily for recovery from abnormal shutdowns
        logger.info("Checking for stale broker processes...")

        try:
            # Find any Python processes running daemon.py
            if platform.system() == "Windows":
                result = subprocess.run(
                    'wmic process where "name=\'python.exe\' or name=\'python3.exe\'" get ProcessId,CommandLine',
                    shell=True, capture_output=True, text=True
                )
                lines = result.stdout.strip().split('\n')
            else:
                result = subprocess.run(
                    "ps aux | grep -E 'python.*daemon.py' | grep -v grep",
                    shell=True, capture_output=True, text=True
                )
                lines = result.stdout.strip().split('\n')

            for line in lines:
                if 'daemon.py' in line and 'broker' in line.lower():
                    # Extract PID
                    parts = line.split()
                    if parts:
                        try:
                            if platform.system() == "Windows":
                                pid = int(parts[-1])  # PID is usually last on Windows
                            else:
                                pid = int(parts[1])  # PID is second column on Unix

                            # Don't kill if it's the current broker
                            if self.pid_file.exists():
                                current_pid = int(self.pid_file.read_text().strip())
                                if pid == current_pid and self._test_connection():
                                    continue

                            # Kill stale process
                            logger.warning(f"Found stale broker process {pid}, terminating...")
                            if platform.system() == "Windows":
                                subprocess.run(f"taskkill /F /PID {pid}",
                                             shell=True, capture_output=True)
                            else:
                                os.kill(pid, 9)
                        except:
                            pass

        except Exception as e:
            logger.debug(f"Error during stale process cleanup: {e}")


def main():
    """Command-line interface for service manager"""
    import argparse

    parser = argparse.ArgumentParser(description="Broker Service Manager")
    parser.add_argument("command", choices=["start", "stop", "restart", "status", "health"],
                       help="Command to execute")
    parser.add_argument("--host", help="Broker host")
    parser.add_argument("--port", type=int, help="Broker port")
    parser.add_argument("--force", action="store_true", help="Force stop")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create service manager
    manager = ServiceManager(host=args.host, port=args.port)

    # Execute command
    if args.command == "start":
        if manager.start_broker():
            print("✅ Broker started successfully")
            sys.exit(0)
        else:
            print("❌ Failed to start broker")
            sys.exit(1)

    elif args.command == "stop":
        if manager.stop_broker(force=args.force):
            print("✅ Broker stopped")
            sys.exit(0)
        else:
            print("❌ Failed to stop broker")
            sys.exit(1)

    elif args.command == "restart":
        if manager.restart_broker():
            print("✅ Broker restarted successfully")
            sys.exit(0)
        else:
            print("❌ Failed to restart broker")
            sys.exit(1)

    elif args.command == "status":
        status = manager.get_broker_status()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status["running"] else 1)

    elif args.command == "health":
        healthy, message = manager.health_check()
        print(f"{'✅' if healthy else '❌'} {message}")
        sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()