# Gemini Context: Claude IPC MCP

## Project Overview

"Claude IPC MCP" is a Python-based system that enables inter-process communication (IPC) between different AI assistants, such as Gemini and Claude. It allows these AIs to send and receive messages using simple natural language commands, creating a persistent and flexible communication channel.

The system is built around a "democratic" broker model. The first AI assistant to connect to the system automatically becomes the message broker, listening for connections on a local TCP socket (port 9876). If the broker instance disconnects, another AI can seamlessly take its place, ensuring high availability.

Messages are persistent, stored in a local SQLite database (`~/.claude-ipc-data/messages.db`). This allows messages to be queued for offline instances or even for instances that have not yet been registered, with a 7-day retention period.

Key technologies include:
- **Python 3.12+**
- **TCP Sockets** for the core communication layer.
- **SQLite** for message and session persistence.
- **`mcp` library** for integration with the AI development environment.

The core logic is encapsulated in a single file, `src/claude_ipc_server.py`, which contains the `MessageBroker` and the `BrokerClient`, as well as the MCP server implementation.

## Building and Running

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jdez427/claude-ipc-mcp.git
    cd claude-ipc-mcp
    ```
2.  **Install `uv`:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
3.  **Install dependencies:**
    ```bash
    uv sync
    ```
4.  **For Claude Code integration, run the installer:**
    ```bash
    ./scripts/install-mcp.sh
    ```

### Running the Server

The application is typically started automatically by an AI assistant's first connection. The main entry point is configured in `pyproject.toml`:

```
[project.scripts]
claude-ipc-mcp = "claude_ipc_server:main"
```

This means the server can be started by running `claude-ipc-mcp` in the shell.

### Basic Commands

- `Register this instance as <name>`
- `Send message to <recipient>: <message>`
- `Check messages`
- `List instances`

## Development Conventions

### Code Style and Quality

- **Formatting:** The project uses `black` for consistent code formatting.
- **Linting:** `ruff` is used for linting to enforce code quality.
- **Type Checking:** `mypy` is used for static type checking.

Configuration for these tools can be found in the `pyproject.toml` file.

### Architecture

- **Single-File Core:** The main application logic, including the broker, client, and MCP server, is located in `src/claude_ipc_server.py`.
- **Stateless Broker (with persistent storage):** The broker itself is stateless, but it relies on a SQLite database for storing messages, instances, and sessions. This makes the broker resilient to crashes and restarts.
- **Natural Language and Scripted Interface:** The system can be controlled via natural language commands (for AIs like Claude) or through direct execution of Python scripts located in the `tools/` directory (for AIs like Gemini).

### Security

- **Session-Based Authentication:** Each registered instance receives a unique session token, which is required for most actions.
- **Identity Validation:** The broker validates the sender's identity to prevent spoofing.
- **Rate Limiting:** The system includes rate limiting for message sending and instance renaming to prevent abuse.
