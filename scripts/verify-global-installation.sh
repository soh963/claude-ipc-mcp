#!/bin/bash
# ================================================================================
# IPC Global Installation Verification Script
# Verifies that IPC slash commands are correctly installed for all AI CLIs
# Platform: Linux/macOS
# ================================================================================

set +e  # Don't exit on errors, we want to show all failures

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} IPC Installation Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ================================================================================
# Verification Functions
# ================================================================================

test_directory_exists() {
    local path=$1
    local name=$2

    if [ -d "$path" ]; then
        echo -e "${GREEN}✓ $name directory exists: $path${NC}"
        return 0
    else
        echo -e "${RED}✗ $name directory NOT found: $path${NC}"
        return 1
    fi
}

test_files_exist() {
    local path=$1
    local pattern=$2
    local expected_count=$3
    local name=$4

    if [ -d "$path" ]; then
        local count=$(find "$path" -maxdepth 1 -name "$pattern" 2>/dev/null | wc -l)

        if [ "$count" -eq "$expected_count" ]; then
            echo -e "${GREEN}✓ $name: $count/$expected_count files found${NC}"
            return 0
        elif [ "$count" -gt 0 ]; then
            echo -e "${YELLOW}⚠ $name: $count/$expected_count files found (incomplete)${NC}"
            return 1
        else
            echo -e "${RED}✗ $name: No files found${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ $name: Directory does not exist${NC}"
        return 1
    fi
}

test_environment_variable() {
    local var_name=$1
    local expected_pattern=$2

    local value="${!var_name}"

    if [ -n "$value" ]; then
        if [ -n "$expected_pattern" ]; then
            if [[ "$value" =~ $expected_pattern ]]; then
                echo -e "${GREEN}✓ $var_name=$value${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ $var_name=$value (unexpected value)${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✓ $var_name=$value${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ $var_name not set${NC}"
        return 1
    fi
}

# ================================================================================
# Verification: Claude Code
# ================================================================================

echo ""
echo -e "${BLUE}[1/4] Verifying Claude Code installation...${NC}"
echo ""

CLAUDE_DIR="$HOME/.claude/commands/ipc"
CLAUDE_OK=true

test_directory_exists "$CLAUDE_DIR" "Claude Code" || CLAUDE_OK=false
test_files_exist "$CLAUDE_DIR" "*.md" 9 "Claude Code commands" || CLAUDE_OK=false

if [ "$CLAUDE_OK" = true ]; then
    echo -e "${GREEN}✓ Claude Code installation: PASS${NC}"
else
    echo -e "${RED}✗ Claude Code installation: FAIL${NC}"
fi

# ================================================================================
# Verification: Gemini CLI
# ================================================================================

echo ""
echo -e "${BLUE}[2/4] Verifying Gemini CLI installation...${NC}"
echo ""

GEMINI_DIR="$HOME/.gemini/commands/ipc"
GEMINI_OK=true

test_directory_exists "$GEMINI_DIR" "Gemini CLI" || GEMINI_OK=false
test_files_exist "$GEMINI_DIR" "*.toml" 9 "Gemini CLI commands" || GEMINI_OK=false

if [ "$GEMINI_OK" = true ]; then
    echo -e "${GREEN}✓ Gemini CLI installation: PASS${NC}"
else
    echo -e "${RED}✗ Gemini CLI installation: FAIL${NC}"
fi

# ================================================================================
# Verification: Codex CLI
# ================================================================================

echo ""
echo -e "${BLUE}[3/4] Verifying Codex CLI installation...${NC}"
echo ""

CODEX_DIR="$HOME/.codex"
CODEX_CONFIG="$CODEX_DIR/config.toml"
CODEX_AGENTS="$CODEX_DIR/AGENTS.md"
CODEX_OK=true

test_directory_exists "$CODEX_DIR" "Codex CLI" || CODEX_OK=false

if [ -f "$CODEX_CONFIG" ]; then
    echo -e "${GREEN}✓ Codex config.toml exists${NC}"

    # Check if config contains IPC commands
    if grep -q "ipc:setup" "$CODEX_CONFIG"; then
        echo -e "${GREEN}✓ Codex config.toml contains IPC commands${NC}"
    else
        echo -e "${YELLOW}⚠ Codex config.toml missing IPC commands${NC}"
        CODEX_OK=false
    fi
else
    echo -e "${RED}✗ Codex config.toml NOT found${NC}"
    CODEX_OK=false
fi

if [ -f "$CODEX_AGENTS" ]; then
    echo -e "${GREEN}✓ Codex AGENTS.md exists${NC}"
else
    echo -e "${RED}✗ Codex AGENTS.md NOT found${NC}"
    CODEX_OK=false
fi

if [ "$CODEX_OK" = true ]; then
    echo -e "${GREEN}✓ Codex CLI installation: PASS${NC}"
else
    echo -e "${RED}✗ Codex CLI installation: FAIL${NC}"
fi

# ================================================================================
# Verification: Environment Variables
# ================================================================================

echo ""
echo -e "${BLUE}[4/4] Verifying environment variables...${NC}"
echo ""

ENV_OK=true

test_environment_variable "IPC_CHAT" "claude-ipc-mcp" || ENV_OK=false
test_environment_variable "IPC_DB_PATH" ".claude-ipc-data/messages.db" || ENV_OK=false
test_environment_variable "IPC_HOST" "127.0.0.1" || ENV_OK=false
test_environment_variable "IPC_GLOBAL_PORT" "9876" || ENV_OK=false

if [ "$ENV_OK" = true ]; then
    echo -e "${GREEN}✓ Environment variables: PASS${NC}"
else
    echo -e "${RED}✗ Environment variables: FAIL${NC}"
fi

# ================================================================================
# Overall Summary
# ================================================================================

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ALL_OK=true
[ "$CLAUDE_OK" = true ] || ALL_OK=false
[ "$GEMINI_OK" = true ] || ALL_OK=false
[ "$CODEX_OK" = true ] || ALL_OK=false
[ "$ENV_OK" = true ] || ALL_OK=false

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}🎉 All checks PASSED!${NC}"
    echo ""
    echo -e "${GREEN}You can now use IPC slash commands in all AI CLIs:${NC}"
    echo -e "${GREEN}  /ipc:setup myname${NC}"
    echo -e "${GREEN}  /ipc:status${NC}"
    echo -e "${GREEN}  /ipc:list${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Some checks FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Results:${NC}"
    [ "$CLAUDE_OK" = true ] && echo -e "  Claude Code: ${GREEN}PASS${NC}" || echo -e "  Claude Code: ${RED}FAIL${NC}"
    [ "$GEMINI_OK" = true ] && echo -e "  Gemini CLI:  ${GREEN}PASS${NC}" || echo -e "  Gemini CLI:  ${RED}FAIL${NC}"
    [ "$CODEX_OK" = true ] && echo -e "  Codex CLI:   ${GREEN}PASS${NC}" || echo -e "  Codex CLI:   ${RED}FAIL${NC}"
    [ "$ENV_OK" = true ] && echo -e "  Environment: ${GREEN}PASS${NC}" || echo -e "  Environment: ${RED}FAIL${NC}"
    echo ""
    echo -e "${YELLOW}Please run: ./scripts/install-all-clis.sh${NC}"
    echo ""
fi

# ================================================================================
# Detailed File Listing (if requested)
# ================================================================================

read -p "Show detailed file listing? (y/N): " show_details

if [ "$show_details" = "y" ] || [ "$show_details" = "Y" ]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Detailed File Listing${NC}"
    echo -e "${BLUE}========================================${NC}"

    echo ""
    echo -e "${BLUE}Claude Code files:${NC}"
    if [ -d "$CLAUDE_DIR" ]; then
        ls -la "$CLAUDE_DIR"/*.md 2>/dev/null | awk '{print "  " $9}'
    fi

    echo ""
    echo -e "${BLUE}Gemini CLI files:${NC}"
    if [ -d "$GEMINI_DIR" ]; then
        ls -la "$GEMINI_DIR"/*.toml 2>/dev/null | awk '{print "  " $9}'
    fi

    echo ""
    echo -e "${BLUE}Codex CLI files:${NC}"
    if [ -d "$CODEX_DIR" ]; then
        ls -la "$CODEX_DIR"/*.toml "$CODEX_DIR"/*.md 2>/dev/null | awk '{print "  " $9}'
    fi
fi

echo ""
echo -e "${BLUE}Verification complete!${NC}"
echo ""
