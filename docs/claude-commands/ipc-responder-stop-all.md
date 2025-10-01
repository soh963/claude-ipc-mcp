---
description: Stop all running IPC auto-responders
tags: [ipc, responder, shutdown, batch]
---

# IPC Responder Stop All

Stop all currently running auto-responder processes.

This command:
- Terminates all active responder processes
- Cleans up PID files
- Updates responder state files
- Gracefully shuts down each responder

## Usage

```bash
uv run python tools/ipc_global_command.py responder stop-all
```

## Example Output

```
Stopping all responders...
✓ Stopped responder for claude-frontend (PID: 12345)
✓ Stopped responder for claude-backend (PID: 12346)
✓ Stopped responder for gemini-assistant (PID: 12347)

Stopped 3 responders successfully.
```

## Notes

- Use `ipc responder status <instance>` to verify shutdown
- PID files are removed from `~/.claude-ipc-data/responders/`
- Responders can be restarted with `ipc responder start` or `start-all`
- Safe to run even if no responders are running
