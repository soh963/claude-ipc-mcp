#!/usr/bin/env python3
"""
🗑️ Clear Project Messages
현재 프로젝트의 모든 메시지를 초기화합니다.
"""

import os
import sys
import sqlite3
import hashlib
import argparse
from pathlib import Path


def get_project_id(project_path=None):
    """Generate project ID from path"""
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)
    project_path = project_path.replace("\\", "/").lower()

    hash_obj = hashlib.sha256(project_path.encode())
    return f"proj_{hash_obj.hexdigest()[:8]}"


def get_db_path():
    """Get database path"""
    home = Path.home()
    db_dir = home / ".claude-ipc-data"
    return db_dir / "messages.db"


def clear_messages(project_id=None, all_messages=False):
    """Clear messages from database"""
    db_path = get_db_path()

    if not db_path.exists():
        print("❌ Database not found. No messages to clear.")
        return 0

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        if all_messages:
            # Clear ALL messages (dangerous!)
            cursor.execute("DELETE FROM messages")
            count = cursor.rowcount
            print(f"⚠️ Deleted ALL {count} messages from database!")

        elif project_id:
            # Clear messages for specific project
            # First, check how many messages exist
            cursor.execute("SELECT COUNT(*) FROM messages WHERE project_id = ?", (project_id,))
            total = cursor.fetchone()[0]

            if total == 0:
                print(f"ℹ️ No messages found for project: {project_id}")
                return 0

            # Delete messages
            cursor.execute("DELETE FROM messages WHERE project_id = ?", (project_id,))
            count = cursor.rowcount
            print(f"✅ Deleted {count} messages for project: {project_id}")

        else:
            print("❌ No project ID specified and --all flag not set")
            return 0

        conn.commit()
        conn.close()
        return count

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 0


def show_message_stats(project_id=None):
    """Show message statistics"""
    db_path = get_db_path()

    if not db_path.exists():
        print("❌ Database not found.")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        if project_id:
            # Stats for specific project
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN read_flag = 0 THEN 1 ELSE 0 END) as unread,
                    COUNT(DISTINCT from_id) as senders,
                    COUNT(DISTINCT to_id) as recipients
                FROM messages
                WHERE project_id = ?
            """,
                (project_id,),
            )
        else:
            # Stats for all projects
            cursor.execute(
                """
                SELECT
                    project_id,
                    COUNT(*) as total,
                    SUM(CASE WHEN read_flag = 0 THEN 1 ELSE 0 END) as unread
                FROM messages
                GROUP BY project_id
            """
            )

        results = cursor.fetchall()

        if project_id and results:
            total, unread, senders, recipients = results[0]
            print("\n📊 Message Statistics:")
            print(f"  • Project: {project_id}")
            print(f"  • Total messages: {total}")
            print(f"  • Unread: {unread}")
            print(f"  • Unique senders: {senders}")
            print(f"  • Unique recipients: {recipients}")
        elif results:
            print("\n📊 Messages by Project:")
            for proj_id, total, unread in results:
                print(f"  • {proj_id}: {total} messages ({unread} unread)")
        else:
            print("ℹ️ No messages found in database")

        conn.close()

    except Exception as e:
        print(f"❌ Error reading stats: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Clear IPC messages for current or specific project"
    )
    parser.add_argument(
        "--project-id", help="Specific project ID to clear (default: current project)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Clear ALL messages from ALL projects (dangerous!)"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show message statistics instead of clearing"
    )
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("🗑️ Project Message Cleaner")
    print("=" * 50 + "\n")

    # Determine project ID
    if args.project_id:
        project_id = args.project_id
    else:
        project_id = get_project_id()
        print(f"📁 Current project: {os.getcwd()}")
        print(f"🔒 Project ID: {project_id}")

    # Show stats if requested
    if args.stats:
        show_message_stats(project_id if not args.all else None)
        return

    # Confirmation
    if not args.confirm:
        print("\n⚠️ Warning: This will delete messages permanently!")

        if args.all:
            print("   You are about to delete ALL messages from ALL projects!")
            confirm = input("   Type 'DELETE ALL' to confirm: ")
            if confirm != "DELETE ALL":
                print("❌ Operation cancelled.")
                return
        else:
            print(f"   Project to clear: {project_id}")
            confirm = input("   Continue? (y/n): ")
            if confirm.lower() != "y":
                print("❌ Operation cancelled.")
                return

    # Clear messages
    print("\n🔄 Clearing messages...")
    count = clear_messages(project_id if not args.all else None, all_messages=args.all)

    if count > 0:
        print(f"\n✨ Successfully cleared {count} messages!")

        # Show remaining stats
        if not args.all:
            show_message_stats()
    else:
        print("\nℹ️ No messages were cleared.")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user.\n")
        sys.exit(0)
