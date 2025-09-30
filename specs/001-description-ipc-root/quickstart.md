# Quickstart: Global IPC CLI (Windows PowerShell)

## Prerequisites
- Windows 10/11, PowerShell 7+
- Python 3.12 installed
- Optional: `uv` for fast isolated runs (see docs/INSTALL_UV.md)

## 1) Global Install (once)
- Start PowerShell as Administrator
- Run the installer:
```
PS> scripts/install-global.ps1
```
- Close and reopen PowerShell to refresh PATH

## 2) Initialize a project
```
PS D:\work\proj-a> ipc init
```
- Creates `.ipc/` (config, secrets, logs, state)
- Ensures broker connectivity or starts it if necessary

## 3) Check status and ping
```
PS D:\work\proj-a> ipc status
PS D:\work\proj-a> ipc ping
```

Status: Minimal init → status → ping flow implemented; validated by `tests/integration/cli/test_quickstart_flow.py`.

Security tip: Set `IPC_SHARED_SECRET` before running the CLI for authenticated registration. See `docs/SECURITY.md`.

## 4) Cross-project chat
```
PS D:\work\proj-b> ipc init
PS D:\work\proj-b> ipc chat --to proj-a "Hello"
```

## 5) Register an instance and start auto-responder
```
PS D:\work\proj-a> python tools/ipc_register_with_responder.py codex
```
- Creates per-instance session at `%USERPROFILE%\.ipc-session-codex` and updates legacy `%USERPROFILE%\.ipc-session` pointer (unless `--no-default`).
- Attempts to launch a background auto-responder for `codex`.
- If the responder is already running, a warning is displayed.

Optional flags:
- `--no-responder`: register only, skip starting the responder
- `--no-default`: don't update legacy default session file

## 6) Ask and manage messages
```
PS D:\work\proj-a> ipc ask --to proj-b "What's the status?"
PS D:\work\proj-a> ipc messages clear --force
```

## 7) Manage responders and instances
```
PS D:\work\proj-a> ipc responder start codex --policy simple --detach
PS D:\work\proj-a> ipc responder stop codex
PS D:\work\proj-a> ipc instances reset
PS D:\work\proj-a> ipc instances delete codex
```

## 8) Troubleshooting
- `ipc doctor` to auto-detect common issues
- Check `.ipc/logs/` and `%USERPROFILE%\\.claude-ipc-data` logs

## Notes
- For macOS/Linux, invoke Python scripts directly and use `start_new_session=True` semantics; best-effort support.
- Version compatibility: broker/CLI major must match; minor ±1.
- Auto-responder launch failures do not fail registration; a warning is printed.
 - `ipc ask` returns exit code 30 on timeout.
