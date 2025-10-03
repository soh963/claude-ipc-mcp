# ⚠️ DEPRECATED: TCP-Based Global Broker

**Date**: 2025-10-02
**Reason**: Migration to local socket-based broker architecture
**Status**: LEGACY - DO NOT USE

## Files Deprecated

The following files implemented the old TCP-based global broker system and are now **DEPRECATED**:

### 1. `claude_ipc_server.py`
- **Purpose**: TCP socket server (port 9876) with SQLite persistence
- **Replaced By**: `local_broker.py` (Unix socket/Named Pipe)
- **Status**: ❌ DO NOT USE

### 2. `core/broker_client.py`
- **Purpose**: TCP socket communication wrapper
- **Replaced By**: `local_broker_client.py`
- **Status**: ❌ DO NOT USE

### 3. `core/project_port.py`
- **Purpose**: SHA256-based port allocation for project isolation
- **Replaced By**: Project root detection in `local_broker_client.py`
- **Status**: ❌ DO NOT USE

### 4. `tools/start_broker.py`
- **Purpose**: Legacy broker launcher script
- **Replaced By**: Auto-start mechanism in `local_broker_client.py`
- **Status**: ❌ DO NOT USE

## Migration Path

All functionality has been migrated to the new local broker system:

```python
# OLD (TCP-based - DEPRECATED)
from core import broker_client
broker_client.register("my-instance")

# NEW (Local socket-based - CURRENT)
import local_broker_client as broker_client
broker_client.register("my-instance")
```

## Why This Change?

### Problems with TCP Broker:
- ❌ Global shared state across all projects
- ❌ Port conflicts and detection issues
- ❌ Complex project isolation logic
- ❌ Unnecessary network overhead for local IPC

### Benefits of Local Broker:
- ✅ Complete project isolation (each project has own broker)
- ✅ No port conflicts (Unix socket/Named Pipe)
- ✅ Simpler architecture (.ipc folder centric)
- ✅ Better performance (local-only communication)
- ✅ Follows absolute rules (project folder first)

## Absolute Rules Compliance

The new architecture follows these absolute rules:

1. **Project Folder First**: Always detect project root
2. **.ipc Folder Centric**: All state in `.ipc/` directory
3. **Local First**: No global shared state
4. **Broker Local Execution**: Each project runs own broker
5. **Complete Project Isolation**: Projects cannot access each other

## Documentation

See the following for current implementation:
- `docs/IPC_ABSOLUTE_RULES.md` - Absolute rules charter
- `docs/LOCAL_BROKER_MIGRATION.md` - Detailed migration status
- `docs/MIGRATION_STATUS_SUMMARY.md` - Current progress (90%)

## Removal Schedule

These files will be **completely removed** in the next major version after:
1. All CLI commands migrated (✅ DONE - 90%)
2. Integration tests pass (⏳ PENDING)
3. Documentation updated (⏳ PENDING)

**DO NOT extend or modify these deprecated files.**
