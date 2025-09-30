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

# 4. For Claude Code: Run installer
./scripts/install-mcp.sh

# 5. Restart Claude Code and test
# Type: Register this instance as myname
```

**Full installation guide:** [docs/INSTALL.md](docs/INSTALL.md)

## Key Features

- 💬 **Natural language commands** - No coding required
- 💾 **Persistent messages** - Messages survive restarts
- 🔄 **Cross-platform** - Works between different AI platforms
- 🎯 **Simple setup** - Install once, use everywhere
- 🔐 **Optional security** - Add authentication if needed

## Basic Commands

```
Register this instance as alice     # Set your name
Send message to bob: Hello!         # Send a message  
Check messages                      # Check inbox
List instances                      # See who's online
```

## Documentation

- **[docs/INSTALL.md](docs/INSTALL.md)** - Complete installation guide
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[docs/](docs/)** - Advanced features and platform-specific guides
- **[GLOBAL_USAGE_KO.md](docs/GLOBAL_USAGE_KO.md)** - 글로벌 사용 가이드(한글)
- **[IPC CLI 명령 (KO)](docs/ipc_cli_commands.md)** - 통합 CLI 사용법과 옵션(한글)
- **[IPC 통합 가이드 (KO)](docs/IPC_UNIFIED_GUIDE_KO.md)** - 전역→프로젝트→CLI→Responder까지 한 페이지 요약
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