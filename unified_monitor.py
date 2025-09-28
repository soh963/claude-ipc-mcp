#!/usr/bin/env python3
"""
🎯 Unified IPC Monitoring System
한 화면에서 모든 메시지를 효과적으로 확인할 수 있는 통합 모니터링
"""

import os
import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Back, Style
import threading

# Initialize colorama for Windows
init()

class UnifiedMonitor:
    def __init__(self):
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]
        self.colors = {
            "claude": Fore.CYAN,
            "gemini": Fore.GREEN,
            "codex": Fore.YELLOW,
            "lm": Fore.MAGENTA,
            "chatgpt": Fore.BLUE,
            "llama": Fore.RED
        }
        self.last_message_id = 0
        self.running = True

    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_header(self):
        """Draw header with system info"""
        self.clear_screen()
        print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}   📊 UNIFIED IPC MONITORING SYSTEM   {datetime.now().strftime('%H:%M:%S')}   {Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
        print()

    def draw_instance_status(self):
        """Draw instance status bar"""
        print(f"{Fore.CYAN}📡 Active Instances:{Style.RESET_ALL}")
        status_line = ""
        for instance in self.instances:
            color = self.colors.get(instance, Fore.WHITE)
            if self.is_instance_active(instance):
                status_line += f"{color}[✓ {instance}]{Style.RESET_ALL}  "
            else:
                status_line += f"{Fore.GRAY}[✗ {instance}]{Style.RESET_ALL}  "
        print(status_line)
        print(f"{Fore.GRAY}{'─'*80}{Style.RESET_ALL}")
        print()

    def is_instance_active(self, instance_id):
        """Check if instance has recent activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check for recent activity (last 5 minutes)
            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE (from_id = ? OR to_id = ?)
                AND timestamp > datetime('now', '-5 minutes')
            """, (instance_id, instance_id))

            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False

    def get_recent_messages(self, limit=20):
        """Get recent messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, from_id, to_id, content, timestamp, read_flag
                FROM messages
                WHERE id > ?
                ORDER BY id DESC
                LIMIT ?
            """, (self.last_message_id, limit))

            messages = cursor.fetchall()
            if messages:
                self.last_message_id = max(msg[0] for msg in messages)

            conn.close()
            return reversed(messages)  # Return in chronological order
        except Exception as e:
            print(f"{Fore.RED}Error reading messages: {e}{Style.RESET_ALL}")
            return []

    def format_message(self, msg):
        """Format message for display"""
        msg_id, from_id, to_id, content, timestamp, read_flag = msg

        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('T', ' ').replace('Z', ''))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp[:8] if len(timestamp) > 8 else timestamp

        # Get colors
        from_color = self.colors.get(from_id, Fore.WHITE)
        to_color = self.colors.get(to_id, Fore.WHITE)

        # Read status
        read_icon = "✓" if read_flag else "●"
        read_color = Fore.GRAY if read_flag else Fore.GREEN

        # Truncate long messages
        if len(content) > 60:
            content = content[:57] + "..."

        # Format the message line
        return (f"{Fore.GRAY}[{time_str}]{Style.RESET_ALL} "
                f"{read_color}{read_icon}{Style.RESET_ALL} "
                f"{from_color}{from_id:8}{Style.RESET_ALL} → "
                f"{to_color}{to_id:8}{Style.RESET_ALL}: "
                f"{content}")

    def draw_messages(self):
        """Draw message list"""
        print(f"{Fore.CYAN}📨 Recent Messages:{Style.RESET_ALL}")
        print(f"{Fore.GRAY}{'─'*80}{Style.RESET_ALL}")

        messages = self.get_recent_messages()

        if not messages:
            print(f"{Fore.GRAY}No recent messages{Style.RESET_ALL}")
        else:
            for msg in messages:
                print(self.format_message(msg))

        print(f"{Fore.GRAY}{'─'*80}{Style.RESET_ALL}")

    def draw_statistics(self):
        """Draw statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]

            # Unread messages
            cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
            unread = cursor.fetchone()[0]

            # Messages per instance
            stats = {}
            for instance in self.instances:
                cursor.execute("""
                    SELECT COUNT(*) FROM messages
                    WHERE from_id = ? OR to_id = ?
                """, (instance, instance))
                stats[instance] = cursor.fetchone()[0]

            conn.close()

            # Display statistics
            print(f"{Fore.CYAN}📊 Statistics:{Style.RESET_ALL}")
            print(f"  Total Messages: {Fore.WHITE}{total}{Style.RESET_ALL}  |  "
                  f"Unread: {Fore.GREEN}{unread}{Style.RESET_ALL}")

            print(f"\n  Message Count by Instance:")
            for instance in self.instances:
                color = self.colors.get(instance, Fore.WHITE)
                count = stats.get(instance, 0)
                bar_length = min(30, count // 2)
                bar = "█" * bar_length
                print(f"  {color}{instance:8}{Style.RESET_ALL}: {bar} {count}")

        except Exception as e:
            print(f"{Fore.RED}Error getting statistics: {e}{Style.RESET_ALL}")

    def draw_help(self):
        """Draw help section"""
        print(f"\n{Fore.CYAN}⌨️ Commands:{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}[Q]{Style.RESET_ALL} Quit  |  "
              f"{Fore.YELLOW}[R]{Style.RESET_ALL} Refresh  |  "
              f"{Fore.YELLOW}[C]{Style.RESET_ALL} Clear messages  |  "
              f"{Fore.YELLOW}[S]{Style.RESET_ALL} Send test")

    def refresh_display(self):
        """Refresh the entire display"""
        self.draw_header()
        self.draw_instance_status()
        self.draw_messages()
        self.draw_statistics()
        self.draw_help()

    def auto_refresh(self):
        """Auto refresh in background"""
        while self.running:
            time.sleep(2)
            if self.running:
                self.refresh_display()

    def send_test_message(self):
        """Send a test message"""
        try:
            import subprocess
            from_id = input("\nFrom instance: ")
            to_id = input("To instance: ")
            message = input("Message: ")

            tools_dir = Path(__file__).parent / "tools"

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
                elif key == 'c':
                    self.clear_old_messages()
                    self.refresh_display()
                elif key == 's':
                    self.send_test_message()
                    self.refresh_display()

        except KeyboardInterrupt:
            self.running = False

        print(f"\n{Fore.CYAN}Monitoring stopped. Goodbye!{Style.RESET_ALL}")

if __name__ == "__main__":
    monitor = UnifiedMonitor()
    monitor.run()