#!/usr/bin/env python3
"""
Standalone Broker Daemon for Claude IPC MCP
Designed to run independently and serve multiple AI CLIs simultaneously
"""

import asyncio
import json
import logging
import os
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import hashlib
import secrets
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # instance_id -> list of timestamps
        self.lock = threading.Lock()

    def is_allowed(self, instance_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        with self.lock:
            now = time.time()

            # Initialize if needed
            if instance_id not in self.requests:
                self.requests[instance_id] = []

            # Remove old requests outside window
            self.requests[instance_id] = [
                ts for ts in self.requests[instance_id]
                if now - ts < self.window_seconds
            ]

            # Check if under limit
            if len(self.requests[instance_id]) >= self.max_requests:
                return False

            # Record this request
            self.requests[instance_id].append(now)
            return True


class BrokerDaemon:
    """
    Standalone Message Broker Daemon
    - Runs independently of any MCP server
    - Serves multiple AI CLIs simultaneously
    - Handles proper Windows/Linux socket options
    - Provides robust lifecycle management
    """

    def __init__(self, host: str = None, port: int = None, project_root: Path = None):
        # Configuration from environment or defaults
        self.host = host or os.getenv("IPC_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("IPC_GLOBAL_PORT",
                                os.getenv("IPC_PORT", "9876")))

        # State management
        self.running = False
        self.server_socket = None
        self.server_thread = None
        self.shutdown_event = threading.Event()
        self.lock = threading.Lock()

        # Message queues and session management
        self.queues: Dict[str, List[Dict[str, Any]]] = {}
        self.instances: Dict[str, datetime] = {}

        # Name change tracking
        self.name_history: Dict[str, Tuple[str, datetime]] = {}  # old_name -> (new_name, when)
        self.last_rename: Dict[str, datetime] = {}  # instance_id -> last rename time

        # Session management for security
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_token -> {instance_id, created_at}
        self.instance_sessions: Dict[str, str] = {}  # instance_id -> session_token

        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

        # Project-local IPC paths
        # Import here to avoid circular imports
        from core.project_local import get_project_ipc_dir, get_project_database

        self.ipc_dir = get_project_ipc_dir(project_root)
        self.db_path = get_project_database()
        self.large_msg_dir = self.ipc_dir / "data" / "large-messages"
        self.pid_file = self.ipc_dir / "state" / "broker.pid"

        # Initialize database and directories
        self._init_persistence()
        self._load_from_database()

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _init_persistence(self):
        """Initialize persistence layer"""
        # Create directories - .ipc structure already created by project_local
        self.large_msg_dir.mkdir(parents=True, exist_ok=True)

        # Secure permissions on directories (Unix only)
        if platform.system() != "Windows":
            os.chmod(self.ipc_dir, 0o700)
            os.chmod(self.large_msg_dir, 0o700)

        # Initialize database (already created by project_local, but ensure schema)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    delivered INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Instances table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS instances (
                    instance_id TEXT PRIMARY KEY,
                    last_seen DATETIME NOT NULL,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_token_hash TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
                )
            """)

            # Name history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS name_history (
                    old_name TEXT PRIMARY KEY,
                    new_name TEXT NOT NULL,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_to_id ON messages(to_id, delivered)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_instance ON sessions(instance_id)")

            conn.commit()

    def _load_from_database(self):
        """Load state from database on startup"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load instances
                cursor = conn.execute("SELECT instance_id, last_seen FROM instances")
                for row in cursor:
                    self.instances[row[0]] = datetime.fromisoformat(row[1])

                # Load name history
                cursor = conn.execute("SELECT old_name, new_name, changed_at FROM name_history")
                for row in cursor:
                    self.name_history[row[0]] = (row[1], datetime.fromisoformat(row[2]))

                # Clean up expired sessions
                conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
                conn.commit()

                logger.info(f"Loaded {len(self.instances)} instances from database")
        except Exception as e:
            logger.error(f"Error loading from database: {e}")

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        if platform.system() != "Windows":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        else:
            # Windows: Use console control handler
            import ctypes
            kernel32 = ctypes.windll.kernel32

            def console_ctrl_handler(ctrl_type):
                self.stop()
                return True

            # Set console control handler
            CTRL_HANDLER = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint32)
            handler = CTRL_HANDLER(console_ctrl_handler)
            kernel32.SetConsoleCtrlHandler(handler, True)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()

    def _create_server_socket(self) -> socket.socket:
        """Create and configure server socket with platform-specific options"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Platform-specific socket options
        if platform.system() == "Windows":
            # Windows: Use SO_EXCLUSIVEADDRUSE to prevent port conflicts
            # This is more reliable than SO_REUSEADDR on Windows
            try:
                # SO_EXCLUSIVEADDRUSE = 0xfffffbfb (negative value)
                SO_EXCLUSIVEADDRUSE = -5
                sock.setsockopt(socket.SOL_SOCKET, SO_EXCLUSIVEADDRUSE, 1)
                logger.info("Windows: Set SO_EXCLUSIVEADDRUSE for exclusive port binding")
            except Exception as e:
                logger.warning(f"Could not set SO_EXCLUSIVEADDRUSE: {e}")
                # Fallback to SO_REUSEADDR
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            # Unix/Linux: Use SO_REUSEADDR safely
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Also set SO_REUSEPORT if available (Linux 3.9+)
            if hasattr(socket, 'SO_REUSEPORT'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Set socket to non-blocking mode for better control
        sock.setblocking(False)

        return sock

    def start(self, background: bool = True) -> bool:
        """Start the broker daemon"""
        with self.lock:
            if self.running:
                logger.warning("Broker is already running")
                return True

            try:
                # Check if another broker is already running
                if self._is_another_broker_running():
                    logger.error(f"Another broker is already running on port {self.port}")
                    return False

                # Create server socket
                self.server_socket = self._create_server_socket()

                # Bind to address
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(128)  # Increased backlog for multiple clients

                # Write PID file
                self.pid_file.write_text(str(os.getpid()))

                self.running = True
                self.shutdown_event.clear()

                logger.info(f"Broker daemon starting on {self.host}:{self.port}")

                if background:
                    # Start server thread
                    self.server_thread = threading.Thread(
                        target=self._run_server,
                        daemon=False  # Not a daemon thread, we want clean shutdown
                    )
                    self.server_thread.start()
                    logger.info("Broker daemon started in background")
                else:
                    # Run in foreground
                    self._run_server()

                return True

            except Exception as e:
                logger.error(f"Failed to start broker: {e}")
                self.running = False
                return False

    def _is_another_broker_running(self) -> bool:
        """Check if another broker is already running"""
        # Check PID file
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text())
                # Check if process is running
                if platform.system() == "Windows":
                    # Windows: Use tasklist
                    import subprocess
                    result = subprocess.run(
                        f'tasklist /FI "PID eq {pid}"',
                        shell=True, capture_output=True, text=True
                    )
                    if str(pid) in result.stdout:
                        # Try to connect to verify it's actually a broker
                        try:
                            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            test_sock.settimeout(1)
                            result = test_sock.connect_ex((self.host, self.port))
                            test_sock.close()
                            return result == 0
                        except:
                            pass
                else:
                    # Unix: Check if process exists
                    try:
                        os.kill(pid, 0)  # Signal 0 = check if process exists
                        # Try to connect to verify
                        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_sock.settimeout(1)
                        result = test_sock.connect_ex((self.host, self.port))
                        test_sock.close()
                        return result == 0
                    except OSError:
                        pass
            except:
                pass

        # Also try direct connection test
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(1)
            result = test_sock.connect_ex((self.host, self.port))
            test_sock.close()
            return result == 0
        except:
            return False

    def _run_server(self):
        """Main server loop"""
        logger.info(f"Broker daemon running on {self.host}:{self.port}")

        while self.running and not self.shutdown_event.is_set():
            try:
                # Use select for non-blocking accept with timeout
                import select
                readable, _, _ = select.select([self.server_socket], [], [], 1.0)

                if readable:
                    try:
                        client_socket, client_addr = self.server_socket.accept()
                        # Handle client in separate thread
                        client_thread = threading.Thread(
                            target=self._handle_client,
                            args=(client_socket, client_addr),
                            daemon=True
                        )
                        client_thread.start()
                    except BlockingIOError:
                        continue  # No connection ready yet
                    except Exception as e:
                        if self.running:  # Only log if we're not shutting down
                            logger.error(f"Error accepting connection: {e}")

            except Exception as e:
                if self.running:
                    logger.error(f"Server loop error: {e}")
                    time.sleep(1)

        logger.info("Broker daemon server loop ended")

    def _handle_client(self, client_socket: socket.socket, client_addr: tuple):
        """Handle a client connection"""
        try:
            client_socket.settimeout(30.0)  # 30 second timeout

            # Receive request
            data = client_socket.recv(65536)  # 64KB max
            if not data:
                return

            request = json.loads(data.decode())

            # Process request
            response = self._process_request(request)

            # Send response
            client_socket.send(json.dumps(response).encode())

        except socket.timeout:
            logger.warning(f"Client {client_addr} timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_addr}: {e}")
            try:
                client_socket.send(json.dumps({"error": "Invalid JSON"}).encode())
            except:
                pass
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a client request"""
        action = request.get("action")

        # Rate limiting (except for status)
        if action != "status":
            instance_id = request.get("instance_id")
            if instance_id and not self.rate_limiter.is_allowed(instance_id):
                return {"error": "Rate limit exceeded"}

        # Route to appropriate handler
        if action == "register":
            return self._handle_register(request)
        elif action == "send":
            return self._handle_send(request)
        elif action == "check":
            return self._handle_check(request)
        elif action == "status":
            return self._handle_status(request)
        elif action == "ping":
            return self._handle_ping(request)
        elif action == "rename":
            return self._handle_rename(request)
        elif action == "list_instances":
            return self._handle_list_instances(request)
        elif action == "broadcast":
            return self._handle_broadcast(request)
        elif action == "clear_messages":
            return self._handle_clear_messages(request)
        else:
            return {"error": f"Unknown action: {action}"}

    def _handle_register(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle instance registration"""
        instance_id = request.get("instance_id")
        if not instance_id:
            return {"error": "instance_id required"}

        # Validate instance_id format
        if not self._validate_instance_id(instance_id):
            return {"error": "Invalid instance_id format"}

        with self.lock:
            # Generate session token
            session_token = secrets.token_hex(32)
            session_hash = hashlib.sha256(session_token.encode()).hexdigest()

            # Store session
            expires_at = datetime.now() + timedelta(hours=24)
            self.sessions[session_token] = {
                "instance_id": instance_id,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }
            self.instance_sessions[instance_id] = session_token

            # Update instance tracking
            self.instances[instance_id] = datetime.now()

            # Initialize queue
            if instance_id not in self.queues:
                self.queues[instance_id] = []

            # Persist to database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Update instance with project_root
                    conn.execute(
                        "INSERT OR REPLACE INTO instances (instance_id, project_root, last_seen) VALUES (?, ?, ?)",
                        (instance_id, str(self.ipc_dir.parent), datetime.now().isoformat())
                    )

                    # Store session (created_at will use DEFAULT CURRENT_TIMESTAMP)
                    conn.execute(
                        "INSERT INTO sessions (session_token_hash, instance_id, created_at, expires_at) VALUES (?, ?, datetime('now'), ?)",
                        (session_hash, instance_id, expires_at.isoformat())
                    )

                    conn.commit()
            except Exception as e:
                logger.error(f"Database error during registration: {e}")

            logger.info(f"Registered instance: {instance_id}")
            return {
                "status": "ok",
                "session_token": session_token,
                "expires_at": expires_at.isoformat()
            }

    def _handle_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message sending"""
        session_token = request.get("session_token")
        if not session_token:
            return {"error": "session_token required"}

        # Validate session
        session_info = self.sessions.get(session_token)
        if not session_info:
            return {"error": "Invalid session"}

        if datetime.now() > session_info["expires_at"]:
            return {"error": "Session expired"}

        from_id = request.get("from_id")
        to_id = request.get("to_id")
        content = request.get("content")

        if not all([from_id, to_id, content]):
            return {"error": "from_id, to_id, and content required"}

        # Check session matches from_id
        if session_info["instance_id"] != from_id:
            return {"error": "Session mismatch"}

        with self.lock:
            # Handle name forwarding
            if to_id in self.name_history:
                new_name, _ = self.name_history[to_id]
                to_id = new_name
                logger.info(f"Forwarding message to renamed instance: {to_id}")

            # Store message
            if to_id not in self.queues:
                self.queues[to_id] = []

            message = {
                "from_id": from_id,
                "to_id": to_id,
                "content": content,
                "timestamp": time.time()
            }

            self.queues[to_id].append(message)

            # Persist to database
            try:
                # Handle large messages
                stored_content = content
                if isinstance(content, str) and len(content) > 10240:  # 10KB threshold
                    # Store in file
                    msg_file = self.large_msg_dir / f"{time.time()}_{from_id}_{to_id}.json"
                    msg_file.write_text(json.dumps(content))
                    stored_content = f"__LARGE_MESSAGE__:{msg_file.name}"

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO messages (from_id, to_id, content, timestamp) VALUES (?, ?, ?, ?)",
                        (from_id, to_id, stored_content, time.time())
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Database error during send: {e}")

            return {"status": "ok", "queued": len(self.queues[to_id])}

    def _handle_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message checking"""
        session_token = request.get("session_token")
        instance_id = request.get("instance_id")

        if not session_token or not instance_id:
            return {"error": "session_token and instance_id required"}

        # Validate session
        session_info = self.sessions.get(session_token)
        if not session_info:
            return {"error": "Invalid session"}

        if datetime.now() > session_info["expires_at"]:
            return {"error": "Session expired"}

        if session_info["instance_id"] != instance_id:
            return {"error": "Session mismatch"}

        with self.lock:
            # Get messages from memory
            messages = self.queues.get(instance_id, [])[:10]  # Max 10 messages at a time

            # Clear retrieved messages from memory queue
            if messages:
                self.queues[instance_id] = self.queues[instance_id][len(messages):]

            # Load any persisted messages from database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT id, from_id, to_id, content, timestamp FROM messages "
                        "WHERE to_id = ? AND delivered = 0 ORDER BY timestamp LIMIT 10",
                        (instance_id,)
                    )

                    db_messages = []
                    msg_ids = []

                    for row in cursor:
                        msg_id, from_id, to_id, content, timestamp = row

                        # Handle large messages
                        if content.startswith("__LARGE_MESSAGE__:"):
                            msg_file = self.large_msg_dir / content.split(":", 1)[1]
                            if msg_file.exists():
                                content = json.loads(msg_file.read_text())

                        db_messages.append({
                            "from_id": from_id,
                            "to_id": to_id,
                            "content": content,
                            "timestamp": timestamp
                        })
                        msg_ids.append(msg_id)

                    # Mark as delivered
                    if msg_ids:
                        placeholders = ",".join("?" * len(msg_ids))
                        conn.execute(
                            f"UPDATE messages SET delivered = 1 WHERE id IN ({placeholders})",
                            msg_ids
                        )
                        conn.commit()

                    # Combine with memory messages
                    messages = messages + db_messages

            except Exception as e:
                logger.error(f"Database error during check: {e}")

            return {"messages": messages}

    def _handle_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request"""
        with self.lock:
            return {
                "status": "ok",
                "instances": list(self.instances.keys()),
                "total_queued": sum(len(q) for q in self.queues.values()),
                "uptime": time.time(),
                "version": "2.0.0"
            }

    def _handle_ping(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "ok": True,
            "timestamp": time.time(),
            "rtt_ms": 0  # Calculated by client
        }

    def _handle_rename(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle instance rename"""
        session_token = request.get("session_token")
        old_name = request.get("old_name")
        new_name = request.get("new_name")

        if not all([session_token, old_name, new_name]):
            return {"error": "session_token, old_name, and new_name required"}

        # Validate session
        session_info = self.sessions.get(session_token)
        if not session_info:
            return {"error": "Invalid session"}

        if session_info["instance_id"] != old_name:
            return {"error": "Session mismatch"}

        # Rate limit renames (1 per hour)
        last_rename = self.last_rename.get(old_name)
        if last_rename and (datetime.now() - last_rename).total_seconds() < 3600:
            return {"error": "Rename rate limit (1 per hour)"}

        with self.lock:
            # Update tracking
            self.name_history[old_name] = (new_name, datetime.now())
            self.last_rename[new_name] = datetime.now()

            # Move queue
            if old_name in self.queues:
                self.queues[new_name] = self.queues.pop(old_name)

            # Update instance
            if old_name in self.instances:
                self.instances[new_name] = self.instances.pop(old_name)

            # Update session
            session_info["instance_id"] = new_name
            self.instance_sessions[new_name] = self.instance_sessions.pop(old_name, session_token)

            # Persist to database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Update instance
                    conn.execute(
                        "UPDATE instances SET instance_id = ? WHERE instance_id = ?",
                        (new_name, old_name)
                    )

                    # Update sessions
                    conn.execute(
                        "UPDATE sessions SET instance_id = ? WHERE instance_id = ?",
                        (new_name, old_name)
                    )

                    # Add to name history
                    conn.execute(
                        "INSERT OR REPLACE INTO name_history (old_name, new_name) VALUES (?, ?)",
                        (old_name, new_name)
                    )

                    conn.commit()
            except Exception as e:
                logger.error(f"Database error during rename: {e}")

            logger.info(f"Renamed instance: {old_name} -> {new_name}")
            return {"status": "ok", "old_name": old_name, "new_name": new_name}

    def _handle_list_instances(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list instances request"""
        with self.lock:
            instances_info = []
            for instance_id, last_seen in self.instances.items():
                instances_info.append({
                    "instance_id": instance_id,
                    "last_seen": last_seen.isoformat(),
                    "queue_size": len(self.queues.get(instance_id, []))
                })

            return {"instances": instances_info}

    def _handle_broadcast(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle broadcast message"""
        session_token = request.get("session_token")
        from_id = request.get("from_id")
        content = request.get("content")

        if not all([session_token, from_id, content]):
            return {"error": "session_token, from_id, and content required"}

        # Validate session
        session_info = self.sessions.get(session_token)
        if not session_info:
            return {"error": "Invalid session"}

        if session_info["instance_id"] != from_id:
            return {"error": "Session mismatch"}

        with self.lock:
            sent_to = []
            for instance_id in self.instances.keys():
                if instance_id != from_id:  # Don't send to self
                    if instance_id not in self.queues:
                        self.queues[instance_id] = []

                    message = {
                        "from_id": from_id,
                        "to_id": instance_id,
                        "content": f"[BROADCAST] {content}",
                        "timestamp": time.time()
                    }

                    self.queues[instance_id].append(message)
                    sent_to.append(instance_id)

                    # Persist to database
                    try:
                        with sqlite3.connect(self.db_path) as conn:
                            conn.execute(
                                "INSERT INTO messages (from_id, to_id, content, timestamp) VALUES (?, ?, ?, ?)",
                                (from_id, instance_id, f"[BROADCAST] {content}", time.time())
                            )
                    except:
                        pass

            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.commit()
            except:
                pass

            return {"status": "ok", "sent_to": sent_to}

    def _handle_clear_messages(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clear messages request"""
        session_token = request.get("session_token")
        instance_id = request.get("instance_id")

        if not all([session_token, instance_id]):
            return {"error": "session_token and instance_id required"}

        # Validate session
        session_info = self.sessions.get(session_token)
        if not session_info:
            return {"error": "Invalid session"}

        if session_info["instance_id"] != instance_id:
            return {"error": "Session mismatch"}

        with self.lock:
            # Clear memory queue
            cleared = len(self.queues.get(instance_id, []))
            self.queues[instance_id] = []

            # Clear database messages
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "DELETE FROM messages WHERE to_id = ?",
                        (instance_id,)
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Database error during clear: {e}")

            return {"status": "ok", "cleared": cleared}

    def _validate_instance_id(self, instance_id: str) -> bool:
        """Validate instance ID format"""
        import re
        # Allow alphanumeric, dash, underscore, 1-32 chars
        return bool(re.match(r'^[a-zA-Z0-9_-]{1,32}$', instance_id))

    def stop(self):
        """Stop the broker daemon gracefully"""
        logger.info("Stopping broker daemon...")

        with self.lock:
            self.running = False
            self.shutdown_event.set()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)

        # Clean up PID file
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except:
            pass

        logger.info("Broker daemon stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def main():
    """Main entry point for standalone broker daemon"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude IPC MCP Broker Daemon")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--project-root", type=str, default=None, help="Project root directory")

    args = parser.parse_args()

    # Convert project_root string to Path if provided
    project_root = Path(args.project_root) if args.project_root else None

    # Get project IPC directory for logging
    from core.project_local import get_project_ipc_dir
    ipc_dir = get_project_ipc_dir(project_root)
    log_file = ipc_dir / "logs" / "broker.log"

    # Configure logging to file in .ipc/logs/
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )

    # Create and start broker
    broker = BrokerDaemon(host=args.host, port=args.port, project_root=project_root)

    try:
        if broker.start(background=not args.foreground):
            if args.foreground:
                # Keep running until interrupted
                try:
                    while broker.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                logger.info("Broker daemon started in background")
                # Keep main thread alive while broker runs in background
                try:
                    while broker.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
        else:
            logger.error("Failed to start broker daemon")
            sys.exit(1)
    finally:
        broker.stop()


if __name__ == "__main__":
    main()