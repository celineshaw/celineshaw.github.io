# Sales demo agent

A prototype of the tool I'd like to build for technical sales: a customer describes what they need in plain
language, and an AI agent turns it into real gdsfactory layouts plus a spec sheet they can take away.

- `design_tools.py`: the engineering. Sizes a ring resonator or MZI for a target FSR, writes GDS, renders the layout, writes a spec sheet.
- `agent.py`: the agent. A Claude tool-use loop that reads the request, calls the tools, and explains the result. Needs `ANTHROPIC_API_KEY`.
- `run_tools_demo.py`: runs the same tools directly for one sample request, no API key needed. Outputs are in `out/`.

Sample request: *"We're building a 4-channel WDM demux. We need a ring filter with about 5 nm FSR at 1550 nm, and an MZI with 20 nm FSR."*

| Tool output | Value |
| --- | --- |
| Ring radius for 5 nm FSR | 18.3 µm |
| Ring intrinsic Q (2 dB/cm) | ≈ 3.7 × 10⁵ |
| MZI path difference for 20 nm FSR | 28.74 µm |

```bash
pip install gdsfactory matplotlib anthropic
python run_tools_demo.py                 # tools only
python agent.py "your customer request"  # full agent
```
