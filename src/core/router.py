#!/usr/bin/env python3
"""
Global Message Router for AI CLI Communication

Supports three modes:
1. Global Mode - All projects can communicate
2. Project Mode - Only same project communication
3. Hybrid Mode - Selective cross-project communication
"""

import os
import json
import hashlib
import socket
import threading
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommunicationMode(Enum):
    """Communication modes for the router"""
    GLOBAL = "global"
    PROJECT = "project"
    HYBRID = "hybrid"


@dataclass
class RouteConfig:
    """Configuration for routing"""
    mode: CommunicationMode
    global_port: int = 9876
    project_port_range: tuple = (9000, 9999)
    allowed_projects: List[str] = None
    enable_tls: bool = False
    enable_audit: bool = True


class ProjectIdentifier:
    """Handles project identification and hashing"""

    @staticmethod
    def get_project_id(path: str = None) -> str:
        """Generate project ID from path"""
        if path is None:
            path = os.getcwd()

        # Normalize path
        path = os.path.abspath(path).replace('\\', '/').lower()

        # Generate hash
        hash_obj = hashlib.sha256(path.encode())
        return f"proj_{hash_obj.hexdigest()[:8]}"

    @staticmethod
    def get_project_port(project_id: str) -> int:
        """Generate unique port for project"""
        hash_obj = hashlib.md5(project_id.encode())
        port_offset = int(hash_obj.hexdigest()[:4], 16) % 1000
        return 9000 + port_offset


class RoutingTable:
    """Manages routing information for messages"""

    def __init__(self):
        self.routes: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def add_route(self, instance_id: str, project_id: str, address: tuple):
        """Add a route to the table"""
        with self.lock:
            self.routes[instance_id] = {
                'project_id': project_id,
                'address': address,
                'last_seen': time.time()
            }

    def get_route(self, instance_id: str) -> Optional[Dict]:
        """Get route information for an instance"""
        with self.lock:
            return self.routes.get(instance_id)

    def get_project_instances(self, project_id: str) -> List[str]:
        """Get all instances in a project"""
        with self.lock:
            return [
                inst_id for inst_id, info in self.routes.items()
                if info['project_id'] == project_id
            ]

    def cleanup_stale_routes(self, timeout: int = 300):
        """Remove routes older than timeout"""
        with self.lock:
            current_time = time.time()
            stale = [
                inst_id for inst_id, info in self.routes.items()
                if current_time - info['last_seen'] > timeout
            ]
            for inst_id in stale:
                del self.routes[inst_id]


