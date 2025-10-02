# Broker Daemon Solution - Complete Implementation

## Overview

This document describes the complete broker daemon solution that addresses all identified issues in the Claude IPC MCP system. The solution provides a robust, standalone message broker that can serve multiple AI CLIs simultaneously.

## Problems Solved

### 1. **Broker Lifecycle Management**
- **Issue**: Broker was embedded in MCP server, causing conflicts when multiple CLIs tried to start it
- **Solution**: Standalone daemon with proper lifecycle management via ServiceManager

### 2. **Multi-CLI Support**
- **Issue**: Each CLI tried to start its own broker, causing port conflicts
- **Solution**: Single system-wide broker serving all CLIs on port 9876

### 3. **Windows Socket Compatibility**
- **Issue**: SO_REUSEADDR behaves differently on Windows, causing "address already in use" errors
- **Solution**: Use SO_EXCLUSIVEADDRUSE on Windows for exclusive port binding

### 4. **State Consistency**
- **Issue**: Database and memory state could become inconsistent
- **Solution**: Unified state management with proper synchronization

### 5. **Process Management**
- **Issue**: Orphaned broker processes and stale PID files
- **Solution**: Robust process tracking and cleanup mechanisms

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   AI CLIs Layer                      │
├──────────┬──────────┬──────────┬──────────┬────────┤
│  Claude  │  Gemini  │  Codex   │ ChatGPT  │ Others │
└──────────┴──────────┴──────────┴──────────┴────────┘
           │          │          │          │
           └──────────┴──────────┴──────────┘
                         │
                    TCP Socket
                   (127.0.0.1:9876)
                         │
           ┌─────────────▼─────────────┐
           │     Broker Daemon         │
           │  (Standalone Process)     │
           ├───────────────────────────┤
           │ • Session Management      │
           │ • Message Routing         │
           │ • Rate Limiting          │
           │ • State Persistence      │
           └───────────────────────────┘
                         │
           ┌─────────────▼─────────────┐
           │   Service Manager         │
           ├───────────────────────────┤
           │ • Start/Stop/Restart      │
           │ • Health Checks           │
           │ • Process Monitoring      │
           │ • Stale Process Cleanup   │
           └───────────────────────────┘
```

## Key Components

### 1. BrokerDaemon (`src/broker/daemon.py`)

**Features:**
- Standalone TCP server running on port 9876
- Platform-specific socket configuration (Windows/Linux)
- Session-based authentication with SHA-256 hashed tokens
- Rate limiting (100 requests/minute per instance)
- SQLite persistence for messages and state
- Large message file storage (>10KB)
- Graceful shutdown with signal handlers
- Instance rename support with forwarding

**Key Methods:**
- `start(background=True)`: Start the broker daemon
- `stop()`: Graceful shutdown
- `_handle_register()`: Register new CLI instance
- `_handle_send()`: Route messages between instances
- `_handle_check()`: Retrieve messages for instance
- `_handle_broadcast()`: Send to all instances

### 2. ServiceManager (`src/broker/service_manager.py`)

**Features:**
- Broker lifecycle management
- Health checks and monitoring
- Automatic restart on failure
- PID file management
- Stale process cleanup
- Platform-specific process handling

**Key Methods:**
- `ensure_broker_running()`: Start broker if not running
- `start_broker()`: Start the daemon process
- `stop_broker()`: Stop gracefully or forcefully
- `restart_broker()`: Full restart cycle
- `health_check()`: Verify broker is healthy
- `cleanup_stale_processes()`: Remove orphaned processes

### 3. Updated CLI Integration

**Improved `ensure_broker()` function:**
```python
def ensure_broker():
    # 1. Check if already running
    if broker_client.status() == "ok":
        return

    # 2. Use ServiceManager to start
    manager = ServiceManager()
    if manager.ensure_broker_running():
        return

    # 3. Fallback to legacy method
    # (for backward compatibility)
