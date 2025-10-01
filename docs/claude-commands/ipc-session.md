---
description: Show current IPC session information
tags: [ipc, session, status]
---

# IPC Session

Display information about the current IPC session for this project.

This command shows:
- Current instance ID (if registered)
- Session token status
- Session creation time
- Last activity time
- Project directory

## Usage

```bash
uv run python tools/ipc_global_command.py session
```

## Example Output

```
Current Session:
  Instance ID: claude-frontend
  Session Token: ****************************** (valid)
  Created: 2025-01-15 10:30:45
  Last Activity: 2025-01-15 14:22:10
  Project: D:\my-project
```

## Notes

- Session information is stored in `.ipc/state/session.json`
- Sessions expire after 24 hours of inactivity
- Use `ipc register <name>` to create a new session
- Use `ipc session clear` to remove session data
