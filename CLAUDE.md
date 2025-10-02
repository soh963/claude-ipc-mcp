# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude IPC MCP enables inter-process communication between AI assistants (Claude, Gemini, ChatGPT, etc.) using a message broker system. AI instances can register themselves, send/receive messages, and communicate across different sessions and platforms.

**Core Concept**: "Email for AIs" - simple, persistent, cross-platform messaging using natural language or CLI commands.

**Key Architecture**: Global TCP broker (port 9876) + per-project `.ipc/` state + SQLite persistence (~/.claude-ipc-data/messages.db)

## Quick Start Commands

```powershell
# Setup (one-time)
uv sync                                    # Install dependencies (Python 3.12+)
./scripts/install-mcp.sh                   # Install MCP for Claude Code (restart required)
./scripts/install-slash-commands.bat       # Install slash commands (Windows, recommended)

# Initialize & verify
uv run python tools/ipc_global_command.py init      # Create .ipc/ structure
uv run python tools/ipc_global_command.py status    # Check broker
uv run python tools/ipc_global_command.py ping      # Test connectivity

# CLI usage (unified command interface)
uv run python tools/ipc_global_command.py ask --to gemini "message" --timeout 10
uv run python tools/ipc_global_command.py responder start gemini --policy smart --detach
uv run python tools/ipc_global_command.py responder status gemini

# Slash commands (recommended - more reliable)
/ipc:setup myname                          # One-click setup (register + auto-responder)
/ipc:send alice bob "Hello!"               # Send message
/ipc:check alice                           # Check inbox
/ipc:status                                # Check connection

# Natural language (MCP tools - after MCP installation)
Register this instance as myname
Send message to alice: Can you help?
Check messages
List instances
```

## Architecture Overview

### Core Components

1. **Message Broker** (`src/claude_ipc_server.py`)
   - TCP socket server (127.0.0.1:9876 by default)
   - SQLite persistence at `~/.claude-ipc-data/messages.db`
   - Session-based authentication with token hashing
   - Rate limiting (100 req/min per instance)
   - Automatic name forwarding for renamed instances
   - Large message file storage (>10KB threshold)

2. **Broker Client** (`src/core/broker_client.py`)
   - Socket communication wrapper
   - Auto-start broker detection
   - Environment-based configuration (IPC_HOST, IPC_GLOBAL_PORT)

3. **Project Context System** (`src/core/project_context.py`)
   - Per-project `.ipc/` directory structure
   - Session state persistence
   - Project isolation support

4. **CLI Entry Point** (`tools/ipc_global_command.py`)
   - Unified command interface for all operations
   - Commands: init, status, ping, ask, responder, messages, instances
   - Global PATH integration via `scripts/ipc.bat`

### Directory Structure

```
src/
├── claude_ipc_server.py          # MCP server & broker
├── core/
│   ├── broker_client.py          # Client communication
│   ├── broker.py                 # Broker implementation
│   ├── async_broker.py           # Async broker variant
│   ├── project_context.py        # Project isolation
│   ├── router.py                 # Message routing
│   ├── security.py               # Auth & validation
│   ├── retry.py                  # Retry logic
│   ├── responder_proc.py         # Auto-responder process
│   └── models/                   # Data models
│       ├── message.py
│       ├── broker.py
│       ├── responder.py
│       ├── routing.py
│       └── project_context.py
├── cli/
│   └── commands/                 # CLI subcommands
│       ├── init_cmd.py
│       ├── status_cmd.py
│       ├── ping_cmd.py
│       ├── chat_cmd.py
│       ├── register_cmd.py
│       └── doctor_cmd.py
tools/
├── ipc_global_command.py         # Main CLI entry point
├── start_broker.py               # Legacy broker launcher
├── auto_responder.py             # Auto-reply daemon
├── chat_once.py                  # Single message sender
├── nl_auto_chat.py               # Natural language chat
└── [various utility scripts]
```

### Key Design Patterns

**Project Isolation**:
- Each project gets `.ipc/` directory with config, logs, state, secret subdirectories
- Project-specific instance IDs and session management
- Global broker serves all projects via TCP

**Message Flow**:
1. Client calls `broker_client.register(instance_id)` → receives session_token
2. Client calls `broker_client.send(session_token, from_id, to_id, content)`
3. Broker validates session, queues message in SQLite
4. Recipient calls `broker_client.check(session_token)` → retrieves messages
5. Messages marked as read after retrieval

