"""Assignment 1, Part A: hosted API call to Anthropic's Claude.

Reads the API key from the ANTHROPIC_API_KEY environment variable,
sends one prompt to the model, and prints the response.
"""

import os
import sys

import anthropic

MODEL = "claude-haiku-4-5-20251001"
PROMPT = "Explain AI engineering in one sentence."


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY is not set. Set it as an environment variable and restart your terminal.")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": PROMPT}],
    )

    print(f"Model: {MODEL}")
    print(f"Prompt: {PROMPT}")
    print(f"Response: {message.content[0].text}")


if __name__ == "__main__":
    main()
