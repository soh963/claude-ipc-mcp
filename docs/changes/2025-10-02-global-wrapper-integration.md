# Global Wrapper Integration for All AI CLIs

**Date**: 2025-10-02
**Type**: Enhancement
**Version Impact**: MINOR (new global integration approach)
**Status**: Completed

## Summary

Integrated global IPC wrapper (`scripts/ipc.bat`) across all AI CLIs (Claude Code, Gemini, Codex) to enable IPC functionality from any directory while respecting project-local `.ipc` settings.

## Problem Statement

Previously, IPC commands had three critical issues:

1. **Claude Code**: Slash commands used relative paths (`uv run python tools/...`) which failed when executed from directories outside `D:/claude-ipc-mcp`
2. **Workspace Constraints**: Claude Code cannot access directories outside current workspace
3. **Inconsistent Implementation**: Each AI CLI had different command structures and path handling

## Solution Implemented

### 1. Unified Global Wrapper Approach

**Core Wrapper**: `D:/claude-ipc-mcp/scripts/ipc.bat`
- Uses absolute path to `ipc_global_command.py`
- Auto-initializes `.ipc` in current directory if missing
- Stays in current directory to use project-local settings
- Provides command aliases for compatibility

**Key Features**:
```batch
set "IPC_CMD=D:\claude-ipc-mcp\tools\ipc_global_command.py"
if not exist ".ipc" (
    echo Project not initialized. Running 'ipc init'...
    %PYTHON_CMD% "%IPC_CMD%" init
)
```

### 2. Claude Code Global Slash Commands (9 commands)

**Location**: `C:\Users\lovecat\.claude\commands\ipc\`

**Updated Command Pattern**:
```bash
# OLD (relative path - failed from other directories)
cd D:/claude-ipc-mcp && uv run python tools/ipc_onboard.py --name $ARGUMENTS

# NEW (global wrapper - works from any directory)
D:/claude-ipc-mcp/scripts/ipc.bat init && D:/claude-ipc-mcp/scripts/ipc.bat register $ARGUMENTS
```

**Commands Updated**:
1. `setup.md` - Initialize + register + auto-responder
2. `send.md` - Send messages
3. `check.md` - List messages
4. `list.md` - List instances (fixed: `instances list --full`)
5. `status.md` - System status
6. `doctor.md` - Diagnostics
7. `responder-start.md` - Start auto-responder
8. `responder-status.md` - Check responder status
9. `responder-stop.md` - Stop auto-responder

### 3. Gemini CLI Global Wrapper

**Location**: `C:\Users\lovecat\.gemini\ipc-wrapper.bat`

**Features**:
- Uses global IPC command with absolute path
- Auto-initializes `.ipc` in current directory
- Environment variable set: `IPC_CHAT=D:\claude-ipc-mcp`

**Integration with TOML Commands** (25 commands in `~/.gemini/commands/ipc/`):
```toml
[[slash_commands]]
name = "ipc-register"
command = "C:\\Users\\lovecat\\.gemini\\ipc-wrapper.bat register {instance_name}"
```

### 4. Codex CLI Global Wrapper

**Location**: `C:\Users\lovecat\.codex\ipc-wrapper.bat`

**Integration with config.toml** (24 commands):
```toml
[[slash_commands]]
name = "ipc-register"
command = "C:\\Users\\lovecat\\.codex\\ipc-wrapper.bat register {instance_name}"
```

### 5. Project-Local Wrapper for test-tem

**Location**: `D:\test-tem\ipc.bat`
- Copy of global wrapper for quick local execution
- Uses same absolute path approach

## Technical Details

### Wrapper Benefits

1. **Directory Independence**: Works from any directory
2. **Project Isolation**: Uses current directory's `.ipc` settings
3. **Auto-Initialization**: Creates `.ipc` structure if missing
4. **Consistent Behavior**: Same commands across all AI CLIs

### Command Aliases

The wrapper provides convenient aliases:
```batch
ipc list              → ipc instances list --full
ipc start-broker      → ipc broker start
ipc stop-broker       → ipc broker stop
ipc start-responder   → ipc responder start
ipc stop-responder    → ipc responder stop
```

### Environment Variables

**Gemini-Specific**:
```bash
IPC_CHAT=D:\claude-ipc-mcp  # Required for Gemini TOML commands
```

**Optional Global Settings**:
```bash
IPC_HOST=127.0.0.1          # Default broker host
IPC_GLOBAL_PORT=9876        # Default broker port
IPC_SHARED_SECRET=...       # Optional authentication
```

## Testing Results

### Test Environment: D:\test-tem

**Successful Operations**:
```bash
# Instance registration
✅ .\ipc.bat register test-alice
✅ .\ipc.bat register gemini
✅ .\ipc.bat register codex

