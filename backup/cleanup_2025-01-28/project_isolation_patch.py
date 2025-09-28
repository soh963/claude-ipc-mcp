#!/usr/bin/env python3
"""
Project Isolation Enhancement for claude_ipc_server.py
This module adds project isolation capabilities to the IPC server
"""

import hashlib
import os
from typing import Dict, Any, Optional
import yaml
from pathlib import Path


class ProjectIsolationManager:
    """
    Manages project isolation for IPC communication.
    Ensures messages only flow between instances in the same project.
    """

    def __init__(self):
        self.project_id = self._get_project_id()
        self.project_port = self._get_project_port()
        self.config = self._load_config()

    def _get_project_id(self) -> str:
        """Generate unique project ID from path"""
        project_path = os.path.abspath(os.getcwd())
        project_path = project_path.replace('\\', '/').lower()
        hash_obj = hashlib.sha256(project_path.encode('utf-8'))
        return f"proj_{hash_obj.hexdigest()[:8]}"

    def _get_project_port(self) -> int:
        """Generate unique port for project"""
        port_hash = hashlib.md5(self.project_id.encode()).hexdigest()[:4]
        port_offset = int(port_hash, 16) % 1000
        return 9000 + port_offset

    def _load_config(self) -> Dict[str, Any]:
        """Load project configuration"""
        config_path = Path(os.getcwd()) / '.ipc_project.yml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except:
                pass
        return {}

    def format_instance_name(self, base_name: str) -> str:
        """Add project namespace to instance name"""
        if '@' not in base_name:
            return f"{base_name}@{self.project_id}"
        return base_name

    def parse_instance_name(self, full_name: str) -> tuple[str, str]:
        """Parse instance name into base and project"""
        if '@' in full_name:
            parts = full_name.split('@', 1)
            return parts[0], parts[1]
        return full_name, self.project_id

    def is_same_project(self, instance_name: str) -> bool:
        """Check if instance belongs to same project"""
        _, project = self.parse_instance_name(instance_name)
        return project == self.project_id

    def validate_message(self, from_instance: str, to_instance: str) -> tuple[bool, str]:
        """
        Validate if message is allowed between instances.
        Returns (allowed, reason)
        """
        # Parse project IDs
        from_base, from_project = self.parse_instance_name(from_instance)
        to_base, to_project = self.parse_instance_name(to_instance)

        # Check isolation mode
        isolation_mode = self.config.get('project', {}).get('isolation_mode', 'strict')

        if isolation_mode == 'disabled':
            return True, "Isolation disabled"

        # Same project always allowed
        if from_project == to_project == self.project_id:
            return True, "Same project"

        # Check if cross-project is allowed
        if isolation_mode == 'relaxed':
            permissions = self.config.get('permissions', {})
            if permissions.get('allow_cross_project', False):
                # Check trusted projects
                trusted = permissions.get('trusted_projects', [])
                if from_project in trusted or to_project in trusted:
                    return True, "Trusted project"

        # Default: reject cross-project
        return False, f"Cross-project communication blocked ({from_project} -> {to_project})"

    def enhance_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add project metadata to message"""
        message['project_id'] = self.project_id
        message['project_port'] = self.project_port
        return message

    def filter_instances(self, instances: Dict[str, Any]) -> Dict[str, Any]:
        """Filter instances to show only same-project ones"""
        isolation_mode = self.config.get('project', {}).get('isolation_mode', 'strict')

        if isolation_mode == 'disabled':
            return instances

        filtered = {}
        for name, info in instances.items():
            if self.is_same_project(name):
                filtered[name] = info

        return filtered

    def get_status(self) -> Dict[str, Any]:
        """Get project isolation status"""
        return {
            'project_id': self.project_id,
            'project_port': self.project_port,
            'isolation_mode': self.config.get('project', {}).get('isolation_mode', 'strict'),
            'allow_cross_project': self.config.get('permissions', {}).get('allow_cross_project', False),
            'trusted_projects': self.config.get('permissions', {}).get('trusted_projects', []),
        }


# Enhanced MessageBroker methods to add
def enhance_message_broker(broker_class):
    """
    Decorator to enhance MessageBroker with project isolation.
    Apply this to the existing MessageBroker class.
    """

    # Store original __init__
    original_init = broker_class.__init__

    def new_init(self, host: str, port: int):
        # Call original init
        original_init(self, host, port)
        # Add project isolation manager
        self.isolation_manager = ProjectIsolationManager()
        # Update port to project-specific port
        self.port = self.isolation_manager.project_port
        logger.info(f"🔒 Project Isolation Active: {self.isolation_manager.project_id} on port {self.port}")

    # Store original _process_request
    original_process = broker_class._process_request if hasattr(broker_class, '_process_request') else None

    def new_process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced request processing with project isolation"""
        # Add project validation for messages
        if request.get('action') == 'send':
            from_instance = request.get('from', 'unknown')
            to_instance = request.get('to', 'unknown')

            # Validate message is allowed
            allowed, reason = self.isolation_manager.validate_message(from_instance, to_instance)
            if not allowed:
                return {
                    'status': 'error',
                    'message': f'Project isolation: {reason}'
                }

            # Enhance message with project metadata
            if 'message_data' in request:
                request['message_data'] = self.isolation_manager.enhance_message(request['message_data'])

        # Add project namespace to registration
        elif request.get('action') == 'register':
            name = request.get('name', '')
            request['name'] = self.isolation_manager.format_instance_name(name)

        # Filter list results
        elif request.get('action') == 'list':
            if original_process:
                result = original_process(self, request)
                if result.get('status') == 'success' and 'instances' in result:
                    result['instances'] = self.isolation_manager.filter_instances(result['instances'])
                return result

        # Call original process method if exists
        if original_process:
            return original_process(self, request)

        return {'status': 'error', 'message': 'Original process method not found'}

    # Apply enhancements
    broker_class.__init__ = new_init
    broker_class._process_request = new_process_request

    # Add status method
    def get_isolation_status(self) -> Dict[str, Any]:
        return self.isolation_manager.get_status()

    broker_class.get_isolation_status = get_isolation_status

    return broker_class


# Test the isolation manager independently
if __name__ == '__main__':
    manager = ProjectIsolationManager()
    print("🔒 Project Isolation Status:")
    print(f"  Project ID: {manager.project_id}")
    print(f"  Project Port: {manager.project_port}")
    print(f"  Config: {manager.config}")

    # Test message validation
    test_cases = [
        ('claude@proj_abc123', 'gemini@proj_abc123'),  # Same project
        ('claude@proj_abc123', 'gemini@proj_xyz789'),  # Different projects
        ('claude', 'gemini'),  # No project specified
    ]

    print("\n📧 Message Validation Tests:")
    for from_inst, to_inst in test_cases:
        allowed, reason = manager.validate_message(from_inst, to_inst)
        status = "✅" if allowed else "❌"
        print(f"  {from_inst} -> {to_inst}: {status} ({reason})")