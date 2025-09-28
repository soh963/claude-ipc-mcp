# 🚨 IPC System Error Report & Learning Database

## Purpose
이 문서는 IPC 시스템에서 발생한 모든 에러와 해결 방법을 기록합니다.
같은 실수를 반복하지 않기 위해 항상 참조해야 합니다.

## Error Categories

### 🔴 Critical Errors (System Failure)
### 🟡 Warning (Partial Failure)
### 🟢 Resolved (Fixed Issues)

---

## Known Issues & Solutions

### 1. Rate Limit Exceeded Error
**Error**: `Rate limit exceeded. Please wait before sending more requests.`
**Cause**: Too many requests in short time (100+ req/min)
**Solution**:
```python
# Add delay between requests
time.sleep(1)  # 1 second delay

# Or reset IPC system
python tools/reset_all_ipc.py
```
**Status**: 🟢 Resolved

### 2. START_IPC.bat Python Error
**Error**: `Error occurred! Check Python installation`
**Cause**: Process cleanup issue in `start_all_ipc.py`
**Solution**:
- Use `START_SAFE.bat` instead
- Or run `python start_simple.py` directly
**Status**: 🟢 Resolved

### 3. IPCManager Initialization Error
**Error**: `TypeError: IPCManager.__init__() takes 1 positional argument but 2 were given`
**Cause**: Wrong initialization in smart_auto_responder.py
**Solution**:
```python
# Wrong:
self.manager = IPCManager(instance_id)

# Correct:
self.manager = IPCManager()
```
**Status**: 🟢 Resolved

### 4. Message Routing Error
**Error**: Messages sent to wrong instance (gemini → llama)
**Cause**: Session file has wrong instance registered
**Solution**:
- Re-register correct instances
- Clear session file: `~/.ipc-session`
**Status**: 🟢 Resolved

### 5. Auto-Responder Not Working
**Error**: Auto-responder doesn't respond to messages
**Cause**: Background process terminated or not started
**Solution**:
```bash
# Start manually
python tools/simple_auto_responder.py gemini

# Or use complete system
python start_complete_system.py
```
**Status**: 🔴 Critical - Frequent failure (2025-09-26)

### 6. Database Lock Error
**Error**: `sqlite3.OperationalError: database is locked`
**Cause**: Multiple processes accessing database simultaneously
**Solution**:
- Add retry logic with delays
- Use connection pooling
- Implement proper locking mechanism
**Status**: 🟡 Warning

### 7. Server Already Running
**Error**: `[Errno 10048] Only one usage of each socket address`
**Cause**: Previous server instance still running on port 9876
**Solution**:
```bash
# Kill existing process
netstat -ano | findstr :9876
taskkill /F /PID <pid>

# Or use reset tool
python tools/reset_all_ipc.py
```
**Status**: 🟢 Resolved

### 8. Module Import Error
**Error**: `ModuleNotFoundError: No module named 'tools'`
**Cause**: Wrong Python path or missing __init__.py
**Solution**:
```python
# Add to script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```
**Status**: 🟢 Resolved

### 9. Auto-Responder Silent Failure (NEW)
**Error**: Auto-responder starts but doesn't process messages
**Cause**:
- IPCManager not properly initialized
- Session token expired or invalid
- Background process has no output redirection
**Solution**:
```python
# 1. Create robust auto-responder with error logging
import logging
logging.basicConfig(filename='auto_responder.log', level=logging.DEBUG)

# 2. Add health check in auto-responder
while True:
    try:
        # Add heartbeat logging
        logging.info(f"Heartbeat: {instance_id} alive at {datetime.now()}")
        messages = manager.check_messages(instance_id)
    except Exception as e:
        logging.error(f"Error: {e}")
        manager.register(instance_id)  # Re-register on error
```
**Status**: 🔴 Critical - Recurring issue (2025-09-26)

### 10. Background Process Output Not Visible
**Error**: Background processes run but output not captured
**Cause**: Output redirected to /dev/null or not captured
**Solution**:
```bash
# Instead of:
python tools/simple_auto_responder.py gemini 2>/dev/null &

# Use:
python tools/simple_auto_responder.py gemini > gemini.log 2>&1 &

# Or capture in Python:
proc = subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```
**Status**: 🟡 Warning - Debugging difficult

### 11. Rate Limit Cascade Failure
**Error**: One rate limit triggers system-wide failure
**Cause**: All operations try to access broker simultaneously after rate limit
**Solution**:
```python
# Implement exponential backoff
import random
import time

def retry_with_backoff(func, max_retries=5):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = (2 ** i) + random.random()
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```
**Status**: 🔴 Critical - Causes complete system failure

### 12. Gemini Instance Specific Failure
**Error**: Gemini auto-responder consistently fails while others work
**Cause**:
- Instance name conflict
- Corrupted session data for gemini
- Special characters in instance name handling
**Solution**:
```bash
# 1. Clear gemini-specific data
sqlite3 ~/.claude-ipc-data/messages.db "DELETE FROM instances WHERE instance_id='gemini';"

# 2. Re-register with fresh session
python tools/ipc_register.py gemini

# 3. Use dedicated responder with logging
python tools/simple_auto_responder.py gemini > gemini_debug.log 2>&1
```
**Status**: 🔴 Critical - Gemini consistently fails (2025-09-26)

