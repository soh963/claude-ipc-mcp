#!/usr/bin/env python3
"""
직접 데이터베이스 등록 스크립트
브로커 연결 실패 시 사용하는 백업 등록 방법
"""

import sqlite3
import hashlib
import uuid
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

def direct_register_instance(instance_id, db_path=None):
    """
    데이터베이스에 직접 인스턴스 등록

    Args:
        instance_id: 등록할 인스턴스 ID
        db_path: 데이터베이스 경로 (기본값: ~/.claude-ipc-data/messages.db)

    Returns:
        tuple: (성공 여부, 세션 토큰 또는 에러 메시지)
    """
    if not db_path:
        db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if not db_path.exists():
        return False, f"데이터베이스 파일이 없습니다: {db_path}"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 세션 토큰 생성
        session_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()

        # 인스턴스 등록 또는 업데이트
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
        conn.close()

        # 세션 파일 저장 (선택적)
        session_file = Path.home() / f'.ipc-session-{instance_id}'
        with open(session_file, 'w') as f:
            json.dump({
                'instance_id': instance_id,
                'token': session_token,
                'timestamp': datetime.now().timestamp()
            }, f)

        return True, session_token

    except Exception as e:
        return False, str(e)

def main():
    """메인 함수"""
    print("\n" + "="*60)
    print(" 직접 데이터베이스 등록 도구")
    print(" (브로커 연결 실패 시 사용)")
    print("="*60)

    # 기본 인스턴스 목록
    default_instances = ['claude', 'gemini', 'codex', 'lm', 'chatgpt', 'llama']

    if len(sys.argv) > 1:
        # 명령줄 인자로 인스턴스 지정
        instances_to_register = sys.argv[1:]
    else:
        # 대화형 모드
        print("\n등록할 인스턴스를 선택하세요:")
        print("1. 전체 기본 인스턴스")
        for i, inst in enumerate(default_instances, 2):
            print(f"{i}. {inst}")
        print(f"{len(default_instances)+2}. 사용자 정의")

        choice = input("\n선택 (번호 또는 인스턴스 이름): ").strip()

        if choice == '1':
            instances_to_register = default_instances
        elif choice.isdigit() and 2 <= int(choice) <= len(default_instances)+1:
            instances_to_register = [default_instances[int(choice)-2]]
        elif choice == str(len(default_instances)+2):
            custom = input("인스턴스 이름 입력: ").strip()
            if custom:
                instances_to_register = [custom]
            else:
                print("❌ 이름이 비어있습니다.")
                return
        elif choice:
            # 직접 이름 입력
            instances_to_register = [choice]
        else:
            print("❌ 잘못된 입력")
            return

    # 등록 수행
    print("\n등록 중...")
    print("-" * 40)

    successful = []
    failed = []

    for instance_id in instances_to_register:
        success, result = direct_register_instance(instance_id)

        if success:
            print(f"✅ {instance_id}: 등록 성공")
            print(f"   세션 토큰: {result[:8]}...")
            successful.append(instance_id)
        else:
            print(f"❌ {instance_id}: 등록 실패 - {result}")
            failed.append(instance_id)

    # 결과 요약
    print("\n" + "="*60)
    print(" 등록 결과")
    print("="*60)
    print(f"✅ 성공: {len(successful)}개 - {', '.join(successful) if successful else '없음'}")
    print(f"❌ 실패: {len(failed)}개 - {', '.join(failed) if failed else '없음'}")

    # 데이터베이스 상태 확인
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT instance_id, last_seen FROM instances")
            instances = cursor.fetchall()

            print("\n현재 등록된 모든 인스턴스:")
            for inst_id, last_seen in instances:
                print(f"  • {inst_id}: {last_seen}")

            conn.close()
        except Exception as e:
            print(f"\n⚠️ DB 조회 실패: {e}")

    print("\n💡 팁: 브로커가 실행 중이 아니면 메시지 송수신이 불가능합니다.")
    print("   이 도구는 응급용이며, 정상적으로는 브로커를 통해 등록하세요.")

if __name__ == "__main__":
    main()