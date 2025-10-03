# Slash Command Path Handling Fix - 2025-10-03

## Version Impact
PATCH

## Change Type
Bugfix

## Description

Fixed path handling in all 27 IPC slash command files to use single-quoted absolute paths instead of unquoted paths. This resolves cross-directory session issues where commands executed from different project directories would fail to recognize registered IPC instances.

### Root Cause
Windows paths with backslashes (e.g., `D:\claude-ipc-mcp\tools\...`) were being parsed incorrectly by Git Bash when used without quotes, causing:
1. Path corruption (backslash escape sequences)
2. Session directory mismatch (commands ran in wrong project context)
3. Instance recognition failures

### The Fix
Changed all command execution paths from:
```bash
uv run python D:\claude-ipc-mcp\tools\ipc_global_command.py [subcommand]
```

To:
```bash
uv run python 'D:\claude-ipc-mcp\tools\ipc_global_command.py' [subcommand]
```

### Why Single Quotes?
- **Double quotes**: Allow variable expansion and escape sequences, causing `\c` to be interpreted as control character
- **Single quotes**: Preserve literal path including backslashes, preventing escape sequence interpretation
- **Result**: Absolute paths work correctly from any project directory without changing working directory context

## Files Modified

All 27 files in `C:\Users\lovecat\.claude\commands\ipc\`:

1. ask.md - Ask and wait for response
2. broadcast.md - Broadcast to all instances
3. broker-start.md - Start message broker
4. broker-status.md - Check broker status
5. broker-stop.md - Stop message broker
6. check.md - Check inbox messages
7. doctor.md - Run diagnostics
8. fix.md - Fix configurations
9. init.md - Initialize IPC structure
10. list.md - List all instances
11. ping.md - Test broker connectivity
12. register.md - Register instance
13. rename.md - Rename instance
14. responder-start.md - Start auto-responder
15. responder-start-all.md - Start all responders
16. responder-status.md - Check responder status
17. responder-stop.md - Stop auto-responder
18. responder-stop-all.md - Stop all responders
19. send.md - Send message
20. session.md - View session details
21. session-clear.md - Clear session
22. setup.md - One-click setup
23. status.md - Check connection status
24. validate.md - Validate configurations
25. instances-delete.md - Delete instance
26. instances-reset.md - Reset instances
27. messages-clear.md - Clear messages

## Additional Changes

1. **Updated command format**: Changed from `/ipc-command` to `/ipc:command` format (colon separator)
2. **Added emojis**: Enhanced command descriptions with visual indicators for better UX
3. **Improved documentation**: Added usage examples, troubleshooting guidance, and related commands sections

## Testing

Verified fix across three AI CLIs:
- **Claude Code**: Running from `D:\test-tem` directory
- **Gemini CLI**: Running from separate project directory
- **Codex CLI**: Running from third project directory

**Result**: All three CLIs now correctly recognize all 4 registered instances (claude, codex, gemini, claude-test) when using commands from any project directory.

## Migration Required

NO - Changes are backward compatible. Existing slash commands will work immediately after updating the command files.

## Impact

### Before Fix
- Commands failed with path errors when run from different directories
- Instance recognition varied between AI CLIs
- Session context mismatches caused by `cd` directory changes

### After Fix
- ✅ Commands work correctly from any project directory
- ✅ All AI CLIs recognize the same registered instances
- ✅ Session context maintained in calling directory
- ✅ Path corruption issues eliminated

## Related Issues

- Cross-directory session isolation maintained via per-project `.ipc/` directories
- Global broker (port 9876) serves all projects while maintaining project-specific sessions
- Session tokens persist in `.ipc/state/session.json` for auto-reconnect

## Future Considerations

1. Consider using environment variables for project root path
2. Explore relative path resolution with proper base directory handling
3. Add automated path validation in command execution