---

## Prevention Strategies

### 1. Always Check Before Starting
```python
def check_prerequisites():
    # Check Python
    # Check existing processes
    # Check database
    # Check network ports
```

### 2. Implement Retry Logic
```python
def safe_operation(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # Exponential backoff
```

### 3. Use Process Managers
- Windows: Use `start /min` for background processes
- Unix: Use `nohup` or `screen`

### 4. Implement Health Checks
```python
def health_check():
    checks = {
        "server": check_server_health(),
        "database": check_database_health(),
        "instances": check_instances_health(),
    }
    return all(checks.values())
```

---

## Best Practices

1. **Always use absolute paths**
   - Prevents path-related errors
   - Ensures consistency across different execution contexts

2. **Implement timeout for all operations**
   - Prevents hanging processes
   - Allows graceful failure

3. **Log all errors with context**
   - Include timestamp
   - Include operation being performed
   - Include full error traceback

4. **Use atomic operations**
   - Database transactions
   - File operations with temp files
   - Network operations with acknowledgments

5. **Implement circuit breakers**
   - Prevent cascade failures
   - Allow system recovery time
   - Provide fallback mechanisms

---

## Testing Checklist

Before deploying any changes:

- [ ] Test on fresh environment
- [ ] Test with existing processes running
- [ ] Test error recovery mechanisms
- [ ] Test with rate limiting active
- [ ] Test cross-platform compatibility
- [ ] Test with multiple instances
- [ ] Test monitoring tools
- [ ] Test auto-responders

---

## Recovery Procedures

### Complete System Reset
```bash
# 1. Stop all processes
python tools/reset_all_ipc.py

# 2. Clear database
rm ~/.claude-ipc-data/messages.db

# 3. Clear session
rm ~/.ipc-session

# 4. Restart
python start_ultimate_system.py
```

### Partial Recovery
```bash
# Just restart specific component
python tools/ipc_register.py <instance>
python tools/simple_auto_responder.py <instance>
```

---

## Monitoring Commands

```bash
# Check system status
python tools/ipc_list.py

# Monitor specific instance
python tools/monitor_instance.py <instance>

# Check database
sqlite3 ~/.claude-ipc-data/messages.db "SELECT COUNT(*) FROM messages;"

# Check network
netstat -an | grep 9876
```

---

## Root Cause Analysis (2025-09-26)

### Primary Issues Identified

1. **Session Management Failure**
   - Sessions expire silently without notification
   - No automatic re-registration mechanism
   - Token validation not performed before operations

2. **Process Lifecycle Management**
   - Background processes have no health monitoring
   - No automatic restart on failure
   - Output/errors not captured for debugging

3. **Rate Limiting Design Flaw**
   - No queuing mechanism for rate-limited requests
   - No backoff strategy implemented
   - All instances share same rate limit pool

4. **Auto-Responder Architecture Issues**
   - Simple polling without error recovery
   - No persistent state between restarts
   - No message acknowledgment system

### Recommended Permanent Solutions

#### 1. Implement Supervisor Process
```python
class AutoResponderSupervisor:
    def __init__(self):
        self.responders = {}
        self.health_check_interval = 30  # seconds

    def start_responder(self, instance_id):
        """Start and monitor responder"""
        process = subprocess.Popen(...)
        self.responders[instance_id] = {
            'process': process,
            'last_heartbeat': time.time(),
            'restart_count': 0
        }

    def health_check(self):
        """Check and restart failed responders"""
        for instance_id, info in self.responders.items():
            if not self.is_alive(info['process']):
                self.restart_responder(instance_id)
```

#### 2. Implement Message Queue System
```python
class MessageQueue:
    def __init__(self):
        self.queue = collections.deque()
        self.processing = False

    def add_message(self, message):
        self.queue.append(message)
        if not self.processing:
            self.process_queue()

    def process_queue(self):
        """Process with rate limiting"""
        self.processing = True
        while self.queue:
            message = self.queue.popleft()
            try:
                self.send_with_retry(message)
            except RateLimitError:
                self.queue.appendleft(message)
                time.sleep(1)
        self.processing = False
```

#### 3. Implement Robust Auto-Responder
```python
class RobustAutoResponder:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.manager = None
        self.reconnect_attempts = 0
        self.setup_logging()

    def run(self):
        while True:
            try:
                if not self.manager:
                    self.connect()

                self.process_messages()
                self.reconnect_attempts = 0

            except Exception as e:
                self.handle_error(e)
                self.reconnect()

    def connect(self):
        """Connect with retry logic"""
        for attempt in range(3):
            try:
                self.manager = IPCManager()
                self.manager.register(self.instance_id)
                return
            except Exception as e:
                time.sleep(2 ** attempt)
        raise ConnectionError("Failed to connect after 3 attempts")
```

## Version History

- **v1.0.0** (2025-09-26): Initial error tracking system
- **v1.1.0** (2025-09-26): Added rate limiting errors
- **v1.2.0** (2025-09-26): Added auto-responder issues
- **v2.0.0** (2025-09-26): Major update with root cause analysis and new critical errors

---

*This document should be updated whenever new errors are encountered*