# Instance listing
✅ .\ipc.bat instances list --full
   Output: 3 instances (claude, gemini, test-alice)

# Status checks
✅ .\ipc.bat status
✅ .\ipc.bat broker status
```

**Claude Code Slash Commands**:
```
✅ /ipc:setup alice     # Works from test-tem
✅ /ipc:list           # Works from test-tem
✅ /ipc:status         # Works from test-tem
```

## Breaking Changes

None. This is a backward-compatible enhancement.

### Migration Path

**For Existing Users**:
1. Claude Code slash commands auto-update on next restart
2. Gemini users: Copy wrapper to `~/.gemini/ipc-wrapper.bat`
3. Codex users: Copy wrapper to `~/.codex/ipc-wrapper.bat`
4. Update TOML/config commands to use new wrapper paths

**For New Users**:
- Installation scripts automatically set up global wrappers
- No manual configuration needed

## Files Modified

### Claude Code Global Commands
- `C:\Users\lovecat\.claude\commands\ipc\setup.md`
- `C:\Users\lovecat\.claude\commands\ipc\send.md`
- `C:\Users\lovecat\.claude\commands\ipc\check.md`
- `C:\Users\lovecat\.claude\commands\ipc\list.md`
- `C:\Users\lovecat\.claude\commands\ipc\status.md`
- `C:\Users\lovecat\.claude\commands\ipc\doctor.md`
- `C:\Users\lovecat\.claude\commands\ipc\responder-start.md`
- `C:\Users\lovecat\.claude\commands\ipc\responder-status.md`
- `C:\Users\lovecat\.claude\commands\ipc\responder-stop.md`

### New Global Wrappers
- `C:\Users\lovecat\.gemini\ipc-wrapper.bat` (new)
- `C:\Users\lovecat\.codex\ipc-wrapper.bat` (new)
- `D:\test-tem\ipc.bat` (new, local convenience wrapper)

### Documentation
- `D:\test-tem\README-SETUP-COMPLETE.md` (new)
- `D:\test-tem\QUICK-TEST.md` (new)
- `D:\claude-ipc-mcp\docs\changes\2025-10-02-global-wrapper-integration.md` (this file)

## Benefits

1. **Universal Access**: IPC works from any directory for all AI CLIs
2. **Project Isolation**: Each project maintains its own `.ipc` settings
3. **Simplified Installation**: Single wrapper installation per AI CLI
4. **Consistent UX**: Same command structure across Claude, Gemini, Codex
5. **Auto-Configuration**: Wrappers auto-initialize projects as needed
6. **Troubleshooting**: Centralized wrapper makes debugging easier

## Known Limitations

1. **Windows-Only**: Current wrappers are `.bat` files (Windows)
   - Future: Create `.sh` equivalents for Linux/Mac
2. **Claude Code Workspace**: Cannot access files outside workspace
   - Workaround: Use global wrapper with absolute paths
3. **Command Aliases**: Some aliases (like `list`) only work in wrapper, not direct CLI

## Future Enhancements

1. Create Unix shell equivalents (`.sh`) for cross-platform support
2. Add wrapper auto-update mechanism
3. Implement wrapper version checking
4. Create unified installer for all AI CLIs
5. Add wrapper telemetry for usage analytics

## Rollback Procedure

To revert to previous behavior:

1. **Claude Code**: Restore old slash commands from git history
   ```bash
   git checkout HEAD~1 C:\Users\lovecat\.claude\commands\ipc\
   ```

2. **Gemini/Codex**: Remove wrapper references from TOML/config
   ```bash
   rm C:\Users\lovecat\.gemini\ipc-wrapper.bat
   rm C:\Users\lovecat\.codex\ipc-wrapper.bat
   ```

3. **Environment**: Unset IPC_CHAT if set
   ```bash
   setx IPC_CHAT ""
   ```

## Related Changes

- **2025-10-02-mcp-removal.md**: Removed MCP, keeping only slash commands
- **2025-09-29-constitution-v1.0.0.md**: Governance principles guiding this change

## Conclusion

This integration provides a unified, reliable IPC experience across all AI CLIs while maintaining project isolation and simplifying installation. The global wrapper approach solves workspace constraints and path issues that previously prevented proper IPC functionality.
