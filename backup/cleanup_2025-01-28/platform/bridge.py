#!/usr/bin/env python3
"""
Platform Bridge for Unified IPC System
Gemini's implementation - Cross-platform communication support
"""

import os
import sys
import platform
import socket
import struct
import subprocess
from typing import Dict, Optional, Any, Tuple, Union
from pathlib import Path
from abc import ABC, abstractmethod
import logging

# Platform-specific imports
if sys.platform == 'win32':
    import win32pipe
    import win32file
    import pywintypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detect and analyze platform environment"""

    @staticmethod
    def detect_platform() -> Dict[str, Any]:
        """Detect current platform and environment"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
            'is_wsl': False,
            'is_docker': False,
            'is_windows': sys.platform == 'win32',
            'is_linux': sys.platform.startswith('linux'),
            'is_mac': sys.platform == 'darwin'
        }

        # Detect WSL
        info['is_wsl'] = PlatformDetector._detect_wsl()

        # Detect Docker
        info['is_docker'] = PlatformDetector._detect_docker()

        return info

    @staticmethod
    def _detect_wsl() -> bool:
        """Detect if running in WSL"""
        if sys.platform != 'linux':
            return False

        # Check for WSL-specific indicators
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version or 'wsl' in version
        except:
            pass

        # Check for WSL environment variable
        return 'WSL_DISTRO_NAME' in os.environ

    @staticmethod
    def _detect_docker() -> bool:
        """Detect if running in Docker container"""
        # Check for .dockerenv file
        if Path('/.dockerenv').exists():
            return True

        # Check cgroup
        try:
            with open('/proc/self/cgroup', 'r') as f:
                return 'docker' in f.read()
        except:
            return False


