#!/bin/bash
# Setup IPC alias for easy terminal usage

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat << 'EOF'
========================================
IPC Wrapper Alias Setup
========================================

Add the following line to your shell profile:

For Bash (~/.bashrc or ~/.bash_profile):
EOF

echo "alias ipc='$SCRIPT_DIR/ipc-wrapper.sh'"

cat << 'EOF'

For PowerShell ($PROFILE):
EOF

echo "Set-Alias -Name ipc -Value '$SCRIPT_DIR\ipc-wrapper.bat'"

cat << 'EOF'

Then restart your terminal or run:
  source ~/.bashrc

Usage after setup:
  ipc status
  ipc register my-name
  ipc send gemini "Hello"
  ipc ask gemini "Status?"

========================================
EOF
