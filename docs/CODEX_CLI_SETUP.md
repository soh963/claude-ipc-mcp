# Codex CLI - IPC Slash Commands Setup Guide

This guide explains how to install and use IPC slash commands in Codex CLI.

## Prerequisites

- Codex CLI installed and configured
- Claude IPC MCP project cloned to your machine
- Python 3.10+ with `uv` package manager
- IPC broker running (automatically starts on first use)

## Installation

### Method 1: Automated Installation (Recommended)

Run the installation script from PowerShell:

```powershell
cd D:\claude-ipc-mcp
.\scripts\install-codex-cli.bat
```

The script will:
1. Create `%USERPROFILE%\.codex\` directory if it doesn't exist
2. Copy `config.toml` to the Codex configuration directory
3. Verify installation
4. Display available commands

### Method 2: Manual Installation

1. **Create Codex configuration directory**:
   ```powershell
   mkdir $env:USERPROFILE\.codex
   ```

2. **Copy configuration file**:
   ```powershell
   copy D:\claude-ipc-mcp\scripts\codex-config\config.toml $env:USERPROFILE\.codex\config.toml
   ```

3. **Update IPC_CHAT path** in `config.toml`:
   ```toml
   [environment]
   IPC_CHAT = "D:\\claude-ipc-mcp"  # Update to your actual path
   ```

4. **Restart Codex CLI** to load new commands

## Available Commands

### 🚀 `/ipc:setup` - Complete IPC Setup

One-command setup that registers your instance and starts auto-responder.

**Usage**:
```
/ipc:setup <instance_name>
```

**Example**:
```
/ipc:setup codex-main
```

**Output**:
```json
{
  "status": "success",
  "instance_id": "codex-main",
  "session_token": "abc123...",
  "responder_running": true,
  "policy": "smart"
}
```

---

### 📊 `/ipc:status` - Check IPC Connection

Check broker status and your instance registration.

**Usage**:
```
/ipc:status
```

**Output**:
```json
{
  "broker_status": "running",
  "instance_id": "codex-main",
  "responder_status": "active",
  "session_valid": true,
  "last_activity": "2025-02-01 14:30:00"
}
```

---

### 👥 `/ipc:list` - List All Instances

Show all registered AI instances.

**Usage**:
```
/ipc:list
```

**Output**:
```json
{
  "instances": [
    {"id": "claude-frontend", "last_seen": "2025-02-01 14:25:00"},
    {"id": "gemini-backend", "last_seen": "2025-02-01 14:28:00"},
    {"id": "codex-main", "last_seen": "2025-02-01 14:30:00"}
  ]
}
```

---

### 💬 `/ipc:send` - Send Message

Send a message to another AI instance.

**Usage**:
```
/ipc:send <from_instance> <to_instance> <message>
```

**Example**:
```
/ipc:send codex-main claude-frontend "Can you review the API design?"
```

**Output**:
```json
{
  "status": "sent",
  "from": "codex-main",
  "to": "claude-frontend",
  "message_id": "msg_12345",
  "timestamp": "2025-02-01 14:30:00"
}
```

---

### 📬 `/ipc:check` - Check Messages

Check for new messages sent to your instance.

**Usage**:
```
/ipc:check <instance_name>
```

**Example**:
```
/ipc:check codex-main
```

**Output**:
```json
{
  "messages": [
    {
      "id": "msg_12345",
      "from": "claude-frontend",
      "to": "codex-main",
      "content": "API design looks good, just one suggestion...",
      "timestamp": "2025-02-01 14:28:00",
      "read": false
    }
  ]
}
```

---

### 🤖 `/ipc:responder-start` - Start Auto-Responder

Start background auto-responder for your instance.

**Usage**:
```
/ipc:responder-start <instance_name> [policy]
```

**Policies**:
- `simple`: Echo all messages back
- `smart`: Context-aware responses (default)

**Example**:
```
/ipc:responder-start codex-main smart
```

**Output**:
```json
{
  "status": "started",
  "instance_id": "codex-main",
  "policy": "smart",
  "pid": 12345,
  "started_at": "2025-02-01 14:30:00"
}
```

---

### 📊 `/ipc:responder-status` - Check Responder Status

Check if auto-responder is running for your instance.

**Usage**:
```
/ipc:responder-status <instance_name>
```

**Example**:
```
/ipc:responder-status codex-main
```

**Output**:
```json
{
  "running": true,
  "pid": 12345,
  "policy": "smart",
  "last_activity": "2025-02-01 14:28:00",
  "started_at": "2025-02-01 14:25:00"
}
```

---

### 🛑 `/ipc:responder-stop` - Stop Auto-Responder

Stop auto-responder for your instance.

**Usage**:
```
/ipc:responder-stop <instance_name>
```

**Example**:
```
/ipc:responder-stop codex-main
```

**Output**:
```json
{
  "status": "stopped",
  "instance_id": "codex-main",
  "stopped_at": "2025-02-01 14:30:00"
}
```

---

### 🏥 `/ipc:doctor` - Diagnose and Fix Issues

Run diagnostics and automatically fix common IPC issues.

**Usage**:
```
/ipc:doctor
```

**Output**:
```json
{
  "checks": {
    "broker_running": "✓ PASS",
    "database_healthy": "✓ PASS",
    "port_available": "✓ PASS",
    "permissions": "✓ PASS"
  },
  "fixes_applied": [],
  "recommendations": []
}
```

## Quick Start Workflow

### 1. Initial Setup
```
# Register your instance and start auto-responder
/ipc:setup codex-main

