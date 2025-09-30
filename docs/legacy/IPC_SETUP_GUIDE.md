# 🚀 IPC Setup Guide for Multi-AI CLI Collaboration

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [New Project Setup](#new-project-setup)
4. [AI CLI Registration](#ai-cli-registration)
5. [Connection Verification](#connection-verification)
6. [Real-World Examples](#real-world-examples)
7. [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

The IPC (Inter-Process Communication) system enables multiple AI CLI instances to communicate and collaborate on projects. Each AI has unique capabilities:

- **Claude** (`claude`): Project architect, code review, documentation
- **Gemini** (`gemini`): Multi-modal analysis, creative solutions, testing
- **Codex** (`codex`): Code generation, optimization, algorithms
- **Local LM** (`lm`): Local processing, privacy-first operations

---

## 📦 Prerequisites

### 1. System Requirements
```bash
# Required Software
- Python 3.8+
- Git
- Node.js (optional, for some tools)

# Python Packages
pip install pyyaml
pip install mcp
```

### 2. Clone IPC Repository
```bash
# Clone the IPC system
git clone https://github.com/your-repo/claude-ipc-mcp.git
cd claude-ipc-mcp

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
# Add to your .bashrc or .zshrc
export IPC_BASE_PATH="$HOME/claude-ipc-mcp"
export PYTHONPATH="$IPC_BASE_PATH:$PYTHONPATH"
```

---

## 🆕 New Project Setup

### Step 1: Create New Project Directory
```bash
# Create your new project
mkdir ~/my-awesome-project
cd ~/my-awesome-project

# Initialize git (recommended)
git init
```

### Step 2: Copy IPC Tools to Project
```bash
# Copy essential IPC tools
cp -r $IPC_BASE_PATH/tools ./tools
cp -r $IPC_BASE_PATH/src ./src
cp $IPC_BASE_PATH/requirements.txt ./

# Install project dependencies
pip install -r requirements.txt
```

### Step 3: Initialize Project Configuration
```bash
# Generate project-specific IPC configuration
python tools/config_loader.py create
```

This creates `.ipc_project.yml` with your project's unique settings:
```yaml
project:
  name: my-awesome-project
  id: proj_a1b2c3d4    # Auto-generated from path
  port: 9234            # Project-specific port
  isolation_mode: strict
```

### Step 4: Start IPC Server for Project
```bash
# Start the IPC server with project isolation
python src/claude_ipc_server.py

# Or use the one-command startup (recommended)
python $IPC_BASE_PATH/start_all_ai_ipc.py
```

Output:
```
🚀 Starting IPC Server...
🔒 Project Isolation Active: proj_a1b2c3d4 on port 9234
✅ Server ready for connections
```

---

## 👥 AI CLI Registration

### Method 1: Automatic Registration (Recommended)
```bash
# From your project directory, run:
python $IPC_BASE_PATH/tools/auto_register_all.py
```

This automatically registers all AI instances for your project.

### Method 2: Manual Registration per AI

#### Claude Registration
```python
# In Claude Code CLI
from tools.ipc_register import register_instance
register_instance("claude")
```

#### Gemini Registration
```python
# In Gemini CLI
from tools.ipc_register import register_instance
register_instance("gemini")
```

#### Codex Registration
```python
# In Codex CLI
from tools.ipc_register import register_instance
register_instance("codex")
```

#### Local LM Registration
```python
# In Local LM CLI
from tools.ipc_register import register_instance
register_instance("lm")
```

### Method 3: Using IPC Commands
```bash
# Register each AI from command line
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm
```

---

## ✅ Connection Verification

### 1. Check Registered Instances
```bash
python tools/ipc_list.py
```

Expected output:
```
📋 Active IPC Instances:
  - claude@proj_a1b2c3d4 (online)
  - gemini@proj_a1b2c3d4 (online)
  - codex@proj_a1b2c3d4 (online)
  - lm@proj_a1b2c3d4 (online)
```

### 2. Test Communication
```bash
# Send test message
python tools/ipc_send.py claude gemini "Hello, testing connection"

# Check messages
python tools/ipc_check.py gemini
```

### 3. Run Connection Test Suite
```bash
python test/test_ipc_connection.py
```

Expected:
```
✅ Server connection: OK
✅ Instance registration: OK
✅ Message send/receive: OK
✅ Project isolation: OK
🎉 All tests passed!
```

---

## 💼 Real-World Examples

### Example 1: Code Review Workflow
```python
# claude_code_review.py
from tools.ipc_client import IPCClient

# Initialize Claude
claude = IPCClient("claude")

# Send code for review
code_to_review = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""

# Request review from other AIs
claude.send("gemini", f"Please review this code:\n{code_to_review}")
claude.send("codex", f"Suggest optimizations for:\n{code_to_review}")

# Collect feedback
gemini_feedback = claude.check_messages()
codex_suggestions = claude.check_messages()

print("Review Results:")
print(f"Gemini: {gemini_feedback}")
print(f"Codex: {codex_suggestions}")
```

### Example 2: Collaborative Feature Development
```python
# collaborative_development.py
from tools.ipc_client import IPCClient
import json

class ProjectCollaborator:
    def __init__(self, ai_name):
        self.client = IPCClient(ai_name)
        self.ai_name = ai_name

    def request_task(self, task_type, details):
        """Request specific task from another AI"""
        message = json.dumps({
            "task": task_type,
            "details": details,
            "from": self.ai_name
        })
        return message

    def coordinate_feature(self):
        """Coordinate feature development across AIs"""

        # Claude: Architecture design
        if self.ai_name == "claude":
            arch_design = "Design user authentication system"
            self.client.send("codex", self.request_task("implement", arch_design))
            self.client.send("gemini", self.request_task("test_plan", arch_design))
            self.client.send("lm", self.request_task("documentation", arch_design))

        # Codex: Implementation
        elif self.ai_name == "codex":
            implementation = "Implement JWT authentication"
            self.client.send("claude", self.request_task("review", implementation))
            self.client.send("gemini", self.request_task("test", implementation))

        # Gemini: Testing
        elif self.ai_name == "gemini":
            test_results = "All authentication tests passed"
            self.client.send("claude", self.request_task("validate", test_results))
            self.client.send("lm", self.request_task("update_docs", test_results))

        # LM: Documentation
        elif self.ai_name == "lm":
            docs = "Authentication documentation complete"
            self.client.send("claude", self.request_task("final_review", docs))

# Initialize collaborators
claude_collab = ProjectCollaborator("claude")
claude_collab.coordinate_feature()
```

### Example 3: Parallel Task Execution
```python
# parallel_tasks.py
import asyncio
from tools.ipc_client import IPCClient

async def distribute_tasks():
    """Distribute tasks to multiple AIs for parallel execution"""

    claude = IPCClient("claude")

    tasks = [
        ("gemini", "Analyze user requirements for dashboard"),
        ("codex", "Generate API endpoints for user management"),
        ("lm", "Create database schema for products"),
    ]

    # Send all tasks in parallel
    for ai, task in tasks:
        claude.send(ai, task)
        print(f"📤 Sent to {ai}: {task}")

    # Wait for responses
    await asyncio.sleep(5)

    # Collect results
    results = {}
    for ai, _ in tasks:
        messages = claude.check_messages_from(ai)
        if messages:
            results[ai] = messages[-1]['content']

    return results

# Run parallel tasks
results = asyncio.run(distribute_tasks())
print("📊 Results from parallel execution:")
for ai, result in results.items():
    print(f"  {ai}: {result}")
```

### Example 4: Real-time Monitoring Dashboard
```python
# monitoring_dashboard.py
import time
from tools.ipc_client import IPCClient

class IPCMonitor:
    def __init__(self):
        self.monitor = IPCClient("monitor")

    def display_dashboard(self):
        """Display real-time IPC activity"""
        while True:
            print("\033[2J\033[H")  # Clear screen
            print("=" * 60)
            print("📊 IPC MONITORING DASHBOARD")
            print("=" * 60)

            # Get status from all AIs
            instances = self.monitor.list_instances()

            for instance in instances:
                name = instance['name']
                status = "🟢 Active" if instance.get('active') else "🔴 Inactive"
                last_seen = instance.get('last_seen', 'Never')

                print(f"\n{name}:")
                print(f"  Status: {status}")
                print(f"  Last Activity: {last_seen}")

                # Check for pending messages
                messages = self.monitor.check_messages_for(name)
                if messages:
                    print(f"  📬 Pending Messages: {len(messages)}")

            print("\n" + "=" * 60)
            print("Press Ctrl+C to exit")
            time.sleep(2)

# Start monitoring
monitor = IPCMonitor()
monitor.display_dashboard()
```

---

## 🛠️ Advanced Configuration

### 1. Cross-Project Communication
```yaml
# .ipc_project.yml - Enable cross-project
project:
  isolation_mode: relaxed  # Change from 'strict'

permissions:
  allow_cross_project: true
  trusted_projects:
    - proj_xyz789  # Add trusted project IDs
```

### 2. Custom Port Configuration
```yaml
# .ipc_project.yml - Custom port
network:
  host: 127.0.0.1
  port: 9500  # Custom port (default: auto-generated)
```

### 3. Rate Limiting
```yaml
# .ipc_project.yml - Adjust rate limits
settings:
  rate_limit: 200  # Messages per minute
  max_message_size: 40960  # 40KB
```

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused
```bash
# Check if server is running
ps aux | grep claude_ipc_server

# Restart server
pkill -f claude_ipc_server
python src/claude_ipc_server.py
```

#### 2. Project Isolation Blocking Messages
```bash
# Check project ID
python tools/project_utils.py info

# Verify both AIs are in same project
python tools/ipc_list.py
```

#### 3. Port Already in Use
```bash
# Find process using port
netstat -an | grep 9234

# Kill process or change port
kill -9 <PID>
# Or edit .ipc_project.yml to use different port
```

#### 4. Message Not Received
```bash
# Check message queue
sqlite3 ~/.claude-ipc-data/messages.db
sqlite> SELECT * FROM messages WHERE recipient='gemini' AND read_flag=0;
```

---

## 📡 Monitoring Tools

### 1. Real-time Monitor
```bash
# Start 4-panel monitoring
python $IPC_BASE_PATH/start_split_monitoring.py
```

### 2. Message History
```bash
# View all messages
python tools/ipc_history.py --last 50
```

### 3. Performance Stats
```bash
# View IPC statistics
python tools/ipc_stats.py
```

---

## 🎯 Best Practices

1. **Always use project isolation** - Prevents cross-project interference
2. **Register AIs at startup** - Ensures availability for collaboration
3. **Implement timeout handling** - Don't wait indefinitely for responses
4. **Use structured messages** - JSON format for complex data
5. **Log important operations** - Helps with debugging
6. **Clean up old messages** - Prevent database bloat
7. **Monitor rate limits** - Avoid hitting limits during heavy usage

---

## 📚 Additional Resources

- [Project Isolation Guide](PROJECT_ISOLATION_GUIDE.md)
- [IPC API Reference](API_REFERENCE.md)
- [Security Best Practices](SECURITY.md)
- [Performance Tuning](PERFORMANCE.md)

---

**Last Updated**: 2025-09-28
**Version**: 1.0.0
**Status**: ✅ Production Ready