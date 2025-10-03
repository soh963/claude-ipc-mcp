# Slash Command Format Migration to Colon Separator - 2025-10-03

## Version Impact
MINOR (1.x.0 → 1.x+1.0)

## Change Type
Improvement / User Experience Enhancement

## Description

Reorganized all Claude Code CLI slash commands to use colon (`:`) separator format instead of dash (`-`) format for better hierarchical command structure and improved discoverability.

**Before:**
```
/ipc-setup
/ipc-status
/ipc-send
/ipc-check
... (27 commands)
```

**After:**
```
/ipc:setup
/ipc:status
/ipc:send
/ipc:check
... (27 commands)
```

### Technical Implementation

- Moved all 27 `ipc-*.md` command files from `C:\Users\lovecat\.claude\commands\` to `C:\Users\lovecat\.claude\commands\ipc\` subdirectory
- Removed `ipc-` prefix from filenames (e.g., `ipc-setup.md` → `setup.md`)
- Claude Code CLI automatically converts directory structure to colon format
- Command execution paths remain unchanged (still use `uv run python tools/ipc_global_command.py`)

### Commands Affected (27 total)

**Setup & Management:**
- `/ipc:setup`, `/ipc:init`, `/ipc:register`, `/ipc:validate`

**Status & Diagnostics:**
- `/ipc:status`, `/ipc:ping`, `/ipc:doctor`, `/ipc:fix`

**Messaging:**
- `/ipc:send`, `/ipc:check`, `/ipc:ask`, `/ipc:broadcast`

**Instance Management:**
- `/ipc:list`, `/ipc:rename`, `/ipc:instances-delete`, `/ipc:instances-reset`

**Auto-Responder:**
- `/ipc:responder-start`, `/ipc:responder-status`, `/ipc:responder-stop`, `/ipc:responder-start-all`, `/ipc:responder-stop-all`

**Broker Management:**
- `/ipc:broker-start`, `/ipc:broker-status`, `/ipc:broker-stop`

**Session & Messages:**
- `/ipc:session`, `/ipc:session-clear`, `/ipc:messages-clear`

## Migration Required

**For Users:**
- Replace all `/ipc-*` commands with `/ipc:*` format
- Old format will no longer work after updating command files
- Update any scripts or documentation referencing old command format

**Migration Examples:**
```bash
# Old → New
/ipc-setup myname          → /ipc:setup myname
/ipc-status                → /ipc:status
/ipc-send alice bob "Hi"   → /ipc:send alice bob "Hi"
/ipc-check alice           → /ipc:check alice
```

**Automated Migration:**
Users can update their command directory manually or re-run:
```powershell
./scripts/install-slash-commands.bat
```

## Enhanced Features

### Improved Command Descriptions
All commands now have emoji icons and detailed descriptions in frontmatter:
```markdown
---
allowed-tools: [Bash]
description: "📊 Check IPC connection status"
---
```

### Post-Restart Troubleshooting
Added comprehensive restart recovery guidance in key commands:
- `/ipc:status` - Auto-reconnect features and troubleshooting steps
- `/ipc:setup` - Post-restart instructions
- `/ipc:send` - Detailed usage examples
- `/ipc:check` - Auto-responder integration notes

### Documentation Updates
- Created `docs/CLAUDE_CODE_SLASH_COMMANDS.md` - Complete 27-command reference guide
- Added restart troubleshooting section with 4-step recovery process
- Documented usage scenarios: AI collaboration, auto-responder, multi-project
- Included best practices and v2.0 changelog

## Testing

**Verification Steps:**
1. Open Claude Code CLI
2. Type `/` and verify menu shows `/ipc:*` commands with emoji icons
3. Test command execution: `/ipc:status`
4. Verify all 27 commands work with new format
5. Test post-restart workflow using troubleshooting guide

**Expected Results:**
- Menu displays hierarchical `ipc:` commands with descriptions
- All commands execute correctly with new format
- Post-restart recovery process resolves connection issues

## Breaking Changes

**Yes - Command syntax changed:**
- Old `/ipc-*` format no longer supported
- Users must update command references in scripts/workflows
- One-time migration required for existing users

## Related Issues

- Addresses user request for hierarchical command structure
- Fixes post-restart broker/instance recognition issues with improved documentation
- Improves command discoverability with consistent naming

## Files Modified

### Command Files (27 files)
- Moved from: `C:\Users\lovecat\.claude\commands\ipc-*.md`
- Moved to: `C:\Users\lovecat\.claude\commands\ipc\*.md`

### Enhanced Commands
- `ipc/status.md` - Added troubleshooting and auto-reconnect guidance
- `ipc/setup.md` - Added post-restart instructions
- `ipc/send.md` - Improved examples and argument descriptions
- `ipc/check.md` - Added auto-responder integration notes

### Documentation
- `docs/CLAUDE_CODE_SLASH_COMMANDS.md` - New comprehensive guide (307 lines)
- `docs/changes/2025-10-03-slash-command-colon-format.md` - This change record

## Rollback Procedure

If needed, rollback by moving files back:
```bash
cd "C:\Users\lovecat\.claude\commands\ipc"
for file in *.md; do
    mv "$file" "../ipc-$file"
done
```

## References

- Claude Code CLI documentation: Uses directory structure for hierarchical commands
- Project Constitution Principle V: Change documentation requirement
- User request: 2025-10-03 command reorganization
