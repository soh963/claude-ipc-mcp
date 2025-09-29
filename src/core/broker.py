#!/usr/bin/env python3
"""
Enhanced Message Broker for Unified IPC System
Claude's implementation - Coordinating with Gemini's security and Codex's async optimization
"""

import json
import socket
import threading
import time
import sqlite3
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BrokerConfig:
    """Configuration for message broker"""
    port: int = 9876
    host: str = '127.0.0.1'
    max_connections: int = 100
    message_timeout: int = 30
    db_path: Path = field(default_factory=lambda: Path.home() / '.claude-ipc-data' / 'broker.db')
    enable_security: bool = True
    enable_metrics: bool = True


@dataclass
class Message:
    """Message structure for IPC communication"""
    id: str
    from_id: str
    to_id: str
    content: Any
    timestamp: float
    scope: str = 'project'
    project_id: Optional[str] = None
    encrypted: bool = False

    def to_dict(self) -> Dict:
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'from_id': self.from_id,
            'to_id': self.to_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'scope': self.scope,
            'project_id': self.project_id,
            'encrypted': self.encrypted
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary"""
        return cls(**data)


class MessageQueue:
    """Thread-safe message queue with persistence"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for message persistence"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    scope TEXT DEFAULT 'project',
                    project_id TEXT,
                    encrypted INTEGER DEFAULT 0,
                    delivered INTEGER DEFAULT 0
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_to_id ON messages(to_id, delivered)
            ''')

    @contextmanager
    def _get_db(self):
        """Database connection context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add_message(self, message: Message):
        """Add message to queue"""
        with self.lock:
            with self._get_db() as conn:
                conn.execute('''
                    INSERT INTO messages
                    (id, from_id, to_id, content, timestamp, scope, project_id, encrypted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.id,
                    message.from_id,
                    message.to_id,
                    json.dumps(message.content) if not isinstance(message.content, str) else message.content,
                    message.timestamp,
                    message.scope,
                    message.project_id,
                    int(message.encrypted)
                ))

    def get_messages(self, instance_id: str, mark_delivered: bool = True) -> List[Message]:
        """Get messages for specific instance"""
        with self.lock:
            messages = []

            with self._get_db() as conn:
                rows = conn.execute('''
                    SELECT * FROM messages
                    WHERE to_id = ? AND delivered = 0
                    ORDER BY timestamp
                ''', (instance_id,))

                for row in rows:
                    content = row['content']
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass  # Keep as string

                    messages.append(Message(
                        id=row['id'],
                        from_id=row['from_id'],
                        to_id=row['to_id'],
                        content=content,
                        timestamp=row['timestamp'],
                        scope=row['scope'],
                        project_id=row['project_id'],
                        encrypted=bool(row['encrypted'])
                    ))

                if mark_delivered and messages:
                    msg_ids = [m.id for m in messages]
                    placeholders = ','.join(['?'] * len(msg_ids))
                    conn.execute(f'''
                        UPDATE messages
                        SET delivered = 1
                        WHERE id IN ({placeholders})
                    ''', msg_ids)

            return messages

    def cleanup_old_messages(self, max_age_seconds: int = 86400):
        """Remove old delivered messages"""
        with self.lock:
            with self._get_db() as conn:
                cutoff_time = time.time() - max_age_seconds
                conn.execute('''
                    DELETE FROM messages
                    WHERE delivered = 1 AND timestamp < ?
                ''', (cutoff_time,))


