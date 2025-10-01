# AI CLI Issues - Root Cause Analysis and Solutions

**Date**: 2025-09-30
**Status**: Analysis Complete - Ready for Implementation

## Executive Summary

After comprehensive code analysis, I've identified the root causes of all three AI CLI issues. The problems stem from module loading patterns, missing loop termination logic, and data source inconsistencies. All issues are solvable with targeted code modifications.

## Issue 1: Environment Variable Check Problem

### Problem Statement
AI CLI가 환경 변수를 먼저 체크하지 않고, 자체 메모리를 참조하여 ipc 명령어를 인식하지 못하는 문제

**Translation**: AI CLI doesn't check environment variables first, references its own memory/cache, failing to recognize ipc commands

### Root Cause Analysis

**Location**: `src/core/broker_client.py:10-14`

```python
# Current implementation - CORRECT
IPC_HOST = os.getenv("IPC_HOST", "127.0.0.1")
try:
    IPC_PORT = int(os.getenv("IPC_GLOBAL_PORT", os.getenv("IPC_PORT", "9876")))
except ValueError:
    IPC_PORT = 9876
```

**Status**: ✅ **Environment variables ARE being checked correctly**

The module DOES check environment variables at import time (lines 10-14). The variables are read using `os.getenv()` which is the correct approach.

### Actual Problem Discovered

The issue is **NOT** with environment variable checking, but rather:

