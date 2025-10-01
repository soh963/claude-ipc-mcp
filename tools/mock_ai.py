#!/usr/bin/env python3
"""
Mock AI CLI for testing purposes
Simulates an actual AI with intelligent responses
"""

import sys
import random
import time

RESPONSES = {
    "greeting": [
        "Hello! I'm a mock AI assistant. How can I help you?",
        "Hi there! I'm here to assist you with testing the IPC system.",
        "Greetings! Mock AI at your service."
    ],
    "question": [
        "That's an interesting question. Based on my mock knowledge, I would say...",
        "Let me think about that... Here's my take:",
        "Good question! My response is:"
    ],
    "task": [
        "I can help with that task. Here's what I recommend:",
        "Sure, I'll work on that. My approach would be:",
        "Absolutely! Let's tackle this together."
    ],
    "default": [
        "I understand your message. As a mock AI, I'm processing your request.",
        "Thanks for your message. I'm analyzing it now.",
        "Received your message loud and clear!"
    ]
}


def generate_response(message: str) -> str:
    """Generate intelligent mock response"""
    message_lower = message.lower()

    # Detect intent
    if any(word in message_lower for word in ["hello", "hi", "hey", "안녕"]):
        response_type = "greeting"
    elif any(word in message_lower for word in ["?", "what", "how", "why", "무엇", "어떻게"]):
        response_type = "question"
    elif any(word in message_lower for word in ["can you", "please", "help", "도와"]):
        response_type = "task"
    else:
        response_type = "default"

    # Select random response template
    template = random.choice(RESPONSES[response_type])

    # Add context
    if response_type == "question":
        template += f"\n\nRegarding '{message[:50]}...', I believe this is worth exploring further."
    elif response_type == "task":
        template += f"\n\n1. First, analyze the request\n2. Then, formulate a plan\n3. Finally, execute the solution"

    # Add timestamp and signature
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    response = f"{template}\n\n[Mock AI Response at {timestamp}]"

    return response


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/mock_ai.py <message>")
        sys.exit(1)

    # Join all args as message
    message = " ".join(sys.argv[1:])

    # Simulate AI processing delay
    time.sleep(0.5)

    # Generate and print response
    response = generate_response(message)
    print(response)
