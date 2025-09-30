# Contract Test Notes

## Test Implementation Observations

After reviewing the contract tests, here are observations about the implementation requirements:

### 1. Acknowledgment Keywords (test_ipc_chat.py)
The test expects one of these acknowledgment words: "ack", "acknowledgment", "acknowledged", "sent", "delivered", "queued"
Current implementation returns "delivered" which should pass, but the test might need case-insensitive check.

### 2. Missing --to Parameter Handling (test_ipc_chat.py)
Test expects non-zero exit code when `--to` parameter is missing.
Implementation currently might be accepting messages without --to parameter.

### 3. Project Initialization Check
Several tests expect commands to fail with non-zero exit code when project is not initialized.
Current implementation might be auto-initializing or not checking for initialization.

### 4. Doctor Command Output Format
The doctor command tests expect specific keywords in output:
- "path" for PATH checking
- "broker" for broker status
- "secret" or "auth" for authentication
- "version" or "compat" for compatibility
- Actionable tips with verbs like "run", "install", "configure", "fix"

### 5. Init Command Requirements
- Should create .ipc/config/settings.json with version info
- Should create .ipc/state/project.json with project_id
- Should create .ipc/.gitignore with specific entries
- Should fail with non-zero exit code for incompatible versions

### 6. Ping Command P95 Metrics
Test expects p95/p99 metrics in output (currently optional in spec).
Implementation could include placeholder metrics like "p95=4ms p99=6ms".

### 7. Status Command JSON Output
Must return valid JSON with specific fields:
- project_id (or projectId)
- broker object with "running" field
- connections (integer)
- last_ping_ms (number or null)

## Test Helper Completeness

The test helpers in `tests/helpers/cli.py` are comprehensive and include:
- `run_ipc()` - Execute IPC commands
- `setup_test_project()` - Initialize test projects
- `parse_json_output()` - Parse JSON from command output
- `wait_for_broker()` - Wait for broker availability
- `extract_correlation_id()` - Extract correlation IDs
- `assert_acknowledgment()` - Check for acknowledgment words
- `assert_timing_info()` - Check for timing information

## Implementation Priority

Based on test failures, the implementation priority should be:

1. **ipc init** - Foundation for all other commands
2. **ipc status** - Provides system state
3. **ipc ping** - Basic connectivity test
4. **ipc chat** - Core messaging functionality
5. **ipc doctor** - Diagnostic tool

## Notes for Implementation

1. All commands should check for project initialization (except `init` and `doctor`)
2. Exit codes must be consistent: 0 for success, non-zero for errors
3. JSON output should be properly formatted and parseable
4. Error messages should be descriptive and actionable
5. The implementation should use `tools/ipc_global_command.py` as the entry point