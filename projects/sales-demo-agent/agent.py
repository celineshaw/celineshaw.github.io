"""A technical-sales assistant agent.

Reads a customer's request in plain language, calls the design tools to build
real gdsfactory layouts, and replies with a summary a sales engineer can send.

Run:
    pip install anthropic gdsfactory matplotlib
    export ANTHROPIC_API_KEY=...
    python agent.py "We need a ring filter with about 5 nm FSR at 1550 nm"
"""
import sys

import anthropic

from design_tools import TOOL_SCHEMAS, call_tool

SYSTEM = (
    "You are a sales engineer for a photonic chip design platform. "
    "Understand what the customer is building, use the design tools to produce real layouts "
    "that meet their spec, then explain the result in plain language: what you built, the key "
    "numbers, any trade-offs, and a clear next step. Always finish by writing a spec sheet."
)

MODEL = "claude-sonnet-5-5"


def run(request: str) -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": request}]
    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=2000, system=SYSTEM, tools=TOOL_SCHEMAS, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"-> {block.name}({block.input})")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": call_tool(block.name, block.input)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:]) or "We need a ring filter with about 5 nm FSR at 1550 nm and an MZI with 20 nm FSR."))
