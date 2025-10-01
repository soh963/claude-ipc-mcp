# IPC Agents for Codex CLI

This file defines custom agents for IPC functionality in Codex CLI.

## IPC Setup Agent

```yaml
agent: ipc-setup
description: Complete IPC setup with auto-responder
triggers:
  - "setup ipc"
  - "initialize ipc"
  - "register ipc instance"
actions:
  - check_broker_status
  - register_instance
  - save_session
  - start_responder
  - verify_connection
output: json
```

## IPC Communication Agent

```yaml
agent: ipc-messenger
description: Handle IPC message sending and receiving
triggers:
  - "send ipc message"
  - "check ipc messages"
  - "ipc communication"
actions:
  - validate_instances
  - queue_message
  - retrieve_messages
  - mark_as_read
output: json
```

## IPC Responder Agent

```yaml
agent: ipc-responder
description: Manage auto-responder lifecycle
triggers:
  - "start responder"
  - "stop responder"
  - "check responder"
actions:
  - check_responder_status
  - start_background_process
  - stop_background_process
  - update_policy
output: json
```

## IPC Doctor Agent

```yaml
agent: ipc-doctor
description: Diagnose and fix IPC issues
triggers:
  - "fix ipc"
  - "diagnose ipc"
  - "ipc problems"
actions:
  - check_broker_connectivity
  - validate_database_schema
  - verify_session_tokens
  - check_file_permissions
  - auto_fix_issues
output: json
```

## Usage

These agents can be invoked naturally in Codex:

1. **Setup**: "Initialize IPC instance as codex-main"
2. **Send Message**: "Send IPC message to claude-worker about API review"
3. **Check Messages**: "Check my IPC messages"
4. **Manage Responder**: "Start IPC responder with smart policy"
5. **Diagnose**: "Fix IPC connection issues"

## Integration with Slash Commands

Agents work alongside slash commands:

- **Slash Commands**: Direct, explicit execution (`/ipc:setup myname`)
- **Agents**: Natural language understanding ("Setup IPC for me")

Both use the same underlying Python tools in `%IPC_CHAT%\tools\`.

## Configuration

Ensure these environment variables are set:

```bash
IPC_CHAT=D:\claude-ipc-mcp
IPC_DB_PATH=%USERPROFILE%\.claude-ipc-data\messages.db
IPC_HOST=127.0.0.1
IPC_GLOBAL_PORT=9876
```

## Troubleshooting

If agents don't respond:

1. Check `%USERPROFILE%\.codex\config.toml` has correct IPC paths
2. Verify broker is running: `/ipc:status`
3. Run diagnostics: `/ipc:doctor`
4. Check agent logs in Codex debug mode
