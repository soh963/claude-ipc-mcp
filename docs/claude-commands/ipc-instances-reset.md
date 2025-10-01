---
description: Reset all IPC instance registrations (system cleanup)
tags: [ipc, instances, reset, cleanup]
---

# IPC Instances Reset

Delete all instance registrations from the IPC system (system-wide reset).

⚠️ **Warning**: This is a destructive operation that affects all instances.

This command:
- Removes all instances from the broker's registry
- Invalidates all session tokens
- Preserves messages (use `ipc messages clear --force` to delete messages)
- Requires confirmation

## Usage

```bash
uv run python tools/ipc_global_command.py instances reset
```

## Use Cases

- Starting fresh after testing
- Cleaning up after multiple failed registrations
- Resolving instance conflicts
- System maintenance

## Notes

- All instances must re-register after reset
- Messages remain in database
- Consider using `ipc instances delete <name>` for single instance removal
- Part of complete system reset workflow (with `ipc messages clear --force`)
