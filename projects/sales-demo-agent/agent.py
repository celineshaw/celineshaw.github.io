"""A solutions-engineering agent for photonic chip design.

Reads a customer's request in plain language, plans the design, lays it out on a
real foundry PDK, rule-checks it, and writes two customer-facing documents: a
technical spec sheet and a proof-of-concept plan with agreed success criteria.

When GDSFactory+ is running (VS Code extension or Cloud workspace) and gfp-mcp is
installed, its tools (cells, DRC, LVS, simulation) are added automatically.

Every run is saved to out/transcript.md.

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...        # your own key, never committed
    python agent.py                     # sample WDM demux request
    python agent.py "your customer's request"
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import anthropic

from design_tools import TOOL_SCHEMAS, call_tool
from gfp_bridge import GFPBridge

MODEL = "claude-sonnet-5-5"

SYSTEM = """You are a solutions engineer for GDSFactory+, a chip design platform.
Customers buy it to remove workflow pain (tape-out delays, manual DRC fixing, brittle
PDK wrappers), not because a layout looks nice. For every request:
1. Restate the customer's goal and the pain behind it in one or two sentences.
2. Plan with plan_wdm_demux when they describe a channel plan; never guess an FSR.
3. Build it on the foundry PDK with build_foundry_demux, then run_rule_checks.
   If gfp_check_drc is available, also run foundry sign-off DRC with it.
4. Never state a number the tools did not return. Report violations honestly.
5. Write the spec sheet (include 3 discovery questions about their current workflow)
   and a POC plan with measurable success criteria agreed up front.
6. Finish with a short reply the account executive could send."""

SAMPLE = (
    "We're building a 4-channel WDM demux with 3.2 nm (400 GHz) spacing at 1550 nm on Cornerstone's "
    "220 nm SOI process. Right now our designers stitch layouts together in KLayout and Python scripts "
    "and fix DRC errors by hand before every tape-out. Can you show us what this looks like in GDSFactory+?"
)


async def run(request: str) -> str:
    client = anthropic.Anthropic()
    gfp = await GFPBridge().start()
    tools = TOOL_SCHEMAS + gfp.tools
    messages = [{"role": "user", "content": request}]
    log = [f"# Agent transcript\n\n_{datetime.now():%Y-%m-%d %H:%M}, model {MODEL}, "
           f"GDSFactory+ tools: {'connected' if gfp.tools else 'not connected'}_\n",
           f"## Customer\n\n{request}\n"]
    try:
        while True:
            response = client.messages.create(model=MODEL, max_tokens=4000, system=SYSTEM,
                                              tools=tools, messages=messages)
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                answer = "".join(b.text for b in response.content if b.type == "text")
                log.append(f"## Agent\n\n{answer}\n")
                return answer
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"-> {block.name}({json.dumps(block.input)[:200]})")
                if gfp.handles(block.name):
                    output = await gfp.call(block.name, block.input)
                else:
                    output = call_tool(block.name, block.input)
                log.append(f"### Tool call: `{block.name}`\n\n```json\n{json.dumps(block.input, indent=2)}\n```\n\n"
                           f"Result:\n\n```json\n{output[:4000]}\n```\n")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            messages.append({"role": "user", "content": results})
    finally:
        Path("out").mkdir(exist_ok=True)
        Path("out/transcript.md").write_text("\n".join(log))
        await gfp.close()


if __name__ == "__main__":
    print(asyncio.run(run(" ".join(sys.argv[1:]) or SAMPLE)))
    print("\nSaved the full run to out/transcript.md")
