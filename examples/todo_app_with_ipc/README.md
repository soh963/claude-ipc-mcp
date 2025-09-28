# Todo App with IPC - Example Project

This is a simple todo application that demonstrates how multiple AI CLI instances can collaborate using IPC to build and enhance a project together.

## Project Overview

A collaborative todo application where different AI instances handle different aspects:
- **Claude**: Architecture design and code review
- **Gemini**: Frontend UI and user experience
- **Codex**: Backend logic and API implementation
- **LM**: Testing and documentation

## Quick Start

### 1. Initialize IPC Environment

```bash
# Setup IPC for this project
python ../../tools/setup_new_project_ipc.py .

# Or manually:
# 1. Copy IPC tools
cp -r ../../tools ./tools
cp -r ../../src ./src

# 2. Generate configuration
python tools/config_loader.py create

# 3. Start IPC server
python src/claude_ipc_server.py
```

### 2. Register AI Instances

```bash
# Auto-register all AI instances
python tools/auto_register_all.py

# Or register individually
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm
```

### 3. Run Collaborative Development

```bash
# Start the collaborative development process
python collaborative_development.py
```

## Project Structure

```
todo_app_with_ipc/
├── src/
│   ├── frontend/          # UI components (Gemini)
│   │   ├── TodoList.js
│   │   ├── TodoItem.js
│   │   └── AddTodo.js
│   ├── backend/           # API logic (Codex)
│   │   ├── api.py
│   │   ├── models.py
│   │   └── database.py
│   └── shared/            # Shared utilities
├── test/                  # Tests (LM)
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── doc/                   # Documentation (LM)
│   ├── API.md
│   ├── USER_GUIDE.md
│   └── ARCHITECTURE.md
├── tools/                 # IPC tools
├── collaborative_development.py  # Main orchestrator
└── .ipc_project.yml      # IPC configuration
```

## Collaborative Workflow

### Phase 1: Planning & Design
1. Claude creates architecture design
2. All AIs review and provide feedback
3. Consensus reached through IPC messages

### Phase 2: Implementation
1. Gemini implements frontend components
2. Codex implements backend API
3. Real-time coordination via IPC

### Phase 3: Testing & Documentation
1. LM creates comprehensive tests
2. All AIs run tests in their domains
3. LM generates documentation

### Phase 4: Review & Optimization
1. Claude performs code review
2. Each AI optimizes their components
3. Final integration testing

## IPC Communication Examples

### Architecture Discussion
```python
# Claude proposes architecture
claude.send("all", {
    "type": "architecture_proposal",
    "design": "MVC pattern with REST API"
})

# Others respond with feedback
gemini.send("claude", {
    "type": "feedback",
    "suggestion": "Consider React for frontend"
})
```

### Task Coordination
```python
# Codex notifies API completion
codex.send("gemini", {
    "type": "api_ready",
    "endpoints": ["/api/todos", "/api/todos/:id"]
})

# Gemini acknowledges and integrates
gemini.send("codex", {
    "type": "integration_complete",
    "status": "Frontend connected to API"
})
```

## Benefits of IPC Collaboration

1. **Parallel Development**: Multiple AIs work simultaneously
2. **Expertise Utilization**: Each AI focuses on their strengths
3. **Real-time Coordination**: Instant communication between AIs
4. **Quality Assurance**: Multiple perspectives on code quality
5. **Faster Development**: Reduced development time through parallelization

## Monitoring Progress

```bash
# Check IPC health
python tools/ipc_health_check.py

# Monitor active instances
python tools/ipc_list.py

# View message queue
python tools/ipc_monitor.py

# Check project status
python check_progress.py
```

## Troubleshooting

If you encounter issues:

1. **Check IPC server**: `ps aux | grep claude_ipc_server`
2. **Verify port**: `netstat -an | grep [PORT]`
3. **Test connection**: `python test/test_ipc_connection.py`
4. **Check logs**: Review terminal output
5. **Reset if needed**: `python tools/reset_all_ipc.py`

## Next Steps

1. Extend the todo app with more features
2. Add more AI instances for specialized tasks
3. Implement real-time UI updates via IPC
4. Create automated deployment pipeline
5. Scale to microservices architecture

## License

This example project is provided as-is for educational purposes.