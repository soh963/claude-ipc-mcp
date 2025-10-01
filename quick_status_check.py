#!/usr/bin/env python3
"""Quick status check without imports that trigger broker start"""
import sys
sys.path.insert(0, "D:/claude-ipc-mcp/src")
from core import broker_client
import json

status = broker_client.status()
print(json.dumps(status, indent=2))

if status.get("status") == "ok":
    print("\n✅ SUCCESS: Broker responding correctly!")
    print(f"Active instances: {len(status.get('instances', []))}")
else:
    print(f"\n❌ FAILURE: {status.get('message', 'Unknown error')}")