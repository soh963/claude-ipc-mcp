#!/usr/bin/env python3
"""
브로커 통신 디버깅 도구

브로커가 실행 중이지만 status 명령이 타임아웃되는 근본 원인을 찾습니다.
"""

import socket
import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_socket_connection():
    """소켓 연결 자체를 테스트"""
    print("\n=== 1. 소켓 연결 테스트 ===")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)

        start = time.perf_counter()
        s.connect(("127.0.0.1", 9876))
        connect_time = time.perf_counter() - start

        print(f"✅ 소켓 연결 성공 ({connect_time*1000:.1f}ms)")
        s.close()
        return True
    except socket.timeout:
        print(f"❌ 소켓 연결 타임아웃 (2초 초과)")
        return False
    except Exception as e:
        print(f"❌ 소켓 연결 실패: {e}")
        return False

def test_send_receive():
    """데이터 전송/수신 테스트"""
    print("\n=== 2. 데이터 송수신 테스트 ===")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)

        # 연결
        start_connect = time.perf_counter()
        s.connect(("127.0.0.1", 9876))
        connect_time = time.perf_counter() - start_connect
        print(f"연결 시간: {connect_time*1000:.1f}ms")

        # 요청 전송
        request = {"action": "list"}
        request_json = json.dumps(request)

        start_send = time.perf_counter()
        bytes_sent = s.send(request_json.encode("utf-8"))
        send_time = time.perf_counter() - start_send
        print(f"전송 시간: {send_time*1000:.1f}ms ({bytes_sent} bytes)")

        # 응답 수신 (여기서 타임아웃이 발생할 가능성 높음)
        print("응답 대기 중...")
        start_recv = time.perf_counter()

        # 버퍼 크기를 작게 시작해서 점진적으로 읽기
        data = b""
        chunk_size = 4096

        while True:
            try:
                chunk = s.recv(chunk_size)
                if not chunk:
                    break
                data += chunk
                print(f"  수신: {len(chunk)} bytes (누적: {len(data)} bytes)")

                # JSON 완성 확인
                try:
                    json.loads(data.decode("utf-8"))
                    print("  JSON 완성 감지")
                    break
                except json.JSONDecodeError:
                    continue

            except socket.timeout:
                print(f"  ❌ 수신 타임아웃 (5초 초과)")
                break

        recv_time = time.perf_counter() - start_recv

        if data:
            print(f"✅ 수신 완료: {len(data)} bytes ({recv_time*1000:.1f}ms)")

            # 응답 파싱
            try:
                response = json.loads(data.decode("utf-8"))
                print(f"응답 상태: {response.get('status')}")
                print(f"인스턴스 수: {len(response.get('instances', []))}")

                total_time = connect_time + send_time + recv_time
                print(f"\n총 소요 시간: {total_time*1000:.1f}ms")

                s.close()
                return True
            except Exception as e:
                print(f"❌ 응답 파싱 실패: {e}")
                print(f"원본 데이터: {data[:200]}")
                s.close()
                return False
        else:
            print(f"❌ 데이터 수신 실패 ({recv_time*1000:.1f}ms)")
            s.close()
            return False

    except socket.timeout:
        print(f"❌ 전체 작업 타임아웃")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_broker_client():
    """broker_client 라이브러리 테스트"""
    print("\n=== 3. broker_client 라이브러리 테스트 ===")
    try:
        from core import broker_client

        start = time.perf_counter()
        response = broker_client.status()
        elapsed = time.perf_counter() - start

        print(f"응답 시간: {elapsed*1000:.1f}ms")
        print(f"응답: {response}")

        if response.get("status") == "ok":
            print("✅ broker_client 정상 작동")
            return True
        else:
            print(f"❌ 오류 응답: {response.get('message')}")
            return False

    except Exception as e:
        print(f"❌ broker_client 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_requests():
    """연속 요청 테스트 (부하 테스트)"""
    print("\n=== 4. 연속 요청 테스트 (10회) ===")

    success_count = 0
    total_time = 0

    for i in range(10):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)

            start = time.perf_counter()
            s.connect(("127.0.0.1", 9876))
            s.send(json.dumps({"action": "list"}).encode("utf-8"))

            data = s.recv(65536)
            elapsed = time.perf_counter() - start

            if data:
                response = json.loads(data.decode("utf-8"))
                if response.get("status") == "ok":
                    success_count += 1
                    total_time += elapsed
                    print(f"  #{i+1}: ✅ {elapsed*1000:.1f}ms")
                else:
                    print(f"  #{i+1}: ❌ 오류 응답")
            else:
                print(f"  #{i+1}: ❌ 데이터 없음")

            s.close()
            time.sleep(0.1)  # 100ms 대기

        except Exception as e:
            print(f"  #{i+1}: ❌ {e}")

    if success_count > 0:
        avg_time = total_time / success_count
        print(f"\n성공률: {success_count}/10 ({success_count*10}%)")
        print(f"평균 응답 시간: {avg_time*1000:.1f}ms")
        return success_count >= 8
    else:
        print(f"\n❌ 모든 요청 실패")
        return False

def main():
    print("=" * 60)
    print("브로커 통신 디버깅 도구")
    print("=" * 60)

    results = {
        "socket_connection": test_socket_connection(),
        "send_receive": test_send_receive(),
        "broker_client": test_broker_client(),
        "multiple_requests": test_multiple_requests()
    }

    print("\n" + "=" * 60)
    print("최종 결과")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ 모든 테스트 통과 - 브로커 통신 정상")
    else:
        print("\n❌ 일부 테스트 실패 - 문제 원인 분석 필요")
        print("\n권장 조치:")

        if not results["socket_connection"]:
            print("  1. 브로커가 실행 중인지 확인: uv run python tools/start_broker.py")
            print("  2. 방화벽 설정 확인")

        if not results["send_receive"]:
            print("  1. 브로커 로그 확인: .ipc/logs/ 디렉토리")
            print("  2. recv() 타임아웃 - 브로커가 응답을 보내지 않음")
            print("  3. 브로커 프로세스 재시작 필요")

        if not results["broker_client"]:
            print("  1. broker_client.py의 _send_request() 함수 확인")
            print("  2. 타임아웃 설정 확인 (현재 5.0초)")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())