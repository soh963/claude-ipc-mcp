# Feature Specification: Global IPC CLI with project-local .ipc and one-command init

**Feature Branch**: `001-description-ipc-root`  
**Created**: 2025-09-29  
**Status**: Draft  
**Input**: User description: "기존 프로젝트를 완벽분석하고, 최적화 하며, 작업 진행사 항을 명확하게 볼수 있도록 한다. 글로벌 명령어를 사용하여, 다른 프로젝트 폴더에서 ipc를 사용하면, root폴더에 ipc관련 파일들이 생성이 되는데 .ipc폴더를 생성하고, 해당 폴더에 관련 파일이 실행 될 수 있도록 설계한다. ipc init만으로 해당 프로젝트에 ai cli인스턴스를 활성화 하고, 자동 응답, 서로 통신 할 수 있는 환경을 만들어야 한다. 1개의 명령어로 모든 환경셋팅이 되어야 하며, 쉽게 사용이 가능해야한다. 그리고 실제 다 른 ai cli가 작동되고 사용되고 있는지를 확인하고 소통하는 과정을 쉽게 확인되어야 한다. 이 프로젝트는 여 러 ai cli가 통합되어 서로 연결되고, 각자의 역할과, 서로의 의견을 주고 받아 최적의 최상의 결과를 도출하 는것이 목표이다. 이 목표를 해결하기 위한 스팩을 설정한다."

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
   → Identify change impact per Constitution (PATCH/MINOR/MAJOR) and note migration needs
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
어떤 프로젝트 디렉터리에서든 사용자는 전역 명령어 `ipc`를 실행할 수 있다. 새 프로젝트에서
`ipc init`을 실행하면 프로젝트 루트에 `.ipc/` 디렉터리가 생성되고, 필요한 설정/시크릿/로그/상태
파일들이 해당 폴더 하위에만 생성된다. 초기화 완료 후 자동 응답이 가능한 AI CLI 인스턴스가 활성화되고,
`ipc status`로 브로커 및 연결 상태를 확인하며, 별도의 다른 프로젝트에서도 `ipc ping` 또는
`ipc chat --to <target>`으로 상호 통신이 가능함을 쉽게 검증한다.

### Acceptance Scenarios
1. Given 빈 프로젝트, When 사용자가 `ipc init` 실행, Then `.ipc/`가 생성되고 프로젝트 범위의
   설정/시크릿/로그/상태 구성이 완료되며, 자동 응답 인스턴스가 활성화된다.
2. Given A 프로젝트에서 인스턴스 활성화 완료, When B 프로젝트에서 `ipc status`/`ipc ping` 실행,
   Then A 인스턴스가 감지되고 왕복 지연(latency)과 건강 상태가 표시된다.
3. Given A·B 프로젝트 인스턴스 간 통신, When B에서 `ipc chat --to A "Hello"` 실행,
   Then A가 메시지를 수신하고 자동 응답 또는 지정된 응답 흐름으로 대화가 진행된다.
4. Given Windows PowerShell 환경, When `ipc` 명령이 PATH 상 노출,
   Then 어느 프로젝트 경로에서도 동일한 UX로 동작한다.

### Edge Cases
- 비밀키(IPC_SHARED_SECRET) 불일치: 초기화 또는 통신 시 인증 실패 메시지와 회복 절차 안내
- 브로커 미가동/포트 충돌: 자동 감지 및 재시도/백오프, 사용 가능한 포트 제안, 수동 해결 지침 제공
- 등록 정보(stale) 잔존: 재등록/정리 경로 제시, `ipc doctor`에서 일괄 복구 옵션 제공
- 다른 OS/셸: 공식 지원은 Windows 10/11 + PowerShell 7+ (pwsh). Mac/Linux는 문서화된 제한 하에 Best-effort 지원하며 대체 경로(심볼릭 링크/직접 실행) 제공.
- 대규모 동시 등록/메시지 폭주: 초기 릴리스 기준 프로젝트 단위 초당 20건 처리 목표, 전역 백프레셔/레이트리밋 적용(자세한 값은 Performance 섹션 참조).

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 전역 명령어 `ipc`는 어떤 프로젝트 디렉터리에서든 실행 가능해야 한다(PATH 노출).
- **FR-002**: `ipc init` 실행 시 프로젝트 루트에 `.ipc/` 디렉터리를 생성하고, 프로젝트 범위의
   구성 파일/시크릿/로그/상태를 `.ipc/` 하위에만 생성해야 한다(루트에 누출 금지).
