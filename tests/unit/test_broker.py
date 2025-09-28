#!/usr/bin/env python3
"""
Unit tests for Message Broker
"""

import unittest
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.broker import MessageBroker, BrokerConfig, Message, MessageQueue


class TestMessage(unittest.TestCase):
    """Test Message class"""

    def test_message_creation(self):
        """Test creating a message"""
        msg = Message(
            id='test123',
            from_id='sender',
            to_id='receiver',
            content={'data': 'test'},
            timestamp=time.time()
        )

        self.assertEqual(msg.id, 'test123')
        self.assertEqual(msg.from_id, 'sender')
        self.assertEqual(msg.to_id, 'receiver')
        self.assertEqual(msg.content['data'], 'test')

    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        msg = Message(
            id='test123',
            from_id='sender',
            to_id='receiver',
            content='test content',
            timestamp=1234567890
        )

        msg_dict = msg.to_dict()

        self.assertIsInstance(msg_dict, dict)
        self.assertEqual(msg_dict['id'], 'test123')
        self.assertEqual(msg_dict['content'], 'test content')

    def test_message_from_dict(self):
        """Test creating message from dictionary"""
        data = {
            'id': 'test456',
            'from_id': 'alice',
            'to_id': 'bob',
            'content': 'hello',
            'timestamp': time.time(),
            'scope': 'project',
            'project_id': 'proj123',
            'encrypted': False
        }

        msg = Message.from_dict(data)

        self.assertEqual(msg.id, 'test456')
        self.assertEqual(msg.from_id, 'alice')
        self.assertEqual(msg.to_id, 'bob')


class TestMessageQueue(unittest.TestCase):
    """Test MessageQueue class"""

    def setUp(self):
        """Set up test queue"""
        self.temp_db = Path.home() / '.claude-ipc-data' / 'test_broker.db'
        self.queue = MessageQueue(self.temp_db)

    def tearDown(self):
        """Clean up test database"""
        if self.temp_db.exists():
            self.temp_db.unlink()

    def test_add_message(self):
        """Test adding message to queue"""
        msg = Message(
            id='test789',
            from_id='sender',
            to_id='receiver',
            content='test message',
            timestamp=time.time()
        )

        self.queue.add_message(msg)

        # Verify message was added
        messages = self.queue.get_messages('receiver')
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, 'test789')

    def test_get_messages(self):
        """Test getting messages from queue"""
        # Add multiple messages
        for i in range(3):
            msg = Message(
                id=f'msg{i}',
                from_id='sender',
                to_id='receiver',
                content=f'message {i}',
                timestamp=time.time()
            )
            self.queue.add_message(msg)

        # Get messages
        messages = self.queue.get_messages('receiver')

        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].id, 'msg0')
        self.assertEqual(messages[2].id, 'msg2')

    def test_mark_delivered(self):
        """Test marking messages as delivered"""
        msg = Message(
            id='deliver_test',
            from_id='sender',
            to_id='receiver',
            content='test',
            timestamp=time.time()
        )
        self.queue.add_message(msg)

        # First get should mark as delivered
        messages = self.queue.get_messages('receiver', mark_delivered=True)
        self.assertEqual(len(messages), 1)

        # Second get should return empty
        messages = self.queue.get_messages('receiver')
        self.assertEqual(len(messages), 0)

    def test_cleanup_old_messages(self):
        """Test cleaning up old messages"""
        # Add old message
        old_msg = Message(
            id='old_msg',
            from_id='sender',
            to_id='receiver',
            content='old',
            timestamp=time.time() - 100000  # Very old
        )
        self.queue.add_message(old_msg)

        # Mark as delivered
        self.queue.get_messages('receiver')

        # Cleanup with short age
        self.queue.cleanup_old_messages(max_age_seconds=1)

        # Should be cleaned up
        with self.queue._get_db() as conn:
            result = conn.execute('SELECT COUNT(*) FROM messages').fetchone()
            self.assertEqual(result[0], 0)


