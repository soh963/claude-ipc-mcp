#!/usr/bin/env python3
"""
Auto-recovery script for 500 Internal Server Error
Automatically recovers from API errors and restarts services
"""

import subprocess
import time
import sys
import os
import shutil
from pathlib import Path

def cleanup_processes():
    """Clean up zombie Python processes"""
    print("🔧 Cleaning up processes...")
    try:
        # Windows
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"],
                      capture_output=True, shell=True)
    except:
        # Unix/Linux
        subprocess.run(["pkill", "-f", "python"], capture_output=True)
    time.sleep(3)

def cleanup_cache():
    """Clean up cache directories"""
    print("🗑️ Cleaning cache...")
    cache_dirs = [
        Path.home() / ".cache" / "claude",
        Path.home() / ".claude" / "cache",
        Path("./tmp"),
        Path("./cache")
    ]

    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✓ Cleaned {cache_dir}")
            except Exception as e:
                print(f"  ⚠️ Could not clean {cache_dir}: {e}")

def restart_services():
    """Restart IPC services"""
    print("🚀 Restarting services...")

    # Start auto-responder
    subprocess.Popen([sys.executable, "tools/auto_responder.py"],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("  ✓ Auto-responder started")
    time.sleep(2)

def check_network():
    """Check network connectivity"""
    print("🌐 Checking network...")
    try:
        result = subprocess.run(["ping", "-n", "1", "api.anthropic.com"],
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("  ✓ Network connection OK")
            return True
        else:
            print("  ⚠️ Network connection issue")
            return False
    except:
        print("  ⚠️ Could not check network")
        return False

def auto_recover_500_error():
    """Main recovery function for 500 errors"""
    print("=" * 60)
    print("🔧 500 Error Auto-Recovery System")
    print("=" * 60)
    print()

    # Step 1: Check network
    if not check_network():
        print("⚠️ Network issues detected. Please check your connection.")
        return False

    # Step 2: Clean up processes
    cleanup_processes()

    # Step 3: Clean cache
    cleanup_cache()

    # Step 4: Restart services
    restart_services()

    print()
    print("=" * 60)
    print("✅ Recovery complete!")
    print("=" * 60)

    return True

def monitor_and_recover():
    """Monitor for errors and auto-recover"""
    print("👁️ Monitoring mode - Press Ctrl+C to exit")
    error_count = 0
    max_errors = 3

    while True:
        try:
            # Check for error indicators (you can expand this)
            # For now, we'll just wait and respond to manual triggers
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            break
        except Exception as e:
            error_count += 1
            print(f"\n⚠️ Error detected ({error_count}/{max_errors}): {e}")

            if error_count >= max_errors:
                print("🔧 Auto-recovery triggered...")
                if auto_recover_500_error():
                    error_count = 0  # Reset counter after successful recovery
                else:
                    print("❌ Recovery failed. Manual intervention required.")
                    break

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Auto-recovery for 500 errors')
    parser.add_argument('--monitor', action='store_true',
                       help='Run in monitoring mode')
    parser.add_argument('--recover', action='store_true',
                       help='Run recovery immediately')

    args = parser.parse_args()

    if args.monitor:
        monitor_and_recover()
    else:
        auto_recover_500_error()