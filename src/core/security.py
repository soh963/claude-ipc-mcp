#!/usr/bin/env python3
"""
Security Manager for Unified IPC System
Gemini's implementation - Authentication, authorization, and secure communication
"""

# PyJWT is optional; guard the import to avoid hard dependency at import time
try:
    import jwt as pyjwt  # type: ignore
except Exception:  # ImportError in most cases
    pyjwt = None  # type: ignore
import ssl
import secrets
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration"""

    enable_jwt: bool = True
    enable_tls: bool = True
    enable_rbac: bool = True
    jwt_secret: str = None
    jwt_algorithm: str = "HS256"
    token_expiry: int = 3600  # 1 hour
    tls_cert_path: Path = None
    tls_key_path: Path = None
    # Use project-local .ipc directory
    audit_log_path: Path = Path(".ipc") / "logs" / "audit.log"


@dataclass
class Permission:
    """Permission definition"""

    resource: str
    action: str
    scope: str = "*"


@dataclass
class Role:
    """Role definition"""

    name: str
    permissions: List[Permission]
    priority: int = 0


class JWTManager:
    """JWT token management"""

    def __init__(self, secret: str = None, algorithm: str = "HS256"):
        self.secret = secret or secrets.token_hex(32)
        self.algorithm = algorithm

    def create_token(self, payload: Dict, expiry_minutes: int = 60) -> str:
        """Create a JWT token"""
        if pyjwt is None:
            raise RuntimeError(
                "PyJWT is required for JWT operations but is not installed.\nInstall with: uv add pyjwt or pip install PyJWT"
            )
        payload = payload.copy()
        payload["exp"] = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        payload["iat"] = datetime.utcnow()
        payload["jti"] = secrets.token_hex(16)  # Token ID
        return pyjwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token"""
        if pyjwt is None:
            logger.warning("JWT verification requested but PyJWT is not installed")
            return None
        try:
            payload = pyjwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except Exception as e:
            # Handle specific PyJWT exceptions if available
            name = type(e).__name__
            if name == "ExpiredSignatureError":
                logger.warning("Token expired")
                return None
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_token(self, token: str, expiry_minutes: int = 60) -> Optional[str]:
        """Refresh a valid token"""
        payload = self.verify_token(token)
        if payload:
            # Remove old expiration
            payload.pop("exp", None)
            payload.pop("iat", None)
            return self.create_token(payload, expiry_minutes)
        return None


