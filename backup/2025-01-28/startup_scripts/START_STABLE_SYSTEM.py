#!/usr/bin/env python3
"""
안정적인 IPC 시스템 시작 스크립트
- 완전 정리 후 시작
- 안정적인 자동 응답
- 세션 관리 및 프로세스 추적
"""

import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path
import threading
import atexit

class StableIPCSystem:
    def __init__(self):
        self.processes = []
        self.server_process = None
        self.responder_processes = {}
        self.monitor_process = None

        # 인스턴스 목록
        self.instances = ['gemini', 'codex', 'lm', 'chatgpt', 'llama', 'claude']

        # 종료 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup_all)

        print("\n" + "="*60)
        print(" 안정적인 IPC 시스템 시작")
        print("="*60)

    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print("\n\n종료 시그널 받음...")
        self.cleanup_all()
        sys.exit(0)

    def cleanup_all(self):
        """모든 프로세스 정리"""
        print("\n정리 작업 시작...")

        # 자동 응답기 종료
        for name, proc in self.responder_processes.items():
            try:
                print(f"  {name} 자동 응답기 종료...")
                proc.terminate()
                time.sleep(0.5)
                if proc.poll() is None:
                    proc.kill()
            except:
                pass

        # 모니터 종료
        if self.monitor_process and self.monitor_process.poll() is None:
            try:
                print("  모니터 종료...")
                self.monitor_process.terminate()
            except:
                pass

        # 서버 종료
        if self.server_process and self.server_process.poll() is None:
            try:
                print("  IPC 서버 종료...")
                self.server_process.terminate()
            except:
                pass

        # 모든 프로세스 종료
        for proc in self.processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    time.sleep(0.5)
                    if proc.poll() is None:
                        proc.kill()
            except:
                pass

        print("정리 완료!\n")

    def run_cleanup(self):
        """시스템 정리"""
        print("\n1단계: 시스템 정리")
        print("-" * 40)

        # 정리 스크립트 실행
        try:
            result = subprocess.run(
                ['python', 'COMPLETE_CLEANUP.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if "정리 완료!" in result.stdout:
                print("✅ 시스템 정리 완료")
            else:
                print("⚠️ 정리 부분 완료")

            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ 정리 실패: {e}")
            return False

    def start_server(self):
        """IPC 서버 시작 - 싱글톤 브로커 사용"""
        print("\n2단계: IPC 서버 시작 (싱글톤 브로커)")
        print("-" * 40)

        try:
            # 싱글톤 브로커 시작 스크립트 사용
            result = subprocess.run(
                ['python', 'tools/start_broker.py'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("✅ 싱글톤 브로커 시작/확인 완료")

                # 연결 확인
                import socket
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect(('localhost', 9876))
                    sock.close()
                    print("✅ IPC 서버 실행 중 (포트 9876)")
                    return True
                except:
                    print("❌ 서버 연결 실패")
                    return False
            else:
                print("❌ 싱글톤 브로커 시작 실패")
                if result.stderr:
                    print(f"  오류: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ 브로커 시작 시간 초과")
            return False
        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
            return False

    def register_instances(self):
        """인스턴스 등록"""
        print("\n3단계: 인스턴스 등록")
        print("-" * 40)

        registered = []

        for instance in self.instances:
            try:
                result = subprocess.run(
                    ['python', 'tools/ipc_register.py', instance],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if 'registered as' in result.stdout.lower() or 'success' in result.stdout.lower() or '성공' in result.stdout:
                    print(f"✅ {instance} 등록 성공")
                    registered.append(instance)
                else:
                    print(f"⚠️ {instance} 등록 실패")

                time.sleep(0.5)

            except Exception as e:
                print(f"❌ {instance} 등록 오류: {e}")

        print(f"\n  총 {len(registered)}/{len(self.instances)} 인스턴스 등록됨")
        return registered

    def start_auto_responders(self, instances):
        """자동 응답기 시작"""
        print("\n4단계: 자동 응답기 시작")
        print("-" * 40)

        # claude는 자동 응답기에서 제외
        responder_instances = [i for i in instances if i != 'claude']

        for instance in responder_instances:
            try:
                # 안정적인 자동 응답기 사용
                proc = subprocess.Popen(
                    ['python', 'STABLE_AUTO_RESPONDER.py', instance],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                self.responder_processes[instance] = proc
                self.processes.append(proc)

                print(f"✅ {instance} 자동 응답기 시작")
                time.sleep(1)

            except Exception as e:
                print(f"❌ {instance} 자동 응답기 시작 실패: {e}")

        print(f"\n  총 {len(self.responder_processes)} 자동 응답기 실행 중")

    def test_communication(self):
        """통신 테스트"""
        print("\n5단계: 통신 테스트")
        print("-" * 40)

        try:
            # 테스트 메시지 전송
            result = subprocess.run(
                ['python', 'tools/ipc_send.py', 'claude', 'gemini',
                 '안녕하세요! 시스템 테스트 메시지입니다.'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if 'success' in result.stdout.lower() or '성공' in result.stdout:
                print("✅ 메시지 전송 성공")

                # 응답 대기
                time.sleep(3)

                # 메시지 확인
                result = subprocess.run(
                    ['python', 'tools/ipc_check.py', 'claude'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if 'gemini' in result.stdout.lower():
                    print("✅ 응답 수신 성공")
                    return True
                else:
                    print("⚠️ 응답 대기 중...")
                    return True

            else:
                print("❌ 메시지 전송 실패")
                return False

        except Exception as e:
            print(f"❌ 통신 테스트 실패: {e}")
            return False

    def start_monitor(self):
        """모니터 시작"""
        print("\n6단계: 모니터 시작")
        print("-" * 40)

        try:
            # 모니터 스크립트 확인
            if Path('enhanced_monitor.py').exists():
                monitor_script = 'enhanced_monitor.py'
            elif Path('start_safe_4panel_monitor.py').exists():
                monitor_script = 'start_safe_4panel_monitor.py'
            else:
                print("⚠️ 모니터 스크립트 없음")
                return False

            self.monitor_process = subprocess.Popen(
                ['python', monitor_script]
            )
            self.processes.append(self.monitor_process)

            print(f"✅ 모니터 시작: {monitor_script}")
            return True

        except Exception as e:
            print(f"❌ 모니터 시작 실패: {e}")
            return False

    def show_status(self):
        """상태 표시"""
        print("\n" + "="*60)
        print(" 시스템 상태")
        print("="*60)

        # 프로세스 상태
        print("\n실행 중인 프로세스:")
        if self.server_process and self.server_process.poll() is None:
            print("  ✅ IPC 서버")
        else:
            print("  ❌ IPC 서버")

        for name, proc in self.responder_processes.items():
            if proc.poll() is None:
                print(f"  ✅ {name} 자동 응답기")
            else:
                print(f"  ❌ {name} 자동 응답기")

        if self.monitor_process and self.monitor_process.poll() is None:
            print("  ✅ 모니터")
        else:
            print("  ❌ 모니터")

        print("\n사용 가능한 명령:")
        print("  python tools/ipc_send.py <from> <to> <message>")
        print("  python tools/ipc_check.py <instance>")
        print("  python tools/ipc_list.py")
        print("  python check_ai_messages.py")

        print("\n종료하려면 Ctrl+C를 누르세요.")

    def run(self):
        """메인 실행"""
        try:
            # 1. 시스템 정리
            if not self.run_cleanup():
                print("\n⚠️ 정리 실패했지만 계속 진행합니다.")

            # 2. 서버 시작
            if not self.start_server():
                print("\n❌ 서버 시작 실패. 종료합니다.")
                return

            # 3. 인스턴스 등록
            registered = self.register_instances()
            if not registered:
                print("\n❌ 인스턴스 등록 실패. 종료합니다.")
                self.cleanup_all()
                return

            # 4. 자동 응답기 시작
            self.start_auto_responders(registered)

            # 5. 통신 테스트
            self.test_communication()

            # 6. 모니터 시작
            self.start_monitor()

            # 7. 상태 표시
            self.show_status()

            # 8. 대기
            print("\n시스템 실행 중...")
            print("="*60)

            while True:
                time.sleep(60)

                # 프로세스 상태 확인
                dead_count = 0
                for name, proc in self.responder_processes.items():
                    if proc.poll() is not None:
                        dead_count += 1

                if dead_count > len(self.responder_processes) // 2:
                    print(f"\n⚠️ {dead_count}개 자동 응답기 중단됨. 재시작 필요.")

        except KeyboardInterrupt:
            print("\n\n사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n\n오류 발생: {e}")
        finally:
            self.cleanup_all()


if __name__ == "__main__":
    system = StableIPCSystem()
    system.run()