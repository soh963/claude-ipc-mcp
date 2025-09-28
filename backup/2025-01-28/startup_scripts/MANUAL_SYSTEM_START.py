#!/usr/bin/env python3
"""
수동 등록 가능한 IPC 시스템 시작 스크립트
- 수동 인스턴스 등록 지원
- 대화형 메뉴 시스템
- 안정적인 프로세스 관리
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
import socket
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta

class ManualIPCSystem:
    def __init__(self):
        self.server_process = None
        self.responder_processes = {}
        self.monitor_process = None
        self.registered_instances = []

        # 기본 인스턴스 목록
        self.default_instances = ['claude', 'gemini', 'codex', 'lm', 'chatgpt', 'llama']

        # 데이터베이스 경로
        self.db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

        # 종료 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup_all)

        print("\n" + "="*60)
        print(" 수동 등록 가능한 IPC 시스템")
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

        print("정리 완료!\n")

    def check_port(self):
        """포트 9876 확인"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 9876))
            sock.close()
            return result == 0
        except:
            return False

    def start_server(self):
        """IPC 서버 시작"""
        print("\n▶ IPC 서버 시작 중...")

        # 이미 실행 중인지 확인
        if self.check_port():
            print("  ✅ 서버가 이미 실행 중입니다 (포트 9876)")
            return True

        try:
            # MCP 서버 시작
            self.server_process = subprocess.Popen(
                ['python', 'src/claude_ipc_server.py'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            print("  서버 시작 대기 중...")

            # 서버 시작 확인 (최대 10초 대기)
            for i in range(10):
                time.sleep(1)
                if self.check_port():
                    print("  ✅ IPC 서버 실행 중 (포트 9876)")
                    return True
                print(f"  대기 중... {i+1}/10")

            print("  ❌ 서버 시작 시간 초과")
            return False

        except Exception as e:
            print(f"  ❌ 서버 시작 실패: {e}")
            return False

    def register_instance(self, instance_id):
        """개별 인스턴스 등록"""
        try:
            result = subprocess.run(
                ['python', 'tools/ipc_register.py', instance_id],
                capture_output=True,
                text=True,
                timeout=5
            )

            if 'registered' in result.stdout.lower() or 'success' in result.stdout.lower():
                print(f"  ✅ {instance_id} 등록 성공")
                if instance_id not in self.registered_instances:
                    self.registered_instances.append(instance_id)
                return True
            else:
                print(f"  ❌ {instance_id} 등록 실패")
                if result.stderr:
                    print(f"     오류: {result.stderr[:100]}")
                return False

        except subprocess.TimeoutExpired:
            print(f"  ⏱️ {instance_id} 등록 시간 초과")
            return False
        except Exception as e:
            print(f"  ❌ {instance_id} 등록 오류: {e}")
            return False

    def manual_register(self):
        """수동 인스턴스 등록"""
        print("\n▶ 수동 인스턴스 등록")
        print("-" * 40)

        while True:
            print("\n1. 기본 인스턴스 전체 등록")
            print("2. 개별 인스턴스 등록")
            print("3. 사용자 정의 인스턴스 등록")
            print("4. 등록된 인스턴스 목록 보기")
            print("5. 📝 직접 DB 등록 (브로커 우회)")
            print("0. 메인 메뉴로 돌아가기")

            choice = input("\n선택: ").strip()

            if choice == '1':
                # 기본 인스턴스 전체 등록
                for instance in self.default_instances:
                    self.register_instance(instance)
                    time.sleep(0.5)

            elif choice == '2':
                # 개별 선택 등록
                print("\n등록할 인스턴스 선택:")
                for i, instance in enumerate(self.default_instances, 1):
                    status = "✅" if instance in self.registered_instances else "❌"
                    print(f"{i}. {instance} {status}")

                idx = input("\n번호 입력 (0=취소): ").strip()
                if idx.isdigit() and 1 <= int(idx) <= len(self.default_instances):
                    instance = self.default_instances[int(idx)-1]
                    self.register_instance(instance)

            elif choice == '3':
                # 사용자 정의 인스턴스
                custom_name = input("인스턴스 이름 입력: ").strip()
                if custom_name:
                    self.register_instance(custom_name)

            elif choice == '4':
                # 등록된 인스턴스 목록
                if self.registered_instances:
                    print("\n등록된 인스턴스:")
                    for instance in self.registered_instances:
                        print(f"  • {instance}")
                else:
                    print("\n등록된 인스턴스가 없습니다.")

            elif choice == '5':
                # 직접 DB 등록
                self.direct_db_register()

            elif choice == '0':
                break

    def start_auto_responders(self):
        """자동 응답기 시작"""
        print("\n▶ 자동 응답기 시작")
        print("-" * 40)

        if not self.registered_instances:
            print("  등록된 인스턴스가 없습니다. 먼저 등록하세요.")
            return

        # claude는 자동 응답기에서 제외
        responder_instances = [i for i in self.registered_instances if i != 'claude']

        if not responder_instances:
            print("  자동 응답 가능한 인스턴스가 없습니다.")
            return

        print("\n시작할 자동 응답기 선택:")
        print("1. 전체 시작")
        print("2. 개별 선택")
        print("0. 취소")

        choice = input("\n선택: ").strip()

        if choice == '1':
            # 전체 시작
            for instance in responder_instances:
                self.start_responder(instance)
                time.sleep(1)

        elif choice == '2':
            # 개별 선택
            for i, instance in enumerate(responder_instances, 1):
                status = "🟢" if instance in self.responder_processes else "⭕"
                print(f"{i}. {instance} {status}")

            idx = input("\n번호 입력: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(responder_instances):
                instance = responder_instances[int(idx)-1]
                self.start_responder(instance)

    def start_responder(self, instance):
        """개별 자동 응답기 시작"""
        # 이미 실행 중인지 확인
        if instance in self.responder_processes:
            if self.responder_processes[instance].poll() is None:
                print(f"  ⚠️ {instance} 자동 응답기가 이미 실행 중입니다")
                return

        try:
            # simple_auto_responder.py 사용
            proc = subprocess.Popen(
                ['python', 'tools/simple_auto_responder.py', instance],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.responder_processes[instance] = proc
            print(f"  ✅ {instance} 자동 응답기 시작")

        except Exception as e:
            print(f"  ❌ {instance} 자동 응답기 시작 실패: {e}")

    def test_communication(self):
        """통신 테스트"""
        print("\n▶ 통신 테스트")
        print("-" * 40)

        if not self.registered_instances:
            print("  등록된 인스턴스가 없습니다.")
            return

        print("\n1. 메시지 전송 테스트")
        print("2. 메시지 확인")
        print("3. 인스턴스 목록 확인")
        print("0. 메인 메뉴로")

        choice = input("\n선택: ").strip()

        if choice == '1':
            # 메시지 전송
            print("\n발신자 인스턴스:")
            for i, instance in enumerate(self.registered_instances, 1):
                print(f"{i}. {instance}")

            from_idx = input("발신자 번호: ").strip()
            if not from_idx.isdigit():
                return

            from_id = self.registered_instances[int(from_idx)-1]

            print("\n수신자 인스턴스:")
            for i, instance in enumerate(self.registered_instances, 1):
                print(f"{i}. {instance}")

            to_idx = input("수신자 번호: ").strip()
            if not to_idx.isdigit():
                return

            to_id = self.registered_instances[int(to_idx)-1]

            message = input("메시지 내용: ").strip()

            if message:
                try:
                    result = subprocess.run(
                        ['python', 'tools/ipc_send.py', from_id, to_id, message],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if 'sent' in result.stdout.lower() or 'success' in result.stdout.lower():
                        print(f"  ✅ 메시지 전송 성공")
                    else:
                        print(f"  ❌ 메시지 전송 실패")

                except Exception as e:
                    print(f"  ❌ 오류: {e}")

        elif choice == '2':
            # 메시지 확인
            print("\n확인할 인스턴스:")
            for i, instance in enumerate(self.registered_instances, 1):
                print(f"{i}. {instance}")

            idx = input("번호: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(self.registered_instances):
                instance = self.registered_instances[int(idx)-1]

                try:
                    result = subprocess.run(
                        ['python', 'tools/ipc_check.py', instance],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    print(result.stdout)

                except Exception as e:
                    print(f"  ❌ 오류: {e}")

        elif choice == '3':
            # 인스턴스 목록
            try:
                result = subprocess.run(
                    ['python', 'tools/ipc_list.py'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                print(result.stdout)

            except Exception as e:
                print(f"  ❌ 오류: {e}")

    def start_monitor(self):
        """모니터 시작"""
        print("\n▶ 모니터 시작")

        # 이미 실행 중인지 확인
        if self.monitor_process and self.monitor_process.poll() is None:
            print("  ⚠️ 모니터가 이미 실행 중입니다")
            return

        try:
            # 모니터 스크립트 확인
            if Path('enhanced_monitor.py').exists():
                monitor_script = 'enhanced_monitor.py'
            elif Path('start_safe_4panel_monitor.py').exists():
                monitor_script = 'start_safe_4panel_monitor.py'
            else:
                print("  ❌ 모니터 스크립트를 찾을 수 없습니다")
                return

            self.monitor_process = subprocess.Popen(
                ['python', monitor_script]
            )

            print(f"  ✅ 모니터 시작: {monitor_script}")

        except Exception as e:
            print(f"  ❌ 모니터 시작 실패: {e}")

    def direct_db_register(self):
        """직접 DB에 인스턴스 등록 (브로커 우회)"""
        print("\n▶ 직접 데이터베이스 등록")
        print("  브로커를 우회하여 직접 DB에 등록합니다.")
        print("-" * 40)

        if not self.db_path.exists():
            print("❌ 데이터베이스 파일이 없습니다.")
            print(f"   경로: {self.db_path}")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            print("\n등록할 인스턴스:")
            for i, instance in enumerate(self.default_instances, 1):
                print(f"  {i}. {instance}")

            print("\n1. 전체 등록")
            print("2. 선택 등록")
            print("0. 취소")

            choice = input("\n선택: ").strip()

            if choice == '1':
                instances_to_register = self.default_instances
            elif choice == '2':
                selected = input("등록할 인스턴스 번호들 (쉼표로 구분): ").strip()
                if not selected:
                    return
                indices = [int(x.strip()) - 1 for x in selected.split(',')]
                instances_to_register = [self.default_instances[i] for i in indices if 0 <= i < len(self.default_instances)]
            elif choice == '0':
                return
            else:
                print("❌ 잘못된 선택")
                return

            registered = []
            for instance_id in instances_to_register:
                try:
                    # 세션 토큰 생성
                    session_token = str(uuid.uuid4())
                    token_hash = hashlib.sha256(session_token.encode()).hexdigest()

                    # 인스턴스 등록
                    cursor.execute("""
                        INSERT OR REPLACE INTO instances (instance_id, last_seen)
                        VALUES (?, datetime('now'))
                    """, (instance_id,))

                    # 세션 등록
                    expires_at = datetime.now() + timedelta(hours=24)
                    cursor.execute("""
                        INSERT OR REPLACE INTO sessions (instance_id, token_hash, expires_at)
                        VALUES (?, ?, ?)
                    """, (instance_id, token_hash, expires_at.isoformat()))

                    conn.commit()
                    print(f"✅ {instance_id} 직접 등록 성공")
                    registered.append(instance_id)

                    if instance_id not in self.registered_instances:
                        self.registered_instances.append(instance_id)

                    # 세션 정보 저장 (선택적)
                    session_file = Path.home() / f'.ipc-session-{instance_id}'
                    with open(session_file, 'w') as f:
                        json.dump({
                            'instance_id': instance_id,
                            'token': session_token,
                            'timestamp': time.time()
                        }, f)

                except Exception as e:
                    print(f"❌ {instance_id} 등록 실패: {e}")

            print(f"\n✅ 총 {len(registered)}/{len(instances_to_register)} 인스턴스 직접 등록됨")
            print("   등록된 인스턴스:", ', '.join(registered))

            conn.close()

        except Exception as e:
            print(f"❌ 데이터베이스 오류: {e}")

        input("\n엔터를 눌러 계속...")

    def show_status(self):
        """시스템 상태 표시"""
        print("\n" + "="*60)
        print(" 시스템 상태")
        print("="*60)

        # 서버 상태
        if self.check_port():
            print("\n✅ IPC 서버: 실행 중 (포트 9876)")
        else:
            print("\n❌ IPC 서버: 중지됨")

        # 등록된 인스턴스
        if self.registered_instances:
            print(f"\n등록된 인스턴스 ({len(self.registered_instances)}개):")
            for instance in self.registered_instances:
                print(f"  • {instance}")
        else:
            print("\n등록된 인스턴스가 없습니다.")

        # 자동 응답기 상태
        if self.responder_processes:
            print(f"\n자동 응답기 ({len(self.responder_processes)}개):")
            for name, proc in self.responder_processes.items():
                if proc.poll() is None:
                    print(f"  ✅ {name}")
                else:
                    print(f"  ❌ {name} (중지됨)")
        else:
            print("\n실행 중인 자동 응답기가 없습니다.")

        # 모니터 상태
        if self.monitor_process and self.monitor_process.poll() is None:
            print("\n✅ 모니터: 실행 중")
        else:
            print("\n❌ 모니터: 중지됨")

        # DB 상태 확인
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
                unread = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM messages")
                total = cursor.fetchone()[0]

                print(f"\n📬 메시지: 총 {total}개 (읽지 않음: {unread}개)")

                conn.close()
            else:
                print("\n⚠️ 데이터베이스 파일 없음")
        except Exception as e:
            print(f"\n⚠️ DB 상태 확인 실패: {e}")

    def main_menu(self):
        """메인 메뉴"""
        while True:
            print("\n" + "="*60)
            print(" 메인 메뉴")
            print("="*60)
            print("1. IPC 서버 시작")
            print("2. 인스턴스 등록 (수동)")
            print("3. 자동 응답기 시작")
            print("4. 통신 테스트")
            print("5. 모니터 시작")
            print("6. 시스템 상태 보기")
            print("7. 시스템 정리 및 재시작")
            print("0. 종료")

            choice = input("\n선택: ").strip()

            if choice == '1':
                self.start_server()
            elif choice == '2':
                self.manual_register()
            elif choice == '3':
                self.start_auto_responders()
            elif choice == '4':
                self.test_communication()
            elif choice == '5':
                self.start_monitor()
            elif choice == '6':
                self.show_status()
            elif choice == '7':
                # 정리 및 재시작
                print("\n시스템을 정리하고 재시작합니다...")
                self.cleanup_all()
                time.sleep(2)
                self.registered_instances = []
                self.responder_processes = {}
                print("\n정리 완료. 서버를 다시 시작하세요.")
            elif choice == '0':
                print("\n시스템을 종료합니다...")
                self.cleanup_all()
                break
            else:
                print("\n잘못된 선택입니다.")

    def run(self):
        """실행"""
        try:
            # 자동으로 서버 시작 시도
            if not self.check_port():
                print("\nIPC 서버가 실행되지 않았습니다.")
                print("서버를 시작하시겠습니까? (y/n): ", end='')
                if input().lower() == 'y':
                    self.start_server()
            else:
                print("\nIPC 서버가 이미 실행 중입니다.")

            # 메인 메뉴 실행
            self.main_menu()

        except KeyboardInterrupt:
            print("\n\n사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n\n오류 발생: {e}")
        finally:
            self.cleanup_all()


if __name__ == "__main__":
    system = ManualIPCSystem()
    system.run()