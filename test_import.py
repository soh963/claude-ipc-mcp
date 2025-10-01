#!/usr/bin/env python3
import sys

# Test if module is importable and where it's loaded from
try:
    # First try importing from src
    sys.path.insert(0, "src")
    import claude_ipc_server
    print(f"Loaded from: {claude_ipc_server.__file__}")

    # Check if the fix is in the loaded file
    import inspect
    source = inspect.getsource(claude_ipc_server.MessageBroker._process_request)
    if 'action not in ("register", "list")' in source:
        print("✅ Fix is present in loaded module")
    elif 'action != "register"' in source:
        print("❌ Fix NOT present - old code loaded")
    else:
        print("⚠️  Could not determine if fix is present")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()