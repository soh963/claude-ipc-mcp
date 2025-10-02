#!/usr/bin/env python3
"""
IPC Configuration Validator

Validates all project configurations and checks for port mismatches.
Provides detailed diagnostics and suggestions.
"""

import json
import socket
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def find_running_broker(host: str = "127.0.0.1") -> Optional[Dict]:
    """Find the running broker and return its info."""
    # Common broker ports to check
    common_ports = [9876] + list(range(9876, 9901)) + list(range(10000, 10100))

    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                # Port is open, try to verify it's a broker
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    sock.connect((host, port))
                    ping_request = json.dumps({"action": "ping"}) + "\n"
                    sock.sendall(ping_request.encode())
                    response = sock.recv(4096).decode()
                    sock.close()

                    data = json.loads(response.strip())
                    if data.get("status") == "ok" or data.get("pong") == True:
                        return {"port": port, "host": host, "verified": True}
                except Exception:
                    pass

                # Port is open but not verified
                return {"port": port, "host": host, "verified": False}
        except Exception:
            continue

    return None


def find_all_project_configs() -> List[Dict]:
    """Find all project.json files in the user's home directory."""
    configs = []
    home = Path.home()

    # Search common project locations
    search_dirs = [
        Path("D:/claude-ipc-mcp"),
        Path("D:/test-tem"),
        home / "Documents",
        home / "Projects",
        home / "Code",
        home / "workspace",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Find .ipc/state/project.json files
        for project_file in search_dir.rglob(".ipc/state/project.json"):
            try:
                data = json.loads(project_file.read_text(encoding="utf-8"))
                configs.append({
                    "path": str(project_file),
                    "project_root": data.get("root_path"),
                    "project_id": data.get("project_id"),
                    "broker_port": data.get("broker_port"),
                    "broker_host": data.get("broker_host", "127.0.0.1"),
                })
            except Exception as e:
                print(f"{YELLOW}⚠️ Warning: Failed to read {project_file}: {e}{RESET}")

    return configs


def validate_configuration() -> int:
    """Validate all project configurations and return exit code."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔍 IPC Configuration Validator{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # 1. Find running broker
    print(f"{BLUE}Step 1: Detecting running broker...{RESET}")
    running_broker = find_running_broker()

    if running_broker:
        verified_str = "✅ Verified" if running_broker["verified"] else "⚠️ Not verified"
        print(f"{GREEN}✅ Found broker on port {running_broker['port']} ({verified_str}){RESET}\n")
    else:
        print(f"{YELLOW}⚠️ No running broker detected{RESET}\n")

    # 2. Find all project configs
    print(f"{BLUE}Step 2: Finding project configurations...{RESET}")
    configs = find_all_project_configs()

    if not configs:
        print(f"{YELLOW}⚠️ No project configurations found{RESET}")
        return 0

    print(f"{GREEN}✅ Found {len(configs)} project(s){RESET}\n")

    # 3. Check for mismatches
    print(f"{BLUE}Step 3: Validating configurations...{RESET}\n")
    issues = []

    for config in configs:
        port = config["broker_port"]
        project_root = config["project_root"]

        # Issue 1: Port mismatch with running broker
        if running_broker and port != running_broker["port"]:
            issues.append({
                "type": "port_mismatch",
                "severity": "high",
                "project": project_root,
                "configured_port": port,
                "expected_port": running_broker["port"],
                "message": f"Project configured for port {port} but broker is on {running_broker['port']}",
            })

        # Issue 2: No running broker but port is not default
        elif not running_broker and port != 9876:
            issues.append({
                "type": "no_broker",
                "severity": "medium",
                "project": project_root,
                "configured_port": port,
                "message": f"No broker running, but project configured for port {port} (default is 9876)",
            })

    # 4. Report results
    if not issues:
        print(f"{GREEN}✅ All configurations are valid!{RESET}\n")
        return 0

    print(f"{RED}❌ Found {len(issues)} issue(s):{RESET}\n")

    for i, issue in enumerate(issues, 1):
        severity_color = RED if issue["severity"] == "high" else YELLOW
        print(f"{severity_color}Issue {i}: [{issue['severity'].upper()}]{RESET}")
        print(f"  Project: {issue['project']}")
        print(f"  Problem: {issue['message']}")

        if issue["type"] == "port_mismatch":
            print(f"  Configured port: {issue['configured_port']}")
            print(f"  Expected port: {issue['expected_port']}")

        print()

    # 5. Provide fix suggestion
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}💡 Suggestion:{RESET}")
    print(f"   Run {GREEN}ipc fix{RESET} or {GREEN}python tools/ipc_fix_all.py{RESET} to automatically fix these issues.")
    print(f"{BLUE}{'='*60}{RESET}\n")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(validate_configuration())
