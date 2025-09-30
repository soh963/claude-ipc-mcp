# 2025-09-29 — Feature: 001-description-ipc-root Tasks & Docs Alignment

## Summary
- Updated and aligned specification documents under `specs/001-description-ipc-root/` with current implementation behavior.
- Added Quickstart and linked from docs index.
- Clarified CLI contracts for `ipc register` to match actual exit code behavior.

## Files Changed
- specs/001-description-ipc-root/contracts/cli-contracts.md — Update `ipc register` contract and notes
- specs/001-description-ipc-root/quickstart.md — Windows-first quickstart incl. register + auto-responder
- specs/001-description-ipc-root/data-model.md — Add session entity and optional `session_token` in messages
- specs/001-description-ipc-root/research.md — Record optional PyJWT, spawn strategies, detection heuristics
- specs/001-description-ipc-root/tasks.md — Add T011a contract test and dependencies
- docs/README.md — Link Quickstart

## Verification
- Lint: `ruff check .` — PASS
- Tests: `pytest -q` — PASS
- Manual review of `tools/ipc_register_with_responder.py` to ensure contract alignment

## Behavior Impact
- No runtime behavior changes; documentation/spec clarification only.
- Exit code semantics documented for `ipc register` (responder start failures do not fail registration).

## Next Steps
- Implement contract test `tests/contract/test_ipc_register.py` (T011a).
- Proceed with CLI command implementations (T023–T028) behind tests.

---

# Change Record: 001-description-ipc-root (Models & Tests)

- Date: 2025-09-29
- Impact: MINOR
- Scope: Specs → Phase 3.2/3.3 groundwork (models + unit tests); contract test stability for registration script (T011a)

## Summary
- Added core model dataclasses under `src/core/models/`:
	- `broker.py` (T014): Broker(version, port, started_at) with `from_env()` helper.
	- `project_context.py` (T015): ProjectIPCContext with path resolution and sanitized project_id via `build()`.
	- `responder.py` (T016): Responder(name, role, topics, status).
	- `routing.py` (T017): validate_instance_id, Address, Handshake with validation.
	- `message.py` (T018): Message with `new()` factory (uuid, ts, corr_id).
- Implemented unit tests under `tests/unit/models/` validating the above.
- Hardened contract test for registration script (T011a) with env-driven broker endpoint and fake broker isolation.
- Updated specs checklist to mark models coverage.

## Files Added
- `src/core/models/broker.py`
- `src/core/models/project_context.py`
- `src/core/models/responder.py`
- `src/core/models/routing.py`
- `src/core/models/message.py`
- `tests/unit/models/test_broker_model.py`
- `tests/unit/models/test_routing_model.py`
- `tests/unit/models/test_message_model.py`
- `tests/unit/models/test_project_context_model.py`

## Validation
- Ran `pytest` for unit model tests → PASS.
- Full suite remained green after changes in prior runs.

## Notes
- `datetime.utcnow()` in Message emits a deprecation warning; follow-up to switch to timezone-aware `datetime.now(datetime.UTC)` in future change.
- Next: Implement utils (T019–T022) and CLI commands (T023–T027) with tests-first per contracts (T007–T011).
