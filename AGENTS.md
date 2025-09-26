# Repository Guidelines

## Project Structure & Module Organization
Core broker logic resides in `src/claude_ipc_server.py`, while CLI helpers and diagnostics (registration, single-shot chat, monitors) live in `tools/`. Launch flows are scripted under `scripts/` plus the top-level `start_*.py`/`.bat` wrappers. Long-form references, platform guides, and architecture notes are collected in `docs/`; walkthroughs and sample scenarios live in `examples/`. Automated checks, rate-limit harnesses, and regression scripts live in `test/`. Runtime state (SQLite database, lock files, logs) is created under `~/.claude-ipc-data/`.

## Build, Test, and Development Commands
Run all commands from the repo root.
- `uv sync` – install or update dependencies with the project’s pinned UV environment.
- `uv run python tools/start_broker.py` – launch or ensure the singleton IPC broker is running before messaging tests.
- `uv run python tools/ipc_register.py codex --no-default` – register a dedicated instance; session persists in `~/.ipc-session-codex`.
- `uv run python tools/chat_once.py codex gemini "테스트 메시지" --auto-responder` – send a message and wait for the reply in a single command.
- `uv run python tools/auto_chat_demo.py codex gemini --message "Ping" --duration 30` – stream a longer auto-conversation with live monitoring.
- `uv run python tools/manage_responders.py --stop-all` – terminate background auto-responders when cleaning up.
- `bash test/test_ipc.sh` / `uv run python test/test_security.py` – smoke/security checks.

## Coding Style & Naming Conventions
Code targets Python 3.12 with `snake_case` modules and descriptive function names. Enforce formatting via `uv run black .` (line length 100) and lint with `uv run ruff check .`. Run `uv run mypy src tools` to guard against type regressions. Prefer explicit logging around network and persistence boundaries, and document externally callable functions with concise docstrings.

## Testing Guidelines
Place new automated tests in `test/` using `test_*.py` naming so they run cleanly with `uv run pytest`. Scenario guides or manual scripts should be captured in `examples/` or `docs/operations/`. Before raising a PR, run `bash test/test_ipc.sh`, `uv run python test/test_security.py`, and any new targeted tests. Note preconditions (e.g., broker running, `IPC_SHARED_SECRET` set) in docstrings or README snippets.

## Commit & Pull Request Guidelines
Follow the Conventional Commit style in the log (`feat:`, `fix:`, `docs:`) and keep scopes focused (`server`, `tools`, `docs`, etc.). Pull requests must describe the change, list verification commands, and link related issues. Include updated screenshots or terminal transcripts whenever user flows or installers change, and ensure relevant docs (`docs/`, top-level markdown) stay synchronized.

## Security & Operations Tips
Distribute a unified `IPC_SHARED_SECRET` via team environment files; mismatches cause hard failures. Run `uv run python tools/ipc_doctor.py` when diagnosing issues—it checks broker reachability, session file integrity, and database schema health. Use `tools/start_broker.py` to prevent duplicate brokers, and avoid committing artifacts from `~/.claude-ipc-data/`. When modifying rate limits or schema, update documentation and add regression tests before merge. For global CLI shortcuts and slash-command integration, see `docs/CLI_INTEGRATION.md`.