```

## Usage

### Starting the Broker

**Method 1: Using ServiceManager (Recommended)**
```bash
python src/broker/service_manager.py start
```

**Method 2: Direct Daemon Start**
```bash
python src/broker/daemon.py
```

**Method 3: Via Updated Tools**
```bash
python tools/start_broker_new.py
```

### Managing the Broker

```bash
# Check status
python src/broker/service_manager.py status

# Stop broker
python src/broker/service_manager.py stop

# Restart broker
python src/broker/service_manager.py restart

# Health check
python src/broker/service_manager.py health
```

### Multi-CLI Communication

Each CLI registers independently and receives a unique session token:

```python
# Claude CLI
response = broker_client.register("claude")
session_token = response["session_token"]

# Send message to Gemini
broker_client.send(session_token, "claude", "gemini", "Hello!")

# Check messages
messages = broker_client.check(session_token, "claude")
```

## Testing

### Unit Tests (`test/test_broker_daemon.py`)
- Broker startup/shutdown
- Multi-CLI registration
- Message routing
- State persistence
- Rate limiting
- Session validation
- Large message handling

### Integration Tests (`test/test_multi_cli_integration.py`)
- Simulates multiple AI CLIs
- Concurrent message handling
- Broker restart resilience
- State consistency verification

### Running Tests

```bash
# Run all broker tests
pytest test/test_broker_daemon.py -v

# Run integration test
python test/test_multi_cli_integration.py
```

## Configuration

### Environment Variables
```bash
IPC_HOST=127.0.0.1          # Broker host (default: localhost)
IPC_GLOBAL_PORT=9876        # Broker port
IPC_SHARED_SECRET=secret    # Optional authentication
```

### File Locations
```
~/.claude-ipc-data/
├── broker.pid              # Process ID file
├── broker.log              # Log file
├── messages.db             # SQLite database
└── large-messages/         # Large message storage
```

## Migration Guide

### For Existing Projects

1. **Stop any running brokers:**
   ```bash
   python tools/start_broker.py  # Old version - stop it
   ```

2. **Install new components:**
   - Copy `src/broker/` directory
   - Update `tools/ipc_global_command.py` with new ensure_broker
   - Or use `tools/ipc_global_command_new.py`

3. **Start new broker:**
   ```bash
   python tools/start_broker_new.py
   ```

4. **Verify operation:**
   ```bash
   python src/broker/service_manager.py status
   ```

### For MCP Server

The MCP server (`src/claude_ipc_server.py`) no longer needs to embed the broker. It should:
1. Connect to the external broker via TCP
2. Provide MCP tools that communicate with the broker
3. Not attempt to start its own broker instance

## Benefits

### 1. **Reliability**
- Single broker instance prevents conflicts
- Graceful handling of failures
- Automatic recovery mechanisms

### 2. **Performance**
- Efficient message routing
- Rate limiting prevents abuse
- Optimized for concurrent connections

### 3. **Compatibility**
- Works on Windows and Linux
- Platform-specific optimizations
- Backward compatibility maintained

### 4. **Maintainability**
- Clean separation of concerns
- Comprehensive test coverage
- Clear error messages and logging

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Use ServiceManager to stop existing broker |
| Broker won't start | Check PID file and clean up stale processes |
| Messages not delivered | Verify both CLIs are registered |
| Session expired | Re-register with broker |
| Windows socket error | Ensure SO_EXCLUSIVEADDRUSE is used |

### Debug Commands

```bash
# Check if port is in use
netstat -an | findstr :9876

# Find broker process (Windows)
tasklist | findstr python

# Kill stale broker (Windows)
taskkill /F /PID <pid>

# View broker logs
type %USERPROFILE%\.claude-ipc-data\broker.log
```

## Future Enhancements

1. **WebSocket Support**: Add WebSocket interface for browser-based CLIs
2. **Clustering**: Multi-broker setup for high availability
3. **Encryption**: End-to-end encryption for messages
4. **Persistence Options**: Support for Redis/PostgreSQL
5. **Admin UI**: Web interface for monitoring and management

## Conclusion

This broker daemon solution provides a robust, scalable foundation for inter-AI communication. It solves all identified issues while maintaining backward compatibility and adding new capabilities for future growth.