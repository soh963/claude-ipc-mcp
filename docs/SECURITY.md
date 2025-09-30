# Claude IPC MCP Security Model

## Overview

The Claude IPC MCP implements session-based authentication to prevent identity spoofing and ensure secure communication between AI instances.

## Security Features

### 1. Shared Secret Authentication
- Set the `IPC_SHARED_SECRET` environment variable before starting
- All instances must use the same shared secret to communicate
- The secret is used to generate authentication tokens during registration

### 2. Session-Based Security
- Registration generates a unique session token
- All subsequent operations require the session token
- Session tokens are cryptographically secure (32 bytes, URL-safe)
- Each instance can only have one active session

### 3. Identity Validation
- The server validates that messages come from the claimed sender
- You cannot send messages as another instance
- Session tokens are tied to specific instance IDs

### 4. Local-Only Communication
- Server binds to 127.0.0.1 (localhost only)
- No external network access
- Communication stays within the local machine

## Setup Instructions

### Windows PowerShell (recommended on Windows)

1. Set the shared secret for the current session:
   ```powershell
   $env:IPC_SHARED_SECRET = "your-strong-random-secret"
   ```

2. Persist the secret for your user profile:
   ```powershell
   [Environment]::SetEnvironmentVariable("IPC_SHARED_SECRET", "your-strong-random-secret", "User")
   # restart PowerShell to apply
   ```

3. Verify:
   ```powershell
   $env:IPC_SHARED_SECRET
   ```

4. Register via CLI (auto):
   - In your project folder:
     ```powershell
     ipc init   # creates .ipc/* and attempts broker registration using the secret
     ipc status
     ipc ping
     ```
   - First chat will auto-register if no session exists:
     ```powershell
     ipc chat --to <target-project> "Hello"
     ```
   - Session is stored per-project at `.ipc/state/session.json`.

Note: The CLI computes an auth token as `sha256(f"{instance_id}:{IPC_SHARED_SECRET}")` and sends that during `register`. The broker validates this before issuing a session token.

### For Claude Code (MCP)

1. Set the shared secret:
   ```bash
   export IPC_SHARED_SECRET="your-secret-key-here"
   ```

2. Add the MCP server:
   ```bash
   claude mcp add claude-ipc -s user -- python /path/to/claude_ipc_server.py
   ```

3. The MCP will handle authentication automatically when you register

### For Python Scripts (for use by other AI models like Gemini)

1. Set the shared secret:
   ```bash
   export IPC_SHARED_SECRET="your-secret-key-here"
   ```

2. Register your instance:
   ```bash
   python tools/ipc_register.py fred
   ```
   The global CLI stores session data in the project at `.ipc/state/session.json`.
   Some legacy tooling may also write `~/.ipc-session` for compatibility.

3. Use other scripts normally - they'll use the session token automatically

## Security Best Practices

1. **Choose a strong shared secret**: Use a long, random string
2. **Keep the secret secure**: Don't commit it to version control
3. **Rotate secrets periodically**: Change the secret if compromised
4. **Monitor for failures**: Check logs for authentication failures

## How It Works

### Registration Flow
1. Client provides instance_id and shared secret
2. Server validates: `sha256(instance_id:shared_secret)`
3. Server generates session token and stores mapping
4. Client receives session token for future requests

CLI details:
- `ipc init` attempts registration using the default instance id derived from the project path.
- `ipc chat` will auto-register if no session exists, then send.
- Both flows use the same auth token formula above.

### Message Flow
1. Client includes session token in all requests
2. Server validates token and extracts true instance_id
3. Server ignores any claimed from_id, using session's instance_id
4. Message delivered with verified sender identity

### Session Storage

#### MCP (Claude Code)
- Session token stored in memory for the MCP instance lifetime
- Automatically included in all tool calls after registration

#### Python Scripts
- Session data saved to `~/.ipc-session` (mode 0600)
- Format:
  ```json
  {
    "instance_id": "fred",
    "session_token": "secure-random-token"
  }
  ```

## Threat Model

### Protected Against
- **Identity spoofing**: Can't pretend to be another instance
- **Unauthorized access**: Must know shared secret to register
- **Session hijacking**: Tokens are random and unpredictable
- **Message tampering**: Each message validated against session

### Not Protected Against
- **Local user access**: Any user on the system can connect to localhost:9876
- **Memory inspection**: Tokens stored in process memory
- **Replay attacks**: Old messages could be resent (include timestamps in your protocol)

## Troubleshooting

### "Invalid auth token"
- Check that `IPC_SHARED_SECRET` is set correctly
- Ensure all instances use the same secret

### "Invalid or missing session token"
- Make sure you've registered first
- For Python scripts, check `~/.ipc-session` exists
- Try re-registering if session was lost

### "Rate limit" on rename
- Wait 1 hour between renames
- This prevents abuse of the forwarding system