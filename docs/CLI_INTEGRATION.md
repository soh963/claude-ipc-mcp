# CLI 통합 및 전역 바로가기

이 가이드는 IPC 도구들을 전역 명령어나 바로가기로 노출하여
Claude CLI, Gemini CLI, Codex CLI(또는 어떤 터미널에서도)에서
즉시 메시지 교환을 트리거하는 방법을 설명합니다.
예시는 Windows PowerShell을 기준으로 하지만, 동일한 개념이 다른 셸에도 적용됩니다.

## 1. tools 디렉터리를 PATH에 추가

리포지토리의 `tools` 폴더를 사용자 수준 `PATH`에 추가하면,
디렉터리 내 스크립트를 전체 경로를 지정하지 않고도 실행할 수 있습니다.

```powershell
$repo = "D:\\claude-ipc-mcp"
$toolsPath = Join-Path $repo "tools"
setx PATH "$env:PATH;$toolsPath"
```

이후 새 터미널을 열어주세요. 이제 어느 위치에서든
`chat_once.py` 또는 `nl_auto_chat.py` 같은 명령을 실행할 수 있습니다.

## 2. 편의용 별칭 정의(선택 사항)

다음 내용을 PowerShell 프로필에 추가하세요(`notepad $PROFILE` 실행).
IPC 채팅 작업을 위한 간단한 명령들과 하나의 환경 변수를 제공합니다.

```powershell
$env:IPC_CHAT = "python $toolsPath\nl_auto_chat.py"
function ipc-chat { python $toolsPath\nl_auto_chat.py @args }
function ipc-ping {
    param(
        $From = "codex",
        $To = "gemini",
        [Parameter(Mandatory=$true)][string]$Message
    )
    python $toolsPath\chat_once.py $From $To $Message --auto-responder --timeout 10
}
function ipc-responder-list { python $toolsPath\manage_responders.py }
function ipc-responder-stop {
    param($Instance)
    if ($Instance) {
        python $toolsPath\manage_responders.py --instance $Instance --stop
    } else {
        python $toolsPath\manage_responders.py --stop-all
    }
}
```

PowerShell을 다시 로드한 뒤 다음처럼 호출할 수 있습니다:

- `ipc-chat "codex가 gemini에게 '테스트' 보내고 확인"`
- `ipc-ping -Message "서버 상태 점검 중"`
- `ipc-responder-list` / `ipc-responder-stop codex`

다른 셸에서도 유사한 별칭을 사용할 수 있습니다(예: `~/.bashrc`에 함수 추가).

## 3. Claude / Gemini / Codex CLI 슬래시 명령에 연결

사용 중인 AI CLI가 사용자 지정 슬래시 명령을 지원한다면,
명령을 자연어 래퍼로 연결하세요:

- **Claude CLI**: `~/.claude/config.json`에 추가(예시)

  ```json
  {
    "slashCommands": {
      "/ipc": "python D:/claude-ipc-mcp/tools/nl_auto_chat.py {input}"
    }
  }
  ```

- **Gemini CLI**: 동일한 Python 명령을 호출하는 `/ipcchat`을 구성 파일에 등록하세요.
- **Codex CLI**: 사용자의 요청을 래퍼로 실행하는 바로가기 또는 명령 팔레트 항목을 등록하세요.

슬래시 명령을 설정하면, AI CLI 내부에서 예를 들어 `/ipc "codex가
 gemini에게 '배포 준비 완료?' 보내고 실시간으로 확인"`처럼 입력하고
`nl_auto_chat.py`가 요청을 해석하고 실행하도록 할 수 있습니다.

## 4. 빠른 참조 명령어

- `chat_once.py <from> <to> <message> [--auto-responder] [--monitor]`
- `auto_chat_demo.py <agent_a> <agent_b> --message ... --duration ...`
- `nl_auto_chat.py <natural-language prompt>`
- `manage_responders.py [--instance codex] [--stop]`

### 다중 에이전트 실행기(신규)

- `launch_agents.py --count 10 --prefix agent`
  - 브로커를 보장하고 agent01~agent10을 병렬 등록합니다.
- `launch_agents.py --count 10 --prefix agent --no-responder`
  - 등록만 수행하고 자동 응답기는 시작하지 않습니다.
- `launch_agents.py --dry-run`
  - 실행 계획만 출력하고 변경은 하지 않습니다.

로그인 시 `start_broker.py`를 실행하여 브로커를 항상 사용 가능하도록 유지하세요
(작업 스케줄러 또는 셸 시작 스크립트).
PATH와 별칭 설정이 완료되면, 어느 위치나 AI CLI 환경에서도
바로 이 도구들을 실행할 수 있습니다.
