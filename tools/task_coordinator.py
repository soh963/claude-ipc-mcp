#!/usr/bin/env python3
"""
Task Coordinator - 실시간 작업 진행상황 추적 및 AI 간 조율
"""

import json
import time
import asyncio
import socket
from datetime import datetime
from typing import Optional

class TaskCoordinator:
    """AI 인스턴스 간 작업 조율 및 진행상황 추적"""

    def __init__(self, instance_id: str = "task_coordinator"):
        self.instance_id = instance_id
        self.tasks = {}
        self.active_instances = ['claude', 'gemini', 'codex']
        self.update_interval = 60  # 1분마다 체크
        self.broker_port = 9876

    def send_message(self, to_instance: str, message: dict) -> bool:
        """다른 AI 인스턴스에 메시지 전송"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(('localhost', self.broker_port))

                request = {
                    'type': 'send',
                    'from_id': self.instance_id,
                    'to_id': to_instance,
                    'content': json.dumps(message, ensure_ascii=False)
                }

                sock.send(json.dumps(request).encode('utf-8'))
                response = sock.recv(8192).decode('utf-8')

                result = json.loads(response)
                return result.get('status') == 'ok'

        except Exception as e:
            print(f"Error sending message to {to_instance}: {e}")
            return False

    def assign_task(self, instance: str, task_id: str, task_data: dict):
        """특정 AI 인스턴스에 작업 할당"""
        message = {
            'type': 'TASK_ASSIGNMENT',
            'task_id': task_id,
            'action': 'START',
            'data': task_data,
            'timestamp': datetime.now().isoformat()
        }

        if self.send_message(instance, message):
            print(f"✅ Task {task_id} assigned to {instance}")
            self.tasks[task_id] = {
                'assigned_to': instance,
                'status': 'ASSIGNED',
                'started_at': datetime.now().isoformat()
            }
        else:
            print(f"❌ Failed to assign task {task_id} to {instance}")

    def broadcast_progress(self, task_id: str, progress: dict):
        """모든 인스턴스에 진행상황 브로드캐스트"""
        message = {
            'type': 'PROGRESS_UPDATE',
            'task_id': task_id,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }

        for instance in self.active_instances:
            if instance != self.instance_id:
                self.send_message(instance, message)

    def check_instance_status(self, instance: str) -> Optional[dict]:
        """특정 인스턴스의 상태 체크"""
        message = {
            'type': 'STATUS_CHECK',
            'request_id': f"status_{int(time.time())}",
            'timestamp': datetime.now().isoformat()
        }

        if self.send_message(instance, message):
            # 실제로는 응답을 기다려야 하지만, 간단히 구현
            return {'instance': instance, 'status': 'ACTIVE'}
        return None

    async def monitor_tasks(self):
        """작업 진행상황 모니터링 (비동기)"""
        while True:
            print(f"\n📊 Task Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)

            for task_id, task_info in self.tasks.items():
                instance = task_info['assigned_to']
                status = self.check_instance_status(instance)

                if status:
                    print(f"Task {task_id}: {instance} - {task_info['status']}")
                else:
                    print(f"Task {task_id}: {instance} - OFFLINE")

            await asyncio.sleep(self.update_interval)

    def initialize_tasks(self):
        """PROJECT_TASKS_v2.md에서 작업 초기화"""

        # Phase 1 작업 할당
        self.assign_task('claude', 'P1', {
            'name': '파일 시스템 정리',
            'priority': 'URGENT',
            'deadline': '2025-09-28T23:00:00',
            'tasks': [
                'backup/ 디렉토리를 archive_2025-09-28.zip으로 압축',
                '압축 완료 후 backup/ 폴더 삭제',
                '중복 시작 스크립트 제거',
                '루트의 *.md 파일을 docs/로 이동'
            ]
        })

        # Gemini 작업
        self.assign_task('gemini', 'P2-1', {
            'name': '보안 모듈 분리',
            'priority': 'HIGH',
            'deadline': '2025-09-29T18:00:00',
            'dependencies': ['P1'],
            'tasks': [
                'claude_ipc_server.py에서 보안 관련 코드 추출',
                'src/security/auth.py로 세션 관리 이동',
                'src/security/rate_limiter.py로 속도 제한 분리'
            ]
        })

        self.assign_task('gemini', 'F1-1', {
            'name': 'AI 간 표준 프로토콜 설계',
            'priority': 'HIGH',
            'deadline': '2025-09-30T18:00:00',
            'tasks': [
                'capabilities discovery 엔드포인트 설계',
                '표준 명령어 세트 정의',
                '프로토콜 버전 관리 전략 수립'
            ]
        })

        # Codex 작업
        self.assign_task('codex', 'P2-2', {
            'name': 'DB 모듈 분리',
            'priority': 'HIGH',
            'deadline': '2025-09-29T18:00:00',
            'dependencies': ['P1'],
            'tasks': [
                '데이터베이스 코드를 src/db/database.py로 추출',
                '비동기 처리 로직 최적화',
                '커넥션 풀링 구현'
            ]
        })

        self.assign_task('codex', 'F2', {
            'name': '단일 진입점 시스템',
            'priority': 'HIGH',
            'deadline': '2025-09-30T18:00:00',
            'dependencies': ['P1'],
            'tasks': [
                'run.py 통합 시작 스크립트 생성',
                '모든 시작 로직 통합',
                'argparse로 옵션 처리'
            ]
        })

        print("\n✅ All initial tasks have been assigned!")

    def send_notification(self):
        """Gemini와 Codex에게 작업 시작 알림"""

        # Gemini에게 알림
        gemini_msg = """
📋 PROJECT_TASKS_v2.md 작업이 시작되었습니다!

담당 작업:
1. P2-1: 보안 모듈 분리 (우선순위: 높음)
   - claude_ipc_server.py에서 보안 코드 추출
   - src/security/ 디렉토리 구조 생성

2. F1-1: AI 간 표준 프로토콜 설계
   - capabilities discovery 설계
   - 표준 명령어 정의

작업 문서: D:\\claude-ipc-mcp\\PROJECT_TASKS_v2.md
상태 업데이트: 1시간마다 보고 부탁드립니다.
        """

        # Codex에게 알림
        codex_msg = """
📋 PROJECT_TASKS_v2.md 작업이 시작되었습니다!

담당 작업:
1. P2-2: DB 모듈 분리 (우선순위: 높음)
   - 데이터베이스 코드 추출
   - 비동기 처리 최적화

2. F2: 단일 진입점 시스템 구현
   - run.py 생성
   - 통합 시작 로직

작업 문서: D:\\claude-ipc-mcp\\PROJECT_TASKS_v2.md
상태 업데이트: 1시간마다 보고 부탁드립니다.
        """

        self.send_message('gemini', {'type': 'TEXT', 'content': gemini_msg})
        self.send_message('codex', {'type': 'TEXT', 'content': codex_msg})

        print("\n📨 Notifications sent to Gemini and Codex!")


async def main():
    """메인 실행 함수"""
    coordinator = TaskCoordinator('claude_coordinator')

    # 초기 작업 할당
    coordinator.initialize_tasks()

    # 알림 전송
    coordinator.send_notification()

    # 모니터링 시작
    try:
        await coordinator.monitor_tasks()
    except KeyboardInterrupt:
        print("\n👋 Task coordinator stopped.")


if __name__ == "__main__":
    print("🚀 Starting Task Coordinator...")
    print("=" * 60)
    asyncio.run(main())