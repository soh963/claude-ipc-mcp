#!/usr/bin/env python3
"""
Global IPC Server - Cross-project AI communication hub
"""

import asyncio
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import jwt
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GlobalIPCServer')


class ProjectConfig:
    """Project configuration"""
    def __init__(self, project_id: str, name: str, visibility: str = "project"):
        self.id = project_id
        self.name = name
        self.visibility = visibility  # project | global | selective
        self.allowed_from: List[str] = []
        self.allowed_to: List[str] = []
        self.created_at = datetime.now()


class InstanceInfo:
    """AI instance information"""
    def __init__(self, name: str, project_id: str, visibility: str = "project"):
        self.name = name
        self.project_id = project_id
        self.visibility = visibility
        self.registered_at = datetime.now()
        self.last_seen = datetime.now()
        self.full_id = f"{name}@project:{project_id}"


class GlobalIPCServer:
    """Global IPC Server for cross-project communication"""

    def __init__(self, port: int = 9876):
        self.port = port
        self.config_path = Path.home() / '.global-ipc'
        self.config_path.mkdir(exist_ok=True)

        # In-memory storage
        self.projects: Dict[str, ProjectConfig] = {}
        self.instances: Dict[str, InstanceInfo] = {}
        self.message_queues: Dict[str, List[dict]] = {}

        # Security
        self.jwt_secret = self.load_or_create_secret()

        # Database
        self.db_path = self.config_path / 'global_ipc.db'
        self.init_database()

        # Performance
        self.route_cache: Dict[str, str] = {}
        self.cache_ttl = 300  # 5 minutes

    def load_or_create_secret(self) -> str:
        """Load or create JWT secret"""
        secret_file = self.config_path / 'jwt_secret.key'

        if secret_file.exists():
            return secret_file.read_text().strip()

        import secrets
        secret = secrets.token_hex(32)
        secret_file.write_text(secret)
        return secret

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                visibility TEXT DEFAULT 'project',
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instances (
                name TEXT,
                project_id TEXT,
                visibility TEXT DEFAULT 'project',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                PRIMARY KEY (name, project_id)
            )
        ''')

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_instance TEXT,
                to_instance TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0
            )
        ''')

        # Cross-project permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                from_project TEXT,
                to_project TEXT,
                allowed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_project, to_project)
            )
        ''')

        conn.commit()
        conn.close()

    async def start(self):
        """Start the global IPC server"""
        server = await asyncio.start_server(
            self.handle_client,
            'localhost',
            self.port
        )

        logger.info(f"🌐 Global IPC Server started on port {self.port}")
        logger.info(f"📁 Configuration directory: {self.config_path}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connections"""
        addr = writer.get_extra_info('peername')
        logger.debug(f"New connection from {addr}")

        try:
            # Read request
            data = await reader.read(65536)
            if not data:
                return

            request = json.loads(data.decode('utf-8'))
            logger.debug(f"Request: {request.get('type')} from {request.get('from', 'unknown')}")

            # Process request
            response = await self.process_request(request)

            # Send response
            response_data = json.dumps(response).encode('utf-8')
            writer.write(response_data)
            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling client: {e}")
            error_response = {'status': 'error', 'message': str(e)}
            writer.write(json.dumps(error_response).encode('utf-8'))
            await writer.drain()

        finally:
            writer.close()
            await writer.wait_closed()

    async def process_request(self, request: dict) -> dict:
        """Process incoming request"""
        request_type = request.get('type')

        handlers = {
            'register': self.handle_registration,
            'send': self.handle_message,
            'check': self.handle_check,
            'list': self.handle_list,
            'permission': self.handle_permission,
            'status': self.handle_status
        }

        handler = handlers.get(request_type)
        if not handler:
            return {'status': 'error', 'message': f'Unknown request type: {request_type}'}

        return await handler(request)

    async def handle_registration(self, request: dict) -> dict:
        """Handle instance registration"""
        name = request.get('name')
        project = request.get('project', 'default')
        project_hash = hashlib.sha256(project.encode()).hexdigest()[:8]
        visibility = request.get('visibility', 'project')

        # Create or update project
        if project_hash not in self.projects:
            self.projects[project_hash] = ProjectConfig(project_hash, project, visibility)
            self.save_project(project_hash)

        # Register instance
        instance_key = f"{name}@{project_hash}"
        self.instances[instance_key] = InstanceInfo(name, project_hash, visibility)

        # Save to database
        self.save_instance(name, project_hash, visibility)

        # Generate JWT token
        token_payload = {
            'name': name,
            'project': project_hash,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, self.jwt_secret, algorithm='HS256')

        logger.info(f"✅ Registered: {name} from project {project} ({project_hash})")

        return {
            'status': 'ok',
            'instance_id': instance_key,
            'project_id': project_hash,
            'token': token
        }

    async def handle_message(self, request: dict) -> dict:
        """Handle message sending"""
        from_id = request.get('from')
        to_id = request.get('to')
        message = request.get('message')
        project = request.get('project')
        require_auth = request.get('require_auth', True)

        # Resolve recipient
        resolved_to = self.resolve_recipient(to_id, project)

        if not resolved_to:
            return {'status': 'error', 'message': f'Recipient not found: {to_id}'}

        # Check permissions if cross-project
        from_project = self.get_project_from_instance(from_id)
        to_project = self.get_project_from_instance(resolved_to)

        if from_project != to_project and require_auth:
            if not self.check_permission(from_project, to_project):
                return {'status': 'error', 'message': 'Cross-project permission denied'}

        # Queue message
        if resolved_to not in self.message_queues:
            self.message_queues[resolved_to] = []

        self.message_queues[resolved_to].append({
            'from': from_id,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'cross_project': from_project != to_project
        })

        # Save to database
        self.save_message(from_id, resolved_to, message)

        logger.info(f"📨 Message: {from_id} → {resolved_to} {'(cross-project)' if from_project != to_project else ''}")

        return {
            'status': 'ok',
            'delivered_to': resolved_to,
            'cross_project': from_project != to_project
        }

    async def handle_check(self, request: dict) -> dict:
        """Handle message checking"""
        instance_id = request.get('instance')

        if instance_id not in self.message_queues:
            return {'status': 'ok', 'messages': []}

        messages = self.message_queues[instance_id]
        self.message_queues[instance_id] = []

        return {'status': 'ok', 'messages': messages, 'count': len(messages)}

    async def handle_list(self, request: dict) -> dict:
        """List active instances"""
        project_filter = request.get('project')
        include_global = request.get('include_global', False)

        instances = []
        for key, info in self.instances.items():
            # Filter by project if specified
            if project_filter and info.project_id != project_filter:
                if not include_global or info.visibility != 'global':
                    continue

            instances.append({
                'name': info.name,
                'project': info.project_id,
                'visibility': info.visibility,
                'registered_at': info.registered_at.isoformat()
            })

        return {'status': 'ok', 'instances': instances}

    async def handle_permission(self, request: dict) -> dict:
        """Handle permission management"""
        action = request.get('action')  # grant | revoke | check
        from_project = request.get('from_project')
        to_project = request.get('to_project')

        if action == 'grant':
            self.grant_permission(from_project, to_project)
            return {'status': 'ok', 'message': 'Permission granted'}
        elif action == 'revoke':
            self.revoke_permission(from_project, to_project)
            return {'status': 'ok', 'message': 'Permission revoked'}
        elif action == 'check':
            allowed = self.check_permission(from_project, to_project)
            return {'status': 'ok', 'allowed': allowed}

        return {'status': 'error', 'message': 'Invalid action'}

    async def handle_status(self, request: dict) -> dict:
        """Handle server status request"""
        return {
            'status': 'ok',
            'server': 'GlobalIPCServer',
            'version': '1.0.0',
            'uptime': time.time(),
            'projects': len(self.projects),
            'instances': len(self.instances),
            'queued_messages': sum(len(q) for q in self.message_queues.values())
        }

    def resolve_recipient(self, to_id: str, from_project: str) -> Optional[str]:
        """Resolve recipient ID to actual instance"""
        # Explicit project specification
        if '@project:' in to_id:
            return to_id

        # Global specification
        if to_id.endswith('@global'):
            name = to_id.replace('@global', '')
            # Find global instance
            for key, info in self.instances.items():
                if info.name == name and info.visibility == 'global':
                    return key
            return None

        # Same project first
        from_project_hash = hashlib.sha256(from_project.encode()).hexdigest()[:8]
        local_key = f"{to_id}@{from_project_hash}"
        if local_key in self.instances:
            return local_key

        # Global search (with permission)
        for key, info in self.instances.items():
            if info.name == to_id and info.visibility in ['global', 'selective']:
                return key

        return None

    def get_project_from_instance(self, instance_id: str) -> str:
        """Get project ID from instance ID"""
        if '@' in instance_id:
            return instance_id.split('@')[-1].replace('project:', '')
        return 'default'

    def check_permission(self, from_project: str, to_project: str) -> bool:
        """Check cross-project permission"""
        if from_project == to_project:
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT allowed FROM permissions WHERE from_project = ? AND to_project = ?',
            (from_project, to_project)
        )

        result = cursor.fetchone()
        conn.close()

        return bool(result and result[0])

    def grant_permission(self, from_project: str, to_project: str):
        """Grant cross-project permission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT OR REPLACE INTO permissions (from_project, to_project, allowed) VALUES (?, ?, 1)',
            (from_project, to_project)
        )

        conn.commit()
        conn.close()

        logger.info(f"✅ Permission granted: {from_project} → {to_project}")

    def revoke_permission(self, from_project: str, to_project: str):
        """Revoke cross-project permission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE permissions SET allowed = 0 WHERE from_project = ? AND to_project = ?',
            (from_project, to_project)
        )

        conn.commit()
        conn.close()

        logger.info(f"❌ Permission revoked: {from_project} → {to_project}")

    def save_project(self, project_id: str):
        """Save project to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        project = self.projects[project_id]
        cursor.execute(
            'INSERT OR REPLACE INTO projects (id, name, visibility) VALUES (?, ?, ?)',
            (project_id, project.name, project.visibility)
        )

        conn.commit()
        conn.close()

    def save_instance(self, name: str, project_id: str, visibility: str):
        """Save instance to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT OR REPLACE INTO instances (name, project_id, visibility, last_seen) VALUES (?, ?, ?, ?)',
            (name, project_id, visibility, datetime.now())
        )

        conn.commit()
        conn.close()

    def save_message(self, from_id: str, to_id: str, message: str):
        """Save message to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO messages (from_instance, to_instance, message) VALUES (?, ?, ?)',
            (from_id, to_id, message)
        )

        conn.commit()
        conn.close()


async def main():
    """Main entry point"""
    server = GlobalIPCServer()
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")