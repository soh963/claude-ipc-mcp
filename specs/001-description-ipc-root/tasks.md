# Tasks: Global IPC CLI

**Input**: Design documents from `specs/001-description-ipc-root/` (plan.md, research.md, data-model.md, contracts/cli-contracts.md, quickstart.md)
**Prerequisites**: Python 3.12, Windows PowerShell 7+, existing repo layout (src/, tools/, scripts/, tests/)

## Format: `[ID] [P?] Description`
- [P]: Can run in parallel (different files, no write conflicts). Maintain dependency notes when applicable.
- Always include exact file paths.

## Path Conventions (per plan)
- Source: `src/` (server in `src/claude_ipc_server.py`, new helpers in `src/core/` and `src/cli/`)
- Tools/Router: `tools/ipc_global_command.py`
- Scripts: `scripts/*.ps1|*.bat`
- Tests: `tests/{contract,integration,unit,perf}/`

---

## Phase 3.1: Setup
- [ ] T001 [P] Create test scaffolding directories and base conftest in `tests/contract/`, `tests/integration/cli/`, `tests/unit/cli/`, `tests/perf/` (add minimal `conftest.py` to share temp dir fixtures).
- [ ] T002 [P] Create CLI test helpers `tests/helpers/cli.py` with `run_ipc(args: list[str]) -> CompletedProcess` wrapper (PowerShell-safe subprocess, captures stdout/stderr, returns code/output).
- [ ] T003 [P] Initialize CLI command package `src/cli/commands/__init__.py` and ensure package is importable.
- [ ] T004 [P] Initialize core models package `src/core/models/__init__.py`.
- [ ] T005 [P] Add `.ipc` filesystem helpers module stub `src/core/ipc_fs.py` (create folders: `.ipc/{config,logs,state,secret}`; path resolution only, no logic yet).
- [ ] T006 [P] Add logging helper stub `src/core/logging_utils.py` (resolve project `.ipc/logs` path; thin wrapper around `logging` config).

Dependency notes: T001–T006 are independent and can run fully in parallel.

## Phase 3.2: Tests First (TDD) — MUST FAIL BEFORE 3.3
Contract tests (from contracts/cli-contracts.md: init, status, ping, chat, doctor)
- [ ] T007 [P] Contract test: `ipc init` in `tests/contract/test_ipc_init.py` (assert: creates `.ipc/` subdirs, idempotent re-run, non-zero on incompatible broker).
- [ ] T008 [P] Contract test: `ipc status` in `tests/contract/test_ipc_status.py` (assert: prints broker version/compat state, project_id present).
- [ ] T009 [P] Contract test: `ipc ping` in `tests/contract/test_ipc_ping.py` (assert: p95 budget placeholder; success exit code; timing metric collected).
- [ ] T010 [P] Contract test: `ipc chat --to <proj> "Hello"` in `tests/contract/test_ipc_chat.py` (assert: message ack and corr_id echoed).
- [ ] T011 [P] Contract test: `ipc doctor` in `tests/contract/test_ipc_doctor.py` (assert: detects common issues, returns actionable tips).

Integration tests (from quickstart.md)
- [ ] T012 Integration test: Quickstart flow in `tests/integration/cli/test_quickstart_flow.py` (init → status → ping within one project; asserts match quickstart expectations). Depends on T007–T011 specs.
- [ ] T013 Integration test: Cross-project chat in `tests/integration/cli/test_cross_project_chat.py` (two temp projects; `proj-b` chats to `proj-a`; avoid parallel run with T012 due to singleton broker). Depends on T007–T011 specs.

Dependency notes:
- T007–T011 can run in parallel (distinct files). T012 and T013 should run serially relative to each other (singleton broker), but can be prepared in parallel.

## Phase 3.3: Core Implementation (ONLY after tests are failing)
Models (from data-model.md)
- [ ] T014 [P] Model: Broker in `src/core/models/broker.py` (semver, port, status, started_at; dataclass + from_env helpers).
- [ ] T015 [P] Model: ProjectIPCContext in `src/core/models/project_context.py` (paths, project_id stable derivation, responders list).
- [ ] T016 [P] Model: Responder in `src/core/models/responder.py` (name, role, topics, status).
- [ ] T017 [P] Model: Identity & Routing in `src/core/models/routing.py` (address format, handshake struct; validation functions).
- [ ] T018 [P] Model: Message in `src/core/models/message.py` (uuid id, from/to, topic, payload, ts, corr_id optional).

Core utilities
- [ ] T019 [P] Implement `.ipc` filesystem utils in `src/core/ipc_fs.py` (create dirs, write default `config.yaml`, `secrets.env`, `state/` sentinel, `logs/` rotate policy; idempotent).
- [ ] T020 [P] Implement version compatibility check in `src/core/compat.py` (broker↔CLI major equal, minor ±1; restricted-mode detection messages).
- [ ] T021 [P] Implement retry/backoff in `src/core/retry.py` (200→400→800→1600ms cap; max 3 attempts; 5s overall timeout guard).
- [ ] T022 [P] Implement project-scoped logging config in `src/core/logging_utils.py` (file+stderr, INFO default, path: `.ipc/logs/cli.log`).

