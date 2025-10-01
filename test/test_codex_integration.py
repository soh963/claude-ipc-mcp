"""
E2E test for Codex CLI integration

Tests:
1. .cursorrules file exists in project root
2. config.toml exists in user .codex directory
3. config.toml has valid TOML syntax
4. All 9 IPC commands are defined
5. Command paths use proper escaping
"""
import os
import sys
from pathlib import Path

# Python 3.11+ has tomllib built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        import toml as tomllib


def test_cursorrules_exists():
    """Test .cursorrules file exists in project root"""
    project_root = Path(__file__).parent.parent
    cursorrules = project_root / ".cursorrules"
    assert cursorrules.exists(), ".cursorrules not found in project root"

    # Check file contains IPC command patterns
    content = cursorrules.read_text(encoding="utf-8")
    assert "IPC Command Integration" in content
    assert "uv run python" in content
    print("✓ .cursorrules exists and contains IPC commands")


def test_config_toml_exists():
    """Test config.toml exists in user .codex directory"""
    config_path = Path.home() / ".codex" / "config.toml"
    assert config_path.exists(), "config.toml not found in ~/.codex/"
    print("✓ config.toml exists in user .codex directory")


def test_config_toml_valid_syntax():
    """Test config.toml has valid TOML syntax"""
    config_path = Path.home() / ".codex" / "config.toml"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    assert "slash_commands" in config, "slash_commands section missing"
    print("✓ config.toml has valid TOML syntax")


def test_all_commands_defined():
    """Test all 9 IPC commands are defined"""
    config_path = Path.home() / ".codex" / "config.toml"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    expected_commands = [
        "ipc:setup",
        "ipc:status",
        "ipc:list",
        "ipc:send",
        "ipc:check",
        "ipc:responder-start",
        "ipc:responder-status",
        "ipc:responder-stop",
        "ipc:doctor"
    ]

    commands = config["slash_commands"]

    for cmd in expected_commands:
        assert cmd in commands, f"Command {cmd} not found"
        assert "command" in commands[cmd], f"Command {cmd} missing 'command' field"
        assert "description" in commands[cmd], f"Command {cmd} missing 'description' field"

    print(f"✓ All {len(expected_commands)} IPC commands defined")


def test_command_paths_escaped():
    """Test command paths use proper backslash escaping in source file"""
    config_path = Path.home() / ".codex" / "config.toml"

    # Read raw file content to check source escaping
    content = config_path.read_text(encoding="utf-8")

    # Check that paths in source file use double backslashes
    assert "%IPC_CHAT%\\\\" in content, "Commands must use double backslashes in source file"

    # Also verify TOML parser interprets it correctly
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    commands = config["slash_commands"]

    for cmd_name, cmd_config in commands.items():
        command = cmd_config["command"]

        # After parsing, single backslash is correct (TOML unescapes it)
        if "%IPC_CHAT%" in command:
            assert "\\" in command, f"Command {cmd_name} must contain backslash in path"

    print("✓ All command paths properly escaped")


def test_environment_section():
    """Test environment variables section exists"""
    config_path = Path.home() / ".codex" / "config.toml"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    assert "environment" in config, "environment section missing"
    env = config["environment"]

    assert "IPC_CHAT" in env, "IPC_CHAT not in environment"
    assert "IPC_DB_PATH" in env, "IPC_DB_PATH not in environment"
    assert "IPC_HOST" in env, "IPC_HOST not in environment"
    assert "IPC_GLOBAL_PORT" in env, "IPC_GLOBAL_PORT not in environment"

    print("✓ Environment variables section complete")


if __name__ == "__main__":
    print("\n=== Codex CLI Integration E2E Test ===\n")

    try:
        test_cursorrules_exists()
        test_config_toml_exists()
        test_config_toml_valid_syntax()
        test_all_commands_defined()
        test_command_paths_escaped()
        test_environment_section()

        print("\n✅ All tests passed! Codex integration is ready.\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        exit(1)
