#!/usr/bin/env python3
"""
Project isolation utilities for IPC system
Provides project ID generation and port allocation based on project path
"""

import hashlib
import os
from pathlib import Path
from typing import Optional


def get_project_id() -> str:
    """
    Generate unique project ID based on current project path.
    Uses SHA-256 hash of normalized path for consistent identification.

    Returns:
        str: Project ID in format 'proj_XXXXXXXX' (8 character hash)
    """
    # Get absolute path of current working directory
    project_path = os.path.abspath(os.getcwd())

    # Normalize path for cross-platform consistency
    # Convert backslashes to forward slashes and lowercase
    project_path = project_path.replace('\\', '/').lower()

    # Generate SHA-256 hash of the path
    hash_obj = hashlib.sha256(project_path.encode('utf-8'))
    project_hash = hash_obj.hexdigest()[:8]  # Use first 8 characters

    return f"proj_{project_hash}"


def get_project_port() -> int:
    """
    Generate unique port number for project based on project ID.
    Maps project to port in range 9000-9999 for isolation.

    Returns:
        int: Port number between 9000-9999
    """
    project_id = get_project_id()

    # Create MD5 hash of project ID for port calculation
    # MD5 is sufficient for port mapping (not security critical)
    port_hash = hashlib.md5(project_id.encode('utf-8')).hexdigest()[:4]

    # Convert first 4 hex characters to integer and map to range 0-999
    port_offset = int(port_hash, 16) % 1000

    # Map to port range 9000-9999
    return 9000 + port_offset


def get_project_name() -> str:
    """
    Get human-readable project name from current directory.

    Returns:
        str: Directory name as project name
    """
    return os.path.basename(os.getcwd())


def get_project_path() -> str:
    """
    Get normalized absolute project path.

    Returns:
        str: Normalized absolute path with forward slashes
    """
    project_path = os.path.abspath(os.getcwd())
    # Normalize to forward slashes for consistency
    return project_path.replace('\\', '/')


def validate_project_id(provided_id: str, expected_id: Optional[str] = None) -> bool:
    """
    Validate that provided project ID matches expected or current project.

    Args:
        provided_id: Project ID to validate
        expected_id: Expected project ID (uses current if not provided)

    Returns:
        bool: True if IDs match, False otherwise
    """
    if expected_id is None:
        expected_id = get_project_id()

    return provided_id == expected_id


def get_project_info() -> dict:
    """
    Get comprehensive project information for isolation.

    Returns:
        dict: Dictionary containing all project isolation parameters
    """
    return {
        'id': get_project_id(),
        'name': get_project_name(),
        'path': get_project_path(),
        'port': get_project_port(),
        'namespace': f"{get_project_id()}.ipc.local"
    }


def format_instance_name(base_name: str, project_id: Optional[str] = None) -> str:
    """
    Format instance name with project namespace.

    Args:
        base_name: Base instance name (e.g., 'claude', 'gemini')
        project_id: Project ID to use (uses current if not provided)

    Returns:
        str: Formatted name with project namespace (e.g., 'claude@proj_abc123')
    """
    if project_id is None:
        project_id = get_project_id()

    return f"{base_name}@{project_id}"


def parse_instance_name(full_name: str) -> tuple[str, str]:
    """
    Parse formatted instance name into base name and project ID.

    Args:
        full_name: Full instance name with project (e.g., 'claude@proj_abc123')

    Returns:
        tuple: (base_name, project_id) or (full_name, '') if not formatted
    """
    if '@' in full_name:
        parts = full_name.split('@', 1)
        return parts[0], parts[1]
    return full_name, ''


def is_same_project(instance_name: str, project_id: Optional[str] = None) -> bool:
    """
    Check if an instance belongs to the same project.

    Args:
        instance_name: Instance name to check (may include project)
        project_id: Project ID to compare against (uses current if not provided)

    Returns:
        bool: True if instance is from same project
    """
    if project_id is None:
        project_id = get_project_id()

    _, instance_project = parse_instance_name(instance_name)

    # If no project specified in name, assume current project
    if not instance_project:
        return True

    return instance_project == project_id


def display_project_status() -> None:
    """
    Display current project isolation status for debugging.
    """
    info = get_project_info()

    print("🔒 Project Isolation Status")
    print("━" * 40)
    print(f"Project Path: {info['path']}")
    print(f"Project Name: {info['name']}")
    print(f"Project ID: {info['id']}")
    print(f"Project Port: {info['port']}")
    print(f"Namespace: {info['namespace']}")
    print("━" * 40)


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'info':
            display_project_status()
        elif command == 'id':
            print(get_project_id())
        elif command == 'port':
            print(get_project_port())
        elif command == 'name':
            print(get_project_name())
        elif command == 'path':
            print(get_project_path())
        else:
            print(f"Unknown command: {command}")
            print("Available commands: info, id, port, name, path")
            sys.exit(1)
    else:
        # Default: show project info
        display_project_status()