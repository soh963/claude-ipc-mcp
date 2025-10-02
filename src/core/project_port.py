"""
Project-based port allocation for multi-project IPC isolation.

PRIORITY ORDER:
1. Detect running global broker (port 9876 default)
2. Use IPC_GLOBAL_PORT environment variable
3. Fall back to project-specific port ONLY if explicitly requested

This ensures all projects use the same global broker by default.
"""

import hashlib
import json
import os
import socket
from pathlib import Path
from typing import Optional, Tuple

# Default global broker port
DEFAULT_GLOBAL_PORT = 9876

# Base port range for project-specific brokers (legacy mode)
BASE_PORT = 10000
PORT_RANGE = 5000  # Ports 10000-14999 for projects


def detect_running_broker(host: str = "127.0.0.1", timeout: float = 0.5) -> Optional[int]:
    """
    Detect if a broker is already running and return its port.

    Checks common ports in order:
    1. IPC_GLOBAL_PORT env var
    2. Default port 9876
    3. Scan known range (9876-9900, 10000-14999)

    Args:
        host: Host address to check
        timeout: Connection timeout in seconds

    Returns:
        Port number if broker found, None otherwise
    """
    # Check environment variable first
    env_port = int(os.getenv("IPC_GLOBAL_PORT", os.getenv("IPC_PORT", "0")))
    if env_port > 0:
        if is_broker_running(env_port, host, timeout):
            return env_port

    # Check default port
    if is_broker_running(DEFAULT_GLOBAL_PORT, host, timeout):
        return DEFAULT_GLOBAL_PORT

    # Quick scan of common broker ports
    common_ports = list(range(9876, 9901)) + list(range(10000, 10100))
    for port in common_ports:
        if is_broker_running(port, host, timeout):
            return port

    return None


def is_broker_running(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """
    Check if a broker is running on the specified port.

    Args:
        port: Port number to check
        host: Host address
        timeout: Connection timeout

    Returns:
        True if broker is responding, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            # Port is open, verify it's actually a broker
            return verify_broker_protocol(port, host, timeout)
        return False
    except Exception:
        return False


def verify_broker_protocol(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """
    Verify that the service on the port is actually an IPC broker.

    Sends a simple ping and checks for valid response.

    Args:
        port: Port number
        host: Host address
        timeout: Connection timeout

    Returns:
        True if broker protocol verified, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # Send ping request
        ping_request = json.dumps({"action": "ping"}) + "\n"
        sock.sendall(ping_request.encode())

        # Receive response
        response = sock.recv(4096).decode()
        sock.close()

        # Check if response is valid JSON with success status
        data = json.loads(response.strip())
        return data.get("status") == "ok" or data.get("pong") == True
    except Exception:
        return False


def get_global_broker_port(host: str = "127.0.0.1") -> int:
    """
    Get the global broker port.

    Priority:
    1. Detect running broker
    2. Use IPC_GLOBAL_PORT environment variable
    3. Use DEFAULT_GLOBAL_PORT (9876)

    Args:
        host: Host address

    Returns:
        Port number for global broker
    """
    # Try to detect running broker
    running_port = detect_running_broker(host)
    if running_port:
        return running_port

    # Check environment variables
    env_port = int(os.getenv("IPC_GLOBAL_PORT", os.getenv("IPC_PORT", "0")))
    if env_port > 0:
        return env_port

    # Return default
    return DEFAULT_GLOBAL_PORT


def get_project_id(project_root: Optional[Path] = None) -> str:
    """
    Generate a unique project ID from project root path.

    Args:
        project_root: Project root directory (None = auto-detect)

    Returns:
        8-character hex project ID
    """
    from core.project_local import detect_project_root

    if project_root is None:
        project_root = detect_project_root()

    # Normalize path for consistent hashing across platforms
    normalized_path = str(project_root.resolve()).lower().replace('\\', '/')

    # Generate hash
    hash_obj = hashlib.sha256(normalized_path.encode())
    project_id = hash_obj.hexdigest()[:8]

    return project_id


def get_project_port(project_root: Optional[Path] = None) -> int:
    """
    Get unique port number for this project (LEGACY MODE).

    Args:
        project_root: Project root directory (None = auto-detect)

    Returns:
        Port number in range 10000-14999
    """
    project_id = get_project_id(project_root)

    # Convert first 4 hex chars to int and mod into range
    port_offset = int(project_id[:4], 16) % PORT_RANGE
    port = BASE_PORT + port_offset

    return port


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host address to bind to

    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(preferred_port: int, host: str = "127.0.0.1", max_attempts: int = 100) -> int:
    """
    Find an available port, starting from preferred port.

    Args:
        preferred_port: Preferred port to try first
        host: Host address to bind to
        max_attempts: Maximum number of ports to try

    Returns:
        Available port number

    Raises:
        RuntimeError: If no available port found
    """
    for offset in range(max_attempts):
        port = preferred_port + offset
        if port > 65535:
            port = BASE_PORT + (port % PORT_RANGE)

        if is_port_available(port, host):
            return port

    raise RuntimeError(f"No available port found after {max_attempts} attempts")


def get_or_create_project_port(
    project_root: Optional[Path] = None,
    host: str = "127.0.0.1",
    force_global: bool = True
) -> Tuple[int, str]:
    """
    Get project port with global broker detection.

    NEW BEHAVIOR:
    - By default (force_global=True), always use global broker detection
    - Returns tuple of (port, mode) where mode is "global" or "project-specific"

    Args:
        project_root: Project root directory (None = auto-detect)
        host: Host address to bind to
        force_global: If True, prioritize global broker detection (default: True)

    Returns:
        Tuple of (port_number, mode_string)
    """
    # Check environment variable for mode override
    use_global = os.getenv("IPC_USE_GLOBAL_BROKER", "true").lower() == "true"

    if use_global or force_global:
        # Global broker mode (default)
        port = get_global_broker_port(host)
        return port, "global"
    else:
        # Legacy project-specific mode
        preferred_port = get_project_port(project_root)

        if is_port_available(preferred_port, host):
            return preferred_port, "project-specific"

        # Preferred port occupied, find next available
        port = find_available_port(preferred_port + 1, host)
        return port, "project-specific"