class TestMessageBroker(unittest.TestCase):
    """Test MessageBroker class"""

    def setUp(self):
        """Set up test broker"""
        config = BrokerConfig(
            port=0,  # Use random port
            db_path=Path.home() / '.claude-ipc-data' / 'test_broker.db'
        )
        self.broker = MessageBroker(config)

    def tearDown(self):
        """Clean up broker"""
        if self.broker.running:
            self.broker.stop()

        # Clean up database
        if self.broker.config.db_path.exists():
            self.broker.config.db_path.unlink()

    def test_broker_initialization(self):
        """Test broker initialization"""
        self.assertIsNotNone(self.broker.queue)
        self.assertIsNotNone(self.broker.handlers)
        self.assertFalse(self.broker.running)

    def test_register_handler(self):
        """Test registering message handlers"""
        self.assertIn('register', self.broker.handlers)
        self.assertIn('send', self.broker.handlers)
        self.assertIn('check', self.broker.handlers)
        self.assertIn('broadcast', self.broker.handlers)

    @patch('socket.socket')
    def test_broker_start_stop(self, mock_socket):
        """Test starting and stopping broker"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        # Start broker
        self.broker.start()
        self.assertTrue(self.broker.running)

        # Stop broker
        self.broker.stop()
        self.assertFalse(self.broker.running)
        mock_sock.close.assert_called_once()

    def test_handle_register(self):
        """Test handling registration request"""
        request = {
            'type': 'register',
            'instance_id': 'test_instance',
            'project_id': 'test_project'
        }

        response = self.broker._handle_register(request)

        self.assertEqual(response['status'], 'ok')
        self.assertIn('test_instance', self.broker.clients)

    def test_handle_send(self):
        """Test handling send message request"""
        request = {
            'type': 'send',
            'from_id': 'sender',
            'to_id': 'receiver',
            'content': 'test message'
        }

        response = self.broker._handle_send(request)

        self.assertEqual(response['status'], 'ok')
        self.assertEqual(response['message'], 'Message sent')

    def test_handle_check(self):
        """Test handling check messages request"""
        # First send a message
        send_request = {
            'from_id': 'sender',
            'to_id': 'test_receiver',
            'content': 'test'
        }
        self.broker._handle_send(send_request)

        # Check messages
        check_request = {
            'instance_id': 'test_receiver'
        }

        response = self.broker._handle_check(check_request)

        self.assertEqual(response['status'], 'ok')
        self.assertIsInstance(response['messages'], list)
        self.assertEqual(len(response['messages']), 1)

    def test_handle_broadcast(self):
        """Test handling broadcast message"""
        # Register some clients
        self.broker.clients['client1'] = {'registered': time.time()}
        self.broker.clients['client2'] = {'registered': time.time()}
        self.broker.clients['sender'] = {'registered': time.time()}

        request = {
            'from_id': 'sender',
            'content': 'broadcast message'
        }

        response = self.broker._handle_broadcast(request)

        self.assertEqual(response['status'], 'ok')
        self.assertIn('Broadcast to 2 instances', response['message'])

    def test_handle_list(self):
        """Test handling list instances request"""
        # Register some clients
        self.broker.clients['client1'] = {
            'registered': time.time(),
            'project_id': 'proj1'
        }
        self.broker.clients['client2'] = {
            'registered': time.time(),
            'project_id': 'proj2'
        }

        request = {}
        response = self.broker._handle_list(request)

        self.assertEqual(response['status'], 'ok')
        self.assertEqual(len(response['instances']), 2)

    def test_set_hooks(self):
        """Test setting hook functions"""
        security_hook = Mock()
        async_hook = Mock()
        metrics_hook = Mock()

        self.broker.set_security_hook(security_hook)
        self.broker.set_async_hook(async_hook)
        self.broker.set_metrics_hook(metrics_hook)

        self.assertEqual(self.broker.security_hook, security_hook)
        self.assertEqual(self.broker.async_hook, async_hook)
        self.assertEqual(self.broker.metrics_hook, metrics_hook)


if __name__ == '__main__':
    unittest.main()