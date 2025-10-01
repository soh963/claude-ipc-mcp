---
description: Stop the global IPC message broker
tags: [ipc, broker, shutdown]
---

# IPC Broker Stop

Stop the running global IPC message broker.

This command:
- Gracefully shuts down the TCP server
- Closes all active connections
- Preserves message database state

## Usage

```bash
uv run python tools/ipc_global_command.py broker stop
```

## Notes

- All registered instances will lose their connections
- Messages remain in the database and persist across restarts
- Instances need to re-register after broker restart
- Use `ipc broker status` to verify shutdown
