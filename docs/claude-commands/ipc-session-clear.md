---
description: Clear current IPC session data
tags: [ipc, session, cleanup]
---

# IPC Session Clear

Clear the current IPC session data for this project.

This command:
- Removes session token from local storage
- Clears instance registration data
- Resets session state in `.ipc/state/session.json`
- Does not affect messages or broker state

## Usage

```bash
uv run python tools/ipc_global_command.py session clear
```

## Use Cases

- Starting fresh with a new instance ID
- Resolving session conflicts
- Switching between different instances in same project
- Troubleshooting authentication issues

## Notes

- You must re-register after clearing session
- Messages remain in the broker
- Other instances are not affected
- Use `ipc register <name>` to create new session
