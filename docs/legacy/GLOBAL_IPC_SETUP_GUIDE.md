# 🌍 글로벌 IPC 설정 가이드 - 한 번 설치, 모든 프로젝트에서 사용

## 🎯 목표
- IPC를 **한 번만** 설치
- **모든 프로젝트**에서 IPC 기능 사용
- 프로젝트마다 GitHub clone 불필요

## 📦 1단계: IPC 중앙 설치 (한 번만!)

### Windows 설정
```powershell
# 1. IPC를 중앙 위치에 설치
cd D:\
git clone https://github.com/your-repo/claude-ipc-mcp.git

# 2. 환경 변수 설정 (영구적)
[System.Environment]::SetEnvironmentVariable("IPC_BASE", "D:\claude-ipc-mcp", "User")
[System.Environment]::SetEnvironmentVariable("PYTHONPATH", "$env:PYTHONPATH;D:\claude-ipc-mcp", "User")

# 3. PATH에 IPC 도구 추가
$env:PATH += ";D:\claude-ipc-mcp\tools"
```

### Mac/Linux 설정
```bash
# 1. IPC를 중앙 위치에 설치
cd ~
git clone https://github.com/your-repo/claude-ipc-mcp.git

# 2. ~/.bashrc 또는 ~/.zshrc에 추가
echo 'export IPC_BASE="$HOME/claude-ipc-mcp"' >> ~/.bashrc
echo 'export PATH="$PATH:$IPC_BASE/tools"' >> ~/.bashrc
echo 'export PYTHONPATH="$PYTHONPATH:$IPC_BASE"' >> ~/.bashrc
source ~/.bashrc
```

## 🚀 2단계: 글로벌 IPC 명령어 생성

### 글로벌 실행 스크립트 생성
```powershell
# Windows: D:\claude-ipc-mcp\ipc.bat 생성
@echo off
python "D:\claude-ipc-mcp\tools\ipc_global_command.py" %*
```

```bash
# Mac/Linux: ~/claude-ipc-mcp/ipc 생성
#!/bin/bash
python "$IPC_BASE/tools/ipc_global_command.py" "$@"
chmod +x ~/claude-ipc-mcp/ipc
```

## 📂 3단계: 새 프로젝트에서 IPC 사용

### 방법 1: 자동 초기화 (권장) ✨

```bash
# 어떤 프로젝트 폴더에서든:
cd D:\my-new-project

# IPC 초기화 (파일 복사 없이 설정만!)
ipc init

# 이렇게 하면:
# ✅ .ipc_project.yml 생성 (프로젝트 설정)
# ✅ 심볼릭 링크 생성 (실제 파일 복사 없음)
# ✅ 프로젝트별 포트 자동 할당
```

### 방법 2: 최소 설정

```bash
# 프로젝트에서
cd D:\my-project

# 설정 파일만 생성
python D:\claude-ipc-mcp\tools\config_loader.py create

# IPC 서버 시작 (중앙 설치 경로에서)
python D:\claude-ipc-mcp\src\claude_ipc_server.py
```

### 방법 3: 심볼릭 링크 사용 (권장) 🔗

```powershell
# Windows (관리자 권한 필요)
cd D:\my-project
mklink /D tools D:\claude-ipc-mcp\tools
mklink /D src D:\claude-ipc-mcp\src

# Mac/Linux
cd ~/my-project
ln -s ~/claude-ipc-mcp/tools tools
ln -s ~/claude-ipc-mcp/src src
```

## 🎨 4단계: 글로벌 IPC 명령어 체계

### 어디서든 사용 가능한 명령어

```bash
# 프로젝트 초기화
ipc init

# IPC 서버 시작 (현재 프로젝트용)
ipc start

# AI 인스턴스 등록
ipc register claude
ipc register gemini
ipc register codex

# 메시지 전송
ipc send claude gemini "메시지 내용"

# 메시지 확인
ipc check claude

# 인스턴스 목록
ipc list

# 상태 점검
ipc health

# 서버 중지
ipc stop
```

## 🔧 5단계: 글로벌 명령어 구현

### 중앙 명령 처리 시스템

```python
# D:\claude-ipc-mcp\tools\ipc_global_command.py
# 모든 프로젝트에서 사용할 수 있는 중앙 명령어 처리기

class GlobalIPCCommand:
    def __init__(self):
        self.ipc_base = Path("D:\\claude-ipc-mcp")
        self.current_dir = Path.cwd()

    def init_project(self, minimal=False):
        """현재 프로젝트를 IPC용으로 초기화"""
        # .ipc_project.yml 생성
        # 심볼릭 링크 생성 (선택적)
        # 프로젝트 고유 ID 및 포트 할당

    def start_server(self):
        """프로젝트별 IPC 서버 시작"""
        # 현재 프로젝트 설정 로드
        # 프로젝트별 포트에서 서버 시작
        # 프로세스 모니터링
```

## 📝 6단계: 실제 사용 예시

### 예시 1: 새 React 프로젝트

```bash
# 1. React 프로젝트 생성
D:\> npx create-react-app my-app
D:\> cd my-app

# 2. IPC 초기화 (파일 복사 없음!)
D:\my-app> ipc init

✅ .ipc_project.yml 생성됨
✅ 프로젝트 ID: proj_a2c4f6e8
✅ 할당된 포트: 9456

# 3. IPC 서버 시작
D:\my-app> ipc start

🚀 IPC 서버 시작됨 (포트: 9456)

# 4. AI 인스턴스 등록
D:\my-app> ipc register claude
D:\my-app> ipc register gemini

# 5. 협업 시작
D:\my-app> ipc send claude gemini "React 컴포넌트 리뷰 부탁해"
```

