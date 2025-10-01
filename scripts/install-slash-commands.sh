#!/bin/bash
########################################################################
#  IPC Slash Commands Installation Script for Claude Code
#  Automatically installs all IPC-related slash commands
#  Platform: Linux/macOS
########################################################################

set -e

# Configuration
CLAUDE_COMMANDS_DIR="$HOME/.claude/commands"
PROJECT_COMMANDS_DIR=".claude/commands"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo " IPC Slash Commands Installer"
echo "========================================"
echo ""

# Ask installation scope
echo "Where would you like to install IPC commands?"
echo ""
echo "[1] User-wide (recommended) - $HOME/.claude/commands"
echo "    Commands available in ALL projects"
echo ""
echo "[2] Project-only - .claude/commands"
echo "    Commands available ONLY in this project"
echo ""
read -p "Enter choice (1 or 2): " INSTALL_SCOPE

if [ "$INSTALL_SCOPE" == "1" ]; then
    TARGET_DIR="$CLAUDE_COMMANDS_DIR"
    SCOPE_NAME="user-wide"
elif [ "$INSTALL_SCOPE" == "2" ]; then
    TARGET_DIR="$PROJECT_COMMANDS_DIR"
    SCOPE_NAME="project-only"
else
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Installing IPC commands ($SCOPE_NAME)...${NC}"
echo "Target directory: $TARGET_DIR"
echo ""

# Create commands directory if it doesn't exist
if [ ! -d "$TARGET_DIR/ipc" ]; then
    echo -e "${GREEN}Creating directory: $TARGET_DIR/ipc${NC}"
    mkdir -p "$TARGET_DIR/ipc"
fi

# Create ipc-setup.md
echo -e "${BLUE}Creating /ipc:setup command...${NC}"
cat > "$TARGET_DIR/ipc/setup.md" << 'EOF'
# IPC Setup Command

Complete IPC setup in one command - register this instance and start auto-responder.

## What this command does:
- Registers this Claude instance with the IPC broker
- Starts auto-responder for automatic message handling
- Verifies connection with ping test

## Usage:
```
/ipc:setup myname
```

## Arguments:
- $ARGUMENTS: Your instance name (alphanumeric, dash, underscore only)

Now executing setup...

```bash
uv run python tools/ipc_onboard.py --name $ARGUMENTS --policy smart
```
EOF

# Create ipc-status.md
echo -e "${BLUE}Creating /ipc:status command...${NC}"
cat > "$TARGET_DIR/ipc/status.md" << 'EOF'
# IPC Status Command

Check your IPC connection status and responder state.

## What this command shows:
- Broker connection status
- Your instance registration
- Auto-responder status
- Recent message activity

## Usage:
```
/ipc:status
```

Checking IPC status...

```bash
uv run python tools/ipc_global_command.py status --json
```
EOF

# Create ipc-list.md
echo -e "${BLUE}Creating /ipc:list command...${NC}"
cat > "$TARGET_DIR/ipc/list.md" << 'EOF'
# IPC List Instances Command

List all AI instances currently connected to the IPC broker.

## What this command shows:
- All registered instances
- Last activity timestamp
- Active auto-responders

## Usage:
```
/ipc:list
```

Retrieving instance list...

```bash
uv run python tools/ipc_global_command.py instances --format table
```
EOF

# Create ipc-send.md
echo -e "${BLUE}Creating /ipc:send command...${NC}"
cat > "$TARGET_DIR/ipc/send.md" << 'EOF'
# IPC Send Message Command

Send a message to another AI instance through IPC.

## Arguments Format:
```
/ipc:send FROM TO MESSAGE
```

## Example:
```
/ipc:send claude gemini "Can you help with the API design?"
```

## What happens:
- Message is queued in broker
- Target instance receives notification
- Auto-responder may reply automatically

Sending message...

```bash
uv run python tools/chat_once.py $ARGUMENTS
```
EOF

