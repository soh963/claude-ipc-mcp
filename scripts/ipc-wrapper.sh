#!/bin/bash
# IPC Wrapper for Easy Terminal Usage
# Usage: ipc-wrapper <command> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

show_help() {
    cat << EOF
Usage: ipc-wrapper <command> [args...]

Available commands:
  status              - Check IPC status
  register <name>     - Register as instance
  list                - List all instances
  send <to> <msg>     - Send message
  ask <to> <msg>      - Send and wait for response
  check               - Check messages
  responder-start <name> - Start auto-responder
  responder-stop <name>  - Stop auto-responder
  responder-status <name> - Check responder status
  doctor              - Run diagnostics

Examples:
  ipc-wrapper status
  ipc-wrapper register codex-main
  ipc-wrapper send gemini "Hello"
  ipc-wrapper ask gemini "What's your status?"
EOF
}

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

CMD=$1
shift

cd "$PROJECT_ROOT"

case "$CMD" in
    status)
        uv run python tools/ipc_global_command.py status
        ;;
    register)
        if [ -z "$1" ]; then
            echo "Error: Instance name required"
            echo "Usage: ipc-wrapper register <name>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py register "$1"
        ;;
    list)
        uv run python tools/ipc_global_command.py instances list --full
        ;;
    send)
        if [ -z "$2" ]; then
            echo "Error: Target and message required"
            echo "Usage: ipc-wrapper send <to> <message>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py chat --to "$1" "$2"
        ;;
    ask)
        if [ -z "$2" ]; then
            echo "Error: Target and message required"
            echo "Usage: ipc-wrapper ask <to> <message>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py ask --to "$1" "$2" --timeout 10
        ;;
    check)
        uv run python tools/ipc_global_command.py messages list
        ;;
    responder-start)
        if [ -z "$1" ]; then
            echo "Error: Instance name required"
            echo "Usage: ipc-wrapper responder-start <name>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py responder start "$1" --policy smart --detach
        ;;
    responder-stop)
        if [ -z "$1" ]; then
            echo "Error: Instance name required"
            echo "Usage: ipc-wrapper responder-stop <name>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py responder stop "$1"
        ;;
    responder-status)
        if [ -z "$1" ]; then
            echo "Error: Instance name required"
            echo "Usage: ipc-wrapper responder-status <name>"
            exit 1
        fi
        uv run python tools/ipc_global_command.py responder status "$1"
        ;;
    doctor)
        uv run python tools/ipc_doctor.py --auto-fix
        ;;
    *)
        echo "Unknown command: $CMD"
        echo "Run 'ipc-wrapper' without arguments to see usage"
        exit 1
        ;;
esac
