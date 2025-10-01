---
description: Delete a specific IPC instance registration
tags: [ipc, instances, cleanup]
---

# IPC Instances Delete

Delete a specific instance registration from the IPC system.

This command:
- Removes the instance from the broker's registry
- Invalidates the instance's session token
- Preserves messages (use `ipc messages clear` to delete messages)

## Usage

```bash
uv run python tools/ipc_global_command.py instances delete <instance_name>
```

## Example

```bash
# Delete the 'old-project' instance
uv run python tools/ipc_global_command.py instances delete old-project
```

## Notes

- Instance can re-register with the same name after deletion
- Does not affect other instances
- Use `ipc instances list` to see available instances before deleting
- For removing all instances, use `ipc instances reset`