**Security Model**:
- Optional shared secret authentication (IPC_SHARED_SECRET env var)
- Session tokens (32-byte random, SHA-256 hashed in DB)
- Instance ID validation (1-32 alphanumeric, dash, underscore)
- Rate limiting per instance
- Secure file permissions (0o700 dirs, 0o600 files)

## Development Workflows

### Testing

```powershell
# Run all tests
uv run pytest test/ -v

# Run specific test suite or function
uv run pytest test/test_security.py -v
uv run pytest test/test_security.py::test_session_token_validation -v
uv run pytest test/ -k "security" -v              # Pattern matching

# Coverage and parallel execution
uv run pytest test/ -v --cov=src --cov-report=html
uv run pytest test/ -v -n auto                     # Parallel (faster)
```

**Main test files**:
- `test/test_security.py` - Session tokens, auth, validation
- `test/test_project_isolation.py` - Per-project .ipc/ isolation
- `test/test_global_ipc.py` - Global broker functionality
- `test/test_cross_cli_communication.py` - Cross-platform messaging
- `test/test_broker_direct.py` - Direct broker testing

### Code Quality

```bash
uv run black src/ tools/ test/             # Format
uv run ruff check src/ tools/ test/        # Lint
uv run mypy src/                           # Type check
```

### Database Management

```powershell
uv run python tools/ipc_doctor.py          # Health check
uv run python tools/fix_database.py        # Schema fixes
python tools/reset_all_ipc.py              # WARNING: Deletes all messages
```

### Debugging

**Broker issues**:
```powershell
uv run python tools/ipc_global_command.py status    # Check status
uv run python tools/start_broker.py                 # Manual start
# Logs: .ipc/logs/ or console output
```

**Common fixes**:
- Port conflict → Set `IPC_GLOBAL_PORT` env var
- Database locked → Stop clients, restart broker
- Session expired → Re-register instance
- Messages not delivered → Check recipient registered and broker running

### Extending the System

**New CLI commands**:
1. Add module in `src/cli/commands/your_cmd.py`
2. Register in `tools/ipc_global_command.py` (see existing commands for pattern)
3. Update `docs/ipc_cli_commands.md`
4. Add tests in `test/test_your_command.py`
5. Document change in `docs/changes/` if it affects behavior

**Auto-responder development**:
- **Policies**:
  - `simple`: Echo messages back to sender
  - `smart`: Context-aware responses (see `src/core/responder_proc.py`)
- **Process files**:
  - PID: `%USERPROFILE%\.claude-ipc-data\responders\<instance>.pid`
  - State: `%USERPROFILE%\.claude-ipc-data\responders\<instance>.json`
- **Custom policies**: Extend `ResponderPolicy` class in `src/core/models/responder.py`

**Adding new AI CLI integrations** (like Gemini, Codex):
1. Create slash commands in `.claude/commands/` (for Claude Code)
2. Add config in `docs/<ai-name>-commands/` or TOML config
3. Test cross-CLI messaging with existing instances
4. Document in `docs/IPC_CLI_INTEGRATION_SUMMARY.md`

## Environment Variables

```bash
IPC_HOST=127.0.0.1              # Broker host (default: localhost)
IPC_GLOBAL_PORT=9876            # Broker port (alias: IPC_PORT)
IPC_SHARED_SECRET=secret        # Optional authentication
IPC_RESPONDER_POLICY=smart      # Responder mode: simple|smart
```

## MCP Tools (Natural Language Interface)

After installing MCP (`./scripts/install-mcp.sh`), use natural language commands:

**Basic operations**:
- `Register this instance as myname` - Register with broker
- `Send message to alice: Help needed` - Send message
- `Check messages` or `Check my inbox` - Retrieve messages
- `List instances` or `Who else is online?` - See active instances

**Advanced operations**:
- `Broadcast: Maintenance in 5 min` - Send to all instances
- `Share file src/config.py with alice` - Share file contents
- `Share command "git status" with bob` - Share command output
- `Rename from oldname to newname` - Change instance ID (1/hour limit)

**Constraints**:
- Must register before using send/check/share tools
- Session tokens expire after 24 hours
- Rate limit: 100 requests/minute per instance
- Messages persist across restarts

## Programming Patterns