# Create ipc-check.md
echo -e "${BLUE}Creating /ipc:check command...${NC}"
cat > "$TARGET_DIR/ipc/check.md" << 'EOF'
# IPC Check Messages Command

Check for new messages sent to this instance.

## Usage:
```
/ipc:check myname
```

## Arguments:
- $ARGUMENTS: Your instance name

## What you'll see:
- List of unread messages
- Sender and timestamp
- Message content

Checking messages...

```bash
uv run python tools/ipc_global_command.py messages check --instance $ARGUMENTS
```
EOF

# Create ipc-responder-start.md
echo -e "${BLUE}Creating /ipc:responder-start command...${NC}"
cat > "$TARGET_DIR/ipc/responder-start.md" << 'EOF'
# IPC Start Auto-Responder Command

Start automatic message responder for this instance.

## Arguments Format:
```
/ipc:responder-start INSTANCE_NAME [POLICY]
```

## Policies:
- **simple**: Echo all messages back
- **smart**: Context-aware responses (default)

## Example:
```
/ipc:responder-start claude smart
```

Starting auto-responder...

```bash
uv run python tools/ipc_global_command.py responder start $ARGUMENTS --detach
```
EOF

# Create ipc-responder-status.md
echo -e "${BLUE}Creating /ipc:responder-status command...${NC}"
cat > "$TARGET_DIR/ipc/responder-status.md" << 'EOF'
# IPC Responder Status Command

Check if auto-responder is running for your instance.

## Usage:
```
/ipc:responder-status myname
```

## Arguments:
- $ARGUMENTS: Your instance name

## What you'll see:
- Running status (active/stopped)
- Process ID if running
- Last activity timestamp
- Current policy

Checking responder status...

```bash
uv run python tools/ipc_global_command.py responder status $ARGUMENTS
```
EOF

# Create ipc-responder-stop.md
echo -e "${BLUE}Creating /ipc:responder-stop command...${NC}"
cat > "$TARGET_DIR/ipc/responder-stop.md" << 'EOF'
# IPC Stop Responder Command

Stop auto-responder for this instance.

## Usage:
```
/ipc:responder-stop myname
```

## Arguments:
- $ARGUMENTS: Your instance name

Stopping responder...

```bash
uv run python tools/ipc_global_command.py responder stop $ARGUMENTS
```
EOF

# Create ipc-doctor.md
echo -e "${BLUE}Creating /ipc:doctor command...${NC}"
cat > "$TARGET_DIR/ipc/doctor.md" << 'EOF'
# IPC Doctor Command

Diagnose and automatically fix common IPC connection issues.

## What this command checks:
- Broker connectivity
- Database integrity
- Session token validity
- Auto-responder health
- File permissions

## What it can fix:
- Restart dead broker
- Reset expired sessions
- Fix database schema
- Clean up zombie processes

## Usage:
```
/ipc:doctor
```

Running diagnostics...

```bash
uv run python tools/ipc_doctor.py --auto-fix
```
EOF

echo ""
echo "========================================"
echo -e "${GREEN} Installation Complete!${NC}"
echo "========================================"
echo ""
echo "Installed commands:"
echo "  /ipc:setup             - One-click IPC setup"
echo "  /ipc:status            - Check connection status"
echo "  /ipc:list              - List all instances"
echo "  /ipc:send              - Send message"
echo "  /ipc:check             - Check messages"
echo "  /ipc:responder-start   - Start auto-responder"
echo "  /ipc:responder-status  - Check responder status"
echo "  /ipc:responder-stop    - Stop responder"
echo "  /ipc:doctor            - Diagnose and fix issues"
echo ""
echo "Location: $TARGET_DIR/ipc/"
echo ""
echo "To use these commands in Claude Code:"
echo "  1. Restart Claude Code to load new commands"
echo "  2. Type / in chat to see all commands"
echo "  3. Use /ipc: prefix to access IPC commands"
echo ""
echo -e "${YELLOW}Example: /ipc:setup claude-main${NC}"
echo ""
