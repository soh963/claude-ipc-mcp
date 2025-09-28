#!/usr/bin/env python3
"""
List all registered IPC instances
"""

import sys
import os
import json

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

try:
    from ipc_manager import IPCManager

    # Create IPC manager
    ipc = IPCManager()

    # List instances
    result = ipc.list_instances()

    if result.get('status') == 'ok':
        instances = result.get('instances', [])
        print(f"\n📊 Active IPC Instances ({len(instances)} found):")
        print("="*50)
        for instance in instances:
            print(f"  ✅ {instance}")
        print("="*50)
    else:
        print(f"Error: {result.get('message')}")

except Exception as e:
    print(f"Error listing instances: {e}")