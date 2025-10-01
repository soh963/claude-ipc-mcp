---
description: Start auto-responders for all registered IPC instances
tags: [ipc, responder, automation, batch]
---

# IPC Responder Start All

Start auto-responders for all currently registered IPC instances.

This command:
- Starts responder processes for each registered instance
- Uses specified policy (simple or smart) for all
- Runs in background (detached) if `--detach` flag is used
- Creates PID and state files for each responder

## Usage

```bash
# Start all with smart policy in background
uv run python tools/ipc_global_command.py responder start-all --policy smart --detach

# Start all with simple policy in foreground
uv run python tools/ipc_global_command.py responder start-all --policy simple
```

## Options

- `--policy <simple|smart>`: Response policy (default: smart)
  - `simple`: Echo back all messages
  - `smart`: Context-aware intelligent replies
- `--detach`: Run in background (recommended)

## Example Output

```
Starting responders for all instances...
✓ Started responder for claude-frontend (PID: 12345)
✓ Started responder for claude-backend (PID: 12346)
✓ Started responder for gemini-assistant (PID: 12347)

Started 3 responders successfully.
```

## Notes

- Use `ipc responder status <instance>` to check individual responder status
- Use `ipc responder stop-all` to stop all responders
- Responders automatically restart on errors
- Status tracked in `~/.claude-ipc-data/responders/`
