#!/bin/bash
# Install IPC Slash Commands for Claude Code CLI
# This script registers all IPC commands as slash commands in Claude Code

set -e

echo "========================================"
echo "IPC Slash Commands Installer for Claude Code"
echo "========================================"
echo ""

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create Claude Code slash commands directory if it doesn't exist
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"

if [ ! -d "$COMMANDS_DIR" ]; then
    echo "Creating commands directory: $COMMANDS_DIR"
    mkdir -p "$COMMANDS_DIR"
fi

# Define all IPC slash commands
declare -A COMMANDS=(
    ["ipc-status"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" status","description":"📊 Check IPC broker connection status","category":"ipc"}'
    ["ipc-register"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" register {args[0]}","description":"📝 Register this instance with IPC broker","category":"ipc","requires_args":1,"arg_names":["instance_name"]}'
    ["ipc-list"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" instances list --full","description":"👥 List all registered IPC instances","category":"ipc"}'
    ["ipc-send"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" chat --to {args[0]} \"{args[1]}\"","description":"💬 Send message to another instance","category":"ipc","requires_args":2,"arg_names":["target_instance","message"]}'
    ["ipc-ask"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" ask --to {args[0]} \"{args[1]}\" --timeout 10","description":"❓ Send message and wait for response (10s timeout)","category":"ipc","requires_args":2,"arg_names":["target_instance","message"]}'
    ["ipc-check"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" messages list","description":"📬 Check messages for this instance","category":"ipc"}'
    ["ipc-broadcast"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" broadcast \"{args[0]}\"","description":"📢 Broadcast message to all instances","category":"ipc","requires_args":1,"arg_names":["message"]}'
    ["ipc-responder-start"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" responder start {args[0]} --policy smart --detach","description":"🤖 Start auto-responder for instance","category":"ipc","requires_args":1,"arg_names":["instance_name"]}'
    ["ipc-responder-status"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" responder status {args[0]}","description":"📊 Check auto-responder status","category":"ipc","requires_args":1,"arg_names":["instance_name"]}'
    ["ipc-responder-stop"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" responder stop {args[0]}","description":"🛑 Stop auto-responder for instance","category":"ipc","requires_args":1,"arg_names":["instance_name"]}'
    ["ipc-doctor"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_doctor.py\" --auto-fix","description":"🏥 Run IPC diagnostics and auto-fix issues","category":"ipc"}'
    ["ipc-init"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" init","description":"🚀 Initialize IPC in current project","category":"ipc"}'
    ["ipc-ping"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" ping","description":"🏓 Ping IPC broker to test connectivity","category":"ipc"}'
    ["ipc-rename"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_global_command.py\" rename --from {args[0]} --to {args[1]}","description":"✏️ Rename an IPC instance (rate limited: 1/hour)","category":"ipc","requires_args":2,"arg_names":["old_name","new_name"]}'
    ["ipc-setup"]='{"command":"uv run python \"'"$PROJECT_ROOT"'/tools/ipc_onboard.py\" --name {args[0]} --policy smart","description":"🎯 Complete IPC setup (register + auto-responder)","category":"ipc","requires_args":1,"arg_names":["instance_name"]}'
)

# Create command files
echo "Installing IPC slash commands..."
INSTALLED=0

for CMD_NAME in "${!COMMANDS[@]}"; do
    CMD_FILE="$COMMANDS_DIR/$CMD_NAME.json"
    echo "${COMMANDS[$CMD_NAME]}" > "$CMD_FILE"
    echo "  ✓ Installed: /$CMD_NAME"
    ((INSTALLED++))
done

echo ""
echo "========================================"
echo "✅ Installation Complete!"
echo "========================================"
echo ""
echo "Installed $INSTALLED IPC slash commands"
echo ""
echo "Usage in Claude Code CLI:"
echo "  /ipc-status              - Check broker status"
echo "  /ipc-register myname     - Register instance"
echo "  /ipc-send gemini 'Hi!'   - Send message"
echo "  /ipc-ask gemini 'How?'   - Ask and wait for reply"
echo "  /ipc-check               - Check messages"
echo "  /ipc-responder-start gem - Start auto-responder"
echo ""
echo "Restart Claude Code to see the new commands!"
echo ""
