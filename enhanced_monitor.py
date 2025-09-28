#!/usr/bin/env python3
"""
🎯 Enhanced IPC Monitoring System with Real-Time Status
실시간 상태 표시를 포함한 향상된 IPC 모니터링 시스템
"""

import os
import sys
import time
import sqlite3
import socket
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from colorama import init, Fore, Back, Style
import subprocess

# Initialize colorama for Windows
init()

class EnhancedMonitor:
    def __init__(self):
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        # Start with default instances, but will be updated dynamically
        self.default_instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]
        self.instances = self.default_instances.copy()
        self.colors = {
            "claude": Fore.CYAN,
            "gemini": Fore.GREEN,
            "codex": Fore.YELLOW,
            "lm": Fore.MAGENTA,
            "chatgpt": Fore.BLUE,
            "llama": Fore.RED
        }
        # Color palette for new instances
        self.color_palette = [Fore.CYAN, Fore.GREEN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE, Fore.RED, Fore.WHITE]
        self.next_color_index = 0
        self.instance_status = {}
        self.last_activity = {}
        self.message_count = {}
        self.auto_responder_status = {}
        self.running = True

        # Initialize status
        for instance in self.instances:
            self.instance_status[instance] = "offline"
            self.last_activity[instance] = None
            self.message_count[instance] = {"sent": 0, "received": 0}
            self.auto_responder_status[instance] = False

    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def check_broker_status(self):
        """Check if broker is running"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", 9876))
            s.close()
            return True
        except:
            return False

    def check_auto_responder(self, instance):
        """Check if auto-responder is running for an instance"""
        try:
            # Windows specific check
            if os.name == 'nt':
                result = subprocess.run(
                    f'tasklist /FI "WINDOWTITLE eq Auto-Responder: {instance}*" 2>nul',
                    shell=True, capture_output=True, text=True
                )
                return "python.exe" in result.stdout
            else:
                # Unix check
                result = subprocess.run(
                    f"ps aux | grep 'simple_auto_responder.py {instance}' | grep -v grep",
                    shell=True, capture_output=True, text=True
                )
                return bool(result.stdout.strip())
        except:
            return False

    def discover_instances(self):
        """Discover all instances from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all unique instances from sessions and messages
            cursor.execute("""
                SELECT DISTINCT instance_id FROM (
                    SELECT instance_id FROM sessions WHERE expires_at > datetime('now')
                    UNION
                    SELECT DISTINCT from_id as instance_id FROM messages
                    UNION
                    SELECT DISTINCT to_id as instance_id FROM messages
                )
            """)

            discovered = set()
            for (instance_id,) in cursor.fetchall():
                if instance_id:  # Ignore null/empty
                    discovered.add(instance_id)

            # Add new instances to the tracking list
            for instance_id in discovered:
                if instance_id not in self.instances:
                    self.instances.append(instance_id)
                    # Assign a color to new instance
                    if instance_id not in self.colors:
                        self.colors[instance_id] = self.color_palette[self.next_color_index % len(self.color_palette)]
                        self.next_color_index += 1
                    # Initialize tracking for new instance
                    if instance_id not in self.instance_status:
                        self.instance_status[instance_id] = "offline"
                    if instance_id not in self.message_count:
                        self.message_count[instance_id] = {"sent": 0, "received": 0}
                    if instance_id not in self.auto_responder_status:
                        self.auto_responder_status[instance_id] = False

            conn.close()
        except Exception as e:
            print(f"Error discovering instances: {e}")

    def update_instance_status(self):
        """Update status for all instances"""
        # First discover any new instances
        self.discover_instances()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get registered instances from sessions table
            cursor.execute("""
                SELECT instance_id, created_at
                FROM sessions
                WHERE expires_at > datetime('now')
            """)

            registered = {}
            for instance_id, created_at in cursor.fetchall():
                registered[instance_id] = created_at

            # Update status for each instance
            for instance in self.instances:
                # Check registration status
                if instance in registered:
                    last = registered[instance]
                    if last:
                        try:
                            last_time = datetime.fromisoformat(last.replace('T', ' ').replace('Z', ''))
                            time_diff = datetime.now() - last_time

                            if time_diff < timedelta(minutes=1):
                                self.instance_status[instance] = "active"
                            else:
                                # Always show as idle if registered (not offline)
                                self.instance_status[instance] = "idle"
                        except:
                            self.instance_status[instance] = "idle"
                    else:
                        self.instance_status[instance] = "idle"
                else:
                    self.instance_status[instance] = "offline"

                # Check auto-responder status
                self.auto_responder_status[instance] = self.check_auto_responder(instance)

                # Get message counts
                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM messages WHERE from_id = ?) as sent,
                        (SELECT COUNT(*) FROM messages WHERE to_id = ?) as received
                """, (instance, instance))

                result = cursor.fetchone()
                if result:
                    self.message_count[instance]["sent"] = result[0]
                    self.message_count[instance]["received"] = result[1]

            conn.close()
        except Exception as e:
            print(f"Error updating status: {e}")

    def get_recent_messages(self, limit=10):
        """Get recent messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT from_id, to_id, content, timestamp, read_flag
                FROM messages
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

            messages = cursor.fetchall()
            conn.close()
            return reversed(messages)  # Return in chronological order
        except:
            return []

    def draw_header(self):
        """Draw header with system status"""
        self.clear_screen()
        print(f"{Back.BLUE}{Fore.WHITE}{'='*100}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}   📊 ENHANCED IPC MONITORING SYSTEM   {datetime.now().strftime('%H:%M:%S')}   {Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'='*100}{Style.RESET_ALL}")

        # Broker status
        broker_status = self.check_broker_status()
        if broker_status:
            print(f"  🖥️ Broker: {Fore.GREEN}ONLINE{Style.RESET_ALL} (port 9876)")
        else:
            print(f"  🖥️ Broker: {Fore.RED}OFFLINE{Style.RESET_ALL}")
        print()

    def draw_instance_panel(self):
        """Draw instance status panel with enhanced information"""
        print(f"{Fore.CYAN}📡 INSTANCE STATUS:{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")

        # Headers
        print(f"  {'Instance':<10} {'Status':<12} {'Auto-Resp':<12} {'Messages':<20} {'Activity':<30}")
        print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*20} {'-'*30}")

        for instance in self.instances:
            color = self.colors.get(instance, Fore.WHITE)

            # Status indicator
            status = self.instance_status[instance]
            if status == "active":
                status_icon = f"{Fore.GREEN}● ACTIVE{Style.RESET_ALL}"
            elif status == "idle":
                status_icon = f"{Fore.YELLOW}● IDLE{Style.RESET_ALL}"
            else:
                status_icon = f"{Fore.RED}○ OFFLINE{Style.RESET_ALL}"

            # Auto-responder status
            if self.auto_responder_status[instance]:
                auto_icon = f"{Fore.GREEN}✓ RUNNING{Style.RESET_ALL}"
            else:
                auto_icon = f"{Fore.RED}✗ STOPPED{Style.RESET_ALL}"

            # Message counts
            sent = self.message_count[instance]["sent"]
            received = self.message_count[instance]["received"]
            msg_info = f"↑{sent} ↓{received}"

            # Last activity
            if self.last_activity.get(instance):
                activity = self.last_activity[instance]
            else:
                activity = "No recent activity"

            print(f"  {color}{instance:<10}{Style.RESET_ALL} {status_icon:<21} {auto_icon:<21} "
                  f"{msg_info:<20} {activity:<30}")

        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")
        print()

    def draw_message_flow(self):
        """Draw real-time message flow"""
        print(f"{Fore.CYAN}💬 RECENT MESSAGE FLOW:{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")

        messages = self.get_recent_messages()

        if not messages:
            print(f"  {Fore.LIGHTBLACK_EX}No recent messages{Style.RESET_ALL}")
        else:
            for msg in messages:
                from_id, to_id, content, timestamp, read_flag = msg

                # Parse timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace('T', ' ').replace('Z', ''))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8] if len(timestamp) > 8 else timestamp

                # Colors
                from_color = self.colors.get(from_id, Fore.WHITE)
                to_color = self.colors.get(to_id, Fore.WHITE)

                # Read status
                if read_flag:
                    read_icon = f"{Fore.LIGHTBLACK_EX}✓{Style.RESET_ALL}"
                else:
                    read_icon = f"{Fore.GREEN}●{Style.RESET_ALL}"

                # Truncate long messages
                if len(content) > 50:
                    content = content[:47] + "..."

                # Format message
                print(f"  {Fore.LIGHTBLACK_EX}[{time_str}]{Style.RESET_ALL} {read_icon} "
                      f"{from_color}{from_id:8}{Style.RESET_ALL} → "
                      f"{to_color}{to_id:8}{Style.RESET_ALL}: {content}")

                # Update last activity
                self.last_activity[from_id] = f"Sent to {to_id} at {time_str}"
                self.last_activity[to_id] = f"Received from {from_id} at {time_str}"

        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")
        print()

    def draw_statistics(self):
        """Draw system statistics"""
        print(f"{Fore.CYAN}📊 SYSTEM STATISTICS:{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]

            # Unread messages
            cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
            unread = cursor.fetchone()[0]

            # Registered instances (not offline)
            cursor.execute("""
                SELECT COUNT(DISTINCT instance_id)
                FROM sessions
                WHERE expires_at > datetime('now')
            """)
            active = cursor.fetchone()[0]

            conn.close()

            print(f"  Total Messages: {Fore.WHITE}{total}{Style.RESET_ALL} | "
                  f"Unread: {Fore.GREEN}{unread}{Style.RESET_ALL} | "
                  f"Registered Instances: {Fore.CYAN}{active}{Style.RESET_ALL}")

            # Message distribution bar chart
            print(f"\n  Message Distribution:")
            max_msgs = max([self.message_count[i]["sent"] + self.message_count[i]["received"]
                           for i in self.instances], default=1)

            for instance in self.instances:
                color = self.colors.get(instance, Fore.WHITE)
                total_msgs = self.message_count[instance]["sent"] + self.message_count[instance]["received"]
                bar_length = int((total_msgs / max_msgs) * 30) if max_msgs > 0 else 0
                bar = "█" * bar_length
                print(f"  {color}{instance:8}{Style.RESET_ALL}: {bar} {total_msgs}")

        except Exception as e:
            print(f"  {Fore.RED}Error getting statistics: {e}{Style.RESET_ALL}")

        print(f"{Fore.LIGHTBLACK_EX}{'─'*100}{Style.RESET_ALL}")

    def draw_help(self):
        """Draw help section"""
        print(f"\n{Fore.CYAN}⌨️ COMMANDS:{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}[Q]{Style.RESET_ALL} Quit | "
              f"{Fore.YELLOW}[R]{Style.RESET_ALL} Refresh | "
              f"{Fore.YELLOW}[S]{Style.RESET_ALL} Send test | "
              f"{Fore.YELLOW}[A]{Style.RESET_ALL} Start all auto-responders | "
              f"{Fore.YELLOW}[C]{Style.RESET_ALL} Clear old messages")

    def refresh_display(self):
        """Refresh the entire display"""
        self.update_instance_status()
        self.draw_header()
        self.draw_instance_panel()
        self.draw_message_flow()
        self.draw_statistics()
        self.draw_help()

    def auto_refresh(self):
        """Auto refresh in background"""
        while self.running:
            time.sleep(2)
            if self.running:
                self.refresh_display()

    def start_all_auto_responders(self):
        """Start auto-responders for all instances except claude"""
        print(f"\n{Fore.CYAN}Starting auto-responders...{Style.RESET_ALL}")

        responder_script = Path(__file__).parent / "tools" / "simple_auto_responder.py"
        if not responder_script.exists():
            print(f"{Fore.RED}Auto-responder script not found{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
            return

        instances_to_start = ["gemini", "codex", "lm", "chatgpt", "llama"]

        for instance in instances_to_start:
            if not self.auto_responder_status[instance]:
                try:
                    if os.name == 'nt':
                        cmd = f'start /min "Auto-Responder: {instance}" {sys.executable} {responder_script} {instance}'
                        subprocess.Popen(cmd, shell=True)
                    else:
                        subprocess.Popen([sys.executable, str(responder_script), instance],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Started auto-responder for {instance}")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  {Fore.RED}✗{Style.RESET_ALL} Failed to start {instance}: {e}")
            else:
                print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL} Auto-responder for {instance} already running")

        input("\nPress Enter to continue...")

    def send_test_message(self):
        """Send a test message"""
        try:
            tools_dir = Path(__file__).parent / "tools"

            from_id = input("\nFrom instance: ")
            to_id = input("To instance: ")
            message = input("Message: ")

            # Register sender
            subprocess.run([sys.executable, tools_dir / "ipc_register.py", from_id],
                         capture_output=True)

            # Send message
            result = subprocess.run(
                [sys.executable, tools_dir / "ipc_send.py", to_id, message],
                capture_output=True, text=True
            )

            if "Sent to" in result.stdout:
                print(f"{Fore.GREEN}✓ Message sent successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Failed to send message{Style.RESET_ALL}")

            input("\nPress Enter to continue...")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            input("\nPress Enter to continue...")

    def clear_old_messages(self):
        """Clear old messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete messages older than 1 hour
            cursor.execute("""
                DELETE FROM messages
                WHERE timestamp < datetime('now', '-1 hour')
            """)

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            print(f"{Fore.GREEN}✓ Cleared {deleted} old messages{Style.RESET_ALL}")
            input("\nPress Enter to continue...")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            input("\nPress Enter to continue...")

    def run(self):
        """Main run loop"""
        # Start auto-refresh thread
        refresh_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        refresh_thread.start()

        # Initial display
        self.refresh_display()

        # Handle user input
        try:
            while self.running:
                key = input().lower()

                if key == 'q':
                    self.running = False
                    break
                elif key == 'r':
                    self.refresh_display()
                elif key == 's':
                    self.send_test_message()
                    self.refresh_display()
                elif key == 'a':
                    self.start_all_auto_responders()
                    self.refresh_display()
                elif key == 'c':
                    self.clear_old_messages()
                    self.refresh_display()

        except KeyboardInterrupt:
            self.running = False

        print(f"\n{Fore.CYAN}Monitoring stopped. Goodbye!{Style.RESET_ALL}")

if __name__ == "__main__":
    monitor = EnhancedMonitor()
    monitor.run()