class MessageBroker:
    """Enhanced message broker with security and monitoring hooks"""

    def __init__(self, config: BrokerConfig):
        self.config = config
        self.queue = MessageQueue(config.db_path)
        self.socket = None
        self.running = False
        self.clients: Dict[str, Dict] = {}
        self.handlers: Dict[str, Callable] = {}
        self.lock = threading.Lock()

        # Hook points for Gemini's security and Codex's async optimization
        self.security_hook: Optional[Callable] = None
        self.async_hook: Optional[Callable] = None
        self.metrics_hook: Optional[Callable] = None

        self._register_handlers()

    def _register_handlers(self):
        """Register message handlers"""
        self.handlers = {
            'register': self._handle_register,
            'send': self._handle_send,
            'check': self._handle_check,
            'broadcast': self._handle_broadcast,
            'list': self._handle_list,
            'status': self._handle_status
        }

    def set_security_hook(self, hook: Callable):
        """Set security validation hook (for Gemini's implementation)"""
        self.security_hook = hook
        logger.info("Security hook registered")

    def set_async_hook(self, hook: Callable):
        """Set async processing hook (for Codex's implementation)"""
        self.async_hook = hook
        logger.info("Async hook registered")

    def set_metrics_hook(self, hook: Callable):
        """Set metrics collection hook (for monitoring)"""
        self.metrics_hook = hook
        logger.info("Metrics hook registered")

    def start(self):
        """Start the broker"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen(self.config.max_connections)
        self.running = True

        logger.info(f"Message broker started on {self.config.host}:{self.config.port}")

        # Start accept thread
        threading.Thread(target=self._accept_connections, daemon=True).start()

        # Start cleanup thread
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

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
        """Handle client connection"""
        try:
            data = client.recv(4096)
            if data:
                request = json.loads(data.decode())

                # Security hook (if set by Gemini)
                if self.security_hook and self.config.enable_security:
                    if not self.security_hook(request, addr):
                        response = {'status': 'error', 'message': 'Security validation failed'}
                        client.send(json.dumps(response).encode())
                        return

                # Process request
                response = self._process_request(request)

                # Metrics hook (if set)
                if self.metrics_hook and self.config.enable_metrics:
                    self.metrics_hook(request, response)

                client.send(json.dumps(response).encode())

        except Exception as e:
            logger.error(f"Error handling client: {e}")
            error_response = {'status': 'error', 'message': str(e)}
            try:
                client.send(json.dumps(error_response).encode())
            except Exception:
                pass
        finally:
            client.close()

    def _process_request(self, request: Dict) -> Dict:
        """Process incoming request"""
        msg_type = request.get('type')

        if msg_type not in self.handlers:
            return {'status': 'error', 'message': f'Unknown message type: {msg_type}'}

        # Async hook for optimization (if set by Codex)
        if self.async_hook:
            return self.async_hook(request, self.handlers[msg_type])
        else:
            return self.handlers[msg_type](request)

    def _handle_register(self, request: Dict) -> Dict:
        """Handle registration request"""
        instance_id = request.get('instance_id')
        project_id = request.get('project_id')

        with self.lock:
            self.clients[instance_id] = {
                'registered': time.time(),
                'project_id': project_id,
                'last_seen': time.time()
            }

        logger.info(f"Registered instance: {instance_id}")
        return {'status': 'ok', 'message': f'Registered {instance_id}'}

    def _handle_send(self, request: Dict) -> Dict:
        """Handle send message request"""
        try:
            message = Message(
                id=hashlib.sha256(f"{time.time()}_{request.get('from_id')}_{request.get('to_id')}".encode()).hexdigest()[:16],
                from_id=request.get('from_id'),
                to_id=request.get('to_id'),
                content=request.get('content'),
                timestamp=time.time(),
                scope=request.get('scope', 'project'),
                project_id=request.get('project_id')
            )

            self.queue.add_message(message)

            return {'status': 'ok', 'message': 'Message sent'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_check(self, request: Dict) -> Dict:
        """Handle check messages request"""
        instance_id = request.get('instance_id')

        messages = self.queue.get_messages(instance_id)

        if messages:
            return {
                'status': 'ok',
                'messages': [m.to_dict() for m in messages]
            }
        else:
            return {
                'status': 'ok',
                'messages': []
            }

    def _handle_broadcast(self, request: Dict) -> Dict:
        """Handle broadcast message"""
        from_id = request.get('from_id')
        content = request.get('content')

        with self.lock:
            recipients = list(self.clients.keys())

        for recipient in recipients:
            if recipient != from_id:
                message = Message(
                    id=hashlib.sha256(f"{time.time()}_{from_id}_{recipient}".encode()).hexdigest()[:16],
                    from_id=from_id,
                    to_id=recipient,
                    content=content,
                    timestamp=time.time(),
                    scope='broadcast'
                )
                self.queue.add_message(message)

        return {'status': 'ok', 'message': f'Broadcast to {len(recipients) - 1} instances'}

    def _handle_list(self, request: Dict) -> Dict:
        """Handle list instances request"""
        with self.lock:
            instances = [
                {
                    'id': instance_id,
                    'project_id': info.get('project_id'),
                    'registered': info.get('registered'),
                    'last_seen': info.get('last_seen')
                }
                for instance_id, info in self.clients.items()
            ]

        return {'status': 'ok', 'instances': instances}

    def _handle_status(self, request: Dict) -> Dict:
        """Handle status request"""
        with self.lock:
            status = {
                'running': self.running,
                'clients': len(self.clients),
                'config': {
                    'host': self.config.host,
                    'port': self.config.port,
                    'security': self.config.enable_security,
                    'metrics': self.config.enable_metrics
                },
                'hooks': {
                    'security': self.security_hook is not None,
                    'async': self.async_hook is not None,
                    'metrics': self.metrics_hook is not None
                }
            }

        return {'status': 'ok', 'broker_status': status}

    def _cleanup_loop(self):
        """Periodic cleanup of old messages and stale clients"""
        while self.running:
            time.sleep(300)  # Every 5 minutes

            # Cleanup old messages
            self.queue.cleanup_old_messages()

            # Cleanup stale clients
            with self.lock:
                current_time = time.time()
                stale_clients = [
                    client_id for client_id, info in self.clients.items()
                    if current_time - info.get('last_seen', 0) > 3600  # 1 hour
                ]
                for client_id in stale_clients:
                    del self.clients[client_id]
                    logger.info(f"Removed stale client: {client_id}")

    def stop(self):
        """Stop the broker"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Message broker stopped")


def main():
    """Main entry point for testing"""
    config = BrokerConfig()
    broker = MessageBroker(config)

    try:
        broker.start()
        logger.info("Broker is running. Press Ctrl+C to stop.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down broker...")
        broker.stop()


if __name__ == "__main__":
    main()