# Repository Guidelines

This document serves as a quick‑start guide for contributors working on the **claude-ipc-mcp** project.

## Project Structure & Module Organization

- `src/` – Core Python package (`claude_ipc_server.py`, utilities).
- `tools/` – Helper scripts (IPC manager, list, monitoring helpers).  Keep experimental code here.
- `scripts/` – Operator‑facing batch / PowerShell wrappers.
- `docs/` – Project documentation and examples.
- `test/` – Smoke tests (`test_security.py`, `test_ipc.sh`). All tests should live under this directory and exit non‑zero on failure.

## Build, Test, and Development Commands

```bash
uv sync                 # Install dependencies (UV required)
uv run claude-ipc-mcp   # Start the IPC MCP server locally
uv run python tools/ipc_manager.py send codex claude "ping"
uv run python test/test_security.py
bash test/test_ipc.sh    # On macOS/Linux; Windows equivalent via PowerShell
```

- `uv sync` – Syncs the project's dependency lock.
- `uv run claude-ipc-mcp` – Launches the MCP server (listens on port 9876).
- Test scripts validate shared‑secret handling, queue behaviour, and message flow.

## Coding Style & Naming Conventions

- Python 3.12 target.
- 4‑space indentation, max line length 100 characters.
- Public functions: `snake_case`; classes: `PascalCase`.
- Run linters before committing:
```bash
uv run ruff check src tools
uv run black src tools test
```
Optional type hints are accepted; `mypy` is configured but may need comments for edge cases.

## Testing Guidelines

- Framework: built‑in `unittest` via `python -m unittest discover`.
- Test files: `test_<feature>.py` under the `test/` directory.
- Run all tests with `uv run python -m unittest discover` or the specific shell scripts above.

## Commit & Pull Request Guidelines

- Commit messages use present‑tense imperative style (e.g., `feat: add IPC broker`).
- PRs should:
  * Summarise changes in a concise description.
  * Link any relevant issue numbers.
  * Include test commands executed and any logs/screenshots for UI changes.
  * Keep unrelated fixes in separate commits for easier review.

## Security & Configuration Tips

- Never commit `IPC_SHARED_SECRET`; use a `.env` file or shell export during development.
- The broker persists data to `%USERPROFILE%/.claude-ipc-data`. Ensure appropriate permissions. Review this path when adding new disk writes.
