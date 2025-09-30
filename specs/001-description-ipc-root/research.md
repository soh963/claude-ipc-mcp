# Phase 0 Research: Global IPC CLI

## Decisions

1) OS/Shell Support (Official)
- Windows 10/11 + PowerShell 7+ (pwsh) 1급 지원.
- macOS/Linux는 제한적 지원(Best-effort)으로 문서화. 실패 시 대체 절차 제공.

Rationale: 현재 저장소의 스크립트/배치(`.bat`, `.ps1`) 중심이며, 사용자 환경 정보도 Windows/Pwsh임.
Alternatives: 완전한 크로스플랫폼 지원(초기 비용↑) → Phase 2 이후 확대.

2) Global Install Strategy
- Primary: `scripts/install-global.ps1`로 PATH에 `scripts/`, `tools/` 추가, `ipc.bat` 배치.
- Secondary: `uv` 설치 권장, 필요 시 `pipx`/`uvx`로 래퍼 제공.

Rationale: 리포지토리 내 존재하는 `install-global.ps1`와 `ipc.bat`를 활용하여 최소 변경으로 목표 달성.
Alternatives: MSI/winget 패키징(유지보수 부담↑), pipx 단독 배포(환경 편차↑).

3) Performance Targets
- Ping p95 ≤ 300ms, Chat p95 ≤ 1.5s(동일 호스트, 간단 자동응답 기준), Project TPS≈20.
- Retry: 지수 백오프(200ms→1600ms, 3회), 전체 타임아웃 5s.

Rationale: 사용자 체감 즉응성 기준과 현재 툴셋의 오버헤드 고려한 현실값.
Alternatives: 더 낮은 p95(<100ms)는 설계 변경/네이티브 IPC 필요.

4) Version Compatibility
- Broker↔CLI 메이저 일치 필수, 마이너 ±1 호환. 초과 시 제한 모드.

Rationale: 안전한 호환 범위로 회귀 위험과 복잡도 균형.
Alternatives: SemVer 엄격 호환(마이너만 동일) → 운영 유연성 낮음.

5) Directory Layout & Ownership
- 프로젝트 로컬: `.ipc/` 하위 config/logs/state/secrets.
- 글로벌 런타임: `%USERPROFILE%\\.claude-ipc-data` (브로커 로그/DB 등).

Rationale: 저장소 청결/격리, 보안(시크릿 VCS 제외), 가이드와 일치.

6) Optional Dependencies
- PyJWT는 선택적 의존성으로 취급. 미설치 시 create_token은 친절한 에러, verify_token은 경고 후 None 반환.
- 목적: 배포 용량 축소, 크로스 플랫폼 환경에서의 설치 실패 회피.

7) Windows/Posix 프로세스 스폰 전략
- Windows: `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` 로 백그라운드 응답자 실행.
- POSIX: `start_new_session=True` 로 터미널 세션 분리.
- 실패 시: 등록은 성공으로 처리(종료 코드 0), stdout에 경고 출력.

8) 리스폰더 탐지 휴리스틱
- Windows: `tasklist` 기반의 best-effort 검출.
- POSIX: `ps aux | grep 'auto_responder.py <instance>' | grep -v grep`.
- 목표: 중복 실행 방지(엄격 보장 아님; 추후 PID 파일/소켓 잠금 고려).

## Investigations

- Existing Tools: `tools/ipc_global_command.py`, `tools/ipc_*` 유틸 존재 → 래핑·통합 가능.
- Installer: `scripts/install-global.ps1` 이미 PATH 수정/별칭/프로필 반영 로직 포함.
- Docs: `docs/GLOBAL_IPC_SETUP_GUIDE.md`, `docs/INSTALL_UV.md`와 정합성 유지 필요.

## Open Questions (Deferred)

- macOS/Linux 완전 지원 수준 확대 시기 및 CI 커버리지 범위
- Broker 다중 인스턴스/다중 포트 정책(현행: 싱글톤 지향)

## Next

- Phase 1: 데이터 모델 추출, CLI 계약 정의, Quickstart 작성.
