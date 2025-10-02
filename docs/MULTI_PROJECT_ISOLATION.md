# Multi-Project IPC Isolation

## Overview

Claude IPC MCP now supports **multiple projects running simultaneously** without port conflicts or data mixing. Each project gets:

1. **Unique Project ID** - 8-character hex hash from project path
2. **Dedicated Port** - Project-specific port (10000-14999 range)
3. **Isolated .ipc Directory** - All data stored in project root `.ipc/`

## Architecture

### Project Identification

```python
# Project ID generation from path
from core.project_port import get_project_id

project_id = get_project_id()  # e.g., "290d855e"
```

**Hash Algorithm**:
- SHA-256 hash of normalized project root path
- First 8 hex characters used as project ID
- Consistent across sessions for same project

### Port Allocation

```python
from core.project_port import get_or_create_project_port

port = get_or_create_project_port()  # e.g., 10509
```

**Port Assignment**:
- Base port: 10000
- Port range: 10000-14999 (5000 ports)
- Formula: `10000 + (int(project_id[:4], 16) % 5000)`
- Fallback: If port occupied, finds next available port

### Directory Structure

Each project maintains isolated state:

```
{project_root}/.ipc/
├── config/
│   └── project.json        # Contains project_id and broker_port
├── data/
│   └── ipc.db             # Project-specific database
├── logs/
│   └── broker.log         # Project-specific logs
├── state/
│   └── broker.pid         # Project-specific broker process
└── secret/
    └── ...                # Project-specific secrets
```

## Configuration File

`{project_root}/.ipc/config/project.json`:

```json
{
  "project_root": "D:\\test-tem",
  "project_name": "test-tem",
  "project_id": "290d855e",
  "broker_host": "127.0.0.1",
  "broker_port": 10509,
  "created_at": "2025-10-02T11:19:55.226082",
  "version": "2.0.0"
}
```

## Usage Examples

### Scenario: Two Projects Running Simultaneously

**Project A** (`D:\project-a`):
```bash
cd D:\project-a
# Initializes with project ID: abc12345, port: 10234
uv run python tools/ipc_global_command.py init
```

**Project B** (`D:\project-b`):
```bash
cd D:\project-b
# Initializes with project ID: def67890, port: 11567
uv run python tools/ipc_global_command.py init
```

**Result**: Both projects run independent brokers on different ports with isolated data.

### Cross-Project Communication

Projects are **isolated by default**. To enable cross-project communication:

1. Share broker port via environment variable
2. Configure instances to connect to specific port
3. Use shared message queue (advanced)

## API Integration

### Broker Client

```python
from core import broker_client
from core.project_local import get_project_config

# Get project-specific configuration
config = get_project_config()
host = config["broker_host"]
port = config["broker_port"]

# Register with project-specific broker
response = broker_client.register("my-instance")
```

### Broker Daemon

```python
from src.broker.daemon import BrokerDaemon
from pathlib import Path

# Start broker for specific project
broker = BrokerDaemon(project_root=Path("/path/to/project"))
broker.start()
```

## CLI Commands

All IPC commands automatically detect and use project-specific configuration:

```bash
# Initialize project IPC
cd /path/to/project
uv run python tools/ipc_global_command.py init

# Check status (uses project-specific port)
uv run python tools/ipc_global_command.py status

# Register instance (uses project-specific broker)
uv run python tools/ipc_global_command.py register my-instance

# Send message within project
uv run python tools/ipc_global_command.py ask --to target "message"
```

## Conflict Prevention

### Port Conflicts
- Each project gets unique port based on project ID
- If port occupied, system finds next available port
- Port recorded in `project.json` for consistency

### Data Isolation
- All IPC data stored in project-specific `.ipc/`
- No shared state between projects
- Each project has independent database, logs, sessions

### Process Management
- Each project can run independent broker process
- PID files stored in project-specific `.ipc/state/`
- No interference between project brokers

## Migration from Global System

To migrate from global `~/.claude-ipc-data/` to project-local:

```python
from core.project_local import migrate_global_to_project

# Migrate global data to current project
migrate_global_to_project()
```

**Migration Process**:
1. Copies instances from global DB to project DB
2. Migrates messages (avoiding duplicates)
3. Transfers name change history
4. Preserves global data (non-destructive)

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :10509

# Kill process
taskkill /F /PID <pid>

# Or change port in project.json and restart broker
```

### Project Detection Issues

```bash
# Manually specify project root
uv run python tools/ipc_global_command.py init --project-root /path/to/project
```

### Database Lock Errors

```bash
# Stop broker first
uv run python tools/ipc_global_command.py status

# Then perform database operations
```

## Best Practices

1. **One Broker Per Project**: Each project should run its own broker instance
2. **Port Documentation**: Document assigned ports in project README
3. **Clean Shutdown**: Always stop brokers gracefully before system shutdown
4. **Backup .ipc Data**: Include `.ipc/` in backup strategy (except logs/temp files)
5. **Version Control**: Add `.ipc/` to `.gitignore` (structure already includes proper .gitignore)

## Technical Details

### Port Calculation Algorithm

```python
def get_project_port(project_root: Optional[Path] = None) -> int:
    project_id = get_project_id(project_root)
    port_offset = int(project_id[:4], 16) % 5000
    return 10000 + port_offset
```

**Example**:
- Project ID: `290d855e`
- First 4 chars: `290d`
- Hex to int: `10509` (decimal)
- Modulo 5000: `509`
- Final port: `10000 + 509 = 10509`

### Port Availability Check

```python
def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False
```

### Fallback Port Selection

If preferred port occupied, system tries:
- `preferred_port + 1`
- `preferred_port + 2`
- ... up to 100 attempts

## Environment Variables

Override project-specific settings:

```bash
# Override host
export IPC_HOST=0.0.0.0

# Override port (not recommended - breaks project isolation)
export IPC_PORT=9999
```

## Related Documentation

- [Project Local IPC Design](PROJECT_LOCAL_IPC_DESIGN.md)
- [CLI Commands Reference](ipc_cli_commands.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
