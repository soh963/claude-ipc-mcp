#!/usr/bin/env python3
"""
Complete IPC System Reset
"""

import os
import subprocess
import time
import sqlite3
from pathlib import Path


def main():
    print("\n" + "=" * 60)
    print("IPC SYSTEM COMPLETE RESET")
    print("=" * 60)

    # 1. Kill all Python processes (Windows)
    print("\n1. Terminating all Python processes...")
    if os.name == "nt":
        subprocess.run("taskkill /F /IM python.exe 2>nul", shell=True, capture_output=True)
        subprocess.run("taskkill /F /IM pythonw.exe 2>nul", shell=True, capture_output=True)

    print("   OK - All processes terminated")
    time.sleep(2)

    # 2. Clean up database
    print("\n2. Cleaning up database...")
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Clear all tables
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM instances")
            cursor.execute("DELETE FROM sessions")
            cursor.execute("DELETE FROM name_history")

            conn.commit()
            print("   OK - Database cleared")
            conn.close()
        except Exception as e:
            print(f"   Warning: {e}")

    # 3. Remove session file
    print("\n3. Removing session file...")
    session_file = Path.home() / ".ipc-session"
    if session_file.exists():
        session_file.unlink()
        print("   OK - Session file removed")

    print("\n" + "=" * 60)
    print("SYSTEM RESET COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
