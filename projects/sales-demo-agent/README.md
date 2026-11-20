# Solutions-engineering agent for GDSFactory+

A prototype of how I'd run a technical sales motion with an AI agent: a customer
describes their problem in plain language, and the agent turns it into a design on a
**real foundry PDK**, routes it, rule-checks it, and writes the two documents a deal
actually moves on: a technical spec sheet and a **proof-of-concept plan with success
criteria agreed up front**.

## The flow

```
customer request (plain language)
  -> plan_wdm_demux        channel plan -> ring FSR, radii, interleaver (design rules in code)
  -> build_foundry_demux   Cornerstone Si220 PDK cells (ring_double, grating couplers),
                           routed to a fiber-coupler row at 127 um pitch -> GDS
  -> run_rule_checks       KLayout DRC engine: spacing, width, crossed routes
  -> gfp_check_drc         foundry sign-off DRC in GDSFactory+ (via gfp-mcp, when running)
  -> write_spec_sheet      results + 3 discovery questions about the customer's workflow
  -> write_poc_plan        30-day trial, measurable success criteria, commercial next step
```

## Sample run (tools only, no API key)

Request: *4-channel WDM demux, 3.2 nm (400 GHz) spacing at 1550 nm, on Cornerstone's
220 nm SOI process, from a team that stitches layouts in KLayout and fixes DRC by hand.*

| Step | Result |
| --- | --- |
| Channel band | 12.8 nm, so each drop ring needs FSR ≥ 14.08 nm |
| Ring radii | 6.466, 6.489, 6.513, 6.536 µm (23.4 nm steps) |
| Layout | 4 PDK `ring_double` cells + 6 grating couplers, 636 × 508 µm |
| Rule checks, PDK gap (270 nm) | **0 violations** |
| Rule checks, generic gap (200 nm) | **128 spacing violations**, caught before tape-out |

Outputs: `out/demux_4ch_gap270nm.gds`, `out/spec_sheet.md`, `out/poc_plan.md`.

## GDSFactory+ integration

`gfp_bridge.py` starts GDSFactory+'s MCP server (`gfp-mcp-serve`), discovers its tools
(`list_cells`, `build_cells`, `check_drc`, `check_lvs`, `simulate_component`, and more)
and gives them to the agent with a `gfp_` prefix. With a GDSFactory+ project open in VS
Code or a GDSFactory+ Cloud workspace, the agent runs foundry sign-off DRC on the same
design. Without one, it runs with its local tools.

Note: `gfp-mcp` 0.4.1 fails to start with `mcp` 2.x (`'Server' object has no attribute
'list_tools'`), so `requirements.txt` pins `mcp<2`.

## Run it

```bash
pip install -r requirements.txt
python run_tools_demo.py              # full tool chain, no API key needed

export ANTHROPIC_API_KEY=...          # your own key; never commit it
python agent.py                       # the agent on the sample request
python agent.py "your customer's request"
```

Each agent run saves `out/transcript.md`: the request, every tool call and result, and
the final answer.

## What's approximate

Ring radii use n_g = 4.2 and n_eff = 2.4 for the PDK strip waveguide; in GDSFactory+ I'd
take these from the PDK's mode solver. The local rule checks use values from the PDK's
tech file (270 nm coupling gap) and are pre-checks, not foundry sign-off.
