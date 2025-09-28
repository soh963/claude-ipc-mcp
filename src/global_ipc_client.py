#!/usr/bin/env python3
"""
Global IPC Client - Cross-project AI communication client library
"""

import socket
import json
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger('GlobalIPCClient')


class GlobalIPCClient:
    """Client for global IPC communication"""

    def __init__(self, project: str = None, config_path: str = None):
        """
        Initialize global IPC client

        Args:
            project: Project name/path (auto-detected if None)
            config_path: Path to configuration file
        """
        # Auto-detect project if not specified
        if project is None:
            project = self._detect_project()

        self.project = project
        self.project_hash = hashlib.sha256(project.encode()).hexdigest()[:8]

        # Load configuration
        self.config = self._load_config(config_path)

        # Server connection info
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 9876)

        # Instance info
        self.instance_id = None
        self.token = None
        self.visibility = self.config.get('visibility', 'project')

        logger.info(f"GlobalIPCClient initialized for project: {project} ({self.project_hash})")

    def _detect_project(self) -> str:
        """Auto-detect project from current directory"""
        cwd = Path.cwd()

        # Look for project markers
        markers = ['.git', 'package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod']

        for marker in markers:
            if (cwd / marker).exists():
                return str(cwd)

        # Use current directory name as fallback
        return cwd.name

    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration from file or environment"""
        config = {
            'host': os.environ.get('GLOBAL_IPC_HOST', 'localhost'),
            'port': int(os.environ.get('GLOBAL_IPC_PORT', 9876)),
            'visibility': os.environ.get('GLOBAL_IPC_VISIBILITY', 'project')
        }

        # Load from config file if specified
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)

        return config

    def _send_request(self, request: dict) -> dict:
        """Send request to global IPC server"""
        try:
            # Add project info to request
            request['project'] = self.project
            request['project_hash'] = self.project_hash

            # Connect to server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))

                # Send request
                request_data = json.dumps(request).encode('utf-8')
                sock.send(request_data)

                # Receive response
                response_data = sock.recv(65536)
                response = json.loads(response_data.decode('utf-8'))

                return response

        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return {'status': 'error', 'message': str(e)}

    def register(self, name: str, visibility: str = None) -> bool:
        """
        Register instance with global IPC server

        Args:
            name: Instance name (e.g., 'claude', 'gemini')
            visibility: 'project' | 'global' | 'selective'

        Returns:
            Success status
        """
        request = {
            'type': 'register',
            'name': name,
            'visibility': visibility or self.visibility
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            self.instance_id = response.get('instance_id')
            self.token = response.get('token')
            logger.info(f"✅ Registered as {name} ({self.instance_id})")
            return True

        logger.error(f"Registration failed: {response.get('message')}")
        return False

    def send(self, to: str, message: str, require_auth: bool = True) -> bool:
        """
        Send message to another instance

        Args:
            to: Recipient ID (name, name@project, name@global)
            message: Message content
            require_auth: Require cross-project authentication

        Returns:
            Success status
        """
        if not self.instance_id:
            logger.error("Not registered. Call register() first.")
            return False

        request = {
            'type': 'send',
            'from': self.instance_id,
            'to': to,
            'message': message,
            'require_auth': require_auth,
            'token': self.token
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            delivered_to = response.get('delivered_to')
            cross_project = response.get('cross_project', False)

            logger.info(
                f"📨 Sent to {delivered_to} "
                f"{'(cross-project)' if cross_project else ''}"
            )
            return True

        logger.error(f"Send failed: {response.get('message')}")
        return False

    def check(self) -> List[dict]:
        """
        Check for messages

        Returns:
            List of messages
        """
        if not self.instance_id:
            logger.error("Not registered. Call register() first.")
            return []

        request = {
            'type': 'check',
            'instance': self.instance_id,
            'token': self.token
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            messages = response.get('messages', [])

            if messages:
                logger.info(f"📬 Received {len(messages)} message(s)")

            return messages

        logger.error(f"Check failed: {response.get('message')}")
        return []

    def list_instances(self, include_global: bool = False) -> List[dict]:
        """
        List available instances

        Args:
            include_global: Include global instances from other projects

        Returns:
            List of instances
        """
        request = {
            'type': 'list',
            'project': self.project_hash if not include_global else None,
            'include_global': include_global
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            return response.get('instances', [])

        logger.error(f"List failed: {response.get('message')}")
        return []

    def grant_permission(self, to_project: str) -> bool:
        """
        Grant permission for cross-project communication

        Args:
            to_project: Target project ID/name

        Returns:
            Success status
        """
        # Hash project name if needed
        if not to_project.startswith('project:'):
            to_project_hash = hashlib.sha256(to_project.encode()).hexdigest()[:8]
        else:
            to_project_hash = to_project.replace('project:', '')

        request = {
            'type': 'permission',
            'action': 'grant',
            'from_project': self.project_hash,
            'to_project': to_project_hash,
            'token': self.token
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            logger.info(f"✅ Permission granted to {to_project}")
            return True

        logger.error(f"Permission grant failed: {response.get('message')}")
        return False

    def revoke_permission(self, to_project: str) -> bool:
        """
        Revoke permission for cross-project communication

        Args:
            to_project: Target project ID/name

        Returns:
            Success status
        """
        # Hash project name if needed
        if not to_project.startswith('project:'):
            to_project_hash = hashlib.sha256(to_project.encode()).hexdigest()[:8]
        else:
            to_project_hash = to_project.replace('project:', '')

        request = {
            'type': 'permission',
            'action': 'revoke',
            'from_project': self.project_hash,
            'to_project': to_project_hash,
            'token': self.token
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            logger.info(f"❌ Permission revoked from {to_project}")
            return True

        logger.error(f"Permission revoke failed: {response.get('message')}")
        return False

    def check_permission(self, to_project: str) -> bool:
        """
        Check if cross-project communication is allowed

        Args:
            to_project: Target project ID/name

        Returns:
            Permission status
        """
        # Hash project name if needed
        if not to_project.startswith('project:'):
            to_project_hash = hashlib.sha256(to_project.encode()).hexdigest()[:8]
        else:
            to_project_hash = to_project.replace('project:', '')

        request = {
            'type': 'permission',
            'action': 'check',
            'from_project': self.project_hash,
            'to_project': to_project_hash
        }

        response = self._send_request(request)

        if response.get('status') == 'ok':
            return response.get('allowed', False)

        return False

    def status(self) -> dict:
        """
        Get server status

        Returns:
            Server status information
        """
        request = {'type': 'status'}
        response = self._send_request(request)

        if response.get('status') == 'ok':
            return response

        logger.error(f"Status failed: {response.get('message')}")
        return {}


# Convenience functions
def quick_register(name: str, project: str = None, visibility: str = 'project') -> GlobalIPCClient:
    """Quick registration helper"""
    client = GlobalIPCClient(project)

    if client.register(name, visibility):
        return client

    return None


def quick_send(from_name: str, to_name: str, message: str, project: str = None) -> bool:
    """Quick message sending helper"""
    client = GlobalIPCClient(project)

    if not client.register(from_name):
        return False

    return client.send(to_name, message)


def quick_check(name: str, project: str = None) -> List[dict]:
    """Quick message checking helper"""
    client = GlobalIPCClient(project)

    if not client.register(name):
        return []

    return client.check()


if __name__ == '__main__':
    # Test the client
    import sys

    if len(sys.argv) < 2:
        print("Usage: python global_ipc_client.py <name> [project]")
        sys.exit(1)

    name = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else None

    # Create client and register
    client = GlobalIPCClient(project)

    if client.register(name):
        print(f"✅ Registered as {name}")

        # List instances
        instances = client.list_instances(include_global=True)
        print(f"📋 Active instances: {len(instances)}")

        for inst in instances:
            print(f"  - {inst['name']} (project: {inst['project']}, visibility: {inst['visibility']})")

        # Check messages
        messages = client.check()
        if messages:
            print(f"📬 Messages:")
            for msg in messages:
                print(f"  From {msg['from']}: {msg['message']}")
        else:
            print("📭 No messages")
    else:
        print("❌ Registration failed")