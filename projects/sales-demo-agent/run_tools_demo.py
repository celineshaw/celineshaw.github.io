"""Run the full tool chain directly, without the language model, for the sample request.

Sample request: a 4-channel WDM demux with 3.2 nm (400 GHz) spacing at 1550 nm on
Cornerstone's 220 nm SOI process, from a team that fixes DRC errors by hand.

Also builds the same demux with a generic 200 nm coupling gap, to show the rule
check catching it.
"""
import json
from design_tools import build_foundry_demux, plan_wdm_demux, run_rule_checks, write_poc_plan, write_spec_sheet

plan = plan_wdm_demux(n_channels=4, channel_spacing_nm=3.2)
layout = build_foundry_demux(n_channels=4, channel_spacing_nm=3.2)
checks = run_rule_checks(layout["gds"])

generic = build_foundry_demux(n_channels=4, channel_spacing_nm=3.2, gap_um=0.20)
generic_checks = run_rule_checks(generic["gds"])

write_spec_sheet("a WDM demux team", plan, layout, checks, open_questions=[
    "How many engineer-hours per tape-out go into fixing DRC errors by hand today?",
    "When Cornerstone updates a PDK layer, who updates your scripts, and how long does it take?",
    "What did your last respin cost, in money and in schedule?",
])
write_poc_plan(
    "a WDM demux team",
    current_pain="Layouts are stitched together in KLayout and Python scripts, and DRC errors are fixed by hand before every tape-out.",
    success_criteria=[
        "Port the 4-channel demux onto the Cornerstone Si220 PDK in GDSFactory+",
        "Pass foundry DRC with 0 errors",
        "Simulated drop-port spectra match the channel plan within 0.5 nm",
        "One designer reproduces the flow from the shared workspace without help",
    ],
)
print(json.dumps({"plan": plan, "layout": layout, "rule_checks": checks,
                  "generic_gap_rule_checks": generic_checks}, indent=2))
