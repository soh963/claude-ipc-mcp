#!/usr/bin/env python3
"""
TCP 브로커 전용 런처

MCP 서버 없이 순수 TCP 소켓 브로커만 실행합니다.
daemon=False로 설정하여 메인 스레드가 종료되지 않도록 합니다.
"""

import os
import sys
import signal
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_ipc_server import MessageBroker, IPC_HOST, IPC_PORT, logger

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal...")
    global broker
    if broker:
        broker.stop()
    sys.exit(0)

# Global broker instance for signal handler
broker = None

def main():
    """Main entry point - start TCP broker only"""
    global broker

    print("=" * 60)
    print("Starting TCP Message Broker (NO MCP)")
    print("=" * 60)
    print(f"Host: {IPC_HOST}")
    print(f"Port: {IPC_PORT}")
    print(f"Database: ~/.claude-ipc-data/messages.db")
    print("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start broker
    broker = MessageBroker(IPC_HOST, IPC_PORT)

    # Start broker in NON-DAEMON thread
    import threading
    broker.running = True
    broker_thread = threading.Thread(target=broker._run_server, daemon=False)
    broker_thread.start()

    print("\n✅ TCP Broker started successfully!")
    print("   Press Ctrl+C to stop\n")

    # Keep main thread alive
    try:
        while broker.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        broker.stop()

    # Wait for broker thread to finish
    broker_thread.join(timeout=5)
    print("✅ Broker stopped")

if __name__ == "__main__":
    main()