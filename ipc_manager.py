#!/usr/bin/env python3
"""
IPC Manager - 시작, 종료, 상태 관리
"""
import os
import sys
import signal
import atexit
import subprocess
import psutil
from pathlib import Path
import time

class IPCManager:
    def __init__(self):
        self.processes = []
        self.running = True

        # 종료 핸들러 등록
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """시그널 핸들러 - Ctrl+C 또는 터미널 종료 시"""
        print("\n[IPC Manager] Received shutdown signal...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """모든 IPC 프로세스 정리"""
        print("[IPC Manager] Cleaning up all IPC processes...")

        # 관리 중인 프로세스 종료
        for proc in self.processes:
            try:
                if proc.poll() is None:  # 프로세스가 실행 중이면
                    proc.terminate()
                    proc.wait(timeout=2)
            except:
                try:
                    proc.kill()  # 강제 종료
                except:
                    pass

        # psutil로 Python 프로세스 확인 및 종료
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in ['python.exe', 'pythonw.exe']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(x in cmdline for x in ['ipc', 'monitor', 'responder', 'broker']):
                        print(f"  Terminating: {proc.info['pid']} - {cmdline[:50]}...")
                        proc.terminate()
                        proc.wait(timeout=2)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass

        # 세션 파일 정리
        session_file = Path.home() / '.ipc-session'
        if session_file.exists():
            session_file.unlink()
            print("  Session file removed")

        print("[IPC Manager] All processes cleaned up!")

    def start_integrated(self):
        """통합 시스템 시작"""
        print("[IPC Manager] Starting integrated system...")

        # 기존 프로세스 정리
        self.cleanup()
        time.sleep(2)

        # 통합 시스템 시작
        proc = subprocess.Popen(
            [sys.executable, 'start_integrated_system.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self.processes.append(proc)

        # 모니터 시작
        proc = subprocess.Popen(
            [sys.executable, 'enhanced_monitor.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self.processes.append(proc)

        print("[IPC Manager] System started! Press Ctrl+C to stop.")

    def start_manual(self):
        """수동 모드 시작"""
        print("[IPC Manager] Starting manual mode...")

        # 기존 프로세스 정리
        self.cleanup()
        time.sleep(2)

        # 브로커만 시작
        proc = subprocess.Popen(
            [sys.executable, 'src/claude_ipc_server.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self.processes.append(proc)

        # 모니터만 시작
        proc = subprocess.Popen(
            [sys.executable, 'enhanced_monitor.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self.processes.append(proc)

        print("[IPC Manager] Manual mode started!")
        print("Register instances manually in separate terminals:")
        print("  python tools/ipc_register.py [instance_name]")
        print("\nPress Ctrl+C to stop.")

    def wait(self):
        """프로세스가 실행되는 동안 대기"""
        try:
            while self.running:
                time.sleep(1)
                # 프로세스 상태 체크
                alive = sum(1 for p in self.processes if p.poll() is None)
                if alive == 0:
                    print("[IPC Manager] All processes have stopped.")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='IPC System Manager')
    parser.add_argument('mode', choices=['integrated', 'manual', 'stop'],
                       help='Operation mode')
    parser.add_argument('--clear-db', action='store_true',
                       help='Clear database before starting')

    args = parser.parse_args()

    manager = IPCManager()

    if args.mode == 'stop':
        manager.cleanup()
    elif args.mode == 'integrated':
        if args.clear_db:
            print("Clearing database...")
            import sqlite3
            db_path = Path.home() / '.claude-ipc-data' / 'messages.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for table in ['messages', 'instances', 'sessions', 'name_history']:
                cursor.execute(f'DELETE FROM {table}')
            conn.commit()
            conn.close()
            print("Database cleared!")
        manager.start_integrated()
        manager.wait()
    elif args.mode == 'manual':
        manager.start_manual()
        manager.wait()

if __name__ == '__main__':
    # psutil 설치 확인
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
        import psutil

    main()