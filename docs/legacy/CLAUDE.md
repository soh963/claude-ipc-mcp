# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ MANDATORY: Read PROJECT_CONSTITUTION.md First!
This project is governed by strict constitutional rules that MUST be followed. Core values are SEND, RECEIVE, RESPOND. Absolute prohibitions include infinite loops, redundant file creation, and untested code in main.

## 🔒 Project Isolation Requirements
**CRITICAL**: AI CLI communication is restricted to the SAME PROJECT only. Cross-project communication is PROHIBITED.
- Each project has unique namespace using path hash
- Messages include mandatory `project_id` field
- See PROJECT_ISOLATION_GUIDE.md for implementation details

## Project Overview

Claude IPC MCP is an AI-to-AI communication system using Model Context Protocol (MCP) server on localhost:9876. It enables message exchange between AI assistants (Claude, Gemini, ChatGPT) with SQLite persistence and session-based authentication.

## Core Architecture

### Three-Layer System
1. **MCP Server Layer** (`src/claude_ipc_server.py`)
   - Handles Claude Code integration via MCP protocol
   - Natural language command processing
   - Session management with SHA-256 hashed tokens

2. **TCP Broker Layer** (port 9876)
   - Thread-safe message routing with locks
   - Rate limiting (100 req/min per instance)
   - Message queuing for offline recipients
   - 2-hour name forwarding for renamed instances

3. **Persistence Layer** (SQLite)
   - Database: `~/.claude-ipc-data/messages.db`
   - 4 tables: messages, instances, sessions, name_history
   - Auto-cleanup after 7 days for unregistered instances
   - Large messages (>10KB) stored as files

## 🚀 Quick Start - All AI CLIs One Command

### 1. Start Complete IPC Environment
```bash
# One-command startup with monitoring (실행 한번으로 모든 환경 구성)
python start_all_ai_ipc.py

# This command will:
# - Start IPC server on project-specific port
# - Register all AI instances automatically
# - Launch 4-panel monitoring system
# - Enable auto-responders for testing
# - Set project isolation namespace

# Alternative: Start auto-responders separately (Windows)
start_auto_responders.bat

# Alternative: Start auto-responders manually (Unix/Mac)
python tools/simple_auto_responder.py gemini &
python tools/simple_auto_responder.py codex &
python tools/simple_auto_responder.py lm &
```

### Auto-Responder Features
- **Smart Responses**: Each AI instance has unique personality and response patterns
- **NO Dummy Text**: All responses are contextual and meaningful
- **Automatic Message Processing**: Checks messages every 3 seconds
- **Inter-AI Communication**: AI instances can talk to each other

### 2. Process Management Commands

```bash
# Initialize/Reset ALL IPC processes (모든 프로세스 초기화)
python tools/reset_all_ipc.py

# Kill specific processes
pkill -f claude_ipc_server
pkill -f monitor_instance
pkill -f auto_responder

# Clear all project messages (프로젝트 메시지 초기화)
python tools/clear_project_messages.py

# Full system reset (complete cleanup)
python tools/full_system_reset.py
```

### 3. Testing Guide (테스트 방법)

```bash
# Test 1: Basic connectivity
python test/test_basic_ipc.py

# Test 2: Project isolation verification
python test/test_project_isolation.py

# Test 3: Multi-instance communication
python test/test_multi_ai.py

# Test 4: Auto-responder functionality (NO dummy text)
python test/test_real_responses.py

# Full test suite
python -m pytest test/ -v
```

## Common Development Commands

```bash
# Build & Run
uv sync                              # Install/update dependencies
uv run claude-ipc-mcp               # Run MCP server locally
python src/claude_ipc_server.py    # Direct server start

# Testing
python test/test_security.py       # Security test suite
bash test/test_ipc.sh              # Integration tests

# Linting & Formatting
uv run black src/ tools/ --line-length 100
uv run ruff check src/ tools/
uv run mypy src/

# Monitoring
python start_split_monitoring.py   # 4-panel monitor
python tools/monitor_instance.py [name]  # Single instance monitor

# Database Operations
sqlite3 ~/.claude-ipc-data/messages.db ".tables"  # Check structure
sqlite3 ~/.claude-ipc-data/messages.db "SELECT * FROM messages WHERE read_flag = 0;"
python tools/fix_database.py       # Repair corrupted DB
```

## High-Level Architecture

### Message Flow Pattern
```
Claude Code → MCP Protocol → TCP Broker → SQLite → Recipient Queue
```

### Critical Thread Safety
All broker operations require locks due to multi-threaded access:
- `self.lock` guards message_queue and sessions
- `self.rate_limiter.lock` guards rate limiting
- Database operations wrapped in try/except

### Auto-Responder Pattern Matching
The `auto_responder.py` uses pattern matching for automated responses:
- Exact match patterns (e.g., "help", "status")
- Keyword detection for intelligent responses
- Loop prevention with chain tracking (max 3 hops)

### Session Token Lifecycle
1. Registration generates 32-byte token
2. Token SHA-256 hashed before storage
3. 24-hour expiration with auto-cleanup
4. All operations except registration require valid token

## Project State Management

### Status Tracking (.status.yml)
Always update `.status.yml` when:
- Starting new work (set IN_PROGRESS)
- Completing tasks (set SUCCESS)
- Encountering failures (set FAILED, move files to backup/)

### File Creation Protocol
Before creating ANY file:
1. Check if similar file exists
2. Verify it serves core values (SEND/RECEIVE/RESPOND)
3. Follow naming conventions in PROJECT_CONSTITUTION.md
4. Failed code → backup/failed_YYYY-MM-DD/
5. Test code → backup/test_YYYY-MM-DD/

## Natural Language MCP Integration

The server understands flexible patterns via `_extract_natural_command()`:
- Registration: "Register as X", "I am X", "My name is X"
- Send: "msg X: content", "tell X that", "send to X"
- Check: "check messages", "any messages?", "inbox"
- List: "who's online", "list instances", "show users"

## Key Implementation Details

### Rate Limiter Algorithm
Sliding window implementation tracking request timestamps:
- Removes expired timestamps older than window
- Checks count against max_requests
- Thread-safe with lock protection

### Name Forwarding Resolution
Recursive resolution with loop detection:
- Checks name_history table for forwards
- Follows chain up to 10 hops
- Returns final destination or original if not found

### Large Message Handling
Messages >10KB automatically:
1. Generate unique filename with timestamp
2. Write full content to file
3. Store file path and summary in DB
4. Recipient receives notification with file location

## ⚠️ CRITICAL: No Dummy Text or Fake Responses

**ABSOLUTE PROHIBITION**: Never use dummy text, placeholder responses, or simulated AI behavior:
- All responses must be from REAL AI instances or actual system status
- Auto-responders must generate meaningful, context-aware responses
- Test data must be realistic and functional, not Lorem Ipsum
- Mock responses are ONLY allowed in clearly marked test files

## Development Workflow

### Adding New Features
1. Create tool script in `tools/` for testing
2. Add MCP handler in `call_tool()`
3. Implement broker logic in `_process_request()`
4. Update `.status.yml` with progress
5. Test with direct script before MCP integration

### Debugging Checklist
- Port check: `netstat -an | grep 9876`
- Process check: `ps aux | grep claude_ipc`
- Database integrity: `python tools/fix_database.py`
- Session validity: Check expiration timestamps
- Rate limit: Monitor request counts