#!/usr/bin/env python3
"""
Project configuration loader for IPC isolation
Manages .ipc_project.yml configuration files
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.project_utils import get_project_id, get_project_port, get_project_name


def get_config_path() -> Path:
    """
    Get path to project configuration file.

    Returns:
        Path: Path to .ipc_project.yml in current directory
    """
    return Path(os.getcwd()) / ".ipc_project.yml"


def load_project_config() -> Dict[str, Any]:
    """
    Load project configuration from .ipc_project.yml file.
    Creates default configuration if file doesn't exist.

    Returns:
        dict: Project configuration dictionary
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Create default configuration
        return create_default_config()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            return config
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")
        print("📝 Creating default configuration...")
        return create_default_config()


def create_default_config() -> Dict[str, Any]:
    """
    Create and save default project configuration.

    Returns:
        dict: Default configuration dictionary
    """
    config = {
        "project": {
            "name": get_project_name(),
            "id": get_project_id(),
            "port": get_project_port(),
            "isolation_mode": "strict",  # strict, relaxed, or disabled
        },
        "allowed_instances": ["claude", "gemini", "codex", "lm", "chatgpt"],
        "settings": {
            "max_message_size": 20480,  # 20KB
            "auto_responder": False,
            "rate_limit": 100,  # messages per minute
            "message_retention_days": 7,
            "enable_forwarding": True,
            "enable_file_messages": True,
        },
        "permissions": {
            "allow_cross_project": False,  # Allow messages from other projects
            "trusted_projects": [],  # List of trusted project IDs
            "allow_broadcast": True,  # Allow broadcast messages within project
        },
        "network": {
            "host": "127.0.0.1",
            "timeout": 30,  # seconds
            "max_connections": 50,
            "buffer_size": 8192,
        },
    }

    # Save configuration
    save_project_config(config)
    return config


def save_project_config(config: Dict[str, Any]) -> bool:
    """
    Save project configuration to .ipc_project.yml file.

    Args:
        config: Configuration dictionary to save

    Returns:
        bool: True if saved successfully, False otherwise
    """
    config_path = get_config_path()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False


def update_config_value(key_path: str, value: Any) -> bool:
    """
    Update a specific configuration value using dot notation.

    Args:
        key_path: Dot-separated path to config key (e.g., 'project.port')
        value: New value to set

    Returns:
        bool: True if updated successfully, False otherwise
    """
    config = load_project_config()

    # Navigate to the key using dot notation
    keys = key_path.split(".")
    current = config

    # Navigate to parent of target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    current[keys[-1]] = value

    # Save updated configuration
    return save_project_config(config)


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get a specific configuration value using dot notation.

    Args:
        key_path: Dot-separated path to config key (e.g., 'project.port')
        default: Default value if key doesn't exist

    Returns:
        Configuration value or default
    """
    config = load_project_config()

    # Navigate to the key using dot notation
    keys = key_path.split(".")
    current = config

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def is_instance_allowed(instance_name: str) -> bool:
    """
    Check if an instance is allowed to communicate.

    Args:
        instance_name: Name of the instance to check

    Returns:
        bool: True if instance is allowed
    """
    config = load_project_config()
    allowed = config.get("allowed_instances", [])

    # Check base name (without project suffix)
    base_name = instance_name.split("@")[0] if "@" in instance_name else instance_name
    return base_name in allowed


def is_cross_project_allowed() -> bool:
    """
    Check if cross-project communication is allowed.

    Returns:
        bool: True if cross-project communication is allowed
    """
    return get_config_value("permissions.allow_cross_project", False)


def is_project_trusted(project_id: str) -> bool:
    """
    Check if a project ID is in the trusted list.

    Args:
        project_id: Project ID to check

    Returns:
        bool: True if project is trusted
    """
    trusted = get_config_value("permissions.trusted_projects", [])
    return project_id in trusted


def add_trusted_project(project_id: str) -> bool:
    """
    Add a project to the trusted list.

    Args:
        project_id: Project ID to trust

    Returns:
        bool: True if added successfully
    """
    config = load_project_config()
    trusted = config.get("permissions", {}).get("trusted_projects", [])

    if project_id not in trusted:
        trusted.append(project_id)
        config.setdefault("permissions", {})["trusted_projects"] = trusted
        return save_project_config(config)
    return True


def display_config_summary() -> None:
    """
    Display current configuration summary.
    """
    config = load_project_config()
    project = config.get("project", {})
    settings = config.get("settings", {})
    permissions = config.get("permissions", {})

    print("📋 Project Configuration")
    print("━" * 40)
    print(f"Name: {project.get('name', 'Unknown')}")
    print(f"ID: {project.get('id', 'Unknown')}")
    print(f"Port: {project.get('port', 'Unknown')}")
    print(f"Isolation Mode: {project.get('isolation_mode', 'strict')}")
    print()
    print("⚙️ Settings:")
    print(f"  Rate Limit: {settings.get('rate_limit', 100)} msg/min")
    print(f"  Max Message Size: {settings.get('max_message_size', 20480)} bytes")
    print(f"  Auto Responder: {settings.get('auto_responder', False)}")
    print()
    print("🔐 Permissions:")
    print(f"  Cross-Project: {permissions.get('allow_cross_project', False)}")
    print(f"  Trusted Projects: {len(permissions.get('trusted_projects', []))}")
    print(f"  Broadcast: {permissions.get('allow_broadcast', True)}")
    print("━" * 40)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "show":
            display_config_summary()
        elif command == "create":
            config = create_default_config()
            print("✅ Default configuration created")
        elif command == "get" and len(sys.argv) > 2:
            key = sys.argv[2]
            value = get_config_value(key)
            print(f"{key}: {value}")
        elif command == "set" and len(sys.argv) > 3:
            key = sys.argv[2]
            value = sys.argv[3]
            # Try to parse value as appropriate type
            try:
                if value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
            except Exception:
                pass
            if update_config_value(key, value):
                print(f"✅ Updated {key} = {value}")
        elif command == "trust" and len(sys.argv) > 2:
            project_id = sys.argv[2]
            if add_trusted_project(project_id):
                print(f"✅ Added {project_id} to trusted projects")
        else:
            print("Available commands:")
            print("  show - Display configuration summary")
            print("  create - Create default configuration")
            print("  get <key> - Get configuration value")
            print("  set <key> <value> - Set configuration value")
            print("  trust <project_id> - Add trusted project")
    else:
        # Default: show configuration
        display_config_summary()