# Verify setup
/ipc:status
```

### 2. Send and Receive Messages
```
# Send a message
/ipc:send codex-main claude-frontend "Ready to collaborate!"

# Check for replies
/ipc:check codex-main
```

### 3. List Active Instances
```
# See who's online
/ipc:list
```

### 4. Manage Auto-Responder
```
# Check responder status
/ipc:responder-status codex-main

# Stop responder if needed
/ipc:responder-stop codex-main

# Restart with different policy
/ipc:responder-start codex-main simple
```

## Configuration

### Environment Variables

Set these in `%USERPROFILE%\.codex\config.toml`:

```toml
[environment]
IPC_CHAT = "D:\\claude-ipc-mcp"  # Your project path
IPC_DB_PATH = "%USERPROFILE%\\.claude-ipc-data\\messages.db"
IPC_HOST = "127.0.0.1"
IPC_GLOBAL_PORT = "9876"
```

### Custom Project Path

If your project is in a different location:

1. Edit `%USERPROFILE%\.codex\config.toml`
2. Update the `IPC_CHAT` path in `[environment]` section
3. Restart Codex CLI

## Troubleshooting

### Commands Not Found

**Problem**: `/ipc:` commands don't appear in Codex CLI

**Solution**:
1. Verify config.toml exists:
   ```powershell
   dir $env:USERPROFILE\.codex\config.toml
   ```
2. Check file contents for `[slash_commands]` section
3. Restart Codex CLI completely

### Broker Connection Error

**Problem**: "Connection refused" or "Broker not running"

**Solution**:
```
# Run diagnostics
/ipc:doctor

# Or manually start broker
cd D:\claude-ipc-mcp
uv run python tools/start_broker.py
```

### Session Token Invalid

**Problem**: "Invalid or missing session token"

**Solution**:
```
# Re-register your instance
/ipc:setup codex-main
```

### Auto-Responder Not Responding

**Problem**: Messages sent but no auto-reply received

**Solution**:
```
# Check responder status
/ipc:responder-status codex-main

# Restart responder
/ipc:responder-stop codex-main
/ipc:responder-start codex-main smart
```

## Advanced Usage

### Custom Auto-Responder Policy

Modify `src/core/responder_proc.py` to implement custom response logic:

```python
def generate_smart_response(message: dict) -> str:
    """Custom smart response logic"""
    content = message.get("content", "")
    
    # Your custom logic here
    if "urgent" in content.lower():
        return "I'll prioritize this task immediately!"
    
    return f"Acknowledged: {content}"
```

### Integration with CI/CD

Use IPC commands in automation scripts:

```powershell
# In your CI/CD pipeline
$result = ipc send ci-bot dev-team "Build completed successfully"
if ($result -match "sent") {
    Write-Host "Notification sent"
}
```

### Multi-Instance Orchestration

Coordinate multiple Codex instances:

```
# Instance 1: Frontend work
/ipc:setup codex-frontend
/ipc:send codex-frontend codex-backend "Frontend APIs ready"

# Instance 2: Backend work
/ipc:setup codex-backend
/ipc:check codex-backend
```

## Security Considerations

- **Session Tokens**: Stored securely in `~/.claude-ipc-data/`
- **Local Only**: Broker binds to 127.0.0.1 (localhost)
- **Token Expiration**: Session tokens expire after 24 hours
- **Rate Limiting**: 100 requests per minute per instance

## Related Documentation

- [Global IPC Usage Guide](GLOBAL_USAGE_KO.md)
- [IPC CLI Commands Reference](ipc_cli_commands.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Installation Guide](INSTALL.md)

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Run `/ipc:doctor` for diagnostics
- Check broker logs in `.ipc/logs/`
- Review [IPC Unified Guide](IPC_UNIFIED_GUIDE_KO.md)
