---
description: Clear all messages from the IPC system
tags: [ipc, messages, cleanup]
---

# IPC Messages Clear

Delete all messages from the IPC message database.

⚠️ **Warning**: This is a destructive operation that cannot be undone.

This command:
- Deletes all messages from the database
- Clears message history for all instances
- Requires `--force` flag to prevent accidental deletion
- Does not affect instance registrations

## Usage

```bash
uv run python tools/ipc_global_command.py messages clear --force
```

## Use Cases

- Cleaning up after testing
- Removing old/stale messages
- Freeing up database space
- Privacy/security cleanup

## Notes

- **Must include `--force` flag** to confirm deletion
- Instance registrations remain intact
- For complete system reset, also use `ipc instances reset`
- Messages in large-message files are also deleted
