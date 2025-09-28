"""
Core components for the Unified IPC System
"""

from .router import GlobalMessageRouter
from .broker import MessageBroker

__all__ = ['GlobalMessageRouter', 'MessageBroker']

__version__ = '2.0.0'