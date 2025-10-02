#!/usr/bin/env python3
"""
Multi-CLI Integration Test
Simulates multiple AI CLIs (Claude, Gemini, Codex) communicating via the broker
"""

import json
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from broker.daemon import BrokerDaemon
from broker.service_manager import ServiceManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger(__name__)


class MockAICLI:
    """Mock AI CLI client for testing"""

    def __init__(self, name: str, broker_host: str = "127.0.0.1", broker_port: int = 9876):
        self.name = name
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.session_token: Optional[str] = None
        self.received_messages: List[Dict[str, Any]] = []
        self.running = False
        self.check_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(f"CLI-{name}")

    def register(self) -> bool:
        """Register with the broker"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            request = json.dumps({
                "action": "register",
                "instance_id": self.name
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()

            if response.get("status") == "ok":
                self.session_token = response.get("session_token")
                self.logger.info(f"✅ Registered successfully")
                return True
            else:
                self.logger.error(f"❌ Registration failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Registration error: {e}")
            return False

    def send_message(self, to_cli: str, content: str) -> bool:
        """Send a message to another CLI"""
        if not self.session_token:
            self.logger.error("Not registered")
            return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            request = json.dumps({
                "action": "send",
                "session_token": self.session_token,
                "from_id": self.name,
                "to_id": to_cli,
                "content": content
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()

            if response.get("status") == "ok":
                self.logger.info(f"📤 Sent to {to_cli}: {content[:50]}...")
                return True
            else:
                self.logger.error(f"Send failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            return False

    def check_messages(self) -> List[Dict[str, Any]]:
        """Check for new messages"""
        if not self.session_token:
            return []

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            request = json.dumps({
                "action": "check",
                "session_token": self.session_token,
                "instance_id": self.name
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(65536).decode())
            sock.close()

            messages = response.get("messages", [])
            if messages:
                for msg in messages:
                    self.logger.info(f"📥 From {msg['from_id']}: {msg['content'][:50]}...")
                self.received_messages.extend(messages)
            return messages
        except Exception:
            return []

    def start_message_checking(self, interval: float = 2.0):
        """Start periodic message checking in background"""
        self.running = True

        def check_loop():
            while self.running:
                self.check_messages()
                time.sleep(interval)

        self.check_thread = threading.Thread(target=check_loop, daemon=True)
        self.check_thread.start()
        self.logger.info("Started message checking")

    def stop(self):
        """Stop message checking"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        self.logger.info("Stopped")

    def broadcast(self, content: str) -> bool:
        """Send a broadcast message to all CLIs"""
        if not self.session_token:
            self.logger.error("Not registered")
            return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            request = json.dumps({
                "action": "broadcast",
                "session_token": self.session_token,
                "from_id": self.name,
                "content": content
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()

            if response.get("status") == "ok":
                self.logger.info(f"📢 Broadcast sent: {content[:50]}...")
                return True
            else:
                self.logger.error(f"Broadcast failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Broadcast error: {e}")
            return False


def simulate_multi_cli_conversation():
    """Simulate a conversation between multiple AI CLIs"""
    logger.info("=" * 80)
    logger.info("🚀 Multi-CLI Integration Test")
    logger.info("=" * 80)

    # Start broker using service manager
    logger.info("\n📡 Starting broker daemon...")
    manager = ServiceManager(port=49876)

    # Clean up any existing broker
    if manager.is_broker_running():
        manager.stop_broker(force=True)
        time.sleep(2)

    if not manager.start_broker():
        logger.error("Failed to start broker")
        return False

    time.sleep(1)

    # Create AI CLI instances
    logger.info("\n🤖 Creating AI CLI instances...")
    claude = MockAICLI("claude", broker_port=49876)
    gemini = MockAICLI("gemini", broker_port=49876)
    codex = MockAICLI("codex", broker_port=49876)

    try:
        # Register all CLIs
        logger.info("\n📝 Registering CLIs with broker...")
        assert claude.register(), "Claude registration failed"
        assert gemini.register(), "Gemini registration failed"
        assert codex.register(), "Codex registration failed"

        # Start message checking for all CLIs
        logger.info("\n👂 Starting message monitors...")
        claude.start_message_checking()
        gemini.start_message_checking()
        codex.start_message_checking()

        time.sleep(1)

        # Simulate conversation
        logger.info("\n💬 Starting multi-CLI conversation...")
        logger.info("-" * 40)

        # Claude starts a discussion
        claude.send_message("gemini", "Gemini, can you help me optimize this Python code?")
        time.sleep(1)

        # Gemini responds and asks Codex
        gemini.send_message("claude", "Sure Claude! Let me analyze it.")
        gemini.send_message("codex", "Codex, what's your take on Python optimization?")
        time.sleep(1)

        # Codex responds to both
        codex.send_message("gemini", "I suggest using list comprehensions and generators.")
        codex.send_message("claude", "Claude, have you considered async patterns?")
        time.sleep(1)

        # Claude broadcasts an update
        claude.broadcast("Team, I found the performance bottleneck!")
        time.sleep(2)

        # Verify message delivery
        logger.info("\n📊 Verification...")
        logger.info(f"Claude received {len(claude.received_messages)} messages")
        logger.info(f"Gemini received {len(gemini.received_messages)} messages")
        logger.info(f"Codex received {len(codex.received_messages)} messages")

        # Test state consistency
        logger.info("\n🔄 Testing state consistency...")

        # Get broker status
        status = manager.get_broker_status()
        assert status["running"], "Broker not running"
        assert len(status.get("instances", [])) >= 3, "Not all instances registered"
        logger.info(f"✅ Broker tracking {len(status['instances'])} instances")

        # Test broker restart resilience
        logger.info("\n🔄 Testing broker restart...")
        manager.restart_broker()
        time.sleep(2)

        # Re-register CLIs after restart
        assert claude.register(), "Claude re-registration failed"
        assert gemini.register(), "Gemini re-registration failed"
        assert codex.register(), "Codex re-registration failed"

        # Send message after restart
        claude.send_message("gemini", "Still working after restart?")
        time.sleep(1)

        # Check message received
        new_messages = gemini.check_messages()
        assert any("restart" in msg["content"] for msg in new_messages), "Message after restart not received"
        logger.info("✅ Messages work after broker restart")

        # Test concurrent operations
        logger.info("\n⚡ Testing concurrent operations...")
        threads = []

        def send_many(cli: MockAICLI, target: str, count: int):
            for i in range(count):
                cli.send_message(target, f"Concurrent message {i}")

        # Send many messages concurrently
        for _ in range(3):
            threads.append(threading.Thread(target=send_many, args=(claude, "gemini", 5)))
            threads.append(threading.Thread(target=send_many, args=(gemini, "codex", 5)))
            threads.append(threading.Thread(target=send_many, args=(codex, "claude", 5)))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        time.sleep(3)

        logger.info("✅ Concurrent message handling successful")

        # Final status
        logger.info("\n📈 Final Status:")
        final_status = manager.get_broker_status()
        logger.info(f"  Broker PID: {final_status.get('pid')}")
        logger.info(f"  Total instances: {len(final_status.get('instances', []))}")
        logger.info(f"  Messages queued: {final_status.get('total_queued', 0)}")

        # Health check
        healthy, message = manager.health_check()
        logger.info(f"  Health: {'✅' if healthy else '❌'} {message}")

        logger.info("\n✅ Multi-CLI integration test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

    finally:
        # Cleanup
        logger.info("\n🧹 Cleaning up...")
        claude.stop()
        gemini.stop()
        codex.stop()
        manager.stop_broker()
        logger.info("Cleanup complete")


def main():
    """Main entry point"""
    success = simulate_multi_cli_conversation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()