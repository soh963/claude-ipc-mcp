#!/usr/bin/env python3
"""
🩺 IPC Doctor - A diagnostic tool for the Claude IPC MCP system.

This tool runs a series of checks to diagnose common communication problems
and provides actionable recommendations.
"""

import os
import json
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876
DB_PATH = Path.home() / ".claude-ipc-data" / "messages.db"
SESSION_FILE_PATH = Path.home() / ".ipc-session"

# --- Helper Functions ---


def print_check(description: str, success: bool, details: str = ""):
    """Formats and prints the result of a check."""
    status = "[✅]" if success else "[❌]"
    print(f"{status} {description:.<40} {'' if not details else '-> ' + details}")
    return success


# --- Check Functions ---


def check_broker_connection() -> bool:
    """Checks if a connection can be made to the IPC broker."""
    try:
        with socket.create_connection((BROKER_HOST, BROKER_PORT), timeout=2):
            return print_check(
                "Broker Connection", True, f"Successfully connected to {BROKER_HOST}:{BROKER_PORT}"
            )
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return print_check("Broker Connection", False, f"Failed to connect: {e}")


def check_session_file() -> dict | None:
    """Checks for the existence and validity of the session file."""
    if not SESSION_FILE_PATH.exists():
        print_check("Session File", False, f"File not found at {SESSION_FILE_PATH}")
        return None

    try:
        with open(SESSION_FILE_PATH, "r") as f:
            session_data = json.load(f)
        if "instance_id" in session_data and "session_token" in session_data:
            print_check(
                "Session File", True, f"Valid JSON for instance '{session_data['instance_id']}'"
            )
            return session_data
        else:
            print_check("Session File", False, "File is missing 'instance_id' or 'session_token'")
            return None
    except (json.JSONDecodeError, TypeError):
        print_check("Session File", False, "File is not valid JSON")
        return None


def check_shared_secret() -> bool:
    """Checks if the IPC_SHARED_SECRET environment variable is set."""
    secret = os.environ.get("IPC_SHARED_SECRET")
    if secret:
        return print_check("Shared Secret Env Var", True, "IPC_SHARED_SECRET is set")
    else:
        return print_check(
            "Shared Secret Env Var",
            False,
            "IPC_SHARED_SECRET is not set (Note: Only an issue if server requires it)",
        )


def check_schema_integrity() -> bool:
    """Connects to the database and verifies table schemas."""
    if not DB_PATH.exists():
        return print_check("Database Schema", False, f"Database not found at {DB_PATH}")

    expected_schema = {
        "instances": ["instance_id", "last_seen"],
        "sessions": ["session_token_hash", "instance_id", "created_at", "expires_at"],
        "messages": ["id", "from_id", "to_id", "content", "timestamp"],
    }
    all_ok = True
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for table, required_columns in expected_schema.items():
                cursor.execute(f"PRAGMA table_info({table})")
                actual_columns = [info[1] for info in cursor.fetchall()]
                if all(col in actual_columns for col in required_columns):
                    print_check(f"  - Table '{table}' Schema", True)
                else:
                    details = f"Missing columns in '{table}'. Expected: {required_columns}, Found: {actual_columns}"
                    print_check(f"  - Table '{table}' Schema", False, details)
                    all_ok = False
    except sqlite3.Error as e:
        return print_check("Database Schema", False, f"DB Error: {e}")

    return all_ok


def check_instance_registration(session_data: dict | None) -> bool:
    """Uses ipc_list.py to check if the current instance is registered."""
    if not session_data:
        return print_check("Instance Registration", False, "Skipped due to missing session file")

    try:
        # Assuming tools are in the parent directory of this script if run from tools/
        script_path = Path(__file__).parent / "ipc_list.py"
        if not script_path.exists():
            script_path = Path(__file__).parent.parent / "tools" / "ipc_list.py"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        instance_id = session_data["instance_id"]
        if f"ID: {instance_id}" in result.stdout:
            return print_check(
                "Instance Registration", True, f"'{instance_id}' is actively registered"
            )
        else:
            return print_check(
                "Instance Registration", False, f"'{instance_id}' not found in active list"
            )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_output = e.stderr or e.stdout or str(e)
        return print_check(
            "Instance Registration", False, f"ipc_list.py failed: {error_output.strip()}"
        )


# --- Main Execution ---


def main():
    """Runs all diagnostic checks and provides a final summary."""
    print("\n--- 🩺 Running IPC Doctor ---")
    recommendations = []

    # Run checks
    broker_ok = check_broker_connection()
    session_data = check_session_file()
    check_shared_secret()
    schema_ok = check_schema_integrity()

    # This check depends on the session and broker being okay
    if broker_ok and session_data:
        check_instance_registration(session_data)

    print("---------------------------------\n")

    # Generate recommendations
    if not broker_ok:
        recommendations.append(
            "The IPC message broker is not running. Start it with `claude-ipc-mcp`."
        )
    if not session_data:
        recommendations.append(
            "Your session file is missing or corrupt. Register your instance with `python tools/ipc_register.py <your_id>`."
        )
    if not schema_ok:
        recommendations.append(
            "The database schema is incorrect or corrupt. This is a critical error. The database may need to be rebuilt or the code updated to match the schema."
        )

    # Final Diagnosis
    if not recommendations:
        print("✅ No major issues found. Your configuration appears to be correct.")
        print(
            "If you still have issues, check for rate limiting or specific logic errors in your AI."
        )
    else:
        print("🚨 Diagnosis & Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    print("\n--- Diagnosis Complete ---\n")


if __name__ == "__main__":
    main()