class CommunicationChannel(ABC):
    """Abstract base for platform-specific communication channels"""

    @abstractmethod
    def connect(self, address: str) -> bool:
        """Connect to communication channel"""
        pass

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Send data through channel"""
        pass

    @abstractmethod
    def receive(self, size: int = 4096) -> Optional[bytes]:
        """Receive data from channel"""
        pass

    @abstractmethod
    def close(self):
        """Close communication channel"""
        pass


class TCPChannel(CommunicationChannel):
    """TCP socket communication (cross-platform)"""

    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self, address: str) -> bool:
        """Connect via TCP socket"""
        try:
            host, port = self._parse_address(address)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            logger.info(f"TCP connected to {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"TCP connection failed: {e}")
            return False

    def _parse_address(self, address: str) -> Tuple[str, int]:
        """Parse TCP address"""
        if ':' in address:
            host, port = address.split(':')
            return host, int(port)
        return address, 9876  # Default port

    def send(self, data: bytes) -> bool:
        """Send data via TCP"""
        if not self.connected or not self.socket:
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"TCP send failed: {e}")
            return False

    def receive(self, size: int = 4096) -> Optional[bytes]:
        """Receive data via TCP"""
        if not self.connected or not self.socket:
            return None

        try:
            return self.socket.recv(size)
        except Exception as e:
            logger.error(f"TCP receive failed: {e}")
            return None

    def close(self):
        """Close TCP connection"""
        if self.socket:
            self.socket.close()
            self.connected = False


class UnixSocketChannel(CommunicationChannel):
    """Unix domain socket communication (Linux/Mac)"""

    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self, address: str) -> bool:
        """Connect via Unix socket"""
        if sys.platform == 'win32':
            logger.warning("Unix sockets not supported on Windows")
            return False

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(address)
            self.connected = True
            logger.info(f"Unix socket connected to {address}")
            return True
        except Exception as e:
            logger.error(f"Unix socket connection failed: {e}")
            return False

    def send(self, data: bytes) -> bool:
        """Send data via Unix socket"""
        if not self.connected or not self.socket:
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Unix socket send failed: {e}")
            return False

    def receive(self, size: int = 4096) -> Optional[bytes]:
        """Receive data via Unix socket"""
        if not self.connected or not self.socket:
            return None

        try:
            return self.socket.recv(size)
        except Exception as e:
            logger.error(f"Unix socket receive failed: {e}")
            return None

    def close(self):
        """Close Unix socket"""
        if self.socket:
            self.socket.close()
            self.connected = False


class NamedPipeChannel(CommunicationChannel):
    """Named pipe communication (Windows)"""

    def __init__(self):
        self.pipe = None
        self.connected = False

    def connect(self, address: str) -> bool:
        """Connect via named pipe"""
        if sys.platform != 'win32':
            logger.warning("Named pipes only supported on Windows")
            return False

        try:
            # Format pipe name
            pipe_name = address
            if not pipe_name.startswith(r'\\.\pipe\\'):
                pipe_name = r'\\.\pipe\\' + pipe_name

            # Connect to pipe
            self.pipe = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )

            self.connected = True
            logger.info(f"Named pipe connected to {pipe_name}")
            return True

        except pywintypes.error as e:
            logger.error(f"Named pipe connection failed: {e}")
            return False

    def send(self, data: bytes) -> bool:
        """Send data via named pipe"""
        if not self.connected or not self.pipe:
            return False

        try:
            win32file.WriteFile(self.pipe, data)
            return True
        except Exception as e:
            logger.error(f"Named pipe send failed: {e}")
            return False

    def receive(self, size: int = 4096) -> Optional[bytes]:
        """Receive data via named pipe"""
        if not self.connected or not self.pipe:
            return None

        try:
            result, data = win32file.ReadFile(self.pipe, size)
            if result == 0:
                return data
            return None
        except Exception as e:
            logger.error(f"Named pipe receive failed: {e}")
            return None

    def close(self):
        """Close named pipe"""
        if self.pipe:
            win32file.CloseHandle(self.pipe)
            self.connected = False


class WSLBridge:
    """Special bridge for WSL2 communication"""

    def __init__(self):
        self.host_ip: Optional[str] = None
        self.wsl_ip: Optional[str] = None

    def detect_ips(self) -> Tuple[Optional[str], Optional[str]]:
        """Detect WSL2 IP addresses"""
        try:
            # Get WSL IP
            result = subprocess.run(
                ['hostname', '-I'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.wsl_ip = result.stdout.strip().split()[0]

            # Get Windows host IP
            result = subprocess.run(
                ['cat', '/etc/resolv.conf'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'nameserver' in line:
                        self.host_ip = line.split()[1]
                        break

            logger.info(f"WSL2 Bridge - Host: {self.host_ip}, WSL: {self.wsl_ip}")
            return self.host_ip, self.wsl_ip

        except Exception as e:
            logger.error(f"Failed to detect WSL2 IPs: {e}")
            return None, None

    def setup_port_forwarding(self, port: int):
        """Setup port forwarding between WSL2 and Windows"""
        if not self.host_ip:
            self.detect_ips()

        try:
            # This would require admin privileges on Windows side
            # Usually configured manually or via PowerShell script
            logger.info(f"Port forwarding setup required for port {port}")
            logger.info("Run in PowerShell as admin:")
            logger.info(f"netsh interface portproxy add v4tov4 listenport={port} listenaddress=0.0.0.0 connectport={port} connectaddress={self.wsl_ip}")

        except Exception as e:
            logger.error(f"Port forwarding setup failed: {e}")


class PlatformBridge:
    """Main platform bridge coordinating all communication methods"""

    def __init__(self):
        self.platform_info = PlatformDetector.detect_platform()
        self.channels: Dict[str, CommunicationChannel] = {}
        self.wsl_bridge: Optional[WSLBridge] = None

        self._init_channels()
        logger.info(f"Platform Bridge initialized: {self.platform_info['system']}")

    def _init_channels(self):
        """Initialize available communication channels"""
        # TCP is always available
        self.channels['tcp'] = TCPChannel()

        # Platform-specific channels
        if self.platform_info['is_windows']:
            self.channels['named_pipe'] = NamedPipeChannel()

        elif self.platform_info['is_linux'] or self.platform_info['is_mac']:
            self.channels['unix_socket'] = UnixSocketChannel()

        # WSL2 special handling
        if self.platform_info['is_wsl']:
            self.wsl_bridge = WSLBridge()
            self.wsl_bridge.detect_ips()

    def select_best_channel(self) -> str:
        """Select the best communication channel for current platform"""
        # Priority order based on platform
        if self.platform_info['is_windows']:
            # Windows: Named pipes are fastest for local
            return 'named_pipe' if 'named_pipe' in self.channels else 'tcp'

        elif self.platform_info['is_linux'] or self.platform_info['is_mac']:
            # Unix: Domain sockets are fastest for local
            return 'unix_socket' if 'unix_socket' in self.channels else 'tcp'

        # Default to TCP
        return 'tcp'

    def create_connection(self, address: str, channel_type: Optional[str] = None) -> Optional[CommunicationChannel]:
        """Create a connection using specified or best channel"""
        if not channel_type:
            channel_type = self.select_best_channel()

        channel = self.channels.get(channel_type)
        if not channel:
            logger.error(f"Channel type {channel_type} not available")
            return None

        if channel.connect(address):
            return channel

        # Fallback to TCP if preferred channel fails
        if channel_type != 'tcp' and 'tcp' in self.channels:
            logger.info("Falling back to TCP")
            tcp_channel = self.channels['tcp']
            if tcp_channel.connect(address):
                return tcp_channel

        return None

    def optimize_for_platform(self) -> Dict[str, Any]:
        """Return platform-specific optimizations"""
        optimizations = {
            'buffer_size': 8192,  # Default
            'timeout': 5.0,
            'max_connections': 100,
            'preferred_channel': self.select_best_channel()
        }

        if self.platform_info['is_windows']:
            # Windows optimizations
            optimizations['buffer_size'] = 65536
            optimizations['max_connections'] = 200

        elif self.platform_info['is_linux']:
            # Linux optimizations
            optimizations['buffer_size'] = 131072
            optimizations['max_connections'] = 1000

        elif self.platform_info['is_mac']:
            # macOS optimizations
            optimizations['buffer_size'] = 65536
            optimizations['max_connections'] = 500

        # WSL2 specific
        if self.platform_info['is_wsl']:
            optimizations['buffer_size'] = 32768
            optimizations['wsl_host_ip'] = self.wsl_bridge.host_ip if self.wsl_bridge else None

        return optimizations

    def get_status(self) -> Dict[str, Any]:
        """Get platform bridge status"""
        return {
            'platform': self.platform_info,
            'available_channels': list(self.channels.keys()),
            'preferred_channel': self.select_best_channel(),
            'optimizations': self.optimize_for_platform()
        }


def main():
    """Test platform bridge"""
    bridge = PlatformBridge()

    # Display platform info
    print(f"Platform: {bridge.platform_info}")
    print(f"Available channels: {list(bridge.channels.keys())}")
    print(f"Best channel: {bridge.select_best_channel()}")
    print(f"Optimizations: {bridge.optimize_for_platform()}")

    # Test connection
    conn = bridge.create_connection("localhost:9876")
    if conn:
        print("Connection successful")
        conn.close()
    else:
        print("Connection failed")


if __name__ == "__main__":
    main()