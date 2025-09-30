#!/usr/bin/env python3
"""
Automated IPC Setup Script for New Projects

This script automatically sets up IPC functionality for a new project:
1. Creates necessary directories and configuration
2. Copies essential IPC tools
3. Generates project-specific configuration
4. Tests the connection
5. Optionally registers AI instances
"""

import os
import sys
import shutil
import subprocess
import time
import argparse
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.project_utils import get_project_id, get_project_port, get_project_name
from tools.config_loader import ConfigLoader


class IPCProjectSetup:
    """Automated IPC setup for new projects"""

    def __init__(self, target_path: str = None, ipc_base_path: str = None):
        """
        Initialize IPC setup

        Args:
            target_path: Path to the target project (default: current directory)
            ipc_base_path: Path to IPC source (default: parent of this script)
        """
        self.target_path = Path(target_path) if target_path else Path.cwd()
        self.ipc_base = Path(ipc_base_path) if ipc_base_path else Path(__file__).parent.parent

        # Essential files and directories to copy
        self.essential_files = {
            "tools": [
                "project_utils.py",
                "config_loader.py",
                "ipc_register.py",
                "ipc_send.py",
                "ipc_check.py",
                "ipc_list.py",
                "auto_register_all.py",
            ],
            "src": ["claude_ipc_server.py", "project_isolation_patch.py"],
            "test": ["test_ipc_connection.py", "test_project_isolation.py"],
        }

        self.setup_status = {
            "directories_created": False,
            "files_copied": False,
            "config_generated": False,
            "server_started": False,
            "connection_tested": False,
            "ai_registered": False,
        }

    def create_directory_structure(self) -> bool:
        """Create necessary directories in target project"""
        print("\n📁 Creating directory structure...")

        directories = ["tools", "src", "test", "doc"]

        try:
            for dir_name in directories:
                dir_path = self.target_path / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Created: {dir_name}/")

            self.setup_status["directories_created"] = True
            return True

        except Exception as e:
            print(f"  ❌ Error creating directories: {e}")
            return False

    def copy_essential_files(self) -> bool:
        """Copy essential IPC files to target project"""
        print("\n📄 Copying essential IPC files...")

        copied_count = 0
        failed_files = []

        for directory, files in self.essential_files.items():
            for file_name in files:
                source = self.ipc_base / directory / file_name
                target = self.target_path / directory / file_name

                if not source.exists():
                    print(f"  ⚠️  Source not found: {source}")
                    failed_files.append(str(source))
                    continue

                try:
                    # Create target directory if it doesn't exist
                    target.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(source, target)
                    print(f"  ✅ Copied: {directory}/{file_name}")
                    copied_count += 1

                except Exception as e:
                    print(f"  ❌ Failed to copy {file_name}: {e}")
                    failed_files.append(file_name)

        # Copy requirements.txt if exists
        req_source = self.ipc_base / "requirements.txt"
        if req_source.exists():
            req_target = self.target_path / "requirements.txt"
            try:
                shutil.copy2(req_source, req_target)
                print("  ✅ Copied: requirements.txt")
                copied_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not copy requirements.txt: {e}")

        print(f"\n📊 Copied {copied_count} files successfully")
        if failed_files:
            print(f"  ⚠️  Failed files: {', '.join(failed_files)}")

        self.setup_status["files_copied"] = copied_count > 0
        return copied_count > 0

    def generate_project_config(self) -> bool:
        """Generate project-specific IPC configuration"""
        print("\n⚙️  Generating project configuration...")

        # Change to target directory for correct project ID generation
        original_cwd = os.getcwd()
        try:
            os.chdir(self.target_path)

            # Get project information
            project_id = get_project_id()
            project_port = get_project_port()
            project_name = get_project_name()

            print(f"  📝 Project Name: {project_name}")
            print(f"  🆔 Project ID: {project_id}")
            print(f"  🔌 Project Port: {project_port}")

            # Create configuration using ConfigLoader
            config_path = self.target_path / ".ipc_project.yml"

            if not config_path.exists():
                loader = ConfigLoader(str(config_path))
                loader.get_config()
                print("  ✅ Created: .ipc_project.yml")
            else:
                print("  ℹ️  Configuration already exists")

            self.setup_status["config_generated"] = True
            return True

        except Exception as e:
            print(f"  ❌ Error generating configuration: {e}")
            return False

        finally:
            os.chdir(original_cwd)

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("\n📦 Installing dependencies...")

        req_file = self.target_path / "requirements.txt"

        if not req_file.exists():
            print("  ⚠️  requirements.txt not found, skipping dependency installation")
            return True

        try:
            # Install dependencies
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                cwd=str(self.target_path),
            )

            if result.returncode == 0:
                print("  ✅ Dependencies installed successfully")
                return True
            else:
                print(f"  ⚠️  Some dependencies may have failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Error installing dependencies: {e}")
            return False

    def start_ipc_server(self) -> Optional[subprocess.Popen]:
        """Start the IPC server for the project"""
        print("\n🚀 Starting IPC server...")

        server_script = self.target_path / "src" / "claude_ipc_server.py"

        if not server_script.exists():
            print(f"  ❌ Server script not found: {server_script}")
            return None

        try:
            # Start server in background
            process = subprocess.Popen(
                [sys.executable, str(server_script)],
                cwd=str(self.target_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a moment for server to start
            time.sleep(2)

            # Check if server is running
            if process.poll() is None:
                print("  ✅ IPC server started successfully")
                self.setup_status["server_started"] = True
                return process
            else:
                print("  ❌ Server failed to start")
                return None

        except Exception as e:
            print(f"  ❌ Error starting server: {e}")
            return None

    def test_connection(self) -> bool:
        """Test IPC connection"""
        print("\n🔍 Testing IPC connection...")

        test_script = self.target_path / "test" / "test_ipc_connection.py"

        if not test_script.exists():
            print("  ⚠️  Test script not found, skipping connection test")
            return True

        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(self.target_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print("  ✅ Connection test passed")
                self.setup_status["connection_tested"] = True
                return True
            else:
                print(f"  ❌ Connection test failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("  ⚠️  Connection test timed out")
            return False
        except Exception as e:
            print(f"  ❌ Error testing connection: {e}")
            return False

    def register_ai_instances(self, instances: List[str] = None) -> bool:
        """Register AI instances"""
        print("\n🤖 Registering AI instances...")

        if instances is None:
            instances = ["claude", "gemini", "codex", "lm"]

        register_script = self.target_path / "tools" / "auto_register_all.py"

        if not register_script.exists():
            print("  ⚠️  Registration script not found")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(register_script)],
                cwd=str(self.target_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print("  ✅ AI instances registered successfully")
                self.setup_status["ai_registered"] = True
                return True
            else:
                print("  ⚠️  Some registrations may have failed")
                return False

        except Exception as e:
            print(f"  ❌ Error registering instances: {e}")
            return False

    def create_readme(self) -> bool:
        """Create IPC README for the project"""
        print("\n📝 Creating IPC documentation...")

        readme_content = f"""# IPC Configuration for {self.target_path.name}

## Project Information
- **Project ID**: {get_project_id()}
- **Project Port**: {get_project_port()}
- **Isolation Mode**: strict (default)

## Quick Start

### 1. Start IPC Server
```bash
python src/claude_ipc_server.py
```

### 2. Register AI Instance
```bash
python tools/ipc_register.py [instance_name]
```

### 3. Send Message
```bash
python tools/ipc_send.py [from] [to] "message"
```

### 4. Check Messages
```bash
python tools/ipc_check.py [instance_name]
```

### 5. List Active Instances
```bash
python tools/ipc_list.py
```

## Auto-Registration
```bash
python tools/auto_register_all.py
```

## Testing
```bash
python test/test_ipc_connection.py
python test/test_project_isolation.py
```

## Configuration
Edit `.ipc_project.yml` to modify:
- Isolation mode (strict/relaxed/disabled)
- Allowed instances
- Rate limits
- Other settings

## Troubleshooting
1. Check server is running: `ps aux | grep claude_ipc_server`
2. Check port availability: `netstat -an | grep {get_project_port()}`
3. Review logs in terminal output
4. Test connection: `python test/test_ipc_connection.py`
"""

        readme_path = self.target_path / "doc" / "IPC_README.md"

        try:
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            readme_path.write_text(readme_content)
            print("  ✅ Created: doc/IPC_README.md")
            return True

        except Exception as e:
            print(f"  ❌ Error creating documentation: {e}")
            return False

    def display_summary(self) -> None:
        """Display setup summary"""
        print("\n" + "=" * 60)
        print("📊 IPC SETUP SUMMARY")
        print("=" * 60)

        for task, completed in self.setup_status.items():
            status = "✅" if completed else "❌"
            task_display = task.replace("_", " ").title()
            print(f"  {status} {task_display}")

        print("=" * 60)

        success_count = sum(1 for v in self.setup_status.values() if v)
        total_count = len(self.setup_status)

        if success_count == total_count:
            print("🎉 IPC setup completed successfully!")
        elif success_count > 0:
            print(f"⚠️  Partial setup: {success_count}/{total_count} tasks completed")
        else:
            print("❌ Setup failed")

        # Display next steps
        print("\n📝 Next Steps:")
        print("1. cd", self.target_path)
        print("2. Review doc/IPC_README.md")
        print("3. Start using IPC commands")

    def run_full_setup(self, skip_server: bool = False, skip_registration: bool = False) -> bool:
        """
        Run complete IPC setup process

        Args:
            skip_server: Skip starting the IPC server
            skip_registration: Skip AI instance registration

        Returns:
            True if setup was successful
        """
        print("\n" + "=" * 60)
        print(f"🚀 SETTING UP IPC FOR: {self.target_path}")
        print("=" * 60)

        # Step 1: Create directories
        if not self.create_directory_structure():
            return False

        # Step 2: Copy files
        if not self.copy_essential_files():
            return False

        # Step 3: Generate configuration
        if not self.generate_project_config():
            return False

        # Step 4: Install dependencies
        self.install_dependencies()

        # Step 5: Start server (optional)
        server_process = None
        if not skip_server:
            server_process = self.start_ipc_server()

        # Step 6: Test connection
        if server_process:
            self.test_connection()

        # Step 7: Register AI instances (optional)
        if not skip_registration and server_process:
            self.register_ai_instances()

        # Step 8: Create documentation
        self.create_readme()

        # Display summary
        self.display_summary()

        # Cleanup
        if server_process:
            print("\n⚠️  Server is running in background")
            print("  To stop: Kill the Python process or press Ctrl+C")

        return sum(1 for v in self.setup_status.values() if v) >= 4


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Automated IPC setup for new projects")

    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )

    parser.add_argument("--ipc-source", help="Path to IPC source directory (default: auto-detect)")

    parser.add_argument("--skip-server", action="store_true", help="Skip starting the IPC server")

    parser.add_argument(
        "--skip-registration", action="store_true", help="Skip AI instance registration"
    )

    parser.add_argument(
        "--minimal", action="store_true", help="Minimal setup (files and config only)"
    )

    args = parser.parse_args()

    # Handle minimal flag
    if args.minimal:
        args.skip_server = True
        args.skip_registration = True

    # Create setup instance
    setup = IPCProjectSetup(args.target, args.ipc_source)

    try:
        # Run setup
        success = setup.run_full_setup(
            skip_server=args.skip_server, skip_registration=args.skip_registration
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
