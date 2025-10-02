#!/usr/bin/env python3
"""
Comprehensive test suite for the standalone broker daemon
Tests multi-CLI support, state consistency, and resilience
"""

import json
import os
import pytest
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from broker.daemon import BrokerDaemon, RateLimiter
from broker.service_manager import ServiceManager


class TestBrokerDaemon:
    """Test suite for BrokerDaemon"""

    @pytest.fixture
    def broker(self):
        """Create a test broker instance"""
        # Use a different port for testing to avoid conflicts
        broker = BrokerDaemon(port=19876)
        yield broker
        # Cleanup
        broker.stop()

    @pytest.fixture
    def running_broker(self, broker):
        """Create and start a test broker"""
        broker.start(background=True)
        # Wait for broker to be ready
        time.sleep(0.5)
        yield broker
        broker.stop()

    def test_broker_startup_shutdown(self, broker):
        """Test broker can start and stop cleanly"""
        assert not broker.running

        # Start broker
        assert broker.start(background=True)
        assert broker.running

        # Wait a moment
        time.sleep(0.5)

        # Stop broker
        broker.stop()
        assert not broker.running

    def test_broker_prevents_duplicate(self):
        """Test that only one broker can run on the same port"""
        broker1 = BrokerDaemon(port=29876)
        broker2 = BrokerDaemon(port=29876)

        try:
            # Start first broker
            assert broker1.start(background=True)
            time.sleep(0.5)

            # Second broker should fail to start
            assert not broker2.start(background=True)

        finally:
            broker1.stop()
            broker2.stop()

    def test_multi_cli_registration(self, running_broker):
        """Test multiple CLIs can register simultaneously"""
        clients = []
        results = []

        def register_client(instance_id: str):
            """Register a client and store result"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(("127.0.0.1", 19876))

                request = json.dumps({
                    "action": "register",
                    "instance_id": instance_id
                })
                sock.send(request.encode())

                response = sock.recv(4096).decode()
                sock.close()

                result = json.loads(response)
                results.append((instance_id, result))
            except Exception as e:
                results.append((instance_id, {"error": str(e)}))

        # Register multiple clients in parallel
        threads = []
        for cli in ["claude", "gemini", "codex", "chatgpt", "llama"]:
            thread = threading.Thread(target=register_client, args=(cli,))
            threads.append(thread)
            thread.start()

        # Wait for all registrations
        for thread in threads:
            thread.join(timeout=5)

        # Check results
        assert len(results) == 5
        for instance_id, result in results:
            assert result.get("status") == "ok", f"Failed for {instance_id}: {result}"
            assert "session_token" in result
            assert result["session_token"] is not None

    def test_message_routing_between_clis(self, running_broker):
        """Test messages can be sent between different CLIs"""
        # Register sender (Claude)
        claude_token = self._register_instance(running_broker, "claude")
        assert claude_token is not None

        # Register receiver (Gemini)
        gemini_token = self._register_instance(running_broker, "gemini")
        assert gemini_token is not None

        # Send message from Claude to Gemini
        send_result = self._send_message(
            running_broker,
            claude_token,
            "claude",
            "gemini",
            "Hello from Claude!"
        )
        assert send_result.get("status") == "ok"

        # Check messages for Gemini
        messages = self._check_messages(running_broker, gemini_token, "gemini")
        assert len(messages) == 1
        assert messages[0]["from_id"] == "claude"
        assert messages[0]["to_id"] == "gemini"
        assert messages[0]["content"] == "Hello from Claude!"

    def test_broadcast_to_all_clis(self, running_broker):
        """Test broadcast functionality to all registered CLIs"""
        # Register multiple CLIs
        tokens = {}
        for cli in ["claude", "gemini", "codex"]:
            tokens[cli] = self._register_instance(running_broker, cli)

        # Send broadcast from Claude
        broadcast_result = self._broadcast_message(
            running_broker,
            tokens["claude"],
            "claude",
            "System maintenance in 5 minutes"
        )
        assert broadcast_result.get("status") == "ok"
        assert set(broadcast_result.get("sent_to", [])) == {"gemini", "codex"}

        # Check each recipient received the broadcast
        for cli in ["gemini", "codex"]:
            messages = self._check_messages(running_broker, tokens[cli], cli)
            assert len(messages) == 1
            assert "[BROADCAST]" in messages[0]["content"]

    def test_state_persistence(self, broker):
        """Test broker persists state across restarts"""
        # Start broker
        broker.start(background=True)
        time.sleep(0.5)

        # Register instances
        claude_token = self._register_instance(broker, "claude")
        gemini_token = self._register_instance(broker, "gemini")

        # Send messages
        self._send_message(broker, claude_token, "claude", "gemini", "Message 1")
        self._send_message(broker, claude_token, "claude", "gemini", "Message 2")

        # Stop broker
        broker.stop()
        time.sleep(1)

        # Restart broker
        broker.start(background=True)
        time.sleep(0.5)

        # Re-register Gemini (would need new session in real scenario)
        new_gemini_token = self._register_instance(broker, "gemini")

        # Check messages are still there
        messages = self._check_messages(broker, new_gemini_token, "gemini")
        assert len(messages) >= 2  # May have persisted messages

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        limiter = RateLimiter(max_requests=5, window_seconds=1)

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_instance")

        # 6th request should be denied
        assert not limiter.is_allowed("test_instance")

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.is_allowed("test_instance")

    def test_session_validation(self, running_broker):
        """Test session token validation"""
        # Register instance
        token = self._register_instance(running_broker, "test")

        # Try with invalid token
        invalid_result = self._send_message(
            running_broker,
            "invalid_token",
            "test",
            "other",
            "Should fail"
        )
        assert invalid_result.get("error") == "Invalid session"

        # Try with valid token but wrong instance
        wrong_result = self._send_message(
            running_broker,
            token,
            "wrong_instance",
            "other",
            "Should fail"
        )
        assert wrong_result.get("error") == "Session mismatch"

    def test_instance_rename(self, running_broker):
        """Test instance rename functionality"""
        # Register instance
        token = self._register_instance(running_broker, "old_name")

        # Rename instance
        rename_result = self._rename_instance(
            running_broker,
            token,
            "old_name",
            "new_name"
        )
        assert rename_result.get("status") == "ok"

        # Register another instance and send to new name
        sender_token = self._register_instance(running_broker, "sender")
        send_result = self._send_message(
            running_broker,
            sender_token,
            "sender",
            "new_name",
            "Message to renamed instance"
        )
        assert send_result.get("status") == "ok"

        # Check with new name
        messages = self._check_messages(running_broker, token, "new_name")
        assert len(messages) == 1
        assert messages[0]["content"] == "Message to renamed instance"

    def test_large_message_handling(self, running_broker):
        """Test handling of large messages"""
        # Register instances
        sender_token = self._register_instance(running_broker, "sender")
        receiver_token = self._register_instance(running_broker, "receiver")

        # Create large message (>10KB)
        large_content = "X" * 15000

        # Send large message
        send_result = self._send_message(
            running_broker,
            sender_token,
            "sender",
            "receiver",
            large_content
        )
        assert send_result.get("status") == "ok"

        # Retrieve large message
        messages = self._check_messages(running_broker, receiver_token, "receiver")
        assert len(messages) == 1
        assert messages[0]["content"] == large_content

    # Helper methods

    def _register_instance(self, broker: BrokerDaemon, instance_id: str) -> Optional[str]:
        """Register an instance and return session token"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", broker.port))

            request = json.dumps({
                "action": "register",
                "instance_id": instance_id
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()

            if response.get("status") == "ok":
                return response.get("session_token")
            return None
        except Exception:
            return None

    def _send_message(self, broker: BrokerDaemon, session_token: str,
                      from_id: str, to_id: str, content: str) -> Dict[str, Any]:
        """Send a message"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", broker.port))

            request = json.dumps({
                "action": "send",
                "session_token": session_token,
                "from_id": from_id,
                "to_id": to_id,
                "content": content
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()
            return response
        except Exception as e:
            return {"error": str(e)}

    def _check_messages(self, broker: BrokerDaemon, session_token: str,
                       instance_id: str) -> list:
        """Check messages for an instance"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", broker.port))

            request = json.dumps({
                "action": "check",
                "session_token": session_token,
                "instance_id": instance_id
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(65536).decode())
            sock.close()
            return response.get("messages", [])
        except Exception:
            return []

    def _broadcast_message(self, broker: BrokerDaemon, session_token: str,
                          from_id: str, content: str) -> Dict[str, Any]:
        """Send a broadcast message"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", broker.port))

            request = json.dumps({
                "action": "broadcast",
                "session_token": session_token,
                "from_id": from_id,
                "content": content
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()
            return response
        except Exception as e:
            return {"error": str(e)}

    def _rename_instance(self, broker: BrokerDaemon, session_token: str,
                        old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename an instance"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", broker.port))

            request = json.dumps({
                "action": "rename",
                "session_token": session_token,
                "old_name": old_name,
                "new_name": new_name
            })
            sock.send(request.encode())

            response = json.loads(sock.recv(4096).decode())
            sock.close()
            return response
        except Exception as e:
            return {"error": str(e)}


class TestServiceManager:
    """Test suite for ServiceManager"""

    @pytest.fixture
    def manager(self):
        """Create a test service manager"""
        # Use a different port for testing
        manager = ServiceManager(port=39876)
        yield manager
        # Cleanup
        manager.stop_broker(force=True)

    def test_service_manager_start_stop(self, manager):
        """Test service manager can start and stop broker"""
        # Initially not running
        assert not manager.is_broker_running()

        # Start broker
        assert manager.start_broker(timeout=10)
        assert manager.is_broker_running()

        # Get status
        status = manager.get_broker_status()
        assert status["running"]
        assert status["responsive"]
        assert status["port"] == 39876

        # Stop broker
        assert manager.stop_broker()
        assert not manager.is_broker_running()

    def test_service_manager_restart(self, manager):
        """Test service manager can restart broker"""
        # Start broker
        assert manager.start_broker()
        first_status = manager.get_broker_status()
        first_pid = first_status.get("pid")

        # Restart broker
        assert manager.restart_broker()
        second_status = manager.get_broker_status()
        second_pid = second_status.get("pid")

        # Should have different PIDs
        assert first_pid != second_pid
        assert manager.is_broker_running()

    def test_service_manager_health_check(self, manager):
        """Test service manager health check"""
        # Start broker
        assert manager.start_broker()

        # Perform health check
        healthy, message = manager.health_check()
        assert healthy
        assert "healthy" in message.lower()

        # Stop broker
        manager.stop_broker()

        # Health check should fail
        healthy, message = manager.health_check()
        assert not healthy
        assert "not running" in message.lower()

    def test_ensure_broker_running(self, manager):
        """Test ensure_broker_running method"""
        # Not running initially
        assert not manager.is_broker_running()

        # Ensure running (should start)
        assert manager.ensure_broker_running()
        assert manager.is_broker_running()

        # Ensure running again (should just return True)
        assert manager.ensure_broker_running()
        assert manager.is_broker_running()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])