#!/usr/bin/env python3
"""
싱글톤 브로커 런처 - 시스템 전체에 단일 브로커만 실행되도록 보장
"""
import os
import sys
import time
import socket
import subprocess
import json
from pathlib import Path

# psutil이 설치되지 않은 경우를 대비한 대체 로직
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil not installed. Using alternative process checking.")


class BrokerManager:
    def __init__(self):
        self.lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
        self.broker_script = Path(__file__).parent.parent / "src" / "claude_ipc_server.py"
        self.broker_host = 'localhost'
        self.broker_port = 9876
        # 데이터 디렉토리 생성
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def is_port_listening(self) -> bool:
        """포트가 실제로 LISTENING 상태인지 확인"""
        if HAS_PSUTIL:
            for conn in psutil.net_connections():
                if conn.laddr.port == self.broker_port and conn.status == 'LISTEN':
                    return True
            return False
        else:
            # 대체 방법: netstat 명령 사용
            import platform
            if platform.system() == 'Windows':
                cmd = f'netstat -an | findstr :{self.broker_port}'
            else:
                cmd = f'netstat -an | grep :{self.broker_port}'

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return 'LISTENING' in result.stdout or 'LISTEN' in result.stdout

    def is_process_running(self, pid: int) -> bool:
        """프로세스가 실행 중인지 확인"""
        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                return process.is_running() and 'python' in process.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        else:
            # 대체 방법: OS 명령 사용
            import platform
            if platform.system() == 'Windows':
                cmd = f'tasklist /FI "PID eq {pid}" 2>nul'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return str(pid) in result.stdout
            else:
                try:
                    os.kill(pid, 0)
                    return True
                except OSError:
                    return False

    def test_broker_connection(self) -> bool:
        """브로커에 실제 연결 시도"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.broker_host, self.broker_port))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"  Connection test failed: {e}")
            return False

    def cleanup_stale_processes(self):
        """TIME_WAIT 상태의 연결과 좀비 프로세스 정리"""
        if HAS_PSUTIL:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if any('claude_ipc_server.py' in str(arg) for arg in cmdline):
                            if proc.pid != self.get_locked_pid():
                                proc.terminate()
                                print(f"  ⚠️ Terminated orphan broker process: {proc.pid}")
                                time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            # 수동으로 정리하기 어려우므로 경고만 표시
            print("  ℹ️ Manual cleanup may be needed for orphan processes")

    def get_locked_pid(self) -> int:
        """락 파일에서 PID 읽기"""
        if self.lock_file.exists():
            try:
                return int(self.lock_file.read_text().strip())
            except (ValueError, OSError):
                return 0
        return 0

    def start_broker(self) -> bool:
        """브로커 시작"""
        print("🚀 Starting singleton broker...")

        # 기존 프로세스 정리
        self.cleanup_stale_processes()

        # Python 실행 파일 경로 확인
        python_exe = sys.executable
        broker_path = str(self.broker_script)

        print(f"  Python: {python_exe}")
        print(f"  Script: {broker_path}")

        # 브로커 시작
        if sys.platform == 'win32':
            # Windows: CREATE_NEW_CONSOLE로 독립 프로세스 생성
            try:
                # Windows에서 백그라운드로 실행
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                proc = subprocess.Popen(
                    [python_exe, broker_path],
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            except Exception as e:
                print(f"  ❌ Failed to start broker: {e}")
                return False
        else:
            # Unix: nohup으로 데몬화
            try:
                proc = subprocess.Popen(
                    ['nohup', python_exe, broker_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
            except Exception as e:
                print(f"  ❌ Failed to start broker: {e}")
                return False

        print(f"  Started process with PID: {proc.pid}")

        # 시작 대기 및 검증
        for i in range(20):  # 10초 대기
            time.sleep(0.5)
            if self.test_broker_connection():
                # 브로커가 응답하면 PID 저장
                self.lock_file.write_text(str(proc.pid))
                print(f"✅ Broker started successfully (PID: {proc.pid})")
                return True
            else:
                print(f"  Waiting for broker to respond... ({i+1}/20)")

        print("❌ Failed to start broker (timeout)")
        return False

    def test_broker_with_registration(self) -> bool:
        """브로커에 실제 테스트 등록 시도"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            # 테스트 등록 요청
            test_id = f"broker_test_{int(time.time())}"
            request = json.dumps({'action': 'register', 'instance_id': test_id})
            sock.send(request.encode())

            # 응답 대기
            response = sock.recv(4096).decode()
            sock.close()

            if response:
                result = json.loads(response)
                # session_token이 있으면 성공
                if 'session_token' in result:
                    print(f"  ✅ Broker test successful (registered as {test_id})")
                    return True

            return False
        except Exception as e:
            print(f"  Test registration failed: {e}")
            return False

    def ensure_broker_running(self) -> bool:
        """브로커가 실행 중인지 확인하고 필요시 시작"""
        print("🔍 Checking broker status...")

        # 1. 실제 연결 테스트 (가장 신뢰할 수 있는 방법)
        if self.test_broker_connection():
            print("✅ Broker is already running and responding")
            # 추가 확인: 실제 등록 테스트
            if self.test_broker_with_registration():
                return True
            else:
                print("  ⚠️ Broker responds but registration failed. Restarting...")

        # 2. 락 파일 확인
        locked_pid = self.get_locked_pid()
        if locked_pid:
            print(f"  Found lock file with PID: {locked_pid}")
            if self.is_process_running(locked_pid):
                # 프로세스는 있지만 응답하지 않음 - 재시작 필요
                print(f"  ⚠️ Broker process {locked_pid} exists but not responding. Restarting...")
                if sys.platform == 'win32':
                    subprocess.run(f'taskkill /F /PID {locked_pid}', shell=True, capture_output=True)
                else:
                    try:
                        os.kill(locked_pid, 9)
                    except OSError:
                        pass
                time.sleep(2)
            else:
                print(f"  Lock file contains stale PID {locked_pid}")

        # 락 파일 삭제
        if self.lock_file.exists():
            self.lock_file.unlink()

        # 3. 브로커 시작
        return self.start_broker()


def main():
    manager = BrokerManager()

    # 여러 번 시도
    for attempt in range(3):
        if manager.ensure_broker_running():
            sys.exit(0)

        if attempt < 2:
            print(f"\n🔄 Retrying... (attempt {attempt + 2}/3)")
            time.sleep(2)

    print("\n❌ Failed to start broker after 3 attempts")
    sys.exit(1)


if __name__ == "__main__":
    main()