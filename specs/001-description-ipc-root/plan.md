
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
전역 `ipc` CLI로 어떤 프로젝트 디렉터리에서도 `ipc init`만으로 `.ipc/` 하위에 설정/시크릿/로그/상태를 생성하고, 싱글톤 브로커와 연결된 자동 응답 AI CLI 인스턴스를 활성화한다. `ipc status/ping/chat`으로 프로젝트 간 통신을 쉽게 검증할 수 있게 하며, Windows PowerShell을 1급 지원 대상으로 한다. 전역 노출은 `scripts/install-global.ps1`로 PATH에 `scripts/`와 `tools/`를 추가하고 `ipc.bat`를 배치하여 달성한다.

## Technical Context
**Language/Version**: Python 3.12  
**Primary Dependencies**: argparse, subprocess, Pathlib; 내부 도구(`tools/*.py`), 브로커(`src/claude_ipc_server.py`)  
**Storage**: `%USERPROFILE%\\.claude-ipc-data` 내 메시지 DB(`messages.db`)  
**Testing**: pytest, 기존 `test/` 스위트 + E2E 스크립트  
**Target Platform**: Windows 10/11 + PowerShell 7+ (pwsh)  
**Project Type**: Single project (CLI+tools+server in repo)  
**Performance Goals**: 핑 p95 ≤ 300ms, 채팅 p95 ≤ 1.5s(동일 호스트)  
**Constraints**: 지수 백오프 3회(200→1600ms), 총 타임아웃 5s, 멱등적 init  
**Scale/Scope**: 동시 프로젝트 수 5~10, 프로젝트당 초당 20 이벤트 처리 목표

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (CLI-first text I/O): 충족 — `ipc` 단일 CLI UX 제공, 예시/도움말 포함
- Principle II (Test-first multi-tier): 충족 — 계약/퀵스타트 기반 E2E 테스트 계획 수립
- Principle III (SemVer/compatibility): 충족 — 브로커↔CLI 메이저 일치, 마이너 ±1 정책 정의
- Principle IV (Observability): 충족 — `.ipc/logs/`와 글로벌 로그 디렉터리 사용, `status/doctor` 제공
- Principle V (Change Docs): 충족 — 변경 기록을 `docs/changes/`에 추가 예정
- Quality Gates: 측정 가능한 목표(p95) 명시, 실패 모드/복구 경로 정의, Windows 우선 문서화

현 시점 위반 없음 — Phase 0/1 이후 재점검 예정

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
src/
├── core/
├── claude_ipc_server.py
└── cli/           # (필요 시) 전역 CLI 진입점 래핑

tools/
├── ipc_global_command.py   # 전역 명령 라우터
├── ipc_register.py
├── ipc_send.py
├── ipc_check.py
├── ipc_list.py
└── ipc_doctor.py

scripts/
├── install-global.ps1
├── ipc.bat
└── monitoring.bat

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: 단일 저장소 구조(서버 in `src/`, CLI/도구 in `tools/`, 배포 스크립트 in `scripts/`). 기존 파일을 활용하여 추가 산출물만 생성.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on current Constitution — See `.specify/memory/constitution.md`*