- **FR-003**: `ipc init`은 단일 명령만으로 AI CLI 인스턴스를 활성화하고 자동 응답을 가능하게 해야 한다.
- **FR-004**: `ipc status`는 싱글톤 브로커 가동 여부, 연결된 CLI/리스폰더, 버전, 헬스 상태를 표시해야 한다.
- **FR-005**: `ipc ping` 및 `ipc chat --to <target>`은 프로젝트 간 왕복 통신 확인과 간단한 대화를 지원해야 한다.
- **FR-006**: `.ipc/secrets.env`에 프로젝트별 IPC_SHARED_SECRET를 저장해야 하며, VCS에서 제외되어야 한다.
- **FR-007**: 초기화는 싱글톤 브로커 미가동 시 시작을 시도하고, 가동 중이면 중복 실행 없이 연결만 확립해야 한다.
- **FR-008**: 초기화/연결/핑/채팅 과정에서 발생한 오류는 명확하고 실행 가능한 메시지와 함께 제공되어야 한다.
- **FR-009**: `ipc doctor`는 일반적인 오구성(시크릿 불일치, 포트 충돌, 스테일 등록)을 탐지/가이드해야 한다.
- **FR-010**: 로깅은 프로젝트 범위 이벤트를 `.ipc/logs/`로 남기고, 브로커 로그는 글로벌 경로
   `%USERPROFILE%\\.claude-ipc-data` 하에 위치하도록 해야 한다.
- **FR-011**: 각 명령은 `--help`를 통해 사용법을 제공해야 하며 예시를 포함해야 한다.
- **FR-012**: 기존 도구들과의 연계를 통해 필요한 동작을 수행해야 한다(예: 브로커 시작, 등록, 단발 채팅 등은
   기존 기능 래핑) — 사용자는 통합된 `ipc` UX만 접한다.
- **FR-013**: 멀티 AI CLI 통합을 위해 역할/토픽/어드레싱/핸드셰이크/메시지 스키마를 정의하고 준수해야 한다.
- **FR-014**: `ipc init`은 멱등적이어야 하며 재실행 시 안전하게 현재 상태를 검증/보정해야 한다.
- **FR-015**: 프로젝트 간 통신 성공 여부는 `status/ping/chat`에서 사람이 쉽게 확인 가능해야 한다(명확한 표시).
- **FR-016**: 테스트/문서/예시는 Windows PowerShell 기준을 포함해야 한다.
- **FR-017**: 버전 호환성 정책을 명시해야 한다(브로커↔CLI는 메이저 버전 일치 필수, 마이너는 ±1 범위 호환). 마이너 차이가 2 이상이면 경고 및 제한 모드로 동작.
- **FR-018**: 관찰가능성(로그/이벤트/메트릭)에 대한 최소 필수 항목을 정의해야 한다(초기화, 연결, 핑, 채팅 등).
- **FR-019**: 실패 모드(브로커 다운/시크릿 불일치/포트 충돌/스테일 등록)에서의 복구 경로를 제공해야 한다.
- **FR-020**: `.ipc/` 디렉터리 레이아웃(예: config.yaml, secrets.env, responders.json, logs/, state/)을 정의해야 한다.
- **FR-021**: `.ipc/` 및 글로벌 런타임 경로는 저장소 가이드라인을 준수해야 한다(AGENTS.md, Repository Guidelines).
- **FR-022**: `ipc status` 표시는 핵심 지표(브로커 가동, 연결 수, 마지막 핑, 버전)를 포함해야 한다.
- **FR-023**: EDP 시나리오(초기화→상태→핑→채팅)는 문서화된 절차대로 재현 가능해야 한다.
- **FR-024**: 문서/도움말에는 오류 사례와 복구 지침이 포함되어야 한다.

