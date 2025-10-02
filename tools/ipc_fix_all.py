#!/usr/bin/env python3
"""
IPC Configuration Fixer

Automatically fixes all project configurations to use the running global broker.
"""

import json
import socket
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def find_running_broker(host: str = "127.0.0.1") -> Optional[Dict]:
    """Find the running broker and return its info."""
    common_ports = [9876] + list(range(9876, 9901)) + list(range(10000, 10100))

    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                # Verify broker protocol
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
                        return {"port": port, "host": host}
                except Exception:
                    pass
        except Exception:
            continue

    return None


def find_all_project_configs() -> List[Dict]:
    """Find all project.json files."""
    configs = []
    home = Path.home()

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

        for project_file in search_dir.rglob(".ipc/state/project.json"):
            try:
                data = json.loads(project_file.read_text(encoding="utf-8"))
                configs.append({
                    "path": str(project_file),
                    "project_root": data.get("root_path"),
                    "broker_port": data.get("broker_port"),
                })
            except Exception:
                pass

    return configs


def fix_all_projects(dry_run: bool = False) -> int:
    """Fix all project configurations."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔧 IPC Configuration Fixer{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    if dry_run:
        print(f"{YELLOW}📋 DRY RUN MODE - No changes will be made{RESET}\n")

    # Find running broker
    print(f"{BLUE}Step 1: Detecting running broker...{RESET}")
    running_broker = find_running_broker()

    if not running_broker:
        print(f"{RED}❌ Error: No running broker found{RESET}")
        print(f"{YELLOW}💡 Please start the broker first: {GREEN}uv run python tools/start_broker.py{RESET}\n")
        return 1

    target_port = running_broker["port"]
    print(f"{GREEN}✅ Found broker on port {target_port}{RESET}\n")

    # Find all configs
    print(f"{BLUE}Step 2: Finding project configurations...{RESET}")
    configs = find_all_project_configs()

    if not configs:
        print(f"{YELLOW}⚠️ No project configurations found{RESET}")
        return 0

    print(f"{GREEN}✅ Found {len(configs)} project(s){RESET}\n")

    # Fix mismatches
    print(f"{BLUE}Step 3: Fixing configurations...{RESET}\n")
    fixed_count = 0
    skipped_count = 0

    for config in configs:
        config_path = Path(config["path"])
        current_port = config["broker_port"]

        if current_port == target_port:
            print(f"{GREEN}✓{RESET} {config['project_root']}: Already correct (port {target_port})")
            skipped_count += 1
            continue

        # Update config
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            data["broker_port"] = target_port

            if not dry_run:
                config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"{GREEN}✓{RESET} {config['project_root']}: Fixed {current_port} → {target_port}")
            else:
                print(f"{YELLOW}→{RESET} {config['project_root']}: Would fix {current_port} → {target_port}")

            fixed_count += 1
        except Exception as e:
            print(f"{RED}✗{RESET} {config['project_root']}: Failed to fix: {e}")

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}📊 Summary:{RESET}")
    print(f"   Fixed: {GREEN}{fixed_count}{RESET}")
    print(f"   Already correct: {GREEN}{skipped_count}{RESET}")
    print(f"   Total: {len(configs)}")

    if dry_run and fixed_count > 0:
        print(f"\n{YELLOW}💡 Run without --dry-run to apply changes:{RESET}")
        print(f"   {GREEN}python tools/ipc_fix_all.py{RESET}")

    print(f"{BLUE}{'='*60}{RESET}\n")

    return 0


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sys.exit(fix_all_projects(dry_run=dry_run))
