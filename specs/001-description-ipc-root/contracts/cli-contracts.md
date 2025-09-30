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

---

### ipc register <instance_id> [--no-default] [--no-responder]
- Purpose: Register an instance with the broker and optionally start a background auto-responder.
- Inputs:
  - `instance_id`: Unique name (e.g., `codex`, `gemini`, `monitor`)
  - `--no-default`: Do not update legacy `~/.ipc-session` pointer
  - `--no-responder`: Skip launching the auto-responder after registration
  - Env: `IPC_SHARED_SECRET` (optional) used to derive `auth_token`
- Outputs:
  - Stdout: human-readable status lines
  - Side effects:
    - Creates/updates session file containing `{ instance_id, session_token }`
    - On success, may spawn background responder process (unless `--no-responder`)
- Exit Codes:
  - 0: success
  - 20: cannot connect to broker (ECONNREFUSED/timeout)
  - 21: broker rejected registration (stdout includes JSON error)
  - 22: reserved for "responder failed to launch" (current implementation returns 0 with a warning)
- Notes:
  - Current behavior: registration returns 0 even if the auto-responder fails to start; a warning is printed to stdout.
  - On Windows, background processes are launched with `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` to avoid extra consoles.
  - If `simple_auto_responder.py` is missing, fall back to `auto_responder.py`.

---

### ipc ask --to <target> <prompt>
- Purpose: Send a prompt and wait for an automatic response from the target's auto-responder.
- Inputs:
  - `--to <target>`: Target instance or address
  - `<prompt>`: Question/prompt string
  - Flags:
    - `--timeout <sec>` (default: 10s)
    - `--poll-interval <sec>` (default: 0.2s) 응답 대기 중 DB 폴링 간격. 작은 값일수록 빠른 응답, 높은 CPU 사용 가능.
    - `--corr <id>` 클라이언트가 직접 상관관계 ID를 지정할 때 사용(선택 사항).
- Outputs:
  - Stdout: acknowledgment with `correlation=` and then a single-line `answer:` or a JSON payload
  - Side effects: enqueues a message and blocks until a response arrives or timeout
- Exit Codes:
  - 0: success (answer received)
  - 30: timeout waiting for response
  - 31: delivery failed

### ipc messages clear [--force]
- Purpose: Clear all messages for the current project (inbox and outbox) with safety checks.
- Inputs: `--force` to skip interactive confirmation
- Outputs: human-readable summary of deleted counts
- Exit Codes:
  - 0: success
  - 40: refused (no --force in non-interactive environment)

### ipc instances reset
- Purpose: Remove all registered instance sessions for this project only (does not kill running processes).
- Outputs: number of sessions removed; tips to re-register
- Exit Codes:
  - 0: success
  - 50: partial failure (some sessions locked)

### ipc instances delete <instance_id>
- Purpose: Delete a single registered instance's session and metadata.
- Outputs: confirmation message
- Exit Codes:
  - 0: success
  - 51: instance not found

### ipc responder start <instance_id>
### ipc responder stop <instance_id>
  - `<instance_id>`
  - Flags: `--policy <simple|smart>` (default: simple), `--detach` (background), `--no-window` (Windows only)
- Outputs:
  - `start`: PID and policy info
  - `stop`: termination status
  - 0: success
  - 60: failed to launch
  - 61: process not found / already stopped
- responder start/stop
  - start
    - Usage: `ipc responder start <instance_id> [--policy simple|smart] [--detach]`
    - Behavior: Starts a background auto-responder bound to the given instance. Writes PID to `%USERPROFILE%\.claude-ipc-data\responders\<instance_id>.pid`. Idempotent if already running.
    - Exit codes: 0 success, 60 start failure (script missing or spawn error)
  - stop
    - Usage: `ipc responder stop <instance_id>`
    - Behavior: Stops the responder using PID file. If not running or PID missing, succeeds (idempotent). Removes PID file when possible.
    - Exit codes: 0 success, 61 stop failure (termination error)
  - Notes: Policy is propagated via `IPC_RESPONDER_POLICY` env var. `smart` may use faster polling.

- responder status
  - Usage: `ipc responder status <instance_id>`
  - Behavior: Prints JSON `{ instance_id, running, pid, pid_file, started_at?, last_check_at?, last_response_at?, policy? }`.
    - `started_at`: 자동 응답기가 시작된 시각(ISO8601, 초 단위)
    - `last_check_at`: 마지막 메시지 스캔 시각
    - `last_response_at`: 마지막 응답을 보낸 시각
    - `policy`: 적용 중인 정책(`simple`|`smart`) — 환경변수 `IPC_RESPONDER_POLICY`로 설정됨
  - Exit Codes: 0 when running, 62 when not running or unknown.