*Ambiguities resolved:*
- **FR-025**: 글로벌 설치 전략은 기본적으로 `scripts/install-global.ps1` 실행을 통해 PATH에 `scripts/`와 `tools/`를 추가하고 `ipc.bat`(또는 alias)를 노출한다. 보조 옵션으로 `uv` 설치를 권장하며, 필요 시 `pipx`/`uvx`로 래퍼를 제공할 수 있다.
- **FR-026**: 최소 성능 목표는 동일 호스트 상 프로젝트 간 핑 p95 ≤ 300ms, 단순 자동응답 대화(chat) p95 ≤ 1.5s. 재시도/백오프는 지수 백오프(200ms, 400ms, 800ms, 1.6s 최대 3회)와 총 타임아웃 5s.
- **FR-027**: 공식 지원 OS/셸은 Windows 10/11 + PowerShell 7+ (pwsh). macOS/Linux는 제한적 지원으로 문서화하며, 실패 시 대체 경로(직접 python 경로 사용) 안내.

### Key Entities *(include if feature involves data)*
- **Broker (Singleton)**: 중앙 라우팅/상태 보유. 가용성/버전/포트 구성.
- **Project IPC Context**: 각 프로젝트의 `.ipc/` 하위 구성/시크릿/로그/상태 집합.
- **Responder/CLI Instance**: 특정 이름/역할/토픽을 가진 통신 주체(자동 응답 가능).
- **Identity & Routing**: 주소 체계(이름/역할/토픽), 핸드셰이크, 인증(시크릿), 메시지 스키마.
- **Message**: 발신/수신자, 토픽, 페이로드, 타임스탬프, 상관관계 식별자.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified
- [ ] Change impact identified (PATCH/MINOR/MAJOR) per Constitution

> Change Impact (per Constitution): MINOR — 전역 CLI 및 프로젝트 로컬 초기화/통신 기능의 신규 도입(파괴적 변경 없음)

---

## Additional Sections

### Scope and Goals
- 전역 CLI `ipc`는 어느 프로젝트 디렉터리에서든 동작해야 함.
- `ipc init`은 프로젝트 로컬 `.ipc/` 내에 모든 IPC 관련 파일을 생성/유지하고, 글로벌 런타임 산출물은
   `%USERPROFILE%\\.claude-ipc-data` 하에 유지(저장소에는 포함되지 않음).
- 여러 AI CLI가 상호 연결/협업하여 최적 해를 도출하는 것을 목표로 함(역할/토픽 기반 협업).

### Architecture and Components
- 싱글톤 브로커에 외부 프로젝트가 연결되는 모델.
- `.ipc/` 레이아웃 예: `config.yaml`, `secrets.env`, `responders.json`, `logs/`, `state/`.
- 관심사 분리: 브로커/서버는 `src/`, 툴링은 `tools/`, 스크립트는 `scripts/`, 문서/예제/테스트는 가이드에 따름.
- 다중 AI CLI 아이덴티티/라우팅: 역할/토픽/주소/핸드셰이크/메시지 스키마 정의.

### Bootstrap and Commands (CLI UX)
- `ipc init`: `.ipc` 생성, 구성 생성, 프로젝트별 시크릿 발급/저장, 브로커 보장(미가동 시 시작),
   리스폰더 등록, 자동 응답 활성화, 연결성 검증.
- `ipc status`: 브로커 상태, 연결 CLI/리스폰더, 버전, 헬스/지표 표시.
- `ipc ping`, `ipc chat --to <target>`: E2E 체크 및 간단 대화.
- 기존 도구(브로커 시작, 등록, 단발 채팅 등)는 통합 CLI에서 투명하게 래핑되어야 함(사용자는 단일 UX 사용).

### Security
- 프로젝트별 IPC_SHARED_SECRET는 `.ipc/secrets.env` 보관, VCS 제외.
- 프로젝트 `.ipc` ↔ 싱글톤 브로커 간 핸드셰이크/인증 흐름, 롤테이션 및 진단 경로 제공.