CLI commands (split per-file to maximize parallelism)
- [ ] T023 [P] Implement `ipc init` in `src/cli/commands/init_cmd.py` (use ipc_fs + compat; print created paths; exit non-zero on incompatible major).
- [ ] T024 [P] Implement `ipc status` in `src/cli/commands/status_cmd.py` (report broker version/compat, project_id, responders count).
- [ ] T025 [P] Implement `ipc ping` in `src/cli/commands/ping_cmd.py` (send ping via broker; measure latency; respects retry/timeouts).
- [ ] T026 [P] Implement `ipc chat` in `src/cli/commands/chat_cmd.py` (send message to address; print corr_id and ack).
- [ ] T027 [P] Implement `ipc doctor` in `src/cli/commands/doctor_cmd.py` (checks: PATH, broker running, secret present, version compat; suggestions).
- [ ] T028 Wire router: update `tools/ipc_global_command.py` to route subcommands to new modules (no behavior change otherwise).

Integration glue
- [ ] T029 Add broker detection/auto-start helper `src/core/broker_client.py` (detect running broker; optionally call `tools/start_broker.py`; used by init/status). Depends on T020.

## Phase 3.4: Validation & Integration
- [ ] T030 Ensure request/response logging to `.ipc/logs/` for all commands via `logging_utils` middleware hooks. Depends on T022, T023–T027.
- [ ] T031 Make T007–T013 tests pass (iterate on implementations until green). Depends on T014–T030.

## Phase 3.5: Polish
- [ ] T032 [P] Unit tests for utils in `tests/unit/cli/test_utils.py` (retry/backoff, compat, logging path resolution).
- [ ] T033 [P] Performance harness: `tests/perf/test_ping_perf.py` (assert median and p95 under targets on localhost; mark as xfail on CI if unstable).
- [ ] T034 [P] Documentation updates: refine `specs/001-description-ipc-root/quickstart.md` and link from `docs/README.md`.
- [ ] T035 Create change record: `docs/changes/2025-09-29-feature-001-description-ipc-root-tasks.md` (impact: MINOR; includes how to execute tasks and validation notes).

---

## Dependencies (summary)
- Setup (T001–T006) → Tests (T007–T013) → Models/Utils (T014–T022) → CLI (T023–T028) → Glue/Validation (T029–T031) → Polish (T032–T035)
- Contract tests T007–T011 independent; Integration tests T012↔T013 serial due to singleton broker
- Models T014–T018 independent (separate files)
- Utils T019–T022 independent (separate files)
- CLI commands T023–T027 independent (separate files); T028 routes them
- T029 depends on compat (T020)
- T030 depends on logging (T022) and command implementations (T023–T027)
- T031 depends on all prior implementation tasks

## Parallel Execution Examples (PowerShell terminals)
- Group G1 — Setup (run in parallel): T001, T002, T003, T004, T005, T006
  - Agent command examples:
    - Task: "T001 Create test scaffolding directories and base conftest"
    - Task: "T002 Create CLI test helpers tests/helpers/cli.py"
    - Task: "T003 Initialize src/cli/commands package"
    - Task: "T004 Initialize src/core/models package"
    - Task: "T005 Add src/core/ipc_fs.py stub"
    - Task: "T006 Add src/core/logging_utils.py stub"
- Group G2 — Contract tests (run in parallel): T007, T008, T009, T010, T011
  - Agent command examples:
    - Task: "T007 Contract test ipc init in tests/contract/test_ipc_init.py"
    - Task: "T008 Contract test ipc status in tests/contract/test_ipc_status.py"
    - Task: "T009 Contract test ipc ping in tests/contract/test_ipc_ping.py"
    - Task: "T010 Contract test ipc chat in tests/contract/test_ipc_chat.py"
    - Task: "T011 Contract test ipc doctor in tests/contract/test_ipc_doctor.py"
- Group G3 — Models & Utils (run in parallel): T014–T022
- Group G4 — CLI commands (run in parallel): T023–T027; then T028 (route) after all five are ready
- Serial pair — Integration tests: T012 then T013 (avoid race on singleton broker)

## Validation Checklist
- [ ] All contracts have corresponding tests (T007–T011)
- [ ] All entities have model tasks (T014–T018)
- [ ] Tests precede implementation for each command
- [ ] Parallel tasks do not touch the same file
- [ ] Each task has exact file paths
- [ ] Change record created and linked (T035)

---
Generated per `.github/prompts/tasks.prompt.md` using available design artifacts.
