#!/usr/bin/env python3
"""
Comprehensive Broker Diagnostics
Checks broker status, port conflicts, process status, and connectivity
"""

import sys
import socket
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import broker_client


class BrokerDiagnostics:
    """Comprehensive broker diagnostics"""

    def __init__(self):
        self.port = broker_client.IPC_PORT
        self.host = broker_client.IPC_HOST
        self.issues = []
        self.warnings = []

    def check_port_listening(self) -> dict:
        """Check if port is listening"""
        result = {"listening": False, "pids": []}

        try:
            if sys.platform == "win32":
                output = subprocess.check_output(
                    f"netstat -ano | findstr :{self.port}",
                    shell=True,
                    text=True
                )
                lines = output.strip().split('\n')
                pid_set = set()
                for line in lines:
                    if "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid_set.add(parts[-1])
                result["pids"] = sorted(list(pid_set))
                result["listening"] = len(result["pids"]) > 0
            else:
                output = subprocess.check_output(
                    f"lsof -ti:{self.port}",
                    shell=True,
                    text=True
                )
                result["pids"] = output.strip().split('\n')
                result["listening"] = len(result["pids"]) > 0
        except subprocess.CalledProcessError:
            result["listening"] = False

        return result

    def check_socket_connect(self) -> dict:
        """Check if socket connection works"""
        result = {"success": False, "error": None}

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((self.host, self.port))
            s.close()
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)

        return result

    def check_api_status(self) -> dict:
        """Check if API responds correctly"""
        result = {"success": False, "response": None, "error": None}

        try:
            response = broker_client.status()
            result["response"] = response
            if response.get("status") == "ok":
                result["success"] = True
            else:
                result["error"] = f"Unexpected status: {response.get('status')}"
        except Exception as e:
            result["error"] = str(e)

        return result

    def check_ping(self) -> dict:
        """Check if ping works"""
        result = {"success": False, "rtt_ms": None, "error": None}

        try:
            ping_result = broker_client.ping()
            if ping_result.get("ok"):
                result["success"] = True
                result["rtt_ms"] = ping_result.get("rtt_ms")
            else:
                result["error"] = "Ping returned not ok"
        except Exception as e:
            result["error"] = str(e)

        return result

    def run_diagnostics(self) -> dict:
        """Run all diagnostics"""
        report = {
            "broker_config": {
                "host": self.host,
                "port": self.port
            }
        }

        # Check 1: Port listening
        print("1. Checking if port is listening...")
        port_check = self.check_port_listening()
        report["port_listening"] = port_check

        if not port_check["listening"]:
            self.issues.append("Port is not listening - broker may not be running")
            print("   ✗ Port is not listening")
        elif len(port_check["pids"]) > 1:
            self.warnings.append(f"Multiple processes ({len(port_check['pids'])}) using port")
            print(f"   ⚠ Multiple processes detected: {port_check['pids']}")
        else:
            print(f"   ✓ Port is listening (PID: {port_check['pids'][0]})")

        # Check 2: Socket connection
        print("2. Checking socket connection...")
        socket_check = self.check_socket_connect()
        report["socket_connect"] = socket_check

        if not socket_check["success"]:
            self.issues.append(f"Socket connection failed: {socket_check['error']}")
            print(f"   ✗ Connection failed: {socket_check['error']}")
        else:
            print("   ✓ Socket connection successful")

        # Check 3: API status
        print("3. Checking API status...")
        api_check = self.check_api_status()
        report["api_status"] = api_check

        if not api_check["success"]:
            self.issues.append(f"API status check failed: {api_check['error']}")
            print(f"   ✗ API check failed: {api_check['error']}")
        else:
            instances = api_check["response"].get("instances", [])
            print(f"   ✓ API working (instances: {len(instances)})")

        # Check 4: Ping
        print("4. Checking ping...")
        ping_check = self.check_ping()
        report["ping"] = ping_check

        if not ping_check["success"]:
            self.warnings.append(f"Ping failed: {ping_check['error']}")
            print(f"   ⚠ Ping failed: {ping_check['error']}")
        else:
            print(f"   ✓ Ping successful (RTT: {ping_check['rtt_ms']}ms)")

        # Summary
        report["issues"] = self.issues
        report["warnings"] = self.warnings
        report["healthy"] = len(self.issues) == 0

        return report


def main():
    """Main function"""
    print("="*60)
    print("BROKER DIAGNOSTICS")
    print("="*60 + "\n")

    diagnostics = BrokerDiagnostics()
    report = diagnostics.run_diagnostics()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if report["healthy"]:
        print("✅ Broker is healthy")
    else:
        print("❌ Broker has issues:")
        for issue in report["issues"]:
            print(f"  - {issue}")

    if report["warnings"]:
        print("\n⚠ Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    # Output JSON report
    print("\n" + "="*60)
    print("FULL REPORT (JSON)")
    print("="*60)
    print(json.dumps(report, indent=2))

    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())