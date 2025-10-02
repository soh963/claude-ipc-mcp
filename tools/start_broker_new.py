#!/usr/bin/env python3
"""
New Broker Launcher using Service Manager
Ensures only one broker instance runs system-wide
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from broker.service_manager import ServiceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("🚀 Starting broker using Service Manager...")

    # Create service manager
    manager = ServiceManager()

    # Clean up any stale processes first
    manager.cleanup_stale_processes()

    # Get current status
    status = manager.get_broker_status()

    if status["running"] and status["responsive"]:
        logger.info(f"✅ Broker is already running (PID: {status.get('pid')})")
        logger.info(f"   Host: {status['host']}  Port: {status['port']}")
        logger.info(f"   Version: {status.get('version')}")
        logger.info(f"   Active instances: {len(status.get('instances', []))}")
        return 0

    # Start broker
    logger.info("Broker not running, starting new instance...")

    if manager.start_broker():
        # Get updated status
        status = manager.get_broker_status()
        logger.info(f"✅ Broker started successfully")
        logger.info(f"   PID: {status.get('pid')}")
        logger.info(f"   Host: {status['host']}  Port: {status['port']}")
        logger.info(f"   Version: {status.get('version')}")

        # Perform health check
        healthy, message = manager.health_check()
        if healthy:
            logger.info(f"✅ Health check: {message}")
        else:
            logger.warning(f"⚠️ Health check: {message}")

        return 0
    else:
        logger.error("❌ Failed to start broker")
        return 1


if __name__ == "__main__":
    sys.exit(main())