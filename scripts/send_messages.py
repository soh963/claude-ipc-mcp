#!/usr/bin/env python3
"""Example script to demonstrate messaging.

This placeholder script simply prints the messages that would be sent to
Claude and Gemini. In a real implementation, this could use an IPC or
network API to deliver the text.
"""

def send_to_claude(message: str) -> None:
    print(f"Sending to Claude: {message}")


def send_to_gemini(message: str) -> None:
    print(f"Sending to Gemini: {message}")


if __name__ == "__main__":
    # Example usage
    send_to_claude("안녕, 난 lm이야.")
    send_to_gemini("Hello!")