### 예시 2: Django 프로젝트

```bash
# 1. Django 프로젝트
D:\> django-admin startproject backend
D:\> cd backend

# 2. 최소 설정만
D:\backend> ipc init --minimal

✅ .ipc_project.yml 생성됨 (설정만)
✅ 프로젝트 ID: proj_d8f2a1b6
✅ 할당된 포트: 9789

# 3. 직접 실행
D:\backend> python D:\claude-ipc-mcp\src\claude_ipc_server.py
```

### 예시 3: 기존 프로젝트 마이그레이션

```bash
# 기존에 IPC를 복사해서 사용하던 프로젝트
D:\old-project> dir
tools/  src/  .ipc_project.yml  (복사된 파일들)

# 글로벌 시스템으로 전환
D:\old-project> rmdir /S tools src
D:\old-project> ipc init

✅ 글로벌 IPC로 전환 완료!
```

## 🔍 7단계: 프로젝트 격리 확인

### 격리 모드 작동 확인

```bash
# 프로젝트 A에서
D:\project-a> ipc init
D:\project-a> ipc register claude-a
D:\project-a> ipc send claude-a claude-a "프로젝트 A 메시지"

# 프로젝트 B에서 (다른 프로젝트)
D:\project-b> ipc init
D:\project-b> ipc register claude-b
D:\project-b> ipc check claude-b
❌ 프로젝트 A의 메시지는 수신되지 않음 (격리됨)
```

### 격리 모드 설정 변경

```yaml
# .ipc_project.yml
project:
  isolation_mode: strict    # 기본값: 완전 격리
  # isolation_mode: relaxed # 신뢰 프로젝트만 허용
  # isolation_mode: disabled # 모든 프로젝트 허용
```

## 🛠️ 8단계: 문제 해결

### Windows 심볼릭 링크 권한 문제

```powershell
# 관리자 권한 없이 심볼릭 링크 생성 허용
# 로컬 보안 정책 > 사용자 권한 할당 > 심볼릭 링크 만들기
# 또는 개발자 모드 활성화:
Start-Process "ms-settings:developers"
```

### 환경 변수가 적용되지 않을 때

```powershell
# PowerShell 새로고침
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 또는 시스템 재시작
```

### 포트 충돌 문제

```bash
# 사용 중인 포트 확인
netstat -an | findstr :9

# 포트 변경
ipc init --port 9999
```

## 🎯 9단계: 고급 설정

### 자동 시작 설정

```bash
# Windows 작업 스케줄러
schtasks /create /tn "IPC_Server" /tr "D:\claude-ipc-mcp\ipc.bat start" /sc onlogon

# Mac/Linux systemd
sudo systemctl enable ipc-server.service
```

### 여러 프로젝트 동시 작업

```bash
# 터미널 1: 프로젝트 A
D:\project-a> ipc start
서버 시작됨 (포트: 9123)

# 터미널 2: 프로젝트 B
D:\project-b> ipc start
서버 시작됨 (포트: 9456)

# 각 프로젝트는 독립된 포트 사용
```

### 프로젝트 간 통신 허용

```yaml
# 프로젝트 A의 .ipc_project.yml
project:
  isolation_mode: relaxed
  trusted_projects:
    - proj_b2c4d6e8  # 프로젝트 B의 ID

# 프로젝트 B의 .ipc_project.yml
project:
  isolation_mode: relaxed
  trusted_projects:
    - proj_a1b3c5d7  # 프로젝트 A의 ID
```

## 🚀 10단계: 빠른 시작 체크리스트

### 설치 확인

- [ ] IPC 저장소 클론 완료 (`D:\claude-ipc-mcp`)
- [ ] 환경 변수 설정 완료 (`IPC_BASE`, `PYTHONPATH`)
- [ ] PATH에 도구 경로 추가
- [ ] `ipc.bat` 파일 생성 (Windows)
- [ ] Python 3.8+ 설치 확인

### 프로젝트 설정

- [ ] 프로젝트 폴더로 이동
- [ ] `ipc init` 실행
- [ ] `.ipc_project.yml` 생성 확인
- [ ] 프로젝트 ID 및 포트 확인

### 실행 테스트

- [ ] `ipc start` - 서버 시작
- [ ] `ipc register [name]` - 인스턴스 등록
- [ ] `ipc list` - 등록된 인스턴스 확인
- [ ] `ipc send [from] [to] "test"` - 메시지 전송
- [ ] `ipc check [name]` - 메시지 확인

## 📚 참조 문서

- [IPC 설정 가이드](./IPC_설정_가이드.md) - 상세한 한글 가이드
- [빠른 시작 가이드](../빠른_시작_가이드.md) - 빠른 설정 방법
- [프로젝트 격리 가이드](../PROJECT_ISOLATION_GUIDE.md) - 격리 시스템 이해

## 💡 핵심 장점

1. **한 번 설치**: GitHub 클론 한 번만
2. **모든 프로젝트 사용**: 어디서든 `ipc` 명령어 사용
3. **파일 복사 없음**: 심볼릭 링크 또는 직접 참조
4. **프로젝트 격리**: 각 프로젝트는 독립된 공간
5. **중앙 업데이트**: IPC 업데이트 시 모든 프로젝트 자동 반영

---

**이제 어떤 프로젝트에서든 IPC를 사용할 수 있습니다! 🎉**