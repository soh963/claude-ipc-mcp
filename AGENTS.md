# Repository Guidelines

## Project Structure & Module Organization
Core runtime lives in `src/`, with the CLI entry-point in `src/claude_ipc_server.py` and reusable modules under `src/cli/` and `src/core/`. Contract and unit tests sit in `tests/contract/` and `tests/unit/`; additional suites (`tests/integration/`, `tests/e2e/`, `tests/perf/`) are opt-in for targeted runs. Shared developer tooling and orchestrators reside in `tools/`, while end-user documentation is consolidated in `docs/` (see `docs/changes/` for behavior change records). Scripts for local automation live in `scripts/` and Windows launchers in the repository root.

## Build, Test, and Development Commands
Run `uv sync` after pulling to align dependencies. Use `uv run pytest` for the default fast contract+unit suite and append `tests/integration` or `-k pattern` when expanding scope. Lint with `uv run ruff check` and format with `uv run black src tests tools`. Type-check critical paths using `uv run mypy src`. To exercise the broker end-to-end, run `uv run python tools/ipc_global_command.py status` or `responder start <agent>` as described in `docs/README.md`.

## Coding Style & Naming Conventions
Python 3.12 is the target; prefer annotations on new public functions and keep line length ≤100 to satisfy Ruff and Black. Modules use snake_case filenames, classes are PascalCase, and async helpers clarify intent with `_async` suffixes. Persist new CLI verbs under `src/cli/commands/` and mirror their handler names in tests. Run `pre-commit run --all-files` before pushing to ensure formatting, linting, and license headers stay consistent.

## Testing Guidelines
Pytest is the unified test runner (`pytest.ini` scopes default discovery to contract and unit suites). Name new test modules `test_<feature>.py` and fixtures in `conftest.py`. For regression fixes, add scenario coverage in `tests/contract/` when touching wire protocols, and place pure logic checks in `tests/unit/`. Capture expected broker dialogues using helper builders from `tests/helpers/`. Surface coverage gaps by running `uv run pytest --cov=src --cov-report=term-missing` for substantial changes.

## Commit & Pull Request Guidelines
Follow Conventional Commit semantics seen in history (`fix(broker): allow unauthenticated 'list' action`). Keep subject ≤72 characters, describe motivation in the body, and reference issues with `Refs #123` when relevant. Pull requests must include a high-level summary, test evidence (command outputs or coverage notes), and screenshots or trace excerpts for UI/log-facing changes. When modifying docs, link to the affected guide and call out any required follow-up tasks.

## Security & Configuration Tips
Do not commit credentials or broker instance URLs; use `.env.local` for developer overrides. Regenerate IPC tokens via `uv run python tools/ipc_global_command.py init` when switching environments, and revoke stale responders with `responder stop <agent>` before sharing logs. Document any security-sensitive configuration changes in `docs/changes/` so downstream agents stay aligned.
