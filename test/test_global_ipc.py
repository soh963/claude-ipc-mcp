#!/usr/bin/env python3
"""
Test Global IPC functionality - Cross-project communication
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from global_ipc_client import GlobalIPCClient


def test_single_project():
    """Test communication within same project"""
    print("\n" + "="*60)
    print("TEST 1: Single Project Communication")
    print("="*60)

    project = "claude-ipc-mcp"

    # Create two clients in same project
    client1 = GlobalIPCClient(project)
    client2 = GlobalIPCClient(project)

    # Register
    assert client1.register("claude", "project")
    print(f"✅ Registered claude in {project}")

    assert client2.register("gemini", "project")
    print(f"✅ Registered gemini in {project}")

    # Send message
    assert client1.send("gemini", "Hello from Claude (same project)")
    print("📨 Sent message: claude → gemini")

    # Check messages
    time.sleep(0.5)
    messages = client2.check()
    assert len(messages) > 0
    print(f"📬 Received: {messages[0]['message']}")

    print("✅ Single project test PASSED")


def test_cross_project():
    """Test communication across different projects"""
    print("\n" + "="*60)
    print("TEST 2: Cross-Project Communication")
    print("="*60)

    project_a = "claude-ipc-mcp"
    project_b = "test-tem"

    # Create clients in different projects
    client_a = GlobalIPCClient(project_a)
    client_b = GlobalIPCClient(project_b)

    # Register
    assert client_a.register("claude", "project")
    print(f"✅ Registered claude in {project_a}")

    assert client_b.register("gemini", "global")  # Global visibility
    print(f"✅ Registered gemini in {project_b} (global)")

    # Grant permission for cross-project (hashes computed implicitly if needed)

    # From A to B
    assert client_a.grant_permission(project_b)
    print(f"✅ Granted permission: {project_a} → {project_b}")

    # Send cross-project message
    assert client_a.send("gemini@global", "Hello from Claude (cross-project)")
    print("📨 Sent cross-project: claude → gemini@global")

    # Check messages
    time.sleep(0.5)
    messages = client_b.check()
    assert len(messages) > 0
    print(f"📬 Received: {messages[0]['message']}")
    print(f"   Cross-project: {messages[0].get('cross_project', False)}")

    print("✅ Cross-project test PASSED")


def test_global_visibility():
    """Test global visibility and discovery"""
    print("\n" + "="*60)
    print("TEST 3: Global Visibility & Discovery")
    print("="*60)

    # Create clients with different visibility
    client_private = GlobalIPCClient("project-private")
    client_global = GlobalIPCClient("project-global")
    client_selective = GlobalIPCClient("project-selective")

    # Register with different visibility
    assert client_private.register("ai_private", "project")
    print("✅ Registered ai_private (project visibility)")

    assert client_global.register("ai_global", "global")
    print("✅ Registered ai_global (global visibility)")

    assert client_selective.register("ai_selective", "selective")
    print("✅ Registered ai_selective (selective visibility)")

    # List instances - project only
    instances = client_private.list_instances(include_global=False)
    print(f"\n📋 Project-only instances: {len(instances)}")
    for inst in instances:
        print(f"  - {inst['name']} ({inst['visibility']})")

    # List instances - include global
    instances = client_private.list_instances(include_global=True)
    print(f"\n📋 All instances (including global): {len(instances)}")
    for inst in instances:
        print(f"  - {inst['name']} ({inst['visibility']})")

    print("✅ Global visibility test PASSED")


def test_permission_management():
    """Test permission grant/revoke"""
    print("\n" + "="*60)
    print("TEST 4: Permission Management")
    print("="*60)

    project_x = "project-x"
    project_y = "project-y"

    client_x = GlobalIPCClient(project_x)
    client_y = GlobalIPCClient(project_y)

    # Register
    client_x.register("ai_x", "project")
    client_y.register("ai_y", "project")

    # Check permission (should be denied)
    allowed = client_x.check_permission(project_y)
    print(f"❌ Permission check (before grant): {allowed}")
    assert not allowed

    # Grant permission
    assert client_x.grant_permission(project_y)
    print(f"✅ Granted permission: {project_x} → {project_y}")

    # Check permission (should be allowed)
    allowed = client_x.check_permission(project_y)
    print(f"✅ Permission check (after grant): {allowed}")
    assert allowed

    # Revoke permission
    assert client_x.revoke_permission(project_y)
    print(f"❌ Revoked permission: {project_x} → {project_y}")

    # Check permission (should be denied again)
    allowed = client_x.check_permission(project_y)
    print(f"❌ Permission check (after revoke): {allowed}")
    assert not allowed

    print("✅ Permission management test PASSED")


def test_server_status():
    """Test server status"""
    print("\n" + "="*60)
    print("TEST 5: Server Status")
    print("="*60)

    client = GlobalIPCClient("status-test")

    status = client.status()
    assert status.get('status') == 'ok'

    print("📊 Server Status:")
    print(f"  - Server: {status.get('server')}")
    print(f"  - Version: {status.get('version')}")
    print(f"  - Projects: {status.get('projects')}")
    print(f"  - Instances: {status.get('instances')}")
    print(f"  - Queued Messages: {status.get('queued_messages')}")

    print("✅ Server status test PASSED")


def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("      GLOBAL IPC TEST SUITE")
    print("🚀"*30)

    try:
        # Test 1: Single project
        test_single_project()

        # Test 2: Cross-project
        test_cross_project()

        # Test 3: Global visibility
        test_global_visibility()

        # Test 4: Permissions
        test_permission_management()

        # Test 5: Server status
        test_server_status()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()