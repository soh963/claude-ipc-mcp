# Quickstart: Global IPC CLI (Windows PowerShell)

## Prerequisites
- Windows 10/11, PowerShell 7+
- Python 3.12 installed

## 1) Global Install (once)
- Start PowerShell as Administrator
- Run: `scripts/install-global.ps1`
- Restart PowerShell session

## 2) Initialize a project
```
PS D:\work\proj-a> ipc init
```
- Creates `.ipc/` (config, secrets, logs, state)
- Ensures broker connectivity

## 3) Check status and ping
```
PS D:\work\proj-a> ipc status
PS D:\work\proj-a> ipc ping
```

## 4) Cross-project chat
```
PS D:\work\proj-b> ipc init
PS D:\work\proj-b> ipc chat --to proj-a "Hello"
```

## 5) Troubleshooting
- `ipc doctor` to auto-detect common issues
- Check `.ipc/logs/` and `%USERPROFILE%\\.claude-ipc-data` logs

## Notes
- For macOS/Linux, use direct python execution or symlinks per docs
- Version compatibility: broker/CLI major must match; minor ±1
