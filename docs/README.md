# Documentation Index

## Getting Started
- **[Installation](INSTALL.md)**
- **[Troubleshooting](TROUBLESHOOTING.md)**
- 🇰🇷 **[IPC 통합 가이드 (KO)](IPC_UNIFIED_GUIDE_KO.md)**

## Core
- **[Features](FEATURES.md)**
- **[Natural Language Commands](NATURAL_LANGUAGE.md)**
- **[Security](SECURITY.md)**
- **[IPC CLI (KO)](ipc_cli_commands.md)**

## Platform Guides
- **[Windsurf](platform-guides/WINDSURF_INTEGRATION_GUIDE.md)**
- **[Gemini](platform-guides/GEMINI_SETUP.md)**
- **[AI Integration](platform-guides/AI_INTEGRATION_GUIDE.md)**

## Advanced
- See legacy/ for archived advanced topics.

## Additional
- **[Claude Hooks](CLAUDE_HOOKS.md)**
- **[Roadmap](ROADMAP.md)**

---
*Most users only need Installation + IPC 통합 가이드.*

## Development

Run linting and tests:

- Lint: `uv run ruff check src tools`
- Test: `uv run pytest -q`

### Pre-commit hooks (optional but recommended)

To enforce formatting and linting before each commit:

1. Install dependencies:
	- `uv sync`
2. Install hooks:
	- `uv run pre-commit install`
3. (Optional) Run on all files once:
	- `uv run pre-commit run --all-files`

Hooks configured:
- Black (line length 100) scoped to `src/` and `tools/`
- Ruff (check + --fix) scoped to `src/` and `tools/`
- Basic hygiene: end-of-file-fixer, trailing-whitespace
