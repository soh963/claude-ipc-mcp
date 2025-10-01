# Claude Code Slash Commands Installation

This directory contains all IPC slash commands for Claude Code CLI.

## Installation

Copy all `.md` files to your Claude Code commands directory:

### Windows (PowerShell)

```powershell
# Create commands directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\commands"

# Copy all command files
Copy-Item "D:\claude-ipc-mcp\docs\claude-commands\*.md" "$env:USERPROFILE\.claude\commands\"
```

### Linux/Mac (Bash)

```bash
# Create commands directory if it doesn't exist
mkdir -p ~/.claude/commands

# Copy all command files
cp D:/claude-ipc-mcp/docs/claude-commands/*.md ~/.claude/commands/
```

## Verification

After copying, restart Claude Code and verify commands are available:

1. Open Claude Code
2. Type `/` to see command list
3. Search for "ipc" to see all IPC commands

## Available Commands

### Core Commands
- `/ipc-init` - Initialize project IPC structure
- `/ipc-status` - Check IPC system status
- `/ipc-ping` - Test broker connectivity
- `/ipc-register` - Register instance
- `/ipc-doctor` - System diagnostics

### Communication
- `/ipc-send` - Send message (fire-and-forget)
- `/ipc-ask` - Send message and wait for response
- `/ipc-check` - Check for new messages
- `/ipc-broadcast` - Broadcast to all instances

### Broker Management
- `/ipc-broker-start` - Start global broker
- `/ipc-broker-stop` - Stop global broker
- `/ipc-broker-status` - Check broker status

### Instance Management
- `/ipc-list` - List all instances
- `/ipc-instances-delete` - Delete specific instance
- `/ipc-instances-reset` - Reset all instances

### Message Management
- `/ipc-messages-clear` - Clear all messages

### Session Management
- `/ipc-session` - Show session info
- `/ipc-session-clear` - Clear session data

### Auto-Responder
- `/ipc-responder-start` - Start auto-responder
- `/ipc-responder-start-all` - Start all responders
- `/ipc-responder-stop` - Stop auto-responder
- `/ipc-responder-stop-all` - Stop all responders
- `/ipc-responder-status` - Check responder status

### Advanced
- `/ipc-setup` - Complete setup wizard

## Notes

- All commands use the global IPC broker (port 9876)
- Broker must be running for IPC operations
- Session tokens are stored in project `.ipc/` directory
- Commands support natural language parameters
