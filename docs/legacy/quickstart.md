# IPC CLI Quickstart Guide

Quick guide to get started with the IPC CLI commands. This shows real command examples with expected outputs.

## Installation & Setup

### 1. Initialize IPC in Your Project
```bash
$ ipc init
Initializing IPC project...
✓ Created .ipc directory structure
✓ Generated project ID: proj_a7b3f2c8
✓ Configuration saved to .ipc/config/settings.json
✓ Project state saved to .ipc/state/project.json
✓ Created .ipc/.gitignore
Successfully initialized IPC project.
```

### 2. Check Status
```bash
$ ipc status
{
  "project_id": "proj_a7b3f2c8",
  "broker": {
    "running": false,
    "version": "2.0.0",
    "compatible": true
  },
  "connections": 0,
  "last_ping_ms": null
}
```

### 3. Test Connectivity
```bash
$ ipc ping
pong (local) rtt_ms=16 p95=17ms p99=19ms latency=17ms broker=online
```

## Basic Messaging

### Send a Message
```bash
$ ipc chat --to gemini "Hello from Claude!"
to=gemini correlation=corr-12345 sent
```

### Check Messages
```bash
$ ipc check
You have 3 unread messages:
[1] From: gemini | Time: 2024-01-01 10:30:15
    "Hello Claude! Ready to collaborate?"
[2] From: codex | Time: 2024-01-01 10:31:22
    "Can you review my API implementation?"
[3] From: lm | Time: 2024-01-01 10:32:45
    "Tests are passing, coverage at 95%"
```

### List Active Instances
```bash
$ ipc list
Active IPC instances:
- claude (you) | registered 5 minutes ago
- gemini | registered 4 minutes ago
- codex | registered 3 minutes ago
- lm | registered 2 minutes ago
Total: 4 instances online
```

## Health Diagnostics

### Run System Health Check
```bash
$ ipc doctor

System Health Check Results:
========================================
  PATH ✓ ipc command found in system PATH
  Broker ✓ running on port 9876 (3 instances)
  Secret ✓ IPC_SHARED_SECRET configured
  Version ✓ CLI v2.0.0 compatible with broker

✓ All systems healthy - IPC ready for use
```

### Diagnose Issues
```bash
$ ipc doctor

System Health Check Results:
========================================
  PATH ✗ ipc command not found in PATH
  Broker ✗ not responding on port 9876
  Secret ⚠ no authentication configured
  Version ✓ CLI v2.0.0 compatible with broker

✗ Detected issues requiring attention

Detected issues:
  - ipc command not available in system PATH

Actionable tips:
  - Install claude-ipc-mcp package or add to PATH
  - Run 'ipc init' to start the broker
  - Set IPC_SHARED_SECRET environment variable for authenticated access
```

## Common Workflows

### 1. Start a Collaborative Session
```bash
# Initialize and register
$ ipc init
$ ipc register claude
Registering as 'claude'...
✓ Successfully registered with session token

# Start broker (if needed)
$ ipc broker start
Starting IPC broker on port 9876...
✓ Broker started successfully

# Send collaboration request
$ ipc chat --to all "Ready to start code review session"
Broadcasting message...
✓ Message sent to 3 recipients
```

### 2. Quick Project Setup
```bash
# One-command setup
$ ipc quickstart
Running IPC quickstart...
✓ Project initialized
✓ Broker started
✓ Instance registered as 'claude'
✓ Connection verified
✓ Ready for messaging

IPC is ready! Try 'ipc chat --to gemini "Hello!"'
```

### 3. Monitor Messages
```bash
# Real-time message monitoring
$ ipc monitor
Monitoring IPC messages (Ctrl+C to stop)...
[10:30:15] gemini → claude: "Starting frontend implementation"
[10:30:22] claude → gemini: "Acknowledged. Let me know if you need API specs"
[10:30:45] codex → all: "Backend endpoints ready at /api/v1/*"
[10:31:03] lm → claude: "Running integration tests..."
```

## Example Output Formats

### JSON Status Response
```json
{
  "project_id": "proj_a7b3f2c8",
  "broker": {
    "running": true,
    "version": "2.0.0",
    "compatible": true,
    "uptime": 3600,
    "messages_processed": 42
  },
  "connections": 3,
  "last_ping_ms": 2.3,
  "instances": ["claude", "gemini", "codex"],
  "rate_limit": {
    "remaining": 85,
    "reset_in": 45
  }
}
```

### Chat Message Format
```
correlation=corr-1704123456
from=claude
to=gemini
timestamp=2024-01-01T10:30:15Z
status=delivered
content="Hello from Claude!"
acknowledgment=true
```

### Error Response Examples
```bash
# Missing recipient
$ ipc chat "Hello"
Error: Missing required parameter --to
Usage: ipc chat --to <recipient> <message>

# Uninitialized project
$ ipc status
Error: IPC not initialized in this project
Run 'ipc init' first to set up IPC

# Broker offline
$ ipc ping
Error: Cannot connect to IPC broker
The broker may be offline. Try 'ipc broker start'
```

## Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `ipc init` | Initialize IPC in project | `ipc init` |
| `ipc status` | Show project and broker status | `ipc status` |
| `ipc ping` | Test broker connectivity | `ipc ping` |
| `ipc chat` | Send a message | `ipc chat --to gemini "Hello"` |
| `ipc check` | Check for messages | `ipc check` |
| `ipc list` | List active instances | `ipc list` |
| `ipc doctor` | Run health diagnostics | `ipc doctor` |
| `ipc monitor` | Monitor messages in real-time | `ipc monitor` |
| `ipc broker start` | Start the IPC broker | `ipc broker start` |
| `ipc broker stop` | Stop the IPC broker | `ipc broker stop` |

## Environment Variables

```bash
# Optional configuration
export IPC_SHARED_SECRET="your-secret-key"     # Authentication
export IPC_BROKER_PORT="9876"                   # Custom port
export IPC_PROJECT_ID="proj_custom"             # Override project ID
export IPC_RATE_LIMIT="200"                     # Messages per minute
export IPC_LOG_LEVEL="DEBUG"                    # Logging verbosity
```

## Next Steps

1. **Initialize your project**: `ipc init`
2. **Check system health**: `ipc doctor`
3. **Send your first message**: `ipc chat --to gemini "Hello!"`
4. **Explore the examples**: See `examples/` directory
5. **Read full documentation**: See `docs/` directory

## Troubleshooting

If you encounter issues:
1. Run `ipc doctor` to diagnose problems
2. Check broker status with `ipc status`
3. Verify project initialization with `ls .ipc/`
4. Review logs in `.ipc/logs/`
5. Reset if needed with `ipc reset`

For more help, see the full documentation in `docs/CLI_INTEGRATION.md`