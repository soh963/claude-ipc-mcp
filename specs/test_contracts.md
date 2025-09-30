# IPC CLI Contract Test Specifications

## Overview
This document specifies the expected behavior for IPC CLI commands that need to be implemented to pass the contract tests in `tests/contract/`.

## T007: IPC Init Command (`ipc init`)

### Purpose
Initialize a new IPC project with necessary directory structure and configuration.

### Requirements

#### 1. Directory Structure Creation
- Creates `.ipc/` directory in project root
- Creates subdirectories:
  - `.ipc/config/` - Configuration files
  - `.ipc/logs/` - Log files
  - `.ipc/state/` - Project state
  - `.ipc/secret/` - Secrets and keys

#### 2. Configuration Files
- Creates `.ipc/config/settings.json` with:
  ```json
  {
    "version": "2.0.0",
    "min_compatible_version": "2.0.0"
  }
  ```
- Creates `.ipc/state/project.json` with:
  ```json
  {
    "project_id": "proj_<8-char-hash>",
    "initialized_at": "<ISO-timestamp>"
  }
  ```

#### 3. Project ID Generation
- Format: `proj_` followed by 8 character hash
- Based on project path hash or random if needed
- Must be consistent across re-runs (idempotent)

#### 4. Idempotent Behavior
- Running `ipc init` multiple times is safe
- Preserves existing `project_id`
- Preserves existing secrets
- Returns exit code 0 on success

#### 5. Version Compatibility
- Returns non-zero exit code if existing config has incompatible major version
- Error message should mention "version" or "incompatible"

#### 6. Gitignore Creation
- Creates `.ipc/.gitignore` containing:
  ```
  secret/
  logs/
  *.log
  ```

### Exit Codes
- `0`: Success (initialized or already initialized)
- `1`: Version incompatibility
- `2`: File system error

---

## T008: IPC Status Command (`ipc status`)

### Purpose
Show current project and broker status in JSON format.

### Requirements

#### 1. JSON Output Format
```json
{
  "project_id": "proj_abc12345",
  "broker": {
    "running": false,
    "version": "2.0.0",
    "compatible": true
  },
  "connections": 0,
  "last_ping_ms": null
}
```

#### 2. Required Fields
- `project_id`: String, project identifier
- `broker`: Object with:
  - `running`: Boolean, broker status
  - `version`: String (optional)
  - `compatible`: Boolean (optional)
- `connections`: Integer, active connections (≥0)
- `last_ping_ms`: Number or null, last ping time in milliseconds

#### 3. Uninitialized Project Handling
- Option A: Return non-zero exit code with error mentioning "not initialized"
- Option B: Return JSON with missing/null project_id

### Exit Codes
- `0`: Success
- `1`: Project not initialized

---

## T009: IPC Ping Command (`ipc ping`)

### Purpose
Test connectivity to IPC broker and measure latency.

### Requirements

#### 1. Success Response
- Returns exit code 0 when broker is reachable
- Output format: `pong (local) rtt_ms=<number>`

#### 2. Timing Information
- Must include one of: "ms", "latency", "time", "rtt", "milliseconds"
- Shows round-trip time in milliseconds

#### 3. P95 Metrics (Optional)
- May include percentile metrics: "p95", "p99", "percentile"
- Format: `p95=<number>ms` (placeholder values acceptable)

#### 4. Error Handling
- Uninitialized project: Exit code 1 with clear error
- Broker offline: Exit code 1 or appropriate message

### Exit Codes
- `0`: Ping successful
- `1`: Ping failed (broker offline or not initialized)

---

## T010: IPC Chat Command (`ipc chat`)

### Purpose
Send messages between IPC instances.

### Requirements

#### 1. Command Syntax
```bash
ipc chat --to <target> "message content"
```

#### 2. Success Response
- Returns exit code 0 on successful send
- Output includes:
  - Target confirmation: `to=<target>`
  - Correlation ID: `correlation=corr-<number>` or similar
  - Acknowledgment: One of "ack", "acknowledged", "sent", "delivered", "queued"

#### 3. Correlation ID Format
- Should match patterns:
  - `corr-<number>`
  - `correlation: <id>`
  - `correlation_id: <id>`
  - `corr_id: <id>`

#### 4. Error Handling
- Missing `--to`: Exit code 1 with error about missing recipient
- Empty message: Either accept with ack OR reject with clear error
- Uninitialized project: Exit code 1 with initialization error

### Exit Codes
- `0`: Message sent successfully
- `1`: Missing parameters or not initialized
- `2`: Broker connection error

---

## T011: IPC Doctor Command (`ipc doctor`)

### Purpose
Diagnose IPC system health and provide actionable remediation tips.

### Requirements

#### 1. Health Checks
Performs checks for:
- **PATH**: Command availability in system PATH
- **Broker**: Connection status and port availability
- **Secret**: Authentication configuration
- **Version**: Compatibility between components

#### 2. Output Format
For healthy project:
- Exit code 0
- Output includes: "healthy", "ok", "good", or "✓"
- Shows each check with status

For issues detected:
- Exit code 1
- Lists detected issues
- Provides actionable tips with verbs: "run", "install", "configure", "fix"

#### 3. Check Keywords
Output must mention checked components:
- Contains "path" for PATH checking
- Contains "broker" for broker status
- Contains "secret" or "auth" for authentication
- Contains "version" or "compat" for compatibility

#### 4. Actionable Tips
When issues detected, provide remediation:
```
Detected issues:
 - .ipc directory missing; run 'ipc init'
 - Broker not running; run 'ipc broker start'
 - Version mismatch; upgrade with 'pip install --upgrade'
```

### Exit Codes
- `0`: All checks passed (healthy)
- `1`: Issues detected (needs remediation)

---

## Implementation Priority

1. **T007 (init)**: Foundation for all other commands
2. **T008 (status)**: Provides system state information
3. **T009 (ping)**: Basic connectivity test
4. **T010 (chat)**: Core messaging functionality
5. **T011 (doctor)**: Diagnostic and troubleshooting

## Helper Functions Available

The test suite provides these helpers in `tests/helpers/cli.py`:

- `run_ipc(args, cwd)`: Execute IPC commands
- `setup_test_project(path)`: Initialize test project
- `parse_json_output(output)`: Parse JSON from command output
- `wait_for_broker(timeout)`: Wait for broker availability
- `extract_correlation_id(output)`: Extract correlation ID from chat
- `assert_acknowledgment(output)`: Check for ack in output
- `assert_timing_info(output)`: Check for timing information

## Testing

Run contract tests:
```bash
# Run all contract tests
pytest tests/contract/ -v

# Run specific test file
pytest tests/contract/test_ipc_init.py -v

# Run with coverage
pytest tests/contract/ --cov=src --cov=tools
```

## Notes for Implementation

1. **JSON Output**: Many commands should output JSON for machine readability
2. **Exit Codes**: Use consistent exit codes (0=success, 1=user error, 2=system error)
3. **Error Messages**: Include actionable information in error messages
4. **Idempotency**: Operations like `init` should be safe to run multiple times
5. **Project Context**: Most commands require initialized project (except `init` and `doctor`)