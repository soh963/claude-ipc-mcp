"""
Standalone Broker Package for Claude IPC MCP
Provides a robust, multi-CLI compatible message broker
"""

from .daemon import BrokerDaemon
from .service_manager import ServiceManager

__all__ = ["BrokerDaemon", "ServiceManager"]

__version__ = "2.0.0"