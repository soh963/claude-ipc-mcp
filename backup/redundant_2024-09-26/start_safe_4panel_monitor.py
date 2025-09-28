#!/usr/bin/env python
"""
Start 4 panel monitoring system without infinite loops
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting Safe 4-Panel Monitoring System")
    print("="*60)
    print("This system prevents infinite loops and duplicate messages")
    print("="*60 + "\n")

    # Define monitoring instances
    instances = ['claude', 'gemini', 'codex', 'lm']

    # Windows Terminal command for 4-panel split
    wt_command = [
        'wt',
        # Panel 1: Claude monitor (top-left)
        'new-tab', '--title', 'Claude Monitor',
        'python', 'tools/instance_monitor.py', 'claude',
        ';',
        # Panel 2: Gemini monitor (top-right)
        'split-pane', '-H', '--title', 'Gemini Monitor',
        'python', 'tools/instance_monitor.py', 'gemini',
        ';',
        # Panel 3: Codex monitor (bottom-left)
        'split-pane', '-V', '--title', 'Codex Monitor',
        'python', 'tools/instance_monitor.py', 'codex',
        ';',
        # Move to first pane and split vertically
        'focus-tab', '-t', '0',
        ';',
        'split-pane', '-V', '--title', 'LM Monitor',
        'python', 'tools/instance_monitor.py', 'lm'
    ]

    try:
        # Try Windows Terminal first
        subprocess.run(wt_command, shell=False)
        print("✅ Windows Terminal 4-panel monitoring started")
    except:
        # Fallback: Start individual monitors
        print("Windows Terminal not available, starting individual monitors...")

        for instance in instances:
            cmd = f'start cmd /k python tools/instance_monitor.py {instance}'
            os.system(cmd)
            print(f"✅ Started {instance} monitor")

    print("\n📊 Monitoring Features:")
    print("  • No duplicate messages")
    print("  • Auto-responder filtering")
    print("  • Message truncation (80 chars)")
    print("  • Incoming/outgoing separation")
    print("  • Real-time updates every 2 seconds")
    print("\nPress Ctrl+C in each window to stop monitoring")

if __name__ == "__main__":
    main()