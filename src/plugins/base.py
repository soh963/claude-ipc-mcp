#!/usr/bin/env python3
"""
Plugin Base Class for Unified IPC System
Codex's implementation - Base class and interfaces for plugins
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None
    config: Dict[str, Any] = None


class PluginBase(ABC):
    """Base class for all plugins"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = False
        self.initialized = False

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize plugin"""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown plugin"""
        pass

    @abstractmethod
    def handle_message(self, message: Dict) -> Optional[Dict]:
        """Handle a message"""
        pass

    def on_enable(self):
        """Called when plugin is enabled"""
        self.enabled = True
        logger.info(f"Plugin {self.get_info().name} enabled")

    def on_disable(self):
        """Called when plugin is disabled"""
        self.enabled = False
        logger.info(f"Plugin {self.get_info().name} disabled")

    def validate_dependencies(self) -> bool:
        """Validate plugin dependencies"""
        info = self.get_info()
        if not info.dependencies:
            return True

        # Check each dependency
        for dep in info.dependencies:
            try:
                __import__(dep)
            except ImportError:
                logger.error(f"Missing dependency: {dep}")
                return False

        return True