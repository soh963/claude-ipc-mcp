# Claude Code IPC Setup Guide

Complete guide for installing and using IPC slash commands in Claude Code.

## Prerequisites

- Claude Code installed and running
- Windows PowerShell or Command Prompt
- Python 3.8+ with `uv` package manager
- This repository cloned to your local machine

## Quick Start (5 Minutes)

### Step 1: Install Slash Commands

Open PowerShell or Command Prompt and run:

```powershell
cd D:\claude-ipc-mcp
.\scripts\install-slash-commands.bat
```

When prompted, choose installation scope:
- **Option 1** (Recommended): User-wide - Commands available in ALL projects
- **Option 2**: Project-only - Commands available ONLY in this project

The installer will create 9 IPC commands in `~\.claude\commands\ipc\` directory.

### Step 2: Restart Claude Code

Close and restart Claude Code to load the new commands.

### Step 3: Test Installation

In Claude Code chat, type `/` and you should see IPC commands listed:

```
/ipc:setup             - One-click IPC setup
/ipc:status            - Check connection status
/ipc:list              - List all instances
/ipc:send              - Send message
/ipc:check             - Check messages
/ipc:responder-start   - Start auto-responder
/ipc:responder-status  - Check responder status
/ipc:responder-stop    - Stop responder
/ipc:doctor            - Diagnose and fix issues
```

### Step 4: Setup Your Instance

Run the setup command with your instance name:

```
/ipc:setup claude-main
```

This command automatically:
1. ✅ Checks if broker is running (starts if needed)
2. ✅ Registers your instance with the broker
3. ✅ Saves session token for future use
4. ✅ Starts auto-responder (smart policy)
5. ✅ Verifies connection with ping test

## Usage Examples

### Scenario 1: First-Time Setup

```markdown
# In Claude Code chat

1. /ipc:setup claude-frontend
   → ✅ Instance registered and auto-responder started

2. /ipc:status
   → 📊 Broker: Connected
   → 📝 Instance: claude-frontend (active)
   → 🤖 Responder: Running (smart policy)

3. /ipc:list
   → 👥 Active instances:
   →    - claude-frontend (you)
   →    - gemini-backend
   →    - codex-worker
```

### Scenario 2: Sending and Receiving Messages

```markdown
# Send a message
/ipc:send claude-frontend gemini-backend "Can you help with API design?"

# Check for replies (in gemini's Claude instance)
/ipc:check gemini-backend
→ 📬 1 new message from claude-frontend:
→    "Can you help with API design?"

# Auto-responder will reply automatically if enabled
# Check your inbox
/ipc:check claude-frontend
→ 📬 1 new message from gemini-backend:
→    "Sure! Let's discuss REST vs GraphQL..."
```

### Scenario 3: Troubleshooting

```markdown
# If something doesn't work
/ipc:doctor

# Output:
→ 🏥 IPC Doctor - Diagnostic Report
→
→ ✅ Broker connectivity: OK (12ms)
→ ✅ Database integrity: OK
→ ✅ Session token: Valid (expires in 18h)
→ ⚠️  Auto-responder: Not running
→
→ 🔧 Auto-fixing issues...
→ ✅ Started auto-responder (PID: 12345)
→
→ 🎉 All systems operational!
```

## Advanced Configuration

### Auto-Responder Policies

**Smart Policy (Default)**
- Context-aware responses
- Can understand and reply to questions
- Uses AI for intelligent replies

**Simple Policy**
- Echo messages back
- Useful for testing
- No AI processing

To change policy:
```
/ipc:responder-stop claude-main
/ipc:responder-start claude-main simple
```

### Manual Commands (Alternative to Slash Commands)

If you prefer command-line interface:

```powershell
# Register instance
uv run python tools/ipc_onboard.py --name claude-main --policy smart

# Check status
uv run python tools/ipc_global_command.py status

# Send message
uv run python tools/chat_once.py claude-main gemini-test "Hello!"

# Check messages
uv run python tools/ipc_global_command.py messages check --instance claude-main
```

## File Structure

After installation, your file structure looks like this:

```
%USERPROFILE%\.claude\
└── commands\
    └── ipc\
        ├── setup.md               (/ipc:setup)
        ├── status.md              (/ipc:status)
        ├── list.md                (/ipc:list)
        ├── send.md                (/ipc:send)
        ├── check.md               (/ipc:check)
        ├── responder-start.md     (/ipc:responder-start)
        ├── responder-status.md    (/ipc:responder-status)
        ├── responder-stop.md      (/ipc:responder-stop)
        └── doctor.md              (/ipc:doctor)
```

## Troubleshooting

### Problem: "/ipc: commands not found after installation"

**Solution:**
1. Verify files were created:
   ```powershell
   dir %USERPROFILE%\.claude\commands\ipc
   ```
2. Restart Claude Code (required to load new commands)
3. Try typing `/ipc` and press Tab to see suggestions

### Problem: "Command execution failed"

**Solution:**
1. Check if broker is running:
   ```
   /ipc:status
   ```
2. If broker is down, run:
   ```
   /ipc:doctor
   ```
3. Verify Python and `uv` are in your PATH

### Problem: "Invalid auth token" error

**Solution:**
1. Re-register your instance:
   ```
   /ipc:setup your-name
   ```
2. Check if `IPC_SHARED_SECRET` environment variable matches broker

### Problem: "Instance not found" when sending messages

**Solution:**
1. Verify target instance is registered:
   ```
   /ipc:list
   ```
2. Use exact instance name (case-sensitive)
3. Ensure target's broker is the same (127.0.0.1:9876)

### Problem: Auto-responder not replying

**Solution:**
1. Check responder status:
   ```
   /ipc:responder-status your-name
   ```
2. Restart responder if stopped:
   ```
   /ipc:responder-start your-name smart
   ```
3. Check responder logs:
   ```powershell
   type %USERPROFILE%\.claude-ipc-data\responders\your-name.json
   ```

## Uninstalling

To remove IPC slash commands:

```powershell
# Remove all IPC commands
rmdir /s /q %USERPROFILE%\.claude\commands\ipc

# Restart Claude Code
```

To completely remove all IPC data:

```powershell
# Remove IPC data directory
rmdir /s /q %USERPROFILE%\.claude-ipc-data

# Remove project state (optional)
rmdir /s /q .ipc
```

## Security Notes

- Session tokens are stored in `%USERPROFILE%\.claude-ipc-data\` with 0600 permissions
- All communication is over localhost (127.0.0.1) by default
- Set `IPC_SHARED_SECRET` environment variable for broker authentication
- Auto-responders run as separate processes with limited permissions

## Next Steps

1. **Install in other AI CLIs**:
   - Follow similar process for Gemini CLI and Codex CLI
   - Ensure all instances use the same broker (same host/port)

2. **Set up cross-CLI messaging**:
   - Register instances in each CLI with unique names
   - Test messaging between different AI assistants

3. **Customize auto-responder**:
   - Implement custom response logic in `src/core/responder_proc.py`
   - Create your own response policy

4. **Integrate with CI/CD**:
   - Use IPC for build notifications
   - Automate testing across multiple AI instances

## Support

For issues and questions:
- Check `docs/TROUBLESHOOTING.md`
- Review broker logs in `.ipc/logs/`
- Run `/ipc:doctor` for automatic diagnostics
- Open GitHub issue with error details

## Related Documentation

- [IPC Unified Guide (Korean)](../IPC_UNIFIED_GUIDE_KO.md)
- [CLI Commands Reference](../ipc_cli_commands.md)
- [Cross-CLI Setup](CROSS_CLI_SETUP.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
