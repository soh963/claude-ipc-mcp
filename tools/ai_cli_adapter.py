#!/usr/bin/env python3
"""
AI CLI Adapter - Real AI Communication Interface
Enables communication with actual AI CLI tools (Gemini, ChatGPT, etc.)
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AIConfig:
    """AI CLI configuration"""
    name: str
    command: str
    args_template: list[str]
    env_vars: Dict[str, str]
    response_parser: str  # 'json' or 'text'


class AICliAdapter:
    """Adapter for communicating with real AI CLI tools"""

    # AI CLI configurations
    AI_CONFIGS = {
        "gemini": AIConfig(
            name="Gemini",
            command="gemini",  # or full path to gemini CLI
            args_template=["chat", "--prompt", "{message}"],
            env_vars={"GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")},
            response_parser="text"
        ),
        "chatgpt": AIConfig(
            name="ChatGPT",
            command="chatgpt",  # or full path to chatgpt CLI
            args_template=["--message", "{message}"],
            env_vars={"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")},
            response_parser="text"
        ),
        "ollama": AIConfig(
            name="Ollama",
            command="ollama",
            args_template=["run", "llama3.2", "{message}"],
            env_vars={},
            response_parser="text"
        ),
        "aider": AIConfig(
            name="Aider",
            command="aider",
            args_template=["--message", "{message}", "--no-git", "--yes"],
            env_vars={},
            response_parser="text"
        ),
        "mock": AIConfig(
            name="Mock AI",
            command="python",
            args_template=["tools/mock_ai.py", "{message}"],
            env_vars={},
            response_parser="text"
        )
    }

    def __init__(self, ai_type: str):
        """
        Initialize AI CLI adapter

        Args:
            ai_type: Type of AI CLI ('gemini', 'chatgpt', 'ollama', etc.)
        """
        self.ai_type = ai_type.lower()
        if self.ai_type not in self.AI_CONFIGS:
            raise ValueError(f"Unsupported AI type: {ai_type}")

        self.config = self.AI_CONFIGS[self.ai_type]
        self._validate_cli()

    def _validate_cli(self) -> bool:
        """Validate that AI CLI is available"""
        try:
            result = subprocess.run(
                [self.config.command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def send_message(self, message: str, timeout: int = 30) -> Optional[str]:
        """
        Send message to AI CLI and get response

        Args:
            message: Message to send to AI
            timeout: Response timeout in seconds

        Returns:
            AI response or None if failed
        """
        # Build command
        args = [arg.format(message=message) for arg in self.config.args_template]
        cmd = [self.config.command] + args

        # Prepare environment
        env = os.environ.copy()
        env.update(self.config.env_vars)

        try:
            print(f"🤖 Invoking {self.config.name} CLI: {' '.join(cmd[:3])}...", flush=True)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            if result.returncode == 0:
                response = self._parse_response(result.stdout)
                print(f"✅ {self.config.name} responded: {response[:100]}...", flush=True)
                return response
            else:
                print(f"❌ {self.config.name} error: {result.stderr}", flush=True)
                return None

        except subprocess.TimeoutExpired:
            print(f"⏱️ {self.config.name} timeout after {timeout}s", flush=True)
            return None
        except Exception as e:
            print(f"❌ {self.config.name} exception: {e}", flush=True)
            return None

    def _parse_response(self, output: str) -> str:
        """Parse AI CLI response based on configuration"""
        if self.config.response_parser == "json":
            try:
                data = json.loads(output)
                return data.get("response", output)
            except json.JSONDecodeError:
                return output
        else:
            # Text response - clean up
            return output.strip()

    @staticmethod
    def detect_available_ais() -> Dict[str, bool]:
        """Detect which AI CLIs are available on the system"""
        available = {}
        for ai_type in AICliAdapter.AI_CONFIGS.keys():
            try:
                adapter = AICliAdapter(ai_type)
                available[ai_type] = adapter._validate_cli()
            except Exception:
                available[ai_type] = False
        return available

    @staticmethod
    def auto_register_ais(ipc_register_cmd: str = "uv run python tools/ipc_global_command.py register"):
        """
        Auto-register detected AI CLIs with IPC system

        Args:
            ipc_register_cmd: Command to register with IPC
        """
        available = AICliAdapter.detect_available_ais()
        registered = []

        for ai_type, is_available in available.items():
            if is_available:
                try:
                    cmd = f"{ipc_register_cmd} {ai_type}"
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        registered.append(ai_type)
                        print(f"✅ Registered {ai_type} with IPC")
                except Exception as e:
                    print(f"❌ Failed to register {ai_type}: {e}")

        return registered


if __name__ == "__main__":
    # Test AI detection
    print("🔍 Detecting available AI CLIs...")
    available = AICliAdapter.detect_available_ais()

    print("\n📊 Available AI CLIs:")
    for ai_type, is_available in available.items():
        status = "✅" if is_available else "❌"
        print(f"{status} {ai_type}")

    # Test Ollama if available
    if available.get("ollama"):
        print("\n🧪 Testing Ollama...")
        adapter = AICliAdapter("ollama")
        response = adapter.send_message("Say hello in one sentence")
        if response:
            print(f"Response: {response}")
