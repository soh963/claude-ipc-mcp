#!/usr/bin/env python3
"""
Automatically register all AI CLI instances for the current project
"""

import sys
import os
import time
import socket
import json
import hashlib
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.project_utils import get_project_id, get_project_port, format_instance_name


class AutoRegister:
    """Automatically register multiple AI instances"""

    def __init__(self):
        self.project_id = get_project_id()
        self.project_port = get_project_port()
        self.host = '127.0.0.1'

        # AI instances to register
        self.ai_instances = [
            {
                'name': 'claude',
                'description': 'Claude Code CLI - Architecture & Review',
                'capabilities': ['architecture', 'code_review', 'documentation']
            },
            {
                'name': 'gemini',
                'description': 'Gemini CLI - Multi-modal & Testing',
                'capabilities': ['testing', 'creative_solutions', 'multi_modal']
            },
            {
                'name': 'codex',
                'description': 'Codex CLI - Code Generation',
                'capabilities': ['code_generation', 'optimization', 'algorithms']
            },
            {
                'name': 'lm',
                'description': 'Local LM CLI - Privacy-first Processing',
                'capabilities': ['local_processing', 'privacy', 'offline_work']
            }
        ]

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to IPC server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.project_port))

            # Send request
            message = json.dumps(request) + '\n'
            sock.sendall(message.encode('utf-8'))

            # Receive response
            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b'\n' in response:
                    break

            sock.close()

            # Parse response
            if response:
                return json.loads(response.decode('utf-8').strip())
            return {'status': 'error', 'message': 'No response'}

        except ConnectionRefusedError:
            return {
                'status': 'error',
                'message': f'Cannot connect to IPC server on port {self.project_port}'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def register_instance(self, ai_info: Dict[str, Any]) -> bool:
        """Register a single AI instance"""
        name = ai_info['name']
        formatted_name = format_instance_name(name)

        request = {
            'action': 'register',
            'name': name,
            'metadata': {
                'description': ai_info['description'],
                'capabilities': ai_info['capabilities'],
                'project_id': self.project_id
            }
        }

        print(f"📝 Registering {formatted_name}...")

        response = self._send_request(request)

        if response.get('status') == 'success':
            token = response.get('token', 'N/A')
            print(f"✅ {formatted_name} registered successfully")
            print(f"   Token: {token[:8]}...")
            return True
        else:
            error = response.get('message', 'Unknown error')
            print(f"❌ Failed to register {formatted_name}: {error}")
            return False

    def check_server_status(self) -> bool:
        """Check if IPC server is running"""
        request = {'action': 'status'}
        response = self._send_request(request)
        return response.get('status') == 'success'

    def list_instances(self) -> List[str]:
        """List currently registered instances"""
        request = {'action': 'list'}
        response = self._send_request(request)

        if response.get('status') == 'success':
            instances = response.get('instances', {})
            return list(instances.keys())
        return []

    def register_all(self) -> Dict[str, bool]:
        """Register all AI instances"""
        print("\n" + "=" * 60)
        print("🚀 AUTO-REGISTRATION FOR AI INSTANCES")
        print("=" * 60)
        print(f"Project ID: {self.project_id}")
        print(f"Project Port: {self.project_port}")
        print("=" * 60)

        # Check server status
        print("\n🔍 Checking IPC server status...")
        if not self.check_server_status():
            print("❌ IPC server is not running!")
            print(f"   Please start it with: python src/claude_ipc_server.py")
            return {}

        print("✅ IPC server is running")

        # Check existing instances
        print("\n📋 Checking existing instances...")
        existing = self.list_instances()
        if existing:
            print(f"   Found {len(existing)} existing instances:")
            for instance in existing:
                print(f"   - {instance}")
        else:
            print("   No existing instances found")

        # Register each AI
        print("\n🔄 Starting registration process...")
        results = {}

        for ai_info in self.ai_instances:
            name = ai_info['name']
            formatted_name = format_instance_name(name)

            # Skip if already registered
            if formatted_name in existing or name in existing:
                print(f"⏭️  {formatted_name} already registered, skipping...")
                results[name] = True
                continue

            # Register new instance
            success = self.register_instance(ai_info)
            results[name] = success

            # Small delay between registrations
            time.sleep(0.5)

        return results

    def display_summary(self, results: Dict[str, bool]):
        """Display registration summary"""
        print("\n" + "=" * 60)
        print("📊 REGISTRATION SUMMARY")
        print("=" * 60)

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        for name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {name}: {status}")

        print("=" * 60)
        print(f"Result: {success_count}/{total_count} instances registered")

        if success_count == total_count:
            print("🎉 All AI instances registered successfully!")
        elif success_count > 0:
            print("⚠️  Some instances registered, but not all")
        else:
            print("❌ No instances were registered")

        # Show how to verify
        print("\n💡 To verify registration:")
        print("   python tools/ipc_list.py")
        print("\n💡 To test communication:")
        print("   python test/test_ipc_connection.py")


def main():
    """Main entry point"""
    registrar = AutoRegister()

    try:
        # Register all instances
        results = registrar.register_all()

        # Display summary
        registrar.display_summary(results)

        # Check final status
        print("\n🔍 Final instance check...")
        instances = registrar.list_instances()
        if instances:
            print(f"✅ {len(instances)} active instances:")
            for instance in instances:
                print(f"   - {instance}")

    except KeyboardInterrupt:
        print("\n⚠️  Registration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during registration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()