#!/usr/bin/env python3
"""
IPC Auto-Check Manager
Manages auto-check settings for IPC message processing
"""
import json
import os
import sys
import time

# Create secure directory if needed
os.makedirs("/tmp/claude-ipc-mcp", exist_ok=True)

CONFIG_FILE = "/tmp/claude-ipc-mcp/auto_check_config.json"

def start_auto_check(interval_minutes=5):
    """Enable auto-checking with specified interval"""
    config = {
        "enabled": True,
        "interval_minutes": interval_minutes,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_check": None  # Will trigger immediate check
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Auto-checking enabled! Checking every {interval_minutes} minutes.")
    print(f"To stop: say 'stop auto checking'")
    
def stop_auto_check():
    """Disable auto-checking"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        config["enabled"] = False
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print("⏹️ Auto-checking disabled. Back to manual mode.")
    else:
        print("Auto-checking was not active.")
        
def get_status():
    """Get current auto-check status"""
    if not os.path.exists(CONFIG_FILE):
        print("Auto-checking is not active.")
        return
        
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    if not config.get("enabled", False):
        print("Auto-checking is disabled.")
        return
    
    interval = config.get("interval_minutes", 5)
    last_check = config.get("last_check")
    
    print(f"✅ Auto-checking is ACTIVE")
    print(f"Interval: Every {interval} minutes")
    
    if last_check:
        from datetime import datetime
        last_dt = datetime.fromisoformat(last_check)
        elapsed = (datetime.now() - last_dt).total_seconds() / 60
        print(f"Last check: {int(elapsed)} minutes ago")
        next_check = interval - int(elapsed)
        if next_check > 0:
            print(f"Next check: in {next_check} minutes")
        else:
            print(f"Next check: any moment now!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ipc_auto_check_manager.py [start|stop|status] [interval]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        # Validate interval
        if interval < 1:
            print("Error: Interval must be at least 1 minute")
            sys.exit(1)
        if interval > 60:
            print("Error: Interval must be 60 minutes or less")
            sys.exit(1)
        start_auto_check(interval)
    elif command == "stop":
        stop_auto_check()
    elif command == "status":
        get_status()
    else:
        print(f"Unknown command: {command}")