<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: (initial adoption)
- Added sections: Core Principles; Additional Constraints; Development Workflow & Quality Gates; Governance
- Removed sections: None
- Templates requiring updates:
	✅ .specify/templates/plan-template.md (Constitution Check note; remove hardcoded version)
	✅ .specify/templates/tasks-template.md (Add Change Documentation task)
	✅ .specify/templates/spec-template.md (Checklist: Change impact identified)
	⚠ pending: .specify/templates/commands/* (no files present)
	⚠ pending: README.md (optional link to constitution and changes directory)
- Follow-up TODOs:
	- TODO(RATIFICATION_DATE): original adoption date unknown; set when formally ratified
	- Decide on CHANGELOG.md summary vs per-change docs/changes/YYYY-MM-DD.md (constitution allows both)
-->

# Claude IPC MCP Constitution

## Core Principles

### I. CLI-First & Text I/O Contracts (NON-NEGOTIABLE)
- All user-facing functionality MUST be invocable via CLI or script entry points
	(PowerShell/cmd/Bash) with text I/O contracts: args/stdin → stdout; errors → stderr.
- Commands SHOULD support both human-readable and JSON output when applicable.
- CLI flags and subcommands MUST remain backward compatible across MINOR releases;
	breaking changes REQUIRE a MAJOR version.
Rationale: The project centers on cross-tool automation (PowerShell, .bat, Python
scripts). Stable text I/O contracts keep tools composable and testable.

### II. Test-First with Multi-Tier Coverage
- Write tests before implementation for new behaviors (unit → contract → integration → e2e).
- New commands/contracts MUST include contract tests that assert request/response shapes.
- CI MUST fail if coverage for changed areas regresses materially or critical tests fail.
Rationale: The repository already contains unit/integration/e2e tests; codifying a
test-first discipline prevents regressions in CLI and inter-agent behavior.

### III. Semantic Versioning & Backward Compatibility
- Follow SemVer: MAJOR for breaking changes; MINOR for additions; PATCH for fixes/clarifications.
- Public CLI contracts and persisted data formats MUST preserve compatibility within a MAJOR line.
- Deprecations MUST include a warning period (≥1 MINOR) and migration notes.
Rationale: Users script against these tools; version signals and deprecation windows are essential.

### IV. Observability & Diagnosability
- All tools MUST log meaningful, structured events (level, context, error details) to aid diagnosis.
- Logs SHOULD default to human-readable; enable JSON mode via flag for machine processing.
- Commands MUST provide a "--verbose" and SHOULD provide "--dry-run" where sensible.
Rationale: The repo ships logging and health/doctor tools; consistent signals speed up support.

### V. Change Documentation & Upgrade Discipline
- For every merged change that alters behavior, data, or contracts, authors MUST create a
	change record separate from code:
	- Either append to CHANGELOG.md under the unreleased/release section, or
	- Create a dated file under docs/changes/YYYY-MM-DD-[short-slug].md
- Each change record MUST include: impact (user-facing/internal), type (PATCH/MINOR/MAJOR),
	migration steps (if any), and links to PR/issues.
- Releases MUST summarize these records in the changelog and tag with the version.
Rationale: The user requirement states all work changes must be documented and stored separately;
this makes review, audit, and upgrades predictable.

## Additional Constraints

- Language/Runtime: Python 3.12+ is the target; scripts MUST state compatible versions
	and avoid non-portable features without justification.
- OS/Shell: Cross-platform behavior MUST be preserved for pwsh/cmd/Bash where applicable;
	Windows-specific scripts SHOULD provide Unix equivalents or document limitations.
- Data & Security: Persisted messages/configs MUST avoid storing secrets in plaintext; provide
	guidance for environment-based secrets when integration requires them.
- Documentation Locations:
	- Constitution: .specify/memory/constitution.md
	- Change records: CHANGELOG.md and/or docs/changes/* (per Principle V)
	- Feature docs: specs/[###-feature]/

## Development Workflow & Quality Gates

- Constitution Check: Plans/specs MUST include a Constitution Check section aligned with this
	document. Violations require justification in Complexity Tracking.
- TDD Gate: Contract and integration tests MUST be written and fail before implementation
	for new or changed contracts.
- Review Gate: Every PR MUST include a link to its change record (Principle V) and state
	version impact (PATCH/MINOR/MAJOR) with rationale.
- Quality Gate: CI MUST run unit, integration, and e2e tests; lint/type checks where applicable.
- Release Gate: Before tagging, ensure changelog updated and migration notes present.

## Governance

- Supremacy: This Constitution governs development practices for this repository. Where other
	documents conflict, this Constitution prevails unless explicitly amended.
- Amendments: Proposals MUST include redlines, version bump type, migration impact, and be
	recorded as a change record (Principle V). Approval: standard review + maintainer sign-off.
- Versioning Policy: CONSTITUTION_VERSION follows SemVer:
	- MAJOR: Breaking governance changes (removals/redefinitions of principles).
	- MINOR: New principle/section or materially expanded guidance.
	- PATCH: Clarifications, wording, non-semantic refinements.
- Compliance Reviews: PR reviewers MUST verify Constitution Check in plans/specs and presence of
	a change record. Non-compliant PRs are rejected.
- Runtime Guidance: Follow docs in README.md and docs/*; prefer CLI contracts and text I/O.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date to be set by maintainers | **Last Amended**: 2025-09-29