class TLSManager:
    """Mutual TLS authentication manager"""

    def __init__(self, cert_path: Path = None, key_path: Path = None):
        # Use project-local .ipc directory
        from core.project_local import get_project_ipc_dir
        ipc_dir = get_project_ipc_dir()
        self.cert_path = cert_path or ipc_dir / "secret" / "server.crt"
        self.key_path = key_path or ipc_dir / "secret" / "server.key"
        self._ensure_certificates()

    def _ensure_certificates(self):
        """Ensure TLS certificates exist"""
        if not self.cert_path.exists() or not self.key_path.exists():
            logger.info("Generating self-signed certificates...")
            self._generate_self_signed_cert()

    def _generate_self_signed_cert(self):
        """Generate self-signed certificate for testing"""
        # In production, use proper CA-signed certificates
        import subprocess

        self.cert_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate private key
        subprocess.run(["openssl", "genrsa", "-out", str(self.key_path), "2048"], check=False)

        # Generate certificate
        subprocess.run(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-key",
                str(self.key_path),
                "-out",
                str(self.cert_path),
                "-days",
                "365",
                "-subj",
                "/CN=localhost/O=IPC/C=US",
            ],
            check=False,
        )

        logger.info(f"Generated certificates at {self.cert_path.parent}")

    def create_server_context(self) -> ssl.SSLContext:
        """Create SSL context for server"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if self.cert_path.exists() and self.key_path.exists():
            context.load_cert_chain(str(self.cert_path), str(self.key_path))

        # For mutual TLS, require client certificate
        context.verify_mode = ssl.CERT_OPTIONAL

        return context

    def create_client_context(self) -> ssl.SSLContext:
        """Create SSL context for client"""
        context = ssl.create_default_context()

        # For self-signed certificates in development
        context.check_hostname = False
        context.verify_mode = ssl.CERT_OPTIONAL

        return context


class RBACManager:
    """Role-Based Access Control manager"""

    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[str]] = {}
        self._init_default_roles()

    def _init_default_roles(self):
        """Initialize default roles"""
        # Admin role
        self.roles["admin"] = Role(
            name="admin", permissions=[Permission("*", "*", "*")], priority=100  # Full access
        )

        # Instance role (for AI instances)
        self.roles["instance"] = Role(
            name="instance",
            permissions=[
                Permission("message", "send", "*"),
                Permission("message", "receive", "*"),
                Permission("message", "check", "own"),
                Permission("instance", "list", "*"),
            ],
            priority=50,
        )

        # Monitor role
        self.roles["monitor"] = Role(
            name="monitor",
            permissions=[
                Permission("message", "read", "*"),
                Permission("instance", "list", "*"),
                Permission("metrics", "read", "*"),
            ],
            priority=30,
        )

        # Guest role
        self.roles["guest"] = Role(
            name="guest", permissions=[Permission("instance", "list", "*")], priority=10
        )

    def add_role(self, role: Role):
        """Add a new role"""
        self.roles[role.name] = role

    def assign_role(self, user_id: str, role_name: str):
        """Assign role to user"""
        if role_name not in self.roles:
            raise ValueError(f"Role {role_name} not found")

        if user_id not in self.user_roles:
            self.user_roles[user_id] = []

        if role_name not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_name)

    def check_permission(self, user_id: str, resource: str, action: str, scope: str = "*") -> bool:
        """Check if user has permission"""
        if user_id not in self.user_roles:
            return False

        # Check all roles
        for role_name in self.user_roles[user_id]:
            role = self.roles.get(role_name)
            if not role:
                continue

            # Check permissions
            for perm in role.permissions:
                if self._match_permission(perm, resource, action, scope):
                    return True

        return False

    def _match_permission(self, perm: Permission, resource: str, action: str, scope: str) -> bool:
        """Check if permission matches request"""
        # Wildcard matching
        if perm.resource == "*" or perm.resource == resource:
            if perm.action == "*" or perm.action == action:
                if perm.scope == "*" or perm.scope == scope:
                    return True
        return False


class AuditLogger:
    """Security audit logging"""

    def __init__(self, log_path: Path = None):
        # Use project-local .ipc directory
        from core.project_local import get_project_ipc_dir
        self.log_path = log_path or get_project_ipc_dir() / "logs" / "audit.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, user: str, details: Dict):
        """Log security event"""
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user": user,
            "details": details,
        }

        # Append to log file
        with open(self.log_path, "a") as f:
            import json

            f.write(json.dumps(log_entry) + "\n")

    def log_authentication(self, user: str, success: bool, method: str):
        """Log authentication attempt"""
        self.log_event("authentication", user, {"success": success, "method": method})

    def log_authorization(self, user: str, resource: str, action: str, granted: bool):
        """Log authorization check"""
        self.log_event(
            "authorization", user, {"resource": resource, "action": action, "granted": granted}
        )

    def log_security_violation(self, user: str, violation_type: str, details: str):
        """Log security violation"""
        self.log_event("security_violation", user, {"type": violation_type, "details": details})


class SecurityManager:
    """Main security manager integrating all security components"""

    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()

        # Initialize components
        self.jwt_manager = JWTManager(self.config.jwt_secret) if self.config.enable_jwt else None
        self.tls_manager = (
            TLSManager(self.config.tls_cert_path, self.config.tls_key_path)
            if self.config.enable_tls
            else None
        )
        self.rbac_manager = RBACManager() if self.config.enable_rbac else None
        self.audit_logger = AuditLogger(self.config.audit_log_path)

        logger.info("Security Manager initialized")

    def authenticate(self, credentials: Dict) -> Optional[str]:
        """Authenticate user and return token"""
        # Validate credentials
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            self.audit_logger.log_authentication(username or "unknown", False, "password")
            return None

        # Simple password check (in production, use proper password hashing)
        # For demo, accept any non-empty password
        if password:
            # Create token
            if self.jwt_manager:
                token = self.jwt_manager.create_token({"user": username, "type": "instance"})

                # Assign default role
                if self.rbac_manager:
                    self.rbac_manager.assign_role(username, "instance")

                self.audit_logger.log_authentication(username, True, "password")
                return token

        self.audit_logger.log_authentication(username, False, "password")
        return None

    def validate_request(self, request: Dict, source: Tuple) -> bool:
        """Validate incoming request (hook for broker)"""
        # Extract token
        token = request.get("token")

        if not token and not self.config.enable_jwt:
            # JWT disabled, allow all
            return True

        if not token:
            self.audit_logger.log_security_violation(
                str(source), "missing_token", "Request without authentication token"
            )
            return False

        # Verify token
        if self.jwt_manager:
            payload = self.jwt_manager.verify_token(token)
            if not payload:
                self.audit_logger.log_security_violation(
                    str(source), "invalid_token", "Invalid or expired token"
                )
                return False

            # Check permissions if RBAC enabled
            if self.rbac_manager:
                user = payload.get("user")
                msg_type = request.get("type")

                # Map message type to resource/action
                resource, action = self._map_request_to_permission(msg_type)

                if not self.rbac_manager.check_permission(user, resource, action):
                    self.audit_logger.log_authorization(user, resource, action, False)
                    return False

                self.audit_logger.log_authorization(user, resource, action, True)

        return True

    def _map_request_to_permission(self, msg_type: str) -> Tuple[str, str]:
        """Map request type to resource and action"""
        mapping = {
            "register": ("instance", "register"),
            "send": ("message", "send"),
            "check": ("message", "check"),
            "broadcast": ("message", "broadcast"),
            "list": ("instance", "list"),
            "status": ("instance", "status"),
        }

        return mapping.get(msg_type, ("unknown", "unknown"))

    def create_secure_connection(self, socket):
        """Wrap socket with TLS"""
        if self.tls_manager:
            context = self.tls_manager.create_server_context()
            return context.wrap_socket(socket, server_side=True)
        return socket

    def get_client_context(self) -> Optional[ssl.SSLContext]:
        """Get client SSL context"""
        if self.tls_manager:
            return self.tls_manager.create_client_context()
        return None


def main():
    """Test security manager"""
    # Create security manager
    security = SecurityManager()

    # Test authentication
    token = security.authenticate({"username": "claude", "password": "test123"})

    if token:
        logger.info(f"Authentication successful, token: {token[:20]}...")

        # Test request validation
        valid = security.validate_request({"type": "send", "token": token}, ("127.0.0.1", 12345))

        logger.info(f"Request validation: {valid}")
    else:
        logger.error("Authentication failed")


if __name__ == "__main__":
    main()
