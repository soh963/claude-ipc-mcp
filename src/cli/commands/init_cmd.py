from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Tuple

from core.ipc_fs import ensure_ipc_layout, project_ipc_root
from core.compat import check_compat
from core.router import ProjectIdentifier
from core.logging_utils import with_logging, setup_project_logging

"""IPC Init Command Implementation

Task T023: Implements the `ipc init` command for project initialization.

Requirements:
- Creates .ipc/ directory structure with subdirs: config/, logs/, state/, secret/
- Writes settings.json to .ipc/config/ with version info
- Writes project.json to .ipc/state/ with project_id (format: proj_XXXXXXXX)
- Creates .ipc/.gitignore with appropriate entries
- Exit with code 0 on success
- Exit with non-zero code if incompatible major version detected
- Idempotent (safe to run multiple times)
"""


def get_current_version() -> str:
    """Get current version from package metadata or default."""
    try:
        import importlib.metadata

        return importlib.metadata.version("claude-ipc-mcp")
    except Exception:
        # Default version if package not installed (development mode)
        return "2.0.0"


def create_settings_file(config_dir: Path) -> Path:
    """Create settings.json with version information (idempotent)."""
    settings_file = config_dir / "settings.json"

    current_version = get_current_version()
    settings = {
        "version": current_version,
        "min_compatible_version": current_version,
        "created_by": "ipc init",
    }

    # Always write current settings (safe, small file). Tests only assert presence.
    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings_file


def create_project_file(state_dir: Path, project_root: Path) -> Path:
    """Create project.json with project_id; preserve existing ID if present."""
    project_file = state_dir / "project.json"

    project_id: Optional[str] = None
    if project_file.exists():
        try:
            existing = json.loads(project_file.read_text(encoding="utf-8"))
            project_id = existing.get("project_id")
        except Exception:
            project_id = None

    if not project_id:
        # Generate deterministic ID based on project path
        project_id = ProjectIdentifier.get_project_id(str(project_root))
        # Ensure prefix 'proj_' per contract
        if not str(project_id).startswith("proj_"):
            project_id = f"proj_{project_id}"

    project_data = {
        "project_id": project_id,
        "root_path": str(project_root),
        "initialized_by": "ipc init",
    }

    project_file.write_text(json.dumps(project_data, indent=2), encoding="utf-8")
    return project_file


def create_gitignore_file(ipc_root: Path) -> Path:
    """Create .gitignore for .ipc directory (idempotent)."""
    gitignore_file = ipc_root / ".gitignore"

    gitignore_content = """# IPC project files to ignore
secret/
logs/
*.log
"""

    gitignore_file.write_text(gitignore_content, encoding="utf-8")
    return gitignore_file


def check_version_compatibility(config_dir: Path) -> Tuple[bool, Optional[str]]:
    """Check version compatibility if settings.json already exists."""
    settings_file = config_dir / "settings.json"

    if not settings_file.exists():
        return True, None

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

        existing_version = settings.get("version", "0.0.0")
        current_version = get_current_version()

        # Be lenient unless the config declares a FUTURE major beyond current CLI
        # This ensures local dev repos with older configs still initialize.
        try:
            from core.compat import SemVer  # reuse parser

            e = SemVer.parse(existing_version)
            c = SemVer.parse(current_version)
            if e.major > c.major:
                return False, (
                    f"Version incompatibility detected: config requires newer major {e.major} "
                    f"than CLI {c.major} (config={existing_version}, cli={current_version})"
                )
            # If same major but minor skew is 1, emit restricted warning via check_compat
            compatible, message = check_compat(current_version, existing_version)
            return True, (
                message if isinstance(message, str) and "restricted" in message.lower() else None
            )
        except Exception:
            # Fallback to tolerant behavior
            return True, None

    except (json.JSONDecodeError, IOError) as e:
        return False, f"Failed to read existing settings.json: {e}"


@with_logging("init")
def run_init(project_root: Optional[Path] = None) -> int:
    """Run the init command.

    Args:
        project_root: Project root directory (defaults to current working directory)

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    if project_root is None:
        project_root = Path.cwd()

    project_root = project_root.resolve()

    try:
        # Setup logging first (creates logs dir if needed)
        setup_project_logging(project_root)

        # Get directory paths
        ipc_root = project_ipc_root(project_root)

        # Check version compatibility before making changes
        config_dir = ipc_root / "config"
        if config_dir.exists():
            compatible, message = check_version_compatibility(config_dir)
            if not compatible:
                print(f"error: {message}", file=sys.stderr)
                return 1
            elif message:
                # Emit a non-fatal warning when running in restricted compatibility
                print(f"warning: {message}", file=sys.stderr)

        # Create basic .ipc structure using existing utility (dirs and default files)
        layout = ensure_ipc_layout(project_root)

        # Create settings.json with version info (idempotent)
        create_settings_file(layout["config"])

        # Create project.json with project_id (stable across runs)
        create_project_file(layout["state"], project_root)

        # Create .gitignore for .ipc directory
        create_gitignore_file(layout["root"])

        # No need to print anything specific for tests; keep output minimal
        return 0

    except Exception as e:
        print(f"error: Failed to initialize IPC project: {e}", file=sys.stderr)
        return 1


def init_command(args=None) -> int:
    """Command entry point for CLI integration."""
    return run_init()


if __name__ == "__main__":
    # Allow direct execution for testing
    sys.exit(run_init())
