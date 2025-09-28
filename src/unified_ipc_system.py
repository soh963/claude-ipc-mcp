#!/usr/bin/env python3
"""
Unified IPC System - Main Integration Point
Coordinates Claude's router, Gemini's security, and Codex's async optimization
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.broker import MessageBroker, BrokerConfig
from core.router import GlobalMessageRouter, RouteConfig, CommunicationMode

# Placeholder imports for Gemini and Codex modules (will be implemented by them)
# from core.security import SecurityManager  # Gemini
# from core.async_broker import AsyncMessageBroker  # Codex
# from platform.bridge import PlatformBridge  # Gemini
# from plugins.manager import PluginManager  # Codex
# from monitoring.metrics import MetricsCollector  # Gemini
# from optimization.cache import CacheManager  # Codex

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedIPCSystem:
    """
    Main orchestrator for the entire IPC system
    Integrates all components from Claude, Gemini, and Codex
    """

    def __init__(self):
        self.broker = None
        self.router = None
        self.security = None  # Will be set by Gemini
        self.async_broker = None  # Will be set by Codex
        self.metrics = None  # Will be set by Gemini
        self.plugins = None  # Will be set by Codex
        self.cache = None  # Will be set by Codex

        self._init_components()

    def _init_components(self):
        """Initialize all system components"""
        logger.info("Initializing Unified IPC System components...")

        # Initialize broker (Claude)
        broker_config = BrokerConfig(
            port=int(os.environ.get('IPC_PORT', '9876')),
            enable_security=True,
            enable_metrics=True
        )
        self.broker = MessageBroker(broker_config)

        # Initialize router (Claude)
        router_config = RouteConfig(
            mode=self._determine_mode(),
            global_port=int(os.environ.get('IPC_GLOBAL_PORT', '9876')),
            enable_audit=True
        )
        self.router = GlobalMessageRouter(router_config)

        logger.info("Core components initialized")

    def _determine_mode(self) -> CommunicationMode:
        """Determine communication mode from environment"""
        if os.environ.get('IPC_HYBRID_MODE', '').lower() == 'true':
            return CommunicationMode.HYBRID
        elif os.environ.get('IPC_GLOBAL_MODE', '').lower() == 'true':
            return CommunicationMode.GLOBAL
        else:
            return CommunicationMode.PROJECT

    def integrate_security(self, security_manager):
        """Integrate Gemini's security module"""
        self.security = security_manager

        # Set security hook in broker
        if hasattr(security_manager, 'validate_request'):
            self.broker.set_security_hook(security_manager.validate_request)

        logger.info("Security module integrated (Gemini)")

    def integrate_async_optimization(self, async_broker, cache_manager):
        """Integrate Codex's async and optimization modules"""
        self.async_broker = async_broker
        self.cache = cache_manager

        # Set async hook in broker
        if hasattr(async_broker, 'process_async'):
            self.broker.set_async_hook(async_broker.process_async)

        logger.info("Async optimization integrated (Codex)")

    def integrate_monitoring(self, metrics_collector):
        """Integrate monitoring system"""
        self.metrics = metrics_collector

        # Set metrics hook in broker
        if hasattr(metrics_collector, 'collect_metrics'):
            self.broker.set_metrics_hook(metrics_collector.collect_metrics)

        logger.info("Monitoring system integrated")

    def integrate_plugins(self, plugin_manager):
        """Integrate plugin system"""
        self.plugins = plugin_manager
        logger.info("Plugin system integrated (Codex)")

    def start(self):
        """Start all system components"""
        logger.info("Starting Unified IPC System...")

        try:
            # Start broker
            self.broker.start()
            logger.info("Message broker started")

            # Start router
            self.router.start()
            logger.info("Message router started")

            # Start async broker if available
            if self.async_broker and hasattr(self.async_broker, 'start'):
                self.async_broker.start()
                logger.info("Async broker started")

            # Start metrics collector if available
            if self.metrics and hasattr(self.metrics, 'start'):
                self.metrics.start()
                logger.info("Metrics collector started")

            # Load plugins if available
            if self.plugins and hasattr(self.plugins, 'load_all'):
                self.plugins.load_all()
                logger.info("Plugins loaded")

            logger.info("✅ Unified IPC System started successfully!")

            # Display status
            self._display_status()

        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop all system components"""
        logger.info("Stopping Unified IPC System...")

        if self.broker:
            self.broker.stop()

        if self.router:
            self.router.stop()

        if self.async_broker and hasattr(self.async_broker, 'stop'):
            self.async_broker.stop()

        if self.metrics and hasattr(self.metrics, 'stop'):
            self.metrics.stop()

        logger.info("System stopped")

    def _display_status(self):
        """Display system status"""
        status = {
            'Mode': self.router.config.mode.value if self.router else 'N/A',
            'Broker': 'Running' if self.broker and self.broker.running else 'Stopped',
            'Router': 'Running' if self.router else 'Stopped',
            'Security': 'Enabled' if self.security else 'Pending (Gemini)',
            'Async': 'Enabled' if self.async_broker else 'Pending (Codex)',
            'Monitoring': 'Enabled' if self.metrics else 'Pending',
            'Plugins': 'Loaded' if self.plugins else 'Pending (Codex)',
            'Cache': 'Active' if self.cache else 'Pending (Codex)'
        }

        logger.info("=" * 50)
        logger.info("SYSTEM STATUS")
        logger.info("=" * 50)
        for key, value in status.items():
            logger.info(f"{key:15}: {value}")
        logger.info("=" * 50)

    def get_status(self) -> dict:
        """Get complete system status"""
        return {
            'broker': self.broker.config.__dict__ if self.broker else None,
            'router': self.router.get_status() if self.router else None,
            'security': 'Enabled' if self.security else 'Not integrated',
            'async': 'Enabled' if self.async_broker else 'Not integrated',
            'monitoring': 'Active' if self.metrics else 'Not integrated',
            'plugins': 'Loaded' if self.plugins else 'Not integrated',
            'cache': 'Active' if self.cache else 'Not integrated'
        }


def main():
    """Main entry point"""
    import signal
    import time

    # Create system
    system = UnifiedIPCSystem()

    # Signal handler for clean shutdown
    def signal_handler(signum, frame):
        logger.info("\nReceived shutdown signal...")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start system
        system.start()

        # TODO: Once Gemini and Codex complete their modules, uncomment these:
        # from core.security import SecurityManager
        # system.integrate_security(SecurityManager())

        # from core.async_broker import AsyncMessageBroker
        # from optimization.cache import CacheManager
        # system.integrate_async_optimization(AsyncMessageBroker(), CacheManager())

        # from monitoring.metrics import MetricsCollector
        # system.integrate_monitoring(MetricsCollector())

        # from plugins.manager import PluginManager
        # system.integrate_plugins(PluginManager())

        logger.info("System is running. Press Ctrl+C to stop.")

        # Keep running
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"System error: {e}")
        system.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()