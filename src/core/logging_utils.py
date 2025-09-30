"""Project-scoped logging helpers.

Resolves the project `.ipc/logs` path and configures logging to file + stderr.
Idempotent and safe to call multiple times.
Includes middleware hooks for request/response logging (T030).
"""

from __future__ import annotations

import functools
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .ipc_fs import logs_dir

# Module logger for CLI operations
logger = logging.getLogger("ipc.cli")


def resolve_logs_path(root: Path | None = None) -> Path:
    return logs_dir(root)


def setup_project_logging(project_root: Path, level: int = logging.INFO) -> None:
    """Configure logging to `.ipc/logs/cli.log` and stderr."""
    ldir = logs_dir(project_root)
    ldir.mkdir(parents=True, exist_ok=True)
    log_file = ldir / "cli.log"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Also ensure our module logger is configured
    logger.setLevel(level)


def log_cli_request(command: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Log a CLI command request.

    Args:
        command: The command being executed (e.g., "init", "status", "ping")
        args: Optional arguments passed to the command
    """
    log_data = {
        "type": "request",
        "command": command,
        "timestamp": time.time(),
    }
    if args:
        # Convert Path objects to strings for JSON serialization
        serializable_args = {}
        for key, value in args.items():
            if hasattr(value, "__fspath__"):  # Check if it's a Path object
                serializable_args[key] = str(value)
            else:
                serializable_args[key] = value
        log_data["args"] = serializable_args

    logger.info(f"CLI Request: {json.dumps(log_data)}")


def log_cli_response(
    command: str,
    success: bool,
    duration_ms: Optional[float] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """Log a CLI command response.

    Args:
        command: The command that was executed
        success: Whether the command succeeded
        duration_ms: Optional execution time in milliseconds
        result: Optional result data
        error: Optional error message if failed
    """
    log_data = {
        "type": "response",
        "command": command,
        "success": success,
        "timestamp": time.time(),
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    if result is not None:
        # Limit result size in logs to prevent huge entries
        result_str = str(result)
        if len(result_str) > 500:
            result_str = result_str[:497] + "..."
        log_data["result"] = result_str
    if error:
        log_data["error"] = error

    if success:
        logger.info(f"CLI Response: {json.dumps(log_data)}")
    else:
        logger.error(f"CLI Response: {json.dumps(log_data)}")


def with_logging(command_name: str) -> Callable:
    """Decorator to add request/response logging to CLI commands.

    Args:
        command_name: Name of the command for logging

    Returns:
        Decorator function that wraps command execution with logging
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Log the request
            log_cli_request(command_name, kwargs)

            # Track execution time
            start_time = time.perf_counter()

            try:
                # Execute the command
                result = func(*args, **kwargs)

                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log successful response
                log_cli_response(
                    command_name,
                    success=True,
                    duration_ms=duration_ms,
                    result=f"exit_code={result}" if isinstance(result, int) else str(result),
                )

                return result

            except Exception as e:
                # Calculate duration even for failures
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log error response
                log_cli_response(command_name, success=False, duration_ms=duration_ms, error=str(e))

                # Re-raise the exception
                raise

        return wrapper

    return decorator
