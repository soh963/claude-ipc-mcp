# MCP Configuration Removal - 2025-10-02

## Change Summary

Removed MCP (Model Context Protocol) configuration from Claude Code setup, keeping only slash commands for IPC functionality.

## Reason

- **Slash commands are more reliable** and work across different AI CLIs without configuration issues
- **MCP is optional**, not required for core IPC functionality
- **Reduces complexity** by having a single, consistent interface

## Changes Made

### 1. MCP Configuration Removed
- **File**: `C:\Users\lovecat\AppData\Roaming\Claude\claude_desktop_config.json`
- **Action**: Removed `claude-ipc` entry from `mcpServers` section
- **Before**:
```json
"claude-ipc": {
  "command": "uvx",
  "args": [
    "--from",
    "D:\\claude-ipc-mcp",
    "claude-ipc-mcp"
  ]
}
```
- **After**: Entry completely removed

### 2. Slash Commands Installed
- **Location**: `C:\Users\lovecat\.claude\commands\ipc\`
- **Scope**: User-wide (all projects)
- **Commands**:
  - `/ipc:setup` - One-click IPC setup
  - `/ipc:status` - Check connection status
  - `/ipc:list` - List all instances
  - `/ipc:send` - Send message
  - `/ipc:check` - Check messages
  - `/ipc:responder-start` - Start auto-responder
  - `/ipc:responder-status` - Check responder status
  - `/ipc:responder-stop` - Stop responder
  - `/ipc:doctor` - Diagnose and fix issues

## Impact

### What Still Works ✅
- All IPC functionality through slash commands
- Message broker operations
- Cross-AI communication
- Auto-responder system
- Session management

### What No Longer Works ❌
- Natural language MCP commands like:
  - "Register this instance as alice"
  - "Send message to bob: Hello"
  - "Check messages"

### Migration Path

**Old (MCP Natural Language)**:
```
Register this instance as alice
Send message to bob: Hello
Check messages
```

**New (Slash Commands)**:
```
/ipc:setup alice
/ipc:send alice bob "Hello"
/ipc:check alice
```

## Version Impact

- **Type**: MINOR (feature removal, backward compatible with slash commands)
- **Version**: Will be documented in next release
- **Breaking Change**: No (slash commands were always available)

## Testing

1. ✅ MCP removed from config file
2. ✅ Slash commands installed in user directory
3. ✅ 9 slash command files created successfully
4. ⚠️ Requires Claude Code restart to load commands

## Next Steps

1. **Restart Claude Code** to load slash commands
2. **Test slash commands**: `/ipc:setup testuser`
3. **Update documentation** to recommend slash commands only
4. **Consider**: Update README.md to make slash commands the primary method

## Related Files

- MCP Server: `src/claude_ipc_server.py` (no changes needed)
- Installation script: `scripts/install-slash-commands.bat`
- Documentation: `docs/platform-guides/CLAUDE_CODE_SETUP.md`
- Config file: `C:\Users\lovecat\AppData\Roaming\Claude\claude_desktop_config.json`

## Rollback Procedure

If MCP functionality is needed again:

```bash
# Reinstall MCP
./scripts/install-mcp.sh

# Choose option 1 (user level)
# Restart Claude Code
```

The slash commands can coexist with MCP if needed.
