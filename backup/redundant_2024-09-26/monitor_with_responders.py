#!/usr/bin/env python3
"""
Enhanced IPC Monitor with Auto-Responder Status
자동 응답기 상태를 포함한 향상된 IPC 모니터
"""

import time
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import platform
import threading

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

class EnhancedIPCMonitor:
    """Enhanced monitor showing auto-responder status"""

    def __init__(self):
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.console = Console() if RICH_AVAILABLE else None
        self.running = True
        self.instances = ['claude', 'gemini', 'codex', 'lm']
        self.message_counts = {inst: 0 for inst in self.instances}
        self.last_activity = {inst: None for inst in self.instances}
        self.auto_responder_status = {inst: False for inst in self.instances}

    def check_auto_responder_status(self):
        """Check if auto-responders are running"""
        # Check if the unified auto-responder is running
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if 'start_all_auto_responders.py' in result.stdout:
                    # All responders running
                    for inst in self.instances:
                        self.auto_responder_status[inst] = True
                    return True
            else:
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if 'start_all_auto_responders.py' in result.stdout:
                    for inst in self.instances:
                        self.auto_responder_status[inst] = True
                    return True
        except:
            pass

        # Check individual responders
        for inst in self.instances:
            self.auto_responder_status[inst] = self.check_individual_responder(inst)

        return any(self.auto_responder_status.values())

    def check_individual_responder(self, instance_id):
        """Check if individual responder is running"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return f'auto_responder.py {instance_id}' in result.stdout
            else:
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return f'auto_responder.py {instance_id}' in result.stdout
        except:
            return False

    def get_instance_status(self):
        """Get current status of all instances"""
        statuses = {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get active instances (those that sent messages recently)
            cursor.execute("""
                SELECT DISTINCT from_id
                FROM messages
                WHERE timestamp > datetime('now', '-5 minutes')
            """)

            active_instances = [row[0] for row in cursor.fetchall()]

            # Get message counts for today
            cursor.execute("""
                SELECT from_id, COUNT(*) as sent_count
                FROM messages
                WHERE timestamp > datetime('now', 'start of day')
                GROUP BY from_id
            """)

            sent_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT to_id, COUNT(*) as received_count
                FROM messages
                WHERE timestamp > datetime('now', 'start of day')
                GROUP BY to_id
            """)

            received_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Get last activity
            cursor.execute("""
                SELECT from_id, MAX(timestamp) as last_sent
                FROM messages
                GROUP BY from_id
            """)

            last_sent = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            # Compile status for each instance
            for inst in self.instances:
                statuses[inst] = {
                    'active': inst in active_instances,
                    'sent_today': sent_counts.get(inst, 0),
                    'received_today': received_counts.get(inst, 0),
                    'last_activity': last_sent.get(inst, 'Never'),
                    'auto_responder': self.auto_responder_status.get(inst, False)
                }

        except Exception as e:
            print(f"Error getting status: {e}")
            for inst in self.instances:
                statuses[inst] = {
                    'active': False,
                    'sent_today': 0,
                    'received_today': 0,
                    'last_activity': 'Unknown',
                    'auto_responder': False
                }

        return statuses

    def get_recent_messages(self, limit=10):
        """Get recent messages"""
        messages = []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                messages.append({
                    'from': row[0],
                    'to': row[1],
                    'content': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
                    'time': row[3]
                })

            conn.close()

        except Exception as e:
            print(f"Error getting messages: {e}")

        return messages

    def create_status_display(self):
        """Create status display using Rich"""
        if not RICH_AVAILABLE:
            return self.create_simple_display()

        # Check auto-responder status
        self.check_auto_responder_status()

        # Create main layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", size=20),
            Layout(name="messages", size=15),
            Layout(name="footer", size=3)
        )

        # Header
        header = Panel(
            Text("🌐 IPC System Monitor with Auto-Responder Status",
                 style="bold cyan", justify="center"),
            style="bold blue"
        )
        layout["header"].update(header)

        # Instance Status Table
        table = Table(title="Instance Status", expand=True)
        table.add_column("Instance", style="cyan", width=10)
        table.add_column("Status", style="green", width=10)
        table.add_column("Auto-Resp", style="yellow", width=10)
        table.add_column("Sent", style="blue", width=8)
        table.add_column("Received", style="magenta", width=8)
        table.add_column("Last Activity", style="white", width=20)

        statuses = self.get_instance_status()

        for inst, status in statuses.items():
            status_icon = "🟢" if status['active'] else "🔴"
            responder_icon = "✅" if status['auto_responder'] else "❌"

            table.add_row(
                inst.upper(),
                f"{status_icon} {'Active' if status['active'] else 'Inactive'}",
                f"{responder_icon} {'ON' if status['auto_responder'] else 'OFF'}",
                str(status['sent_today']),
                str(status['received_today']),
                str(status['last_activity'])[:19]
            )

        layout["main"].update(Panel(table, title="System Status"))

        # Recent Messages
        msg_table = Table(title="Recent Messages", expand=True)
        msg_table.add_column("From", style="cyan", width=8)
        msg_table.add_column("To", style="magenta", width=8)
        msg_table.add_column("Message", style="white", width=40)
        msg_table.add_column("Time", style="yellow", width=19)

        messages = self.get_recent_messages()
        for msg in messages:
            msg_table.add_row(
                msg['from'],
                msg['to'],
                msg['content'],
                msg['time'][:19]
            )

        layout["messages"].update(Panel(msg_table))

        # Footer with auto-responder status
        responder_running = any(self.auto_responder_status.values())
        responder_status = "✅ Auto-Responders ACTIVE" if responder_running else "❌ Auto-Responders NOT RUNNING"

        footer_text = f"[bold green]{responder_status}[/] | Press Ctrl+C to exit | Updated: {datetime.now().strftime('%H:%M:%S')}"

        if not responder_running:
            footer_text += "\n[bold yellow]Run start_auto_responders.bat to enable bi-directional communication[/]"

        footer = Panel(
            Text(footer_text, justify="center"),
            style="bold"
        )
        layout["footer"].update(footer)

        return layout

    def create_simple_display(self):
        """Create simple text display without Rich"""
        self.check_auto_responder_status()

        os.system('cls' if os.name == 'nt' else 'clear')

        print("="*70)
        print(" "*20 + "IPC SYSTEM MONITOR")
        print("="*70)

        # Auto-responder status
        responder_running = any(self.auto_responder_status.values())
        if responder_running:
            print("\n✅ AUTO-RESPONDERS: ACTIVE")
        else:
            print("\n❌ AUTO-RESPONDERS: NOT RUNNING")
            print("   Run start_auto_responders.bat to enable bi-directional communication")

        print("\nINSTANCE STATUS:")
        print("-"*70)
        print(f"{'Instance':<10} {'Status':<10} {'AutoResp':<10} {'Sent':<8} {'Recv':<8} {'Last Activity':<20}")
        print("-"*70)

        statuses = self.get_instance_status()
        for inst, status in statuses.items():
            status_text = "Active" if status['active'] else "Inactive"
            responder_text = "ON" if status['auto_responder'] else "OFF"
            print(f"{inst:<10} {status_text:<10} {responder_text:<10} {status['sent_today']:<8} {status['received_today']:<8} {str(status['last_activity'])[:19]:<20}")

        print("\nRECENT MESSAGES:")
        print("-"*70)

        messages = self.get_recent_messages(5)
        for msg in messages:
            print(f"{msg['time'][:19]} | {msg['from']} → {msg['to']}: {msg['content']}")

        print("-"*70)
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return None

    def run(self):
        """Run the monitor"""
        print("Starting Enhanced IPC Monitor...")
        print("Checking auto-responder status...")

        if RICH_AVAILABLE:
            with Live(self.create_status_display(),
                     refresh_per_second=0.5,
                     console=self.console) as live:
                try:
                    while self.running:
                        time.sleep(2)
                        live.update(self.create_status_display())
                except KeyboardInterrupt:
                    self.running = False
                    print("\n\nMonitor stopped by user")
        else:
            try:
                while self.running:
                    self.create_simple_display()
                    time.sleep(3)
            except KeyboardInterrupt:
                self.running = False
                print("\n\nMonitor stopped by user")

    def start_auto_responders(self):
        """Start auto-responders if not running"""
        if not any(self.auto_responder_status.values()):
            print("\nStarting auto-responders...")
            try:
                if platform.system() == "Windows":
                    subprocess.Popen(['start_auto_responders.bat'], shell=True)
                else:
                    subprocess.Popen(['python3', 'start_all_auto_responders.py'])
                print("Auto-responders started!")
                time.sleep(3)
            except Exception as e:
                print(f"Failed to start auto-responders: {e}")


def main():
    """Main entry point"""
    monitor = EnhancedIPCMonitor()

    # Check if auto-responders are running
    monitor.check_auto_responder_status()

    if not any(monitor.auto_responder_status.values()):
        print("\n⚠️  Auto-responders are not running!")
        print("This means messages can be sent but not responded to.")
        response = input("\nStart auto-responders? (y/n): ").lower()

        if response == 'y':
            monitor.start_auto_responders()

    # Run monitor
    monitor.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")