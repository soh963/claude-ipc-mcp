# Claude IPC MCP - Let Your AIs Talk to Each Other

![Version](https://img.shields.io/badge/version-2.0.0-blue)
[![CI](https://github.com/soh963/claude-ipc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/soh963/claude-ipc-mcp/actions/workflows/ci.yml)
![GitHub stars](https://img.shields.io/github/stars/soh963/claude-ipc-mcp)
![License](https://img.shields.io/badge/license-MIT-green)

Enable AI-to-AI communication using simple natural language commands. Works with Claude Code, Gemini, ChatGPT, and any Python-capable AI assistant.

Quickstart (new CLI): see [docs/README.md](docs/README.md) or [IPC 통합 가이드 (KO)](docs/IPC_UNIFIED_GUIDE_KO.md) for `ipc init → ipc status → ipc ping`.

한국어 빠른 시작:

1) 의존성 동기화: `uv sync`
2) 초기화/상태: `uv run python tools/ipc_global_command.py init` → `status`
3) 핑: `uv run python tools/ipc_global_command.py ping`
4) 질의응답: `uv run python tools/ipc_global_command.py ask --to gemini "상태 어때?" --timeout 10 --poll-interval 0.1`
5) 자동 응답기 시작/상태:
	- `uv run python tools/ipc_global_command.py responder start gemini --policy smart --detach`
	- `uv run python tools/ipc_global_command.py responder status gemini`

## What It Does

Claude IPC MCP lets different AI assistants send messages to each other, even across different platforms and sessions. Think of it as email for AIs - simple, reliable, and persistent.

```
# AI #1 (Claude)
Register this instance as claude
Send message to gemini: Can you help with the database schema?

# AI #2 (Gemini) 
Register this instance as gemini
Check messages
> "Can you help with the database schema?" - from claude
```

## Quick Install (2 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/soh963/claude-ipc-mcp.git
cd claude-ipc-mcp

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. For Claude Code: Install MCP tools (for natural language commands)
./scripts/install-mcp.sh

# 5. For Claude Code: Install slash commands (recommended)
#    Windows:
.\scripts\install-slash-commands.bat

#    Linux/macOS:
chmod +x scripts/install-slash-commands.sh
./scripts/install-slash-commands.sh

# 6. Restart Claude Code and test
#    Natural language: "Register this instance as myname"
#    Slash command: /ipc:setup myname
```

**Full installation guide:** [docs/INSTALL.md](docs/INSTALL.md)

## Key Features

- 💬 **Natural language commands** - No coding required
- 💾 **Persistent messages** - Messages survive restarts
- 🔄 **Cross-platform** - Works between different AI platforms
- 🎯 **Simple setup** - Install once, use everywhere
- 🔐 **Optional security** - Add authentication if needed

## Basic Commands

### Natural Language (MCP Tools)
```
Register this instance as alice     # Set your name
Send message to bob: Hello!         # Send a message
Check messages                      # Check inbox
List instances                      # See who's online
```

### Slash Commands (Recommended)
```
/ipc:setup alice                    # One-click setup (register + auto-responder)
/ipc:send alice bob "Hello!"        # Send message
/ipc:check alice                    # Check inbox
/ipc:list                           # See who's online
/ipc:status                         # Check connection status
/ipc:doctor                         # Diagnose and fix issues
```

**Why slash commands?** They're more reliable and work across different AI CLIs without configuration issues.

## What's New in v2.0

🎉 **Slash Command Format Update** - All Claude Code slash commands now use colon (`:`) separator format:
- `/ipc:setup` (was `/ipc-setup`)
- `/ipc:status` (was `/ipc-status`)
- `/ipc:send` (was `/ipc-send`)
- ... and 24 more commands

See [docs/changes/2025-10-03-slash-command-colon-format.md](docs/changes/2025-10-03-slash-command-colon-format.md) for migration guide.

## Documentation

### Getting Started
- **[docs/INSTALL.md](docs/INSTALL.md)** - Complete installation guide
- **[docs/CLAUDE_CODE_SLASH_COMMANDS.md](docs/CLAUDE_CODE_SLASH_COMMANDS.md)** - Complete slash command reference (27 commands) ⭐
- **[docs/platform-guides/CLAUDE_CODE_SETUP.md](docs/platform-guides/CLAUDE_CODE_SETUP.md)** - Claude Code slash commands setup
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### AI CLI Integration
- **[docs/IPC_CLI_INTEGRATION_SUMMARY.md](docs/IPC_CLI_INTEGRATION_SUMMARY.md)** - Complete CLI integration across all platforms
- **[docs/claude-commands/INSTALL.md](docs/claude-commands/INSTALL.md)** - Claude Code slash commands (25 commands)
- **[docs/gemini-commands/INSTALL.md](docs/gemini-commands/INSTALL.md)** - Gemini CLI integration (24 commands)
- **[docs/codex-config.toml](docs/codex-config.toml)** - Codex CLI configuration (24 commands)

### Korean Documentation
- **[GLOBAL_USAGE_KO.md](docs/GLOBAL_USAGE_KO.md)** - 글로벌 사용 가이드(한글)
- **[IPC CLI 명령 (KO)](docs/ipc_cli_commands.md)** - 통합 CLI 사용법과 옵션(한글)
- **[IPC 통합 가이드 (KO)](docs/IPC_UNIFIED_GUIDE_KO.md)** - 전역→프로젝트→CLI→Responder까지 한 페이지 요약

### Advanced
- **[docs/](docs/)** - Advanced features and platform-specific guides
- **Constitution**: See `.specify/memory/constitution.md`
- **Change Records**: See `docs/changes/` (each behavior/contract change must have a record)

## Requirements

- Python 3.12+ (check with `python3 --version` or `python --version`)
- Any AI assistant with Python execution capability

## Support

Having issues? [Open a GitHub issue](https://github.com/soh963/claude-ipc-mcp/issues)

## License

MIT - Use freely in your projects

---
*"Can't spell EMAIL without AI!"* 📧