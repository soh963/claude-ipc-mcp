# Repository Guidelines

## Project Structure & Module Organization
- Core IPC broker and server logic lives in `src/claude_ipc_server.py` and neighboring modules; keep new broker features inside `src/`.
- CLI and maintenance utilities reside in `tools/`; pair each script with an inline `--help` example for discoverability.
- Launch helpers are in `scripts/`, while reference docs sit in `docs/` and walkthroughs in `examples/`.
- Tests belong under `test/`; runtime artifacts go to `%USERPROFILE%\.claude-ipc-data` and must stay out of version control.

## Build, Test, and Development Commands
- `uv sync` — install or update the pinned Python 3.12 toolchain into `.venv`.
- `uv run python tools/start_broker.py` — launch the singleton broker; run once per machine.
- `uv run python tools/ipc_register.py codex --no-default` — register a responder without touching legacy session files.
- `uv run python tools/chat_once.py codex gemini "Ping" --auto-responder` — quick end-to-end health check.

## Coding Style & Naming Conventions
- Follow Python 3.12 best practices: 4-space indentation, snake_case modules and functions, descriptive CLI script names.
- Format with `uv run black .` (line length 100) and lint via `uv run ruff check .`; resolve warnings before pushing.
- Keep modules cohesive—broker/server code in `src/`, tooling in `tools/`, scripts in `scripts/`.

## Testing Guidelines
- Place unit tests in files named `test_*.py` under `test/`; include docstrings describing scenario prerequisites (e.g., broker running, `IPC_SHARED_SECRET` set).
- Run the full suite with `uv run pytest`; execute smoke checks such as `bash test/test_ipc.sh` and `uv run python test/test_security.py` before major merges.
- Target meaningful coverage on critical IPC pathways and document any gaps in PR notes.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat: server …`, `fix: tools …`); group changes by logical scope.
- PR descriptions should state behavioral impact, verification steps, and link related issues; attach transcripts or screenshots when altering responder flows.
- Keep PRs focused; rebase or merge `main` before requesting review to avoid noisy diffs.

## Security & Configuration Tips
- Store `IPC_SHARED_SECRET` securely; mismatches prevent responder registration.
- Use `uv run python tools/ipc_doctor.py` for diagnostics and `uv run python tools/manage_responders.py --stop-all` to clean up lingering processes.
- Review `.gitignore` before adding new tooling to ensure runtime caches stay untracked.
