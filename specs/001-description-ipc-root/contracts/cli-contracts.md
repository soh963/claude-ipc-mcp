# CLI Contracts: Global IPC

## Contract format
- Inputs: flags/args, expected env
- Outputs: stdout schema, side effects
- Errors: exit codes, stderr messages

---

### ipc init
- Inputs: [--minimal]
- Outputs: creates `.ipc/` with config/secrets/logs/state; prints project_id, port
- Errors:
  - 1: Python not found
  - 2: permission denied (symlink/mklink)
  - 3: broker start failed

### ipc status
- Inputs: none
- Outputs (stdout JSON suggestion):
```json
{
  "broker": {"running": true, "version": "1.2.0", "port": 9456},
  "connections": 3,
  "last_ping_ms": 120
}
```
- Errors:
  - 10: broker not running

### ipc ping
- Inputs: [--to <target-project>]
- Outputs: "pong" with rtt ms
- Errors:
  - 11: target unreachable

### ipc chat --to <target> <message>
- Inputs: required `--to`, message string
- Outputs: conversation snippet (stdout), correlation id
- Errors:
  - 12: message delivery failed

### ipc doctor
- Inputs: none
- Outputs: detected issues and fixes applied or instructions
- Errors:
  - 13: unrecoverable misconfiguration