class MessageBroker:
    """Individual message broker for handling messages"""

    def __init__(self, port: int, project_id: str = None):
        self.port = port
        self.project_id = project_id
        self.socket = None
        self.running = False
        self.clients = {}
        self.lock = threading.Lock()

    def start(self):
        """Start the broker"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('127.0.0.1', self.port))
        self.socket.listen(5)
        self.running = True

        logger.info(f"Broker started on port {self.port} (Project: {self.project_id})")

        # Start accepting connections in a thread
        threading.Thread(target=self._accept_connections, daemon=True).start()

    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client, addr = self.socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, client: socket.socket, addr: tuple):
        """Handle a client connection"""
        try:
            data = client.recv(4096)
            if data:
                request = json.loads(data.decode())
                response = self.process_message(request)
                client.send(json.dumps(response).encode())
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client.close()

    def process_message(self, message: Dict) -> Dict:
        """Process a message"""
        # Basic message processing
        msg_type = message.get('type')

        if msg_type == 'register':
            return self._handle_register(message)
        elif msg_type == 'send':
            return self._handle_send(message)
        elif msg_type == 'check':
            return self._handle_check(message)
        else:
            return {'status': 'error', 'message': 'Unknown message type'}

    def _handle_register(self, message: Dict) -> Dict:
        """Handle registration"""
        instance_id = message.get('instance_id')
        with self.lock:
            self.clients[instance_id] = {
                'registered': time.time(),
                'messages': []
            }
        return {'status': 'ok', 'message': f'Registered {instance_id}'}

    def _handle_send(self, message: Dict) -> Dict:
        """Handle send message"""
        to_id = message.get('to_id')
        from_id = message.get('from_id')
        content = message.get('content')

        with self.lock:
            if to_id in self.clients:
                self.clients[to_id]['messages'].append({
                    'from': from_id,
                    'content': content,
                    'timestamp': time.time()
                })
                return {'status': 'ok', 'message': 'Message sent'}
            else:
                return {'status': 'error', 'message': 'Recipient not found'}

    def _handle_check(self, message: Dict) -> Dict:
        """Handle check messages"""
        instance_id = message.get('instance_id')
        with self.lock:
            if instance_id in self.clients:
                messages = self.clients[instance_id]['messages']
                self.clients[instance_id]['messages'] = []
                return {'status': 'ok', 'messages': messages}
            else:
                return {'status': 'error', 'message': 'Not registered'}

    def stop(self):
        """Stop the broker"""
        self.running = False
        if self.socket:
            self.socket.close()


class GlobalMessageRouter:
    """Main router for handling global/project/hybrid communication"""

    def __init__(self, config: RouteConfig):
        self.config = config
        self.routing_table = RoutingTable()
        self.global_broker = None
        self.project_brokers: Dict[str, MessageBroker] = {}
        self.lock = threading.Lock()
        self.audit_log = []

    def start(self):
        """Start the router based on configuration"""
        logger.info(f"Starting router in {self.config.mode.value} mode")

        if self.config.mode in [CommunicationMode.GLOBAL, CommunicationMode.HYBRID]:
            # Start global broker
            self.global_broker = MessageBroker(
                self.config.global_port,
                project_id="GLOBAL"
            )
            self.global_broker.start()

        if self.config.mode in [CommunicationMode.PROJECT, CommunicationMode.HYBRID]:
            # Start project broker for current project
            project_id = ProjectIdentifier.get_project_id()
            self._get_or_create_project_broker(project_id)

        # Start cleanup thread
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def _get_or_create_project_broker(self, project_id: str) -> MessageBroker:
        """Get or create a project broker"""
        with self.lock:
            if project_id not in self.project_brokers:
                port = ProjectIdentifier.get_project_port(project_id)
                broker = MessageBroker(port, project_id)
                broker.start()
                self.project_brokers[project_id] = broker
            return self.project_brokers[project_id]

    def route_message(self, message: Dict) -> Dict:
        """Route a message based on scope and permissions"""
        scope = message.get('scope', 'project')

        # Audit logging
        if self.config.enable_audit:
            self._audit_log(message)

        # Route based on scope
        if scope == 'global':
            if self.config.mode == CommunicationMode.PROJECT:
                return {'status': 'error', 'message': 'Global communication disabled'}
            return self._route_global(message)

        elif scope == 'project':
            return self._route_project(message)

        elif scope == 'cross':
            if self.config.mode != CommunicationMode.HYBRID:
                return {'status': 'error', 'message': 'Cross-project communication disabled'}
            return self._route_cross_project(message)

        else:
            return {'status': 'error', 'message': 'Invalid scope'}

    def _route_global(self, message: Dict) -> Dict:
        """Route to global broker"""
        if self.global_broker:
            return self.global_broker.process_message(message)
        return {'status': 'error', 'message': 'Global broker not available'}

    def _route_project(self, message: Dict) -> Dict:
        """Route to project broker"""
        project_id = message.get('project_id', ProjectIdentifier.get_project_id())
        broker = self._get_or_create_project_broker(project_id)
        return broker.process_message(message)

    def _route_cross_project(self, message: Dict) -> Dict:
        """Route cross-project with permission check"""
        target_project = message.get('target_project')

        # Check if target project is allowed
        if self.config.allowed_projects:
            if target_project not in self.config.allowed_projects:
                return {'status': 'error', 'message': 'Target project not allowed'}

        # Route to target project broker
        broker = self._get_or_create_project_broker(target_project)
        return broker.process_message(message)

    def _audit_log(self, message: Dict):
        """Log message for audit"""
        log_entry = {
            'timestamp': time.time(),
            'scope': message.get('scope'),
            'from': message.get('from_id'),
            'to': message.get('to_id'),
            'project': message.get('project_id')
        }
        self.audit_log.append(log_entry)

        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

    def _cleanup_loop(self):
        """Cleanup stale routes periodically"""
        while True:
            time.sleep(60)  # Run every minute
            self.routing_table.cleanup_stale_routes()

    def stop(self):
        """Stop all brokers"""
        if self.global_broker:
            self.global_broker.stop()

        for broker in self.project_brokers.values():
            broker.stop()

    def get_status(self) -> Dict:
        """Get router status"""
        return {
            'mode': self.config.mode.value,
            'global_broker': 'running' if self.global_broker else 'stopped',
            'project_brokers': len(self.project_brokers),
            'routes': len(self.routing_table.routes),
            'audit_entries': len(self.audit_log)
        }


def create_router_from_env() -> GlobalMessageRouter:
    """Create router based on environment variables"""
    mode_str = os.getenv('IPC_GLOBAL_MODE', 'false').lower()
    hybrid_str = os.getenv('IPC_HYBRID_MODE', 'false').lower()

    if hybrid_str == 'true':
        mode = CommunicationMode.HYBRID
    elif mode_str == 'true':
        mode = CommunicationMode.GLOBAL
    else:
        mode = CommunicationMode.PROJECT

    # Parse allowed projects
    allowed_projects = None
    if mode == CommunicationMode.HYBRID:
        projects_str = os.getenv('IPC_ALLOWED_PROJECTS', '')
        if projects_str:
            allowed_projects = projects_str.split(',')

    config = RouteConfig(
        mode=mode,
        global_port=int(os.getenv('IPC_GLOBAL_PORT', '9876')),
        allowed_projects=allowed_projects,
        enable_audit=os.getenv('IPC_ENABLE_AUDIT', 'true').lower() == 'true'
    )

    return GlobalMessageRouter(config)


if __name__ == "__main__":
    # Test the router
    import sys

    # Create router from environment
    router = create_router_from_env()

    try:
        # Start router
        router.start()
        logger.info("Router started successfully")
        logger.info(f"Status: {router.get_status()}")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        router.stop()
        sys.exit(0)