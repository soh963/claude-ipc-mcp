#!/usr/bin/env python3
"""
Integration tests for Unified IPC System
"""

import unittest
import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from unified_ipc_system import UnifiedIPCSystem
from core.router import CommunicationMode
from core.security import SecurityManager, SecurityConfig
from core.async_broker import AsyncMessageBroker, AsyncConfig
from monitoring.metrics import MetricsCollector
from plugins.manager import PluginManager
from optimization.cache import CacheManager


class TestUnifiedSystem(unittest.TestCase):
    """Test the complete Unified IPC System"""

    def setUp(self):
        """Set up test system"""
        self.system = UnifiedIPCSystem()

    def tearDown(self):
        """Clean up system"""
        if self.system:
            self.system.stop()

    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system.broker)
        self.assertIsNotNone(self.system.router)
        self.assertIsNone(self.system.security)  # Not integrated yet
        self.assertIsNone(self.system.async_broker)  # Not integrated yet

    def test_component_integration(self):
        """Test integrating all components"""
        # Create components
        security = SecurityManager(SecurityConfig(enable_jwt=False))
        async_broker = AsyncMessageBroker(AsyncConfig())
        cache = CacheManager()
        metrics = MetricsCollector()
        plugins = PluginManager()

        # Integrate components
        self.system.integrate_security(security)
        self.system.integrate_async_optimization(async_broker, cache)
        self.system.integrate_monitoring(metrics)
        self.system.integrate_plugins(plugins)

        # Verify integration
        self.assertEqual(self.system.security, security)
        self.assertEqual(self.system.async_broker, async_broker)
        self.assertEqual(self.system.cache, cache)
        self.assertEqual(self.system.metrics, metrics)
        self.assertEqual(self.system.plugins, plugins)

    @patch('socket.socket')
    def test_system_start_stop(self, mock_socket):
        """Test starting and stopping the system"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock

        # Start system
        self.system.start()

        # Verify components started
        self.assertTrue(self.system.broker.running)
        # Router doesn't have a running flag but should be started

        # Stop system
        self.system.stop()

        # Verify components stopped
        self.assertFalse(self.system.broker.running)

    def test_get_status(self):
        """Test getting system status"""
        status = self.system.get_status()

        self.assertIn('broker', status)
        self.assertIn('router', status)
        self.assertIn('security', status)
        self.assertIn('async', status)
        self.assertIn('monitoring', status)

    def test_communication_modes(self):
        """Test different communication modes"""
        # Test project mode
        self.system.router.config.mode = CommunicationMode.PROJECT
        self.assertEqual(self.system.router.config.mode, CommunicationMode.PROJECT)

        # Test global mode
        self.system.router.config.mode = CommunicationMode.GLOBAL
        self.assertEqual(self.system.router.config.mode, CommunicationMode.GLOBAL)

        # Test hybrid mode
        self.system.router.config.mode = CommunicationMode.HYBRID
        self.assertEqual(self.system.router.config.mode, CommunicationMode.HYBRID)


class TestMessageFlow(unittest.TestCase):
    """Test complete message flow through the system"""

    def setUp(self):
        """Set up test system with all components"""
        self.system = UnifiedIPCSystem()

        # Integrate all components
        self.system.integrate_security(SecurityManager(SecurityConfig(enable_jwt=False)))
        self.system.integrate_monitoring(MetricsCollector())

        # Mock async broker to avoid actual async operations
        self.async_broker = Mock()
        self.cache = CacheManager(memory_size=1024*1024)
        self.system.integrate_async_optimization(self.async_broker, self.cache)

    def tearDown(self):
        """Clean up"""
        if self.system:
            self.system.stop()

    def test_message_routing(self):
        """Test message routing through the system"""
        # Register instances
        self.system.broker._handle_register({
            'instance_id': 'sender',
            'project_id': 'test_project'
        })

        self.system.broker._handle_register({
            'instance_id': 'receiver',
            'project_id': 'test_project'
        })

        # Send message
        send_response = self.system.broker._handle_send({
            'from_id': 'sender',
            'to_id': 'receiver',
            'content': 'test message'
        })

        self.assertEqual(send_response['status'], 'ok')

        # Check message
        check_response = self.system.broker._handle_check({
            'instance_id': 'receiver'
        })

        self.assertEqual(check_response['status'], 'ok')
        self.assertEqual(len(check_response['messages']), 1)

    def test_broadcast_message(self):
        """Test broadcasting messages"""
        # Register multiple instances
        for i in range(5):
            self.system.broker._handle_register({
                'instance_id': f'instance_{i}',
                'project_id': 'test_project'
            })

        # Broadcast message
        broadcast_response = self.system.broker._handle_broadcast({
            'from_id': 'instance_0',
            'content': 'broadcast test'
        })

        self.assertEqual(broadcast_response['status'], 'ok')
        self.assertIn('Broadcast to 4 instances', broadcast_response['message'])

    def test_caching_integration(self):
        """Test cache integration"""
        # Cache a message
        message = {
            'id': 'test123',
            'type': 'test',
            'content': 'cached content'
        }

        cache_key = self.system.cache.cache_message(message)
        self.assertIsNotNone(cache_key)

        # Retrieve from cache
        cached = self.system.cache.get(cache_key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['content'], 'cached content')

    def test_metrics_collection(self):
        """Test metrics collection"""
        # Perform some operations
        self.system.broker._handle_register({
            'instance_id': 'metrics_test',
            'project_id': 'test'
        })

        # Simulate request with metrics
        request = {
            'type': 'send',
            'from_id': 'sender',
            'to_id': 'receiver',
            'content': 'test',
            '_start_time': time.time()
        }

        response = {'status': 'ok'}

        # Collect metrics
        self.system.metrics.collect_metrics(request, response)

        # Get dashboard data
        dashboard = self.system.metrics.get_dashboard_data()
        self.assertIn('metrics', dashboard)
        self.assertIn('application', dashboard)


class TestAsyncOperations(unittest.TestCase):
    """Test asynchronous operations"""

    def setUp(self):
        """Set up async broker"""
        self.async_broker = AsyncMessageBroker(AsyncConfig(max_queue_size=100))

    def tearDown(self):
        """Clean up"""
        if self.async_broker.running:
            asyncio.run(self.async_broker.stop())

    def test_async_message_processing(self):
        """Test async message processing"""
        async def run_test():
            # Register handler
            async def test_handler(data):
                return {'processed': data}

            self.async_broker.register_handler('test', test_handler)

            # Start broker
            await self.async_broker.start(worker_count=2)

            # Send messages
            results = []
            for i in range(10):
                request = {
                    'type': 'test',
                    'id': str(i),
                    'data': f'message_{i}'
                }
                result = await self.async_broker.process_async(
                    request,
                    lambda x: x
                )
                results.append(result)

            # All should be accepted
            accepted = sum(1 for r in results if r['status'] == 'accepted')
            self.assertEqual(accepted, 10)

            # Wait for processing
            await asyncio.sleep(0.5)

            # Check stats
            stats = self.async_broker.get_stats()
            self.assertGreater(stats['messages_processed'], 0)

            # Stop broker
            await self.async_broker.stop()

        # Run async test
        asyncio.run(run_test())

    def test_backpressure_management(self):
        """Test backpressure management"""
        async def run_test():
            # Create broker with small queue
            broker = AsyncMessageBroker(AsyncConfig(max_queue_size=5))

            # Start broker
            await broker.start(worker_count=1)

            # Send many messages quickly
            results = []
            for i in range(10):
                request = {
                    'type': 'test',
                    'id': str(i)
                }
                result = await broker.process_async(request, lambda x: x)
                results.append(result)

            # Some should be rejected due to backpressure
            rejected = sum(1 for r in results if r['status'] == 'error')
            self.assertGreater(rejected, 0)

            # Stop broker
            await broker.stop()

        asyncio.run(run_test())


class TestSecurityIntegration(unittest.TestCase):
    """Test security integration"""

    def setUp(self):
        """Set up security manager"""
        self.security = SecurityManager(SecurityConfig(enable_jwt=True))

    def test_authentication(self):
        """Test authentication"""
        # Authenticate user
        token = self.security.authenticate({
            'username': 'test_user',
            'password': 'test_pass'
        })

        self.assertIsNotNone(token)

        # Validate token
        valid = self.security.validate_request({
            'type': 'send',
            'token': token
        }, ('127.0.0.1', 12345))

        self.assertTrue(valid)

    def test_authorization(self):
        """Test authorization"""
        # Authenticate and get token
        token = self.security.authenticate({
            'username': 'test_user',
            'password': 'test_pass'
        })

        # Test different request types
        requests = [
            {'type': 'send', 'token': token},
            {'type': 'register', 'token': token},
            {'type': 'list', 'token': token}
        ]

        for request in requests:
            valid = self.security.validate_request(
                request,
                ('127.0.0.1', 12345)
            )
            self.assertTrue(valid)

    def test_invalid_token(self):
        """Test invalid token handling"""
        valid = self.security.validate_request({
            'type': 'send',
            'token': 'invalid_token'
        }, ('127.0.0.1', 12345))

        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()