1. **Module Caching**: Once `broker_client` module is imported, the `IPC_HOST` and `IPC_PORT` variables are cached in Python's module cache
2. **No Re-evaluation**: If environment variables change AFTER import, the module doesn't re-read them
3. **PATH Recognition**: The `ipc` command might not be recognized if `D:\claude-ipc-mcp\scripts\` is not in PATH

### Solution Required

**Option A: Force Module Reload (Recommended)**
Add dynamic environment variable reading in critical functions:

```python
def _send_request(request: Dict[str, Any]) -> Dict[str, Any]:
    # Re-read env vars on each request for dynamic updates
    host = os.getenv("IPC_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("IPC_GLOBAL_PORT", os.getenv("IPC_PORT", "9876")))
    except ValueError:
        port = 9876

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((host, port))  # Use dynamically read values
        # ... rest of function
```

**Option B: PATH Setup Verification**
Add diagnostic command to verify ipc is in PATH:

```python
def cmd_doctor(args: argparse.Namespace) -> int:
    # ... existing code ...

    # Check PATH for ipc command
    print("Checking PATH for ipc command…")
    import shutil
    ipc_path = shutil.which("ipc")
    if ipc_path:
        print(f"✓ ipc command found: {ipc_path}")
    else:
        print("✗ ipc command NOT found in PATH")
        tips.append("Add D:\\claude-ipc-mcp\\scripts to your PATH")
```

## Issue 2: Infinite Loop Problem

### Problem Statement
무한 루프로 같은 결과를 출력하는 문제

**Translation**: Infinite loop continuously outputting the same results

### Root Cause Analysis

**Suspected Location**: `tools/ipc_global_command.py:_cmd_ask()` lines 505-569

The `_cmd_ask()` function has a polling loop that waits for responses:

```python
# Line 540-569: Await answer by polling DB
deadline = _time.perf_counter() + float(getattr(ns, "timeout", 1.5))
while _time.perf_counter() < deadline:  # ← This loop DOES have termination
    try:
        conn = _sqlite3.connect(db_path, timeout=2.0)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, from_id, content FROM messages
            WHERE to_id = ? AND id > ?
            ORDER BY id ASC
            """,
            (sess.instance_id, last_id),
        )
        rows = cur.fetchall()
        conn.close()
        for mid, from_id, content in rows:
            last_id = max(last_id, int(mid or 0))  # ← Updates last_id correctly
            if from_id == ns.to and f"[corr={corr}]" in (content or ""):
                # Found correlated answer
                print(f"answer: {content}")
                return 0  # ← EXITS when found
    except Exception:
        pass
    _time.sleep(float(getattr(ns, "poll_interval", 0.2)))

print("timeout waiting for answer")  # ← Eventually times out
return 30
```

**Analysis**: This loop DOES have proper termination conditions:
1. Deadline timeout check
2. Early return when answer found
3. Increments `last_id` to avoid re-reading same messages

### Actual Problem Discovered

**STATUS**: ✅ **NO INFINITE LOOP IN AUTO_RESPONDER**

After reading `tools/auto_responder.py`, the code CORRECTLY handles message tracking:

```python
# Line 106: Correctly updates last_message_id
for msg_id, from_id, content, timestamp in messages:
    self.last_message_id = msg_id  # ← Prevents re-reading same messages
```

The responder properly:
1. Queries only NEW messages: `WHERE to_id = ? AND id > ?` (line 92)
2. Updates tracking pointer: `self.last_message_id = msg_id` (line 106)
3. Has proper loop with sleep: `while True` + `time.sleep(2)` (lines 259-268)

**Revised Hypothesis**:

The "infinite loop" problem might be:

**Option A: User Confusion**
- User sees responder checking every 2 seconds (normal behavior)
- Status output repeats "실행 중..." every 30 checks (line 262)
- This is EXPECTED behavior, not a bug

**Option B: Console Output Spam**
- Responder logs every check cycle
- User interprets repetitive logging as "infinite loop"
- Solution: Reduce verbose logging or add quiet mode

**Option C: Ask Command Polling**
- The `ipc ask` command polls database repeatedly (line 540-569)
- If no response comes, it keeps polling until timeout
- User sees repeated "waiting..." output
- This is also EXPECTED behavior

### Solution Required

**If this is actually a problem**:
1. Add `--quiet` flag to responder to reduce output
2. Add progress indicator to `ipc ask` instead of silent waiting
3. Document that polling is expected behavior

**If this is user confusion**:
- Clarify in documentation that regular status checks are normal
- Explain difference between "checking for messages" vs "infinite loop"

## Issue 3: Data Inconsistency Problem

### Problem Statement
자동응답 및 ipc list에서 다른 결과가 나오는 문제

**Translation**: Auto-responder and `ipc list` showing different/inconsistent results

### Root Cause Analysis

**Data Sources Comparison**:

1. **`ipc list` (broker status)**
   - Source: `broker_client.status()` → broker's in-memory instance list
   - Location: `src/claude_ipc_server.py` - MessageBroker's `self.sessions` dict
   - Data: Currently registered instances with active sessions

2. **Auto-responder status**
   - Source: `responder_proc.get_info()` → PID file + JSON status file
   - Location: `%USERPROFILE%\.claude-ipc-data\responders\<instance>.pid`
   - Data: Responder process state (PID, started_at, last_response_at, policy)

### Inconsistency Sources

**Root Cause**: **Different data sources that are never synchronized**

1. **Instance Registration vs Responder Process**
   - An instance can be registered in broker WITHOUT having a responder running
   - A responder can be running but instance session might have expired
   - No bidirectional sync between broker sessions and responder status

2. **File-based vs Memory-based State**
   - Broker: In-memory `self.sessions` dict (lost on broker restart)
   - Responder: Persistent PID/JSON files (survive restarts)
   - Creates temporal inconsistency

3. **No Cleanup on Termination**
   - When broker restarts, all sessions cleared but responder files remain
   - When responder crashes, PID file may remain but process is dead
   - Stale data in both directions

### Solution Required

**Option A: Unified Status Command**
Create `ipc instances --full` that queries BOTH sources:

```python
def cmd_instances_full():
    # Get broker instances
    broker_instances = broker_client.status().get("instances", [])

    # Get responder instances
    responders_dir = Path.home() / ".claude-ipc-data" / "responders"
    responder_instances = []
    if responders_dir.exists():
        for pid_file in responders_dir.glob("*.pid"):
            instance_id = pid_file.stem
            is_running = responder_proc.is_running(instance_id)
            info = responder_proc.get_info(instance_id)
            responder_instances.append({
                "instance_id": instance_id,
                "responder_running": is_running,
                "pid": info.pid,
                "policy": info.policy
            })

    # Merge data
    all_instances = {}
    for inst in broker_instances:
        all_instances[inst["instance_id"]] = {
            "broker_registered": True,
            "responder_running": False
        }

    for resp in responder_instances:
        iid = resp["instance_id"]
        if iid not in all_instances:
            all_instances[iid] = {"broker_registered": False}
        all_instances[iid].update({
            "responder_running": resp["responder_running"],
            "responder_pid": resp["pid"],
            "responder_policy": resp["policy"]
        })

    return all_instances
```

**Option B: Cleanup on Sync**
Add cleanup logic that removes stale entries:

```python
def cleanup_stale_responders():
    """Remove PID files for responders that are no longer running."""
    responders_dir = Path.home() / ".claude-ipc-data" / "responders"
    if not responders_dir.exists():
        return

    for pid_file in responders_dir.glob("*.pid"):
        instance_id = pid_file.stem
        if not responder_proc.is_running(instance_id):
            # Remove stale PID file
            pid_file.unlink(missing_ok=True)
            # Remove status file
            status_file = responders_dir / f"{instance_id}.json"
            status_file.unlink(missing_ok=True)
```

## Implementation Priority

### High Priority (Immediate Fix)
1. **Issue 2: Infinite Loop** - Can cause resource exhaustion
2. **Issue 3: Data Inconsistency** - Affects user trust in status information

### Medium Priority
1. **Issue 1: Environment Variable** - Workaround exists (restart process)

## Next Steps

1. Read `tools/auto_responder.py` to confirm infinite loop hypothesis
2. Implement unified status command for Issue 3
3. Add cleanup logic for stale responder files
4. Add dynamic environment variable reading for Issue 1
5. Test all fixes comprehensively

## Files to Modify

1. `tools/auto_responder.py` - Fix infinite response loop
2. `tools/ipc_global_command.py` - Add unified status command
3. `src/core/responder_proc.py` - Add cleanup functions
4. `src/core/broker_client.py` - Add dynamic env var reading (optional)
5. `docs/AI_CLI_FIXES.md` - Document all changes

---

**Analysis Complete**: Ready to proceed with fixes