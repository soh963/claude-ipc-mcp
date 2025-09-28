#!/usr/bin/env python3
"""
Global IPC Status Monitor
실시간으로 모든 AI CLI 인스턴스의 상태를 모니터링합니다.
"""

import sys
import os
import time
import json
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich library not available. Install with: pip install rich")

class GlobalStatusMonitor:
    def __init__(self):
        self.ipc = IPCManager()
        self.last_update = None
        self.message_stats = {}

        if RICH_AVAILABLE:
            self.console = Console()

    def get_instances_info(self):
        """Get information about all instances"""
        try:
            result = self.ipc.list_instances()
            if result.get('status') == 'ok':
                return result.get('instances', [])
            return []
        except Exception as e:
            return []

    def test_instance_connectivity(self, instance_name):
        """Test if instance can receive messages"""
        try:
            # Send a ping
            self.ipc.send("monitor", instance_name, "ping-test")
            # This is just a connectivity test
            return "🟢 Connected"
        except:
            return "🔴 Unreachable"

    def get_database_stats(self):
        """Get database statistics"""
        try:
            import sqlite3
            db_path = os.path.expanduser("~/.claude-ipc-data/messages.db")
            if not os.path.exists(db_path):
                return {"total_messages": 0, "unread_messages": 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]

            # Unread messages
            cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
            unread = cursor.fetchone()[0]

            # Messages per instance
            cursor.execute("""
                SELECT to_id, COUNT(*)
                FROM messages
                WHERE read_flag = 0
                GROUP BY to_id
            """)
            unread_per_instance = dict(cursor.fetchall())

            conn.close()

            return {
                "total_messages": total,
                "unread_messages": unread,
                "unread_per_instance": unread_per_instance
            }
        except Exception as e:
            return {"total_messages": 0, "unread_messages": 0, "error": str(e)}

    def format_simple_output(self):
        """Format output for terminals without Rich"""
        output = []
        output.append("=" * 60)
        output.append(f"IPC Global Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)

        # Get instances
        instances = self.get_instances_info()
        if instances:
            output.append(f"\n📡 Active Instances ({len(instances)}):")
            for inst in instances:
                last_seen = inst.get('last_seen', 'Never')
                output.append(f"  • {inst['id']}: Last seen {last_seen}")
        else:
            output.append("\n❌ No active instances found")

        # Database stats
        stats = self.get_database_stats()
        output.append(f"\n📊 Database Statistics:")
        output.append(f"  • Total messages: {stats['total_messages']}")
        output.append(f"  • Unread messages: {stats['unread_messages']}")

        if stats.get('unread_per_instance'):
            output.append("\n📬 Unread messages by instance:")
            for inst, count in stats['unread_per_instance'].items():
                output.append(f"  • {inst}: {count} messages")

        output.append("=" * 60)
        return "\n".join(output)

    def get_status_table(self):
        """Create Rich status table"""
        if not RICH_AVAILABLE:
            return self.format_simple_output()

        # Main table
        table = Table(title=f"🌐 IPC Global Status - {datetime.now().strftime('%H:%M:%S')}")

        table.add_column("Instance", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Last Seen", style="yellow")
        table.add_column("Unread", style="magenta")
        table.add_column("Connectivity", style="blue")

        # Get data
        instances = self.get_instances_info()
        db_stats = self.get_database_stats()
        unread_per_instance = db_stats.get('unread_per_instance', {})

        # Add rows
        if instances:
            for inst in instances:
                instance_id = inst['id']
                last_seen = inst.get('last_seen', 'Never')

                # Calculate time since last seen
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen)
                    time_diff = (datetime.now() - last_seen_dt).total_seconds()
                    if time_diff < 60:
                        status = "🟢 Active"
                    elif time_diff < 300:
                        status = "🟡 Idle"
                    else:
                        status = "🔴 Inactive"
                except:
                    status = "⚫ Unknown"

                # Format last seen
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen)
                    last_seen_str = last_seen_dt.strftime("%H:%M:%S")
                except:
                    last_seen_str = last_seen

                unread = str(unread_per_instance.get(instance_id, 0))
                connectivity = self.test_instance_connectivity(instance_id)

                table.add_row(
                    instance_id,
                    status,
                    last_seen_str,
                    unread,
                    connectivity
                )
        else:
            table.add_row("No instances", "—", "—", "—", "—")

        # Create layout with additional info
        layout = Layout()
        layout.split_column(
            Layout(Panel(table), name="main"),
            Layout(Panel(
                f"📊 Total Messages: {db_stats['total_messages']} | "
                f"📬 Total Unread: {db_stats['unread_messages']} | "
                f"🔄 Last Update: {datetime.now().strftime('%H:%M:%S')}"
            ), name="stats", size=3)
        )

        return layout

    def monitor(self, refresh_rate=1):
        """Start monitoring with live updates"""
        if RICH_AVAILABLE:
            print("🔍 Starting Global IPC Monitor (Press Ctrl+C to stop)")
            try:
                with Live(self.get_status_table(), refresh_per_second=1/refresh_rate, screen=True) as live:
                    while True:
                        time.sleep(refresh_rate)
                        live.update(self.get_status_table())
            except KeyboardInterrupt:
                print("\n👋 Monitor stopped")
        else:
            # Simple monitoring without Rich
            print("🔍 Starting Global IPC Monitor (Press Ctrl+C to stop)")
            try:
                while True:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(self.format_simple_output())
                    time.sleep(refresh_rate)
            except KeyboardInterrupt:
                print("\n👋 Monitor stopped")

    def show_once(self):
        """Show status once and exit"""
        if RICH_AVAILABLE:
            self.console.print(self.get_status_table())
        else:
            print(self.format_simple_output())

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Global IPC Status Monitor')
    parser.add_argument('--once', action='store_true', help='Show status once and exit')
    parser.add_argument('--refresh', type=float, default=1.0, help='Refresh rate in seconds (default: 1.0)')

    args = parser.parse_args()

    monitor = GlobalStatusMonitor()

    if args.once:
        monitor.show_once()
    else:
        monitor.monitor(refresh_rate=args.refresh)

if __name__ == "__main__":
    main()