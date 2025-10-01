---
description: Check global IPC message broker status
tags: [ipc, broker, status]
---

# IPC Broker Status

Check if the global IPC message broker is running and show connection details.

This command displays:
- Broker running status (✓ Running / ✗ Not running)
- Connection details (host, port)
- Database location
- Number of active instances

## Usage

```bash
uv run python tools/ipc_global_command.py broker status
```

## Example Output

```
Broker Status:
  Status: ✓ Running
  Host: 127.0.0.1
  Port: 9876
  Database: C:\Users\user\.claude-ipc-data\messages.db
  Active Instances: 3
```

## Notes

- Use this command to verify broker is running before IPC operations
- Part of the troubleshooting workflow with `ipc doctor`