### Observability and Diagnostics
- 프로젝트 이벤트는 `.ipc/logs/`, 브로커 로그는 글로벌 디렉터리.
- `ipc doctor`: 흔한 오구성 표면화 및 가이드.
- 초기화/연결/핑/채팅 메트릭/이벤트 정의.

### Performance and Reliability
- 성능 목표: 동일 호스트 간 핑 p95 ≤ 300ms, 채팅 p95 ≤ 1.5s(간단 자동응답 기준). 처리율 목표는 프로젝트 단위 초당 20 이벤트.
- 신뢰성: 지수 백오프(200ms→1.6s, 3회)와 총 타임아웃(5s) 적용. `ipc init`은 멱등적으로 재실행 가능하며, 브로커 재시작 시 자동 재연결 시도.

### Failure Modes and Recovery
- 시크릿 불일치, 브로커 불가용, 포트 충돌, 스테일 등록 등의 복구 경로와 사용자 안내 제공.

### Compatibility and Distribution
- 기본 전역 설치 전략: `scripts/install-global.ps1`로 환경 변수/경로를 구성하고 `ipc.bat`를 PATH에 노출. 보조로 `uv` 설치 권장 및 `pipx`/`uvx` 래핑 옵션 제공.
- CLI↔브로커 버전 호환 정책 명시.

### Testing
- `test/` 하 단위 테스트: 전제조건(docstring): 브로커 가동, IPC_SHARED_SECRET 설정.
- 스모크: `test/test_ipc.sh`, `uv run python test/test_security.py`에 상응하는 시나리오.
- E2E: `ipc init → ipc status → ipc ping → ipc chat` 다중 프로젝트 경로.
- 주요 IPC 경로 커버리지 목표 및 공백 문서화.

### Rollout and Migration
- `.ipc`를 `.gitignore`에 추가, 안전 기본값, 롤백(폴더 정리, 리스폰더 해제) 절차.
- `.ipc`와 `%USERPROFILE%\\.claude-ipc-data` 사이 데이터 소유 경계 명확화.

### Acceptance Criteria (explicit)
1) 어떤 프로젝트에서든 `ipc init`만으로 `.ipc` 생성 및 AI CLI 인스턴스 활성화(자동 응답 포함)가 완료된다.
2) 다른 프로젝트가 해당 인스턴스를 감지/통신할 수 있으며 `status/ping`으로 교차 연결이 명확히 확인된다.

---

## Clarifications

1) 공식 지원 OS/셸 범위
   - Windows 10/11, PowerShell 7+ (pwsh)을 1급 지원 대상으로 한다.
   - macOS/Linux는 제한적 지원: 심볼릭 링크/직접 실행 경로로 동등 기능 제공을 시도하되, 일부 자동화(예: mklink 권한)는 대체 절차로 안내한다.

2) 글로벌 설치 전략
   - 1차: `scripts/install-global.ps1`로 PATH(`scripts/`, `tools/`) 추가 및 `ipc.bat` 배치. 재부팅 후 어느 경로에서나 `ipc` 사용 가능.
   - 2차(선택): `uv` 설치 권장. 필요 시 `pipx`/`uvx`로 랩핑하여 `ipc`를 별도 위치에 노출.

3) 성능 목표 및 백오프
   - 동일 호스트 내 프로젝트 간 핑 p95 ≤ 300ms, 단순 자동응답 대화 p95 ≤ 1.5s.
   - 재시도: 지수 백오프 3회(200ms→400ms→800ms→1600ms 상한), 총 타임아웃 5s.

4) 버전 호환성 정책
   - 브로커↔CLI는 메이저 버전 일치가 필수. 마이너는 ±1까지 상호 운용 지원.
   - 범위를 벗어나면 경고를 표기하고 제한 모드(읽기 전용 상태/핑만)로 동작.

5) 문서/테스트 기준 환경
   - 모든 예시/테스트는 Windows PowerShell 기준을 기본 포함. 타 OS는 별도 부록으로 제공.
3) IPC 관련 파일은 `.ipc/` 외에 프로젝트 루트에 생성되지 않으며, 런타임 산출물은 VCS에서 제외된다.
4) 모든 명령은 명확한 오류 메시지와 `--help` 사용법을 제공한다.

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---
