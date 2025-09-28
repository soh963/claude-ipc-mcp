#!/usr/bin/env python3
"""
IPC Health Check and Diagnostic Tool

Comprehensive health check for IPC system:
- Server connectivity
- Database integrity
- Instance registration status
- Message queue health
- Network diagnostics
- Configuration validation
"""

import os
import sys
import socket
import json
import time
import sqlite3
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.project_utils import get_project_id, get_project_port
from tools.config_loader import ConfigLoader


class IPCHealthChecker:
    """Comprehensive IPC health check and diagnostics"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_id = get_project_id()
        self.project_port = get_project_port()
        self.host = '127.0.0.1'

        # Health check results
        self.health_status = {
            'server_running': False,
            'port_accessible': False,
            'database_healthy': False,
            'config_valid': False,
            'instances_active': 0,
            'message_queue_size': 0,
            'rate_limit_ok': True,
            'disk_space_ok': True,
            'memory_ok': True
        }

        self.diagnostics = []
        self.warnings = []
        self.errors = []

    def check_server_process(self) -> bool:
        """Check if IPC server process is running"""
        print("\n🔍 Checking server process...")

        server_found = False
        server_pids = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('claude_ipc_server' in str(arg) for arg in cmdline):
                        server_pids.append(proc.info['pid'])
                        server_found = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if server_found:
                print(f"  ✅ Server process found (PIDs: {server_pids})")
                self.health_status['server_running'] = True
            else:
                print("  ❌ Server process not found")
                self.errors.append("IPC server is not running")

            return server_found

        except Exception as e:
            print(f"  ❌ Error checking process: {e}")
            self.errors.append(f"Process check failed: {e}")
            return False

    def check_port_accessibility(self) -> bool:
        """Check if the IPC port is accessible"""
        print(f"\n🔌 Checking port {self.project_port} accessibility...")

        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.host, self.project_port))
            sock.close()

            if result == 0:
                print(f"  ✅ Port {self.project_port} is accessible")
                self.health_status['port_accessible'] = True
                return True
            else:
                print(f"  ❌ Port {self.project_port} is not accessible")
                self.errors.append(f"Cannot connect to port {self.project_port}")
                return False

        except Exception as e:
            print(f"  ❌ Error checking port: {e}")
            self.errors.append(f"Port check failed: {e}")
            return False

    def check_database_health(self) -> bool:
        """Check SQLite database health"""
        print("\n💾 Checking database health...")

        db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

        if not db_path.exists():
            print(f"  ⚠️  Database not found at {db_path}")
            self.warnings.append("Database file does not exist yet")
            return True  # Not an error if DB doesn't exist yet

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ['messages', 'instances', 'sessions', 'name_history']
            missing_tables = set(expected_tables) - set(tables)

            if missing_tables:
                print(f"  ⚠️  Missing tables: {missing_tables}")
                self.warnings.append(f"Missing database tables: {missing_tables}")
            else:
                print(f"  ✅ All required tables present")

            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]

            if integrity == 'ok':
                print("  ✅ Database integrity check passed")
                self.health_status['database_healthy'] = True
            else:
                print(f"  ❌ Database integrity issues: {integrity}")
                self.errors.append(f"Database corruption detected: {integrity}")

            # Get statistics
            if 'messages' in tables:
                cursor.execute("SELECT COUNT(*) FROM messages WHERE read_flag = 0")
                unread_count = cursor.fetchone()[0]
                self.health_status['message_queue_size'] = unread_count
                print(f"  ℹ️  Unread messages: {unread_count}")

            if 'instances' in tables:
                cursor.execute("SELECT COUNT(*) FROM instances WHERE project_id = ?",
                             (self.project_id,))
                instance_count = cursor.fetchone()[0]
                self.health_status['instances_active'] = instance_count
                print(f"  ℹ️  Registered instances: {instance_count}")

            conn.close()
            return self.health_status['database_healthy']

        except Exception as e:
            print(f"  ❌ Database check failed: {e}")
            self.errors.append(f"Database error: {e}")
            return False

    def check_configuration(self) -> bool:
        """Validate IPC configuration"""
        print("\n⚙️  Checking configuration...")

        config_path = Path('.ipc_project.yml')

        if not config_path.exists():
            print("  ⚠️  Configuration file not found")
            self.warnings.append("Missing .ipc_project.yml configuration")
            return False

        try:
            loader = ConfigLoader()
            config = loader.get_config()

            # Validate required fields
            required_fields = ['project', 'settings', 'permissions']
            missing_fields = []

            for field in required_fields:
                if field not in config:
                    missing_fields.append(field)

            if missing_fields:
                print(f"  ⚠️  Missing configuration fields: {missing_fields}")
                self.warnings.append(f"Incomplete configuration: {missing_fields}")
            else:
                print("  ✅ Configuration structure valid")

            # Check project ID match
            config_project_id = config.get('project', {}).get('id')
            if config_project_id != self.project_id:
                print(f"  ⚠️  Project ID mismatch: {config_project_id} vs {self.project_id}")
                self.warnings.append("Project ID mismatch in configuration")
            else:
                print(f"  ✅ Project ID matches: {self.project_id}")

            # Check port configuration
            config_port = config.get('project', {}).get('port')
            if config_port != self.project_port:
                print(f"  ⚠️  Port mismatch: {config_port} vs {self.project_port}")
                self.warnings.append("Port mismatch in configuration")
            else:
                print(f"  ✅ Port configured correctly: {self.project_port}")

            self.health_status['config_valid'] = len(missing_fields) == 0
            return self.health_status['config_valid']

        except Exception as e:
            print(f"  ❌ Configuration check failed: {e}")
            self.errors.append(f"Configuration error: {e}")
            return False

    def check_system_resources(self) -> bool:
        """Check system resources"""
        print("\n💻 Checking system resources...")

        all_ok = True

        try:
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024 ** 3)

            if free_gb < 1:
                print(f"  ⚠️  Low disk space: {free_gb:.2f} GB free")
                self.warnings.append(f"Low disk space: {free_gb:.2f} GB")
                self.health_status['disk_space_ok'] = False
                all_ok = False
            else:
                print(f"  ✅ Disk space: {free_gb:.2f} GB free")
                self.health_status['disk_space_ok'] = True

            # Check memory
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 ** 2)

            if available_mb < 100:
                print(f"  ⚠️  Low memory: {available_mb:.2f} MB available")
                self.warnings.append(f"Low memory: {available_mb:.2f} MB")
                self.health_status['memory_ok'] = False
                all_ok = False
            else:
                print(f"  ✅ Memory: {available_mb:.2f} MB available")
                self.health_status['memory_ok'] = True

            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                print(f"  ⚠️  High CPU usage: {cpu_percent}%")
                self.warnings.append(f"High CPU usage: {cpu_percent}%")
            else:
                print(f"  ✅ CPU usage: {cpu_percent}%")

            return all_ok

        except Exception as e:
            print(f"  ❌ Resource check failed: {e}")
            self.errors.append(f"Resource check error: {e}")
            return False

    def test_ipc_communication(self) -> bool:
        """Test actual IPC communication"""
        print("\n📡 Testing IPC communication...")

        if not self.health_status['port_accessible']:
            print("  ⏭️  Skipping: Port not accessible")
            return False

        try:
            # Prepare test message
            test_request = {
                'action': 'status',
                'name': 'health_checker',
                'project_id': self.project_id
            }

            # Connect and send
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.project_port))

            # Send request
            message = json.dumps(test_request) + '\n'
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
                result = json.loads(response.decode('utf-8').strip())
                if result.get('status') == 'success':
                    print("  ✅ Communication test successful")
                    return True
                else:
                    print(f"  ⚠️  Server responded with: {result.get('message')}")
                    self.warnings.append(f"Server response: {result.get('message')}")
                    return False
            else:
                print("  ❌ No response from server")
                self.errors.append("Server not responding")
                return False

        except socket.timeout:
            print("  ❌ Communication timeout")
            self.errors.append("IPC communication timeout")
            return False
        except Exception as e:
            print(f"  ❌ Communication test failed: {e}")
            self.errors.append(f"Communication error: {e}")
            return False

    def check_active_instances(self) -> List[Dict]:
        """Get list of active instances"""
        print("\n👥 Checking active instances...")

        if not self.health_status['port_accessible']:
            print("  ⏭️  Skipping: Server not accessible")
            return []

        try:
            # Request instance list
            request = {
                'action': 'list',
                'name': 'health_checker',
                'project_id': self.project_id
            }

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.project_port))

            message = json.dumps(request) + '\n'
            sock.sendall(message.encode('utf-8'))

            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b'\n' in response:
                    break

            sock.close()

            if response:
                result = json.loads(response.decode('utf-8').strip())
                if result.get('status') == 'success':
                    instances = result.get('instances', {})
                    if instances:
                        print(f"  ✅ Found {len(instances)} active instances:")
                        for name, info in instances.items():
                            last_seen = info.get('last_seen', 'Never')
                            print(f"     - {name}: Last seen {last_seen}")
                        return list(instances.keys())
                    else:
                        print("  ℹ️  No active instances found")
                        return []
                else:
                    print(f"  ⚠️  Could not get instance list")
                    return []
            else:
                print("  ❌ No response from server")
                return []

        except Exception as e:
            print(f"  ❌ Failed to get instances: {e}")
            return []

    def generate_diagnostics(self) -> None:
        """Generate diagnostic recommendations"""
        print("\n🔧 Generating diagnostics...")

        # Server not running
        if not self.health_status['server_running']:
            self.diagnostics.append({
                'issue': 'IPC server not running',
                'severity': 'CRITICAL',
                'solution': 'Start the server with: python src/claude_ipc_server.py'
            })

        # Port not accessible
        if not self.health_status['port_accessible']:
            if self.health_status['server_running']:
                self.diagnostics.append({
                    'issue': f'Port {self.project_port} blocked',
                    'severity': 'CRITICAL',
                    'solution': f'Check firewall settings or if another process is using port {self.project_port}'
                })

        # Configuration issues
        if not self.health_status['config_valid']:
            self.diagnostics.append({
                'issue': 'Invalid or missing configuration',
                'severity': 'HIGH',
                'solution': 'Run: python tools/config_loader.py create'
            })

        # Database issues
        if not self.health_status['database_healthy']:
            self.diagnostics.append({
                'issue': 'Database corruption or missing',
                'severity': 'HIGH',
                'solution': 'Run: python tools/fix_database.py'
            })

        # No active instances
        if self.health_status['instances_active'] == 0:
            self.diagnostics.append({
                'issue': 'No AI instances registered',
                'severity': 'MEDIUM',
                'solution': 'Run: python tools/auto_register_all.py'
            })

        # High message queue
        if self.health_status['message_queue_size'] > 100:
            self.diagnostics.append({
                'issue': f'Large message queue: {self.health_status["message_queue_size"]} unread',
                'severity': 'LOW',
                'solution': 'Check if instances are processing messages'
            })

        # Resource issues
        if not self.health_status['disk_space_ok']:
            self.diagnostics.append({
                'issue': 'Low disk space',
                'severity': 'MEDIUM',
                'solution': 'Free up disk space or clean old messages'
            })

        if not self.health_status['memory_ok']:
            self.diagnostics.append({
                'issue': 'Low memory available',
                'severity': 'MEDIUM',
                'solution': 'Close unnecessary applications or restart system'
            })

    def display_report(self) -> None:
        """Display comprehensive health report"""
        print("\n" + "=" * 60)
        print("📊 IPC HEALTH CHECK REPORT")
        print("=" * 60)
        print(f"Project ID: {self.project_id}")
        print(f"Project Port: {self.project_port}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        # Overall health score
        health_score = sum(1 for v in self.health_status.values() if v and isinstance(v, bool))
        total_checks = sum(1 for v in self.health_status.values() if isinstance(v, bool))
        health_percent = (health_score / total_checks) * 100 if total_checks > 0 else 0

        if health_percent >= 80:
            status_emoji = "🟢"
            status_text = "HEALTHY"
        elif health_percent >= 60:
            status_emoji = "🟡"
            status_text = "WARNING"
        else:
            status_emoji = "🔴"
            status_text = "CRITICAL"

        print(f"\n{status_emoji} Overall Status: {status_text} ({health_percent:.0f}%)")

        # Display health checks
        print("\n📋 Health Checks:")
        for check, value in self.health_status.items():
            if isinstance(value, bool):
                status = "✅" if value else "❌"
                check_name = check.replace('_', ' ').title()
                print(f"  {status} {check_name}")
            elif check == 'instances_active':
                print(f"  📊 Active Instances: {value}")
            elif check == 'message_queue_size':
                print(f"  📬 Message Queue Size: {value}")

        # Display warnings
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        # Display errors
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")

        # Display diagnostics
        if self.diagnostics:
            print("\n🔧 Recommended Actions:")
            for i, diag in enumerate(self.diagnostics, 1):
                severity_color = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                emoji = severity_color.get(diag['severity'], '⚪')
                print(f"\n  {i}. {emoji} [{diag['severity']}] {diag['issue']}")
                print(f"     Solution: {diag['solution']}")

        print("\n" + "=" * 60)

    def run_full_check(self) -> bool:
        """Run complete health check"""
        print("\n🏥 Starting IPC Health Check...")
        print("=" * 60)

        # Run all checks
        self.check_server_process()
        self.check_port_accessibility()
        self.check_database_health()
        self.check_configuration()
        self.check_system_resources()

        # Test communication if server is accessible
        if self.health_status['port_accessible']:
            self.test_ipc_communication()
            self.check_active_instances()

        # Generate diagnostics
        self.generate_diagnostics()

        # Display report
        self.display_report()

        # Return overall health status
        return len(self.errors) == 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="IPC Health Check and Diagnostic Tool"
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix detected issues'
    )

    args = parser.parse_args()

    # Create health checker
    checker = IPCHealthChecker(verbose=args.verbose)

    try:
        # Run health check
        healthy = checker.run_full_check()

        # Output JSON if requested
        if args.json:
            output = {
                'healthy': healthy,
                'status': checker.health_status,
                'warnings': checker.warnings,
                'errors': checker.errors,
                'diagnostics': checker.diagnostics
            }
            print("\n" + json.dumps(output, indent=2))

        # Attempt fixes if requested
        if args.fix and checker.diagnostics:
            print("\n🔧 Attempting automatic fixes...")
            # This could be expanded to actually fix issues
            print("  ℹ️  Automatic fixes not yet implemented")

        sys.exit(0 if healthy else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()