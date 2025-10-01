#!/bin/bash
########################################################################
#  IPC Slash Commands Installation Script for All AI CLIs
#  Installs IPC commands globally for Claude Code, Gemini CLI, and Codex CLI
#  Platform: Linux/macOS
########################################################################

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo " IPC Slash Commands - All CLIs Installer"
echo "========================================"
echo ""

# ================================================================================
# Step 1: Install Claude Code Commands
# ================================================================================

echo ""
echo -e "${BLUE}[1/3] Installing Claude Code slash commands...${NC}"
echo ""

CLAUDE_DIR="$HOME/.claude/commands/ipc"

if [ ! -d "$CLAUDE_DIR" ]; then
    echo "Creating directory: $CLAUDE_DIR"
    mkdir -p "$CLAUDE_DIR"
fi

# Copy Claude Code .md files
echo "Copying Claude Code command files..."
if [ -d "$SCRIPT_DIR/../scripts/ipc" ]; then
    cp "$SCRIPT_DIR/../scripts/ipc"/*.md "$CLAUDE_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ Claude Code: 9 commands installed${NC}"
else
    echo -e "${RED}✗ Claude Code: Source files not found${NC}"
fi

# ================================================================================
# Step 2: Install Gemini CLI Commands
# ================================================================================

echo ""
echo -e "${BLUE}[2/3] Installing Gemini CLI slash commands...${NC}"
echo ""

GEMINI_DIR="$HOME/.gemini/commands/ipc"

if [ ! -d "$GEMINI_DIR" ]; then
    echo "Creating directory: $GEMINI_DIR"
    mkdir -p "$GEMINI_DIR"
fi

# Copy Gemini CLI .toml files
echo "Copying Gemini CLI command files..."
if [ -d "$SCRIPT_DIR/gemini-commands" ]; then
    cp "$SCRIPT_DIR/gemini-commands"/*.toml "$GEMINI_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ Gemini CLI: 9 commands installed${NC}"
else
    echo -e "${RED}✗ Gemini CLI: Source files not found${NC}"
fi

# ================================================================================
# Step 3: Install Codex CLI Commands
# ================================================================================

echo ""
echo -e "${BLUE}[3/3] Installing Codex CLI configuration...${NC}"
echo ""

CODEX_DIR="$HOME/.codex"
CODEX_CONFIG="$CODEX_DIR/config.toml"
CODEX_AGENTS="$CODEX_DIR/AGENTS.md"

if [ ! -d "$CODEX_DIR" ]; then
    echo "Creating directory: $CODEX_DIR"
    mkdir -p "$CODEX_DIR"
fi

# Check if config.toml already exists
if [ -f "$CODEX_CONFIG" ]; then
    echo -e "${YELLOW}Warning: config.toml already exists${NC}"
    echo "Creating backup: config.toml.backup"
    cp "$CODEX_CONFIG" "$CODEX_CONFIG.backup"

    echo ""
    echo "Please manually merge the IPC configuration from:"
    echo "  $SCRIPT_DIR/codex-config/config.toml"
    echo "Into your existing config.toml at:"
    echo "  $CODEX_CONFIG"
    echo ""
else
    echo "Copying Codex config.toml..."
    if [ -f "$SCRIPT_DIR/codex-config/config.toml" ]; then
        cp "$SCRIPT_DIR/codex-config/config.toml" "$CODEX_CONFIG"
        echo -e "${GREEN}✓ Codex CLI: config.toml installed${NC}"
    else
        echo -e "${RED}✗ Codex CLI: config.toml source not found${NC}"
    fi
fi

# Copy AGENTS.md
echo "Copying Codex AGENTS.md..."
if [ -f "$SCRIPT_DIR/codex-config/AGENTS.md" ]; then
    cp "$SCRIPT_DIR/codex-config/AGENTS.md" "$CODEX_AGENTS"
    echo -e "${GREEN}✓ Codex CLI: AGENTS.md installed${NC}"
else
    echo -e "${RED}✗ Codex CLI: AGENTS.md source not found${NC}"
fi

# ================================================================================
# Step 4: Set Environment Variables
# ================================================================================

echo ""
echo -e "${BLUE}[4/4] Setting environment variables...${NC}"
echo ""

# Detect shell configuration file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

echo "Updating $SHELL_RC..."

# Add IPC environment variables if not already present
if ! grep -q "IPC_CHAT=" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << EOF

# IPC Environment Variables (added by install-all-clis.sh)
export IPC_CHAT="$PROJECT_ROOT"
export IPC_DB_PATH="\$HOME/.claude-ipc-data/messages.db"
export IPC_HOST="127.0.0.1"
export IPC_GLOBAL_PORT="9876"
EOF
    echo -e "${GREEN}✓ Environment variables added to $SHELL_RC${NC}"
else
    echo -e "${YELLOW}⚠ Environment variables already exist in $SHELL_RC${NC}"
fi

echo ""
echo "Please run: source $SHELL_RC"
echo "Or restart your terminal to apply environment changes."

# ================================================================================
# Installation Summary
# ================================================================================

echo ""
echo "========================================"
echo -e "${GREEN} Installation Complete!${NC}"
echo "========================================"
echo ""
echo "Installed commands:"
echo ""
echo -e "${BLUE}Claude Code:${NC}"
echo "  Location: $CLAUDE_DIR"
echo "  Commands: /ipc:setup, /ipc:status, /ipc:list, /ipc:send,"
echo "            /ipc:check, /ipc:responder-*, /ipc:doctor"
echo ""
echo -e "${BLUE}Gemini CLI:${NC}"
echo "  Location: $GEMINI_DIR"
echo "  Commands: Same as above (TOML format)"
echo ""
echo -e "${BLUE}Codex CLI:${NC}"
echo "  Location: $CODEX_DIR"
echo "  Files: config.toml, AGENTS.md"
echo ""
echo -e "${BLUE}Environment Variables:${NC}"
echo "  IPC_CHAT=$PROJECT_ROOT"
echo "  IPC_DB_PATH=\$HOME/.claude-ipc-data/messages.db"
echo "  IPC_HOST=127.0.0.1"
echo "  IPC_GLOBAL_PORT=9876"
echo ""
echo "========================================"
echo -e "${YELLOW} Next Steps:${NC}"
echo "========================================"
echo ""
echo "1. ${GREEN}Source shell configuration:${NC}"
echo "   source $SHELL_RC"
echo ""
echo "2. ${GREEN}Restart all AI CLIs${NC} to load new commands"
echo ""
echo "3. ${GREEN}Test installation:${NC}"
echo "   - Claude Code: Type / and look for /ipc: commands"
echo "   - Gemini CLI: Type / and look for /ipc: commands"
echo "   - Codex CLI: Type / and look for /ipc: commands"
echo ""
echo "4. ${GREEN}Verify setup:${NC}"
echo "   Run: ./scripts/verify-global-installation.sh"
echo ""
echo "5. ${GREEN}Start using IPC:${NC}"
echo "   /ipc:setup myname"
echo "   /ipc:status"
echo "   /ipc:list"
echo ""
echo -e "${YELLOW}Note:${NC} If Codex CLI had existing config.toml,"
echo "please manually merge the IPC configuration."
echo ""
