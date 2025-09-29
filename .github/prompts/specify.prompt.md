---
description: Create or update the feature specification from a natural language feature description.
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

The text the user typed after `/specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. Run the script `.specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS"` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.
2. Load `.specify/templates/spec-template.md` to understand required sections.
3. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.

Additional project-specific requirements (MUST be reflected in the generated spec; preserve the template section order and append any missing sections at the end):

- Scope and Goals:
  - Global CLI command “ipc” MUST support running from any project directory.
  - Running “ipc init” in a target project MUST create a project-local .ipc folder and place all project-scoped IPC files there. The global broker/runtime artifacts remain under %USERPROFILE%\.claude-ipc-data per repository guidelines.
  - The objective is to enable multiple AI CLIs to be integrated, connected, and collaborate to reach optimal outcomes.

- Architecture and Components:
  - Describe the singleton broker model and how external projects connect.
  - Define .ipc directory layout (e.g., .ipc/config.yaml, .ipc/secrets.env, .ipc/responders.json, .ipc/logs/, .ipc/state/), ownership, and VCS ignore requirements.
  - Clarify separation of concerns: broker/server in src/, tooling in tools/, scripts in scripts/, docs/examples/tests per AGENTS.md.
  - Explain identity/routing model for multiple AI CLIs (roles, topics, addressing, handshake, message schema).

- Bootstrap and Commands (CLI UX):
  - ipc init: detects/creates .ipc, generates configs, provisions per-project IPC_SHARED_SECRET (stored in .ipc/secrets.env), ensures broker is running (start if needed), registers responders, enables auto-responder, and verifies connectivity.
  - ipc status: shows broker status, connected CLIs/responders, versions, and health.
  - ipc ping / ipc chat --to <target>: simple E2E check across CLIs and between projects.
  - Provide how these wrap or interop with existing tools (e.g., uv run python tools/start_broker.py, tools/ipc_register.py, tools/chat_once.py).
  - Include --help behavior examples.

- Security:
  - Use IPC_SHARED_SECRET; per-project secret lives in .ipc/secrets.env; storage must be secure and excluded from VCS.
  - Handshake/auth flow between project .ipc and singleton broker; rotation workflow and diagnostics.

- Observability and Diagnostics:
  - Logging under .ipc/logs for project-scoped events; broker logs remain under %USERPROFILE%\.claude-ipc-data.
  - Doctor commands (ipc doctor) surfacing common misconfigurations and remediation steps.
  - Metrics/events for init, connect, ping, chat.

- Performance and Reliability:
  - Constraints (latency targets for ping/chat), backoff/retry, idempotency for init, and resilience to broker restarts.

- Failure Modes and Recovery:
  - Secret mismatch, broker unavailable, port conflicts, stale registrations; self-heal paths and user guidance.

- Compatibility and Distribution:
  - Global installation strategy (e.g., uvx/pipx) to expose ipc on PATH.
  - Version compatibility policy between CLI and broker.

- Testing:
  - Unit tests under test/ (test_*.py) with prerequisites docstrings (broker running, IPC_SHARED_SECRET set).
  - Smoke tests mirroring: bash test/test_ipc.sh and uv run python test/test_security.py.
  - E2E scenario: ipc init → ipc status → ipc ping → ipc chat between multiple AI CLIs.
  - Coverage goals for critical IPC pathways; gaps documented.

- Rollout and Migration:
  - Git ignore rule for .ipc, safe defaults, rollback plan (cleanup .ipc, unregister responders).
  - Data ownership boundary between .ipc and %USERPROFILE%\.claude-ipc-data.

- Acceptance Criteria (must be explicitly listed in the spec):
  - “ipc init” in any project creates .ipc and fully activates an AI CLI instance with auto-responder enabled using a single command.
  - Another project can detect and communicate with that instance; status/ping visibly confirm cross-project connectivity.
  - No IPC files leak into project root outside .ipc; runtime artifacts remain out of version control.
  - Commands provide clear, actionable errors and --help usage.

Implementation note for this prompt:
- Still run .specify/scripts/powershell/create-new-feature.ps1 exactly once and parse its JSON for BRANCH_NAME and SPEC_FILE.
- Load .specify/templates/spec-template.md and follow its section order. If the template lacks sections required above, append them at the end under “Additional Sections”.
- Write the final specification to SPEC_FILE with concrete, testable details derived from the feature description.
