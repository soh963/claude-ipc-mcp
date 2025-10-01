---
description: Start the global IPC message broker (port 9876)
tags: [ipc, broker, setup]
---

# IPC Broker Start

Start the global IPC message broker on port 9876 (or IPC_GLOBAL_PORT if set).

The broker must be running for all IPC operations to work. This command:
- Starts TCP server on 127.0.0.1:9876 (default)
- Initializes SQLite database at ~/.claude-ipc-data/messages.db
- Enables session-based authentication
- Activates rate limiting (100 req/min per instance)

## Usage

```bash
uv run python tools/ipc_global_command.py broker start
```

## Environment Variables

- `IPC_HOST`: Broker host (default: 127.0.0.1)
- `IPC_GLOBAL_PORT`: Broker port (default: 9876)
- `IPC_SHARED_SECRET`: Optional authentication token

## Verification

After starting, verify with:
```bash
uv run python tools/ipc_global_command.py broker status
```

## Notes

- Only one broker instance can run at a time
- Broker state persists across restarts
- Use `ipc doctor` if broker won't start
