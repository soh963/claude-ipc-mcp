#!/usr/bin/env python3
"""
Test Global IPC Connectivity
모든 AI CLI 인스턴스 간의 연결을 테스트합니다.
"""

import sys
import os
import time
import json
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

class GlobalConnectionTester:
    def __init__(self):
        self.ipc = IPCManager()
        self.test_results = {}
        self.test_instances = ["claude", "gemini", "codex", "cursor", "windsurf", "lm"]

    def print_header(self):
        """Print test header"""
        print("""
╔════════════════════════════════════════╗
║   🔍 Global IPC Connection Test        ║
║   Testing all AI CLI instances         ║
╚════════════════════════════════════════╝
        """)

    def test_broker_connection(self):
        """Test connection to broker server"""
        print("\n📡 Testing Broker Server Connection...")

        try:
            # Try to list instances
            result = self.ipc.list_instances()
            if result.get('status') == 'ok':
                print("  ✅ Broker server is running on port 9876")
                instances = result.get('instances', [])
                if instances:
                    print(f"  📊 Found {len(instances)} active instance(s)")
                    for inst in instances[:5]:  # Show first 5
                        print(f"     • {inst['id']}")
                return True
            else:
                print(f"  ❌ Broker error: {result.get('message')}")
                return False
        except Exception as e:
            print(f"  ❌ Cannot connect to broker: {e}")
            print("  💡 Try running: python src/claude_ipc_server.py")
            return False

    def test_instance_registration(self, instance_name):
        """Test registering an instance"""
        try:
            result = self.ipc.register(instance_name)
            if result.get('status') == 'ok':
                session_token = result.get('session_token', 'N/A')
                self.test_results[instance_name] = {
                    'registered': True,
                    'session_token': session_token[:10] + '...' if len(session_token) > 10 else session_token
                }
                return True
            else:
                self.test_results[instance_name] = {
                    'registered': False,
                    'error': result.get('message', 'Unknown error')
                }
                return False
        except Exception as e:
            self.test_results[instance_name] = {
                'registered': False,
                'error': str(e)
            }
            return False

    def test_message_send(self, from_instance, to_instance, message):
        """Test sending a message"""
        try:
            result = self.ipc.send(from_instance, to_instance, message)
            if result.get('status') == 'ok':
                return True
            return False
        except:
            return False

    def test_message_receive(self, instance_name):
        """Test receiving messages"""
        try:
            result = self.ipc.check(instance_name)
            if result.get('status') == 'ok':
                messages = result.get('messages', [])
                return len(messages)
            return 0
        except:
            return 0

    def run_individual_tests(self):
        """Run tests for each instance"""
        print("\n📌 Testing Individual Instances:")
        print("-" * 40)

        for instance in self.test_instances:
            print(f"\n🔧 Testing '{instance}':")

            # Registration test
            print(f"  1. Registration... ", end="")
            if self.test_instance_registration(instance):
                print("✅ Success")

                # Self-message test
                print(f"  2. Self-message... ", end="")
                test_msg = f"Test message from {instance} at {datetime.now().strftime('%H:%M:%S')}"
                if self.test_message_send(instance, instance, test_msg):
                    print("✅ Sent")

                    # Receive test
                    time.sleep(0.5)  # Small delay for message processing
                    print(f"  3. Receive... ", end="")
                    msg_count = self.test_message_receive(instance)
                    if msg_count > 0:
                        print(f"✅ {msg_count} message(s)")
                    else:
                        print("⚠️ No messages")
                else:
                    print("❌ Failed")
            else:
                error = self.test_results[instance].get('error', 'Unknown')
                print(f"❌ Failed - {error}")

    def run_cross_instance_test(self):
        """Test cross-instance communication"""
        print("\n🔄 Cross-Instance Communication Test:")
        print("-" * 40)

        # Find registered instances
        registered = [name for name, result in self.test_results.items()
                     if result.get('registered')]

        if len(registered) < 2:
            print("  ⚠️ Need at least 2 registered instances for cross-testing")
            return

        # Test between first two registered instances
        sender = registered[0]
        receiver = registered[1]

        print(f"\n  Testing: {sender} → {receiver}")

        # Send message
        test_msg = f"Cross-test from {sender} to {receiver}"
        print(f"  Sending... ", end="")
        if self.test_message_send(sender, receiver, test_msg):
            print("✅ Sent")

            time.sleep(0.5)
            # Check reception
            print(f"  Checking {receiver}... ", end="")
            msg_count = self.test_message_receive(receiver)
            if msg_count > 0:
                print(f"✅ Received {msg_count} message(s)")
            else:
                print("⚠️ No messages received")
        else:
            print("❌ Send failed")

        # Reverse test
        print(f"\n  Testing: {receiver} → {sender}")
        test_msg = f"Reply from {receiver} to {sender}"
        print(f"  Sending... ", end="")
        if self.test_message_send(receiver, sender, test_msg):
            print("✅ Sent")

            time.sleep(0.5)
            print(f"  Checking {sender}... ", end="")
            msg_count = self.test_message_receive(sender)
            if msg_count > 0:
                print(f"✅ Received {msg_count} message(s)")
            else:
                print("⚠️ No messages received")
        else:
            print("❌ Send failed")

    def run_broadcast_test(self):
        """Test broadcasting to all instances"""
        print("\n📢 Broadcast Test:")
        print("-" * 40)

        registered = [name for name, result in self.test_results.items()
                     if result.get('registered')]

        if not registered:
            print("  ⚠️ No registered instances for broadcast test")
            return

        broadcaster = registered[0]
        print(f"  Broadcasting from '{broadcaster}'... ", end="")

        try:
            result = self.ipc.broadcast(broadcaster, f"Broadcast test from {broadcaster}")
            if result.get('status') == 'ok':
                print("✅ Sent")
                print(f"  Message sent to {result.get('message', 'unknown number of')} instances")
            else:
                print(f"❌ Failed: {result.get('message')}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def test_database_persistence(self):
        """Test database persistence"""
        print("\n💾 Database Persistence Test:")
        print("-" * 40)

        db_path = os.path.expanduser("~/.claude-ipc-data/messages.db")
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024  # KB
            print(f"  ✅ Database exists: {db_path}")
            print(f"  📊 Size: {size:.2f} KB")

            # Try to read some stats
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM messages")
                total_messages = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM instances")
                total_instances = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]

                conn.close()

                print(f"  📨 Total messages: {total_messages}")
                print(f"  🤖 Total instances: {total_instances}")
                print(f"  🔑 Total sessions: {total_sessions}")
            except Exception as e:
                print(f"  ⚠️ Could not read database stats: {e}")
        else:
            print(f"  ❌ Database not found at {db_path}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        registered_count = sum(1 for r in self.test_results.values() if r.get('registered'))
        total_tested = len(self.test_results)

        print(f"\n✅ Registered: {registered_count}/{total_tested}")
        print(f"❌ Failed: {total_tested - registered_count}/{total_tested}")

        if registered_count > 0:
            print("\n🟢 Successfully registered instances:")
            for name, result in self.test_results.items():
                if result.get('registered'):
                    print(f"  • {name}")

        if registered_count < total_tested:
            print("\n🔴 Failed registrations:")
            for name, result in self.test_results.items():
                if not result.get('registered'):
                    error = result.get('error', 'Unknown error')
                    print(f"  • {name}: {error}")

        # Overall status
        print("\n" + "=" * 50)
        if registered_count == total_tested:
            print("🎉 ALL TESTS PASSED - System fully operational!")
        elif registered_count > 0:
            print("⚠️ PARTIAL SUCCESS - Some instances are working")
        else:
            print("❌ ALL TESTS FAILED - Check broker server")
        print("=" * 50)

    def run_all_tests(self):
        """Run all connectivity tests"""
        self.print_header()

        # Test broker first
        if not self.test_broker_connection():
            print("\n❌ Cannot proceed without broker connection")
            print("Please start the broker server first:")
            print("  python src/claude_ipc_server.py")
            return False

        # Run individual tests
        self.run_individual_tests()

        # Cross-instance tests
        self.run_cross_instance_test()

        # Broadcast test
        self.run_broadcast_test()

        # Database test
        self.test_database_persistence()

        # Summary
        self.print_summary()

        return True

def main():
    """Main entry point"""
    tester = GlobalConnectionTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()