### Python API

```python
from core import broker_client

# Register and get session token
response = broker_client.register("my-instance")
session_token = response["session_token"]

# Send message
broker_client.send(session_token, "my-instance", "target-instance", "Hello!")

# Check messages
response = broker_client._send_request({
    "action": "check",
    "instance_id": "my-instance",
    "session_token": session_token
})
messages = response.get("messages", [])
```

### Natural Language (Korean)

```powershell
ipc-chat "codex가 gemini에게 '업데이트 상황 보고' 전달"  # PowerShell helper
python tools/nl_auto_chat.py "codex가 gemini에게 '빌드 결과' 공유"  # Direct
```

## Common Workflows

### AI-to-AI Collaboration Setup

```
# Claude instance 1
Register this instance as claude-frontend
Check messages

# Claude instance 2 (different session/project)
Register this instance as claude-backend
Send message to claude-frontend: Ready to collaborate on API design
Check messages

# Claude instance 1
Check messages
Send message to claude-backend: Let's start with authentication
```

### Debugging Workflow

```powershell
# Health checks
uv run python tools/ipc_global_command.py status
uv run python tools/ipc_doctor.py

# In Claude: List instances

# View/clear messages
uv run python tools/ipc_global_command.py messages list
uv run python tools/ipc_global_command.py messages clear --force
```

### Auto-Responder Workflow

```powershell
# Start background responder
uv run python tools/ipc_global_command.py responder start gemini --policy smart --detach

# Monitor
uv run python tools/ipc_global_command.py responder status gemini

# Test
uv run python tools/ipc_global_command.py ask --to gemini "Ping" --timeout 10

# Stop
uv run python tools/ipc_global_command.py responder stop gemini
```

## Key Operational Notes

- **Broker requirement**: Must be running before any IPC operations
- **Session expiry**: 24 hours (stored in `~/.claude-ipc-data/`)
- **Databases**:
  - Global: `~/.claude-ipc-data/messages.db`
  - Per-project: `.ipc/state/messages.db`
- **Large messages**: >10KB stored as files in `~/.claude-ipc-data/large-messages/`
- **Platform**: Windows - use PowerShell (batch files in `scripts/`)
- **Project isolation**: Each project has `.ipc/` directory, shares global broker

## Troubleshooting

See `docs/TROUBLESHOOTING.md` for details. Quick fixes:

| Issue | Solution |
|-------|----------|
| Broker won't start | Check port 9876, set `IPC_GLOBAL_PORT` if needed |
| Session invalid | Re-register instance |
| Database locked | Stop clients, delete `.ipc/state/messages.db`, restart |
| Messages not delivered | Verify recipient registered and broker running |
| Responder not responding | Check `responder status <instance>` |

## Documentation

### Core Documentation
- **README.md** - Quick start guide
- **docs/INSTALL.md** - Installation details
- **docs/TROUBLESHOOTING.md** - Detailed troubleshooting
- **docs/ipc_cli_commands.md** - CLI reference

### Platform-Specific Guides
- **docs/platform-guides/CLAUDE_CODE_SETUP.md** - Claude Code slash commands
- **docs/claude-commands/INSTALL.md** - Claude Code integration (25 commands)
- **docs/gemini-commands/INSTALL.md** - Gemini CLI integration (24 commands)
- **docs/codex-config.toml** - Codex CLI configuration (24 commands)

### Korean Documentation
- **docs/IPC_UNIFIED_GUIDE_KO.md** - Comprehensive guide (Korean)
- **docs/GLOBAL_USAGE_KO.md** - Global usage guide (Korean)

### Development
- **test/** - Test suite with comprehensive coverage
- **docs/changes/** - Change records (Constitution Principle V: all behavior changes documented)
- **.cursorrules** - Cursor IDE integration rules

## Project Governance

This project follows a **Constitution** (documented in `.specify/memory/constitution.md` and `docs/changes/2025-09-29-constitution-v1.0.0.md`):

**Key Principle V**: Every behavior/contract-affecting change requires a separate change record in `docs/changes/` or `CHANGELOG.md` entry with version impact (PATCH/MINOR/MAJOR).

When making changes:
1. Document behavior changes in `docs/changes/YYYY-MM-DD-feature-name.md`
2. Follow the change record template (see existing records)
3. Note version impact and migration requirements
4. Link change record in commit messages