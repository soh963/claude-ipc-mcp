#!/usr/bin/env python3
"""
Test project isolation functionality
Verifies that messages are properly isolated between projects
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.project_utils import get_project_id, get_project_port, format_instance_name
from tools.config_loader import load_project_config


def test_project_info():
    """Test project information generation"""
    print("\n" + "="*60)
    print("TEST 1: Project Information")
    print("="*60)

    project_id = get_project_id()
    project_port = get_project_port()
    config = load_project_config()

    print(f"✅ Project ID: {project_id}")
    print(f"✅ Project Port: {project_port}")
    print(f"✅ Isolation Mode: {config['project']['isolation_mode']}")
    print(f"✅ Cross-Project Allowed: {config['permissions']['allow_cross_project']}")

    assert project_id.startswith('proj_'), "Project ID should start with 'proj_'"
    assert 9000 <= project_port <= 9999, "Project port should be in range 9000-9999"

    print("✅ Project information test PASSED")


def test_instance_naming():
    """Test instance name formatting with project namespace"""
    print("\n" + "="*60)
    print("TEST 2: Instance Naming")
    print("="*60)

    project_id = get_project_id()

    # Test formatting
    test_names = ['claude', 'gemini', 'codex']
    for name in test_names:
        formatted = format_instance_name(name)
        expected = f"{name}@{project_id}"
        print(f"  {name} -> {formatted}")
        assert formatted == expected, f"Expected {expected}, got {formatted}"

    # Test parsing
    test_full = f"claude@{project_id}"
    from tools.project_utils import parse_instance_name
    base, proj = parse_instance_name(test_full)
    assert base == "claude", f"Expected base 'claude', got '{base}'"
    assert proj == project_id, f"Expected project '{project_id}', got '{proj}'"

    print("✅ Instance naming test PASSED")


def test_message_validation():
    """Test message validation between projects"""
    print("\n" + "="*60)
    print("TEST 3: Message Validation")
    print("="*60)

    # Import isolation manager
    from src.project_isolation_patch import ProjectIsolationManager

    manager = ProjectIsolationManager()
    project_id = manager.project_id

    # Test cases
    test_cases = [
        # (from, to, expected_result, description)
        (f"claude@{project_id}", f"gemini@{project_id}", True, "Same project"),
        ("claude", "gemini", True, "No project (assumes current)"),
        ("claude@proj_other", f"gemini@{project_id}", False, "Different projects"),
        (f"claude@{project_id}", "gemini@proj_other", False, "Different projects"),
    ]

    for from_inst, to_inst, expected, desc in test_cases:
        allowed, reason = manager.validate_message(from_inst, to_inst)
        status = "✅" if allowed == expected else "❌"
        print(f"  {desc}: {status}")
        print(f"    {from_inst} -> {to_inst}: {'Allowed' if allowed else 'Blocked'} ({reason})")
        assert allowed == expected, f"Validation failed for {desc}"

    print("✅ Message validation test PASSED")


def test_config_isolation_modes():
    """Test different isolation modes"""
    print("\n" + "="*60)
    print("TEST 4: Isolation Modes")
    print("="*60)

    from tools.config_loader import update_config_value, get_config_value
    from src.project_isolation_patch import ProjectIsolationManager

    # Save original mode
    original_mode = get_config_value('project.isolation_mode')

    # Test strict mode
    update_config_value('project.isolation_mode', 'strict')
    update_config_value('permissions.allow_cross_project', False)
    manager = ProjectIsolationManager()

    allowed, _ = manager.validate_message('claude@proj_other', 'gemini@proj_3f5ad8cd')
    assert not allowed, "Strict mode should block cross-project"
    print("✅ Strict mode: Cross-project blocked")

    # Test relaxed mode with permissions
    update_config_value('project.isolation_mode', 'relaxed')
    update_config_value('permissions.allow_cross_project', True)
    update_config_value('permissions.trusted_projects', ['proj_other'])
    manager = ProjectIsolationManager()

    allowed, _ = manager.validate_message('claude@proj_other', 'gemini@proj_3f5ad8cd')
    assert allowed, "Relaxed mode with trust should allow cross-project"
    print("✅ Relaxed mode: Trusted cross-project allowed")

    # Test disabled mode
    update_config_value('project.isolation_mode', 'disabled')
    manager = ProjectIsolationManager()

    allowed, _ = manager.validate_message('claude@proj_any', 'gemini@proj_any2')
    assert allowed, "Disabled mode should allow all"
    print("✅ Disabled mode: All communication allowed")

    # Restore original mode
    update_config_value('project.isolation_mode', original_mode)
    update_config_value('permissions.allow_cross_project', False)
    update_config_value('permissions.trusted_projects', [])

    print("✅ Isolation modes test PASSED")


def test_project_status_display():
    """Test project status display"""
    print("\n" + "="*60)
    print("TEST 5: Status Display")
    print("="*60)

    from src.project_isolation_patch import ProjectIsolationManager

    manager = ProjectIsolationManager()
    status = manager.get_status()

    print("📊 Project Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    assert 'project_id' in status
    assert 'project_port' in status
    assert 'isolation_mode' in status

    print("✅ Status display test PASSED")


def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("      PROJECT ISOLATION TEST SUITE")
    print("🚀"*30)

    try:
        test_project_info()
        test_instance_naming()
        test_message_validation()
        test_config_isolation_modes()
        test_project_status_display()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Project isolation is properly configured and functional")

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