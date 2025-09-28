#!/bin/bash
# Bash Script to Setup AI CLI Environment Variables
# For Mac/Linux systems

echo "🚀 AI CLI Environment Setup"
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to add to PATH
add_to_path() {
    local path_to_add="$1"
    local shell_rc="$2"

    if [[ ":$PATH:" != *":$path_to_add:"* ]]; then
        echo "export PATH=\"\$PATH:$path_to_add\"" >> "$shell_rc"
        export PATH="$PATH:$path_to_add"
        echo -e "${GREEN}✅ Added to PATH: $path_to_add${NC}"
    else
        echo -e "${YELLOW}⏭️ Already in PATH: $path_to_add${NC}"
    }
}

# Detect shell configuration file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    echo "Detected Zsh shell"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    echo "Detected Bash shell"
else
    SHELL_RC="$HOME/.profile"
    echo "Using default profile"
fi

# 1. Check Node.js/npm
echo -e "\n${BLUE}📦 Checking Node.js/npm...${NC}"
if command -v npm &> /dev/null; then
    NPM_PREFIX=$(npm config get prefix)
    NPM_BIN="$NPM_PREFIX/bin"
    add_to_path "$NPM_BIN" "$SHELL_RC"
    echo -e "  Claude CLI path: $NPM_BIN"
else
    echo -e "${RED}❌ npm not found. Please install Node.js first.${NC}"
    echo "  Download from: https://nodejs.org/"
fi

# 2. Check Python
echo -e "\n${BLUE}🐍 Checking Python...${NC}"
if command -v python3 &> /dev/null || command -v python &> /dev/null; then
    # Python user base
    PYTHON_USER_BASE=$(python3 -m site --user-base 2>/dev/null || python -m site --user-base 2>/dev/null)
    if [ -n "$PYTHON_USER_BASE" ]; then
        PYTHON_BIN="$PYTHON_USER_BASE/bin"
        add_to_path "$PYTHON_BIN" "$SHELL_RC"
        echo -e "  Gemini CLI path: $PYTHON_BIN"
    fi

    # Also add .local/bin
    LOCAL_BIN="$HOME/.local/bin"
    if [ -d "$LOCAL_BIN" ]; then
        add_to_path "$LOCAL_BIN" "$SHELL_RC"
    fi
else
    echo -e "${RED}❌ Python not found. Please install Python first.${NC}"
    echo "  Download from: https://python.org/"
fi

# 3. Check GitHub CLI
echo -e "\n${BLUE}🔧 Checking GitHub CLI...${NC}"
if command -v gh &> /dev/null; then
    GH_EXT_PATH="$HOME/.config/gh/extensions"
    if [ -d "$GH_EXT_PATH" ]; then
        add_to_path "$GH_EXT_PATH" "$SHELL_RC"
        echo -e "  GitHub Copilot CLI path: $GH_EXT_PATH"
    fi
else
    echo -e "${RED}❌ GitHub CLI not found. Please install gh first.${NC}"
    echo "  Download from: https://cli.github.com/"
fi

# 4. Create unified AI CLI wrapper
echo -e "\n${BLUE}🎯 Creating Unified AI CLI Wrapper...${NC}"

WRAPPER_PATH="$HOME/.ai-cli/bin"
mkdir -p "$WRAPPER_PATH"
add_to_path "$WRAPPER_PATH" "$SHELL_RC"

# Create wrapper scripts
cat > "$WRAPPER_PATH/claude-cli" << 'EOF'
#!/bin/bash
if command -v claude-cli &> /dev/null; then
    claude-cli "$@"
else
    npx claude-cli "$@"
fi
EOF

cat > "$WRAPPER_PATH/gemini-cli" << 'EOF'
#!/bin/bash
if command -v gemini-cli &> /dev/null; then
    gemini-cli "$@"
else
    python3 -m gemini_cli "$@"
fi
EOF

cat > "$WRAPPER_PATH/codex-cli" << 'EOF'
#!/bin/bash
gh copilot "$@"
EOF

# Make scripts executable
chmod +x "$WRAPPER_PATH"/*

echo -e "${GREEN}✅ Wrapper scripts created in: $WRAPPER_PATH${NC}"

# 5. Install AI CLI packages
echo -e "\n${BLUE}📥 Installing AI CLI packages...${NC}"

read -p "Do you want to install AI CLI packages now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install Claude CLI
    if command -v npm &> /dev/null; then
        echo "Installing Claude CLI..."
        npm install -g @anthropic-ai/claude-cli
    fi

    # Install Gemini CLI
    if command -v pip3 &> /dev/null; then
        echo "Installing Gemini CLI..."
        pip3 install google-generativeai-cli
    elif command -v pip &> /dev/null; then
        echo "Installing Gemini CLI..."
        pip install google-generativeai-cli
    fi

    # Install GitHub Copilot CLI
    if command -v gh &> /dev/null; then
        echo "Installing GitHub Copilot CLI..."
        gh extension install github/gh-copilot
    fi
fi

# 6. Source the shell configuration
echo -e "\n${BLUE}🔄 Refreshing environment variables...${NC}"
source "$SHELL_RC"

# 7. Verify installation
echo -e "\n${GREEN}✅ Verification:${NC}"
echo "================================"

# Test each CLI
for cli in claude-cli gemini-cli codex-cli gh; do
    if command -v $cli &> /dev/null; then
        echo -e "${GREEN}✅ $cli: Found${NC}"
    else
        echo -e "${RED}❌ $cli: Not found${NC}"
    fi
done

echo -e "\n${CYAN}🎉 Setup Complete!${NC}"
echo -e "${YELLOW}Please run: source $SHELL_RC${NC}"
echo -e "${YELLOW}Or restart your terminal for changes to take effect.${NC}"

echo -e "\n${BLUE}Usage examples:${NC}"
echo "  claude-cli 'Hello Claude!'"
echo "  gemini-cli 'Hello Gemini!'"
echo "  codex-cli 'Generate Python code'"