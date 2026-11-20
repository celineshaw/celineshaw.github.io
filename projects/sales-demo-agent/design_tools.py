"""Design and sales tools a solutions-engineering agent can call.

The engineering lives here, in tested code, so the agent never has to invent a
number. Flow for a customer request:

    plan_wdm_demux      channel plan -> ring and interleaver requirements
    build_foundry_demux requirements -> real foundry PDK cells, routed to a
                        grating-coupler row at fiber-array pitch, written to GDS
    run_rule_checks     KLayout geometry checks on the layout (spacing, width,
                        collisions). Foundry sign-off DRC runs in GDSFactory+
                        through gfp-mcp (see gfp_bridge.py).
    write_spec_sheet    one-page technical summary for the customer
    write_poc_plan      mutual proof-of-concept plan with success criteria
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gdsfactory as gf
import klayout.db as kdb
from cspdk.si220.cband import PDK
from cspdk.si220.cband.tech import LAYER, TECH

PDK.activate()

OUT = Path("out")
OUT.mkdir(exist_ok=True)

PDK_NAME = "Cornerstone Si220 C-band (cspdk)"
N_G, N_EFF = 4.2, 2.4      # approximate 450 x 220 nm strip waveguide indices near 1550 nm
PITCH = 127.0              # standard fiber-array pitch, um
GC_Y = 120.0               # grating-coupler row height above the bus, um


# ---------------------------------------------------------------- planning
def plan_wdm_demux(n_channels: int, channel_spacing_nm: float, wavelength_nm: float = 1550.0) -> dict:
    """Turn a WDM channel plan into ring and interleaver requirements.

    Design rules encoded here:
    - each drop ring must resonate on only one channel, so its FSR must be wider than
      the whole band (n_channels x spacing), plus 10% margin;
    - an odd/even MZI interleaver needs FSR = 2 x channel spacing;
    - rings are tuned onto neighbouring channels with small radius steps.
    """
    lam_um = wavelength_nm / 1e3
    band = n_channels * channel_spacing_nm
    ring_fsr = round(band * 1.1, 2)
    r0 = round(lam_um**2 / (N_G * ring_fsr / 1e3) / (2 * math.pi), 3)
    if r0 < TECH.radius:
        return {"error": f"An FSR of {ring_fsr} nm needs R = {r0} um, below this PDK's {TECH.radius} um minimum bend radius. "
                         "Reduce the channel count or spacing, or consider a different filter topology."}
    dr = r0 * channel_spacing_nm * N_G / (wavelength_nm * N_EFF)   # d(lambda)/lambda = (n_eff/n_g) dL/L
    radii = [round(r0 + i * dr, 3) for i in range(n_channels)]
    interleaver_dl = round(lam_um**2 / (N_G * 2 * channel_spacing_nm / 1e3), 2)
    return {
        "channel_plan": f"{n_channels} channels x {channel_spacing_nm} nm = {band:g} nm band at {wavelength_nm:g} nm",
        "ring_fsr_target_nm": ring_fsr,
        "ring_rule": f"ring FSR {ring_fsr} nm > band {band:g} nm, so each ring drops exactly one channel",
        "ring_radii_um": radii,
        "radius_step_nm": round(dr * 1e3, 1),
        "interleaver_rule": f"MZI FSR = 2 x {channel_spacing_nm} nm = {2 * channel_spacing_nm:g} nm",
        "interleaver_delta_length_um": interleaver_dl,
        "assumptions": f"n_g = {N_G}, n_eff = {N_EFF} for the PDK strip waveguide; confirm with the PDK's mode solver in GDSFactory+.",
    }


# ---------------------------------------------------------------- layout on a foundry PDK
@gf.cell
def demux_chip(radii: tuple[float, ...] = (6.5,), gap: float = TECH.gap_strip) -> gf.Component:
    """PDK ring_double cells on a shared bus, every port routed to a grating coupler."""
    c = gf.Component()
    rings = []
    for i, R in enumerate(radii):
        r = c.add_ref(gf.get_component("ring_double", radius=R, gap=gap), name=f"ring{i + 1}")
        r.dmove((i * PITCH, 0))
        rings.append(r)
    for a, b in zip(rings[:-1], rings[1:]):
        gf.routing.route_single(c, a.ports["o2"], b.ports["o1"], cross_section="strip")

    def gc(x: float, name: str):
        g = c.add_ref(gf.get_component("grating_coupler_rectangular"), name=name)
        g.drotate(90)
        g.dmove(g.ports["o1"].dcenter, (x, GC_Y))
        return g

    x0 = rings[0].ports["o1"].dcenter[0]
    targets = [("in", rings[0].ports["o1"], x0 - PITCH + 10 - 30)]
    for i, r in enumerate(rings):
        targets.append((f"drop{i + 1}", r.ports["o3"], r.ports["o3"].dcenter[0] - 30))
    targets.append(("thru", rings[-1].ports["o2"], rings[-1].ports["o2"].dcenter[0] + PITCH - 50))
    for name, port, x in targets:
        g = gc(x, f"gc_{name}")
        gf.routing.route_single(c, port, g.ports["o1"], cross_section="strip")
    return c


def build_foundry_demux(n_channels: int, channel_spacing_nm: float, gap_um: float | None = None) -> dict:
    """Plan the demux, then lay it out with real foundry PDK cells and route it to fiber couplers."""
    plan = plan_wdm_demux(n_channels, channel_spacing_nm)
    if "error" in plan:
        return plan
    gap = TECH.gap_strip if gap_um is None else gap_um
    chip = demux_chip(radii=tuple(plan["ring_radii_um"]), gap=gap)
    name = f"demux_{n_channels}ch_gap{int(round(gap * 1000))}nm"
    gds = OUT / f"{name}.gds"
    chip.write_gds(gds)
    chip.plot()
    plt.gcf().set_size_inches(10, 8)
    png = OUT / f"{name}.png"
    plt.savefig(png, dpi=120, bbox_inches="tight")
    plt.close("all")
    x0, y0, x1, y1 = (float(v) for v in chip.bbox_np().flatten())
    return {
        "pdk": PDK_NAME,
        "cells_used": ["ring_double", "grating_coupler_rectangular", "strip routes (bend_euler, straight)"],
        "ring_radii_um": plan["ring_radii_um"],
        "coupling_gap_um": gap,
        "fiber_couplers": n_channels + 2,
        "fiber_pitch_um": PITCH,
        "footprint_um": [round(x1 - x0, 1), round(y1 - y0, 1)],
        "gds": str(gds),
        "layout_png": str(png),
    }


# ---------------------------------------------------------------- verification
def run_rule_checks(gds: str, min_space_um: float = TECH.gap_strip, min_width_um: float = 0.15) -> dict:
    """Geometry checks on the PDK waveguide layer with KLayout's DRC engine (Region API).

    WG.S  spacing below the PDK's coupling-gap value
    WG.W  features narrower than min_width_um
    WG.X  waveguides from two different placed instances overlap (crossed routes)
    These are pre-checks; foundry sign-off DRC runs in GDSFactory+ (check_drc via gfp-mcp).
    """
    ly = kdb.Layout()
    ly.read(gds)
    top = ly.top_cell()
    li = ly.layer(*LAYER.WG)
    dbu = ly.dbu
    wg = kdb.Region(top.begin_shapes_rec(li)).merged()
    space = wg.space_check(int(round(min_space_um / dbu)) - 1)
    width = wg.width_check(int(round(min_width_um / dbu)))
    regions = [kdb.Region(kdb.RecursiveShapeIterator(ly, inst.cell, li)).transformed(inst.cplx_trans).merged()
               for inst in top.each_inst()]
    overlaps = 0
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            ov = (regions[i] & regions[j]).merged()
            if ov.area() * dbu * dbu > 0.01:
                overlaps += ov.count()
    checks = {
        f"WG.S spacing < {min_space_um} um": space.count(),
        f"WG.W width < {min_width_um} um": width.count(),
        "WG.X crossed or overlapping routes": overlaps,
    }
    return {"gds": gds, "checks": checks, "violations": sum(checks.values()), "passed": sum(checks.values()) == 0}


# ---------------------------------------------------------------- customer-facing outputs
def write_spec_sheet(customer: str, plan: dict, layout: dict, checks: dict, open_questions: list[str] | None = None) -> dict:
    """One-page technical summary the customer can read after the call."""
    lines = [f"# Design summary for {customer}", "", f"PDK: {layout.get('pdk', PDK_NAME)}", "",
             "## Channel plan", f"- {plan['channel_plan']}", f"- {plan['ring_rule']}", f"- {plan['interleaver_rule']}", "",
             "## Layout",
             f"- Ring radii: {', '.join(str(r) for r in layout['ring_radii_um'])} um (step {plan['radius_step_nm']} nm)",
             f"- Coupling gap: {layout['coupling_gap_um']} um",
             f"- {layout['fiber_couplers']} grating couplers at {layout['fiber_pitch_um']:g} um fiber-array pitch",
             f"- Footprint: {layout['footprint_um'][0]} x {layout['footprint_um'][1]} um", f"- GDS: {layout['gds']}", "",
             "## Verification",
             *[f"- {k}: {v}" for k, v in checks["checks"].items()],
             f"- Result: {'PASS, 0 violations' if checks['passed'] else str(checks['violations']) + ' violations'}", "",
             "## Assumptions", f"- {plan['assumptions']}"]
    if open_questions:
        lines += ["", "## Questions for your team", *[f"- {q}" for q in open_questions]]
    path = OUT / "spec_sheet.md"
    path.write_text("\n".join(lines) + "\n")
    return {"spec_sheet": str(path)}


def write_poc_plan(customer: str, current_pain: str, success_criteria: list[str], trial_days: int = 30, seats: int = 5) -> dict:
    """Mutual proof-of-concept plan: agree up front what 'success' means and what happens next."""
    start = date.today()
    lines = [f"# Proof of concept: {customer} x GDSFactory+", "",
             f"**Why now:** {current_pain}", "",
             f"**Trial:** {trial_days} days, {start:%b %d} to {start + timedelta(days=trial_days):%b %d}", "",
             "## Success criteria (agreed before the trial starts)",
             *[f"{i + 1}. {c}" for i, c in enumerate(success_criteria)], "",
             "## Milestones",
             f"- Week 1: port the reference design onto the customer's foundry PDK; first DRC run",
             f"- Week 2: close DRC to zero; circuit simulation against measured or expected spectra",
             f"- Week 3: hand-off session with the CAD/PDK owner (version control, PDK update path)",
             f"- Week 4: results review with the engineering lead",
             "", "## If the criteria are met",
             f"Move forward with a {seats}-seat GDSFactory+ license, with PDK updates and support included."]
    path = OUT / "poc_plan.md"
    path.write_text("\n".join(lines) + "\n")
    return {"poc_plan": str(path)}


TOOLS = {
    "plan_wdm_demux": plan_wdm_demux,
    "build_foundry_demux": build_foundry_demux,
    "run_rule_checks": run_rule_checks,
    "write_spec_sheet": write_spec_sheet,
    "write_poc_plan": write_poc_plan,
}

TOOL_SCHEMAS = [
    {"name": "plan_wdm_demux",
     "description": "Turn a WDM channel plan (channel count and spacing) into ring and interleaver requirements. Use this whenever a customer describes channels rather than an FSR.",
     "input_schema": {"type": "object", "properties": {
         "n_channels": {"type": "integer"}, "channel_spacing_nm": {"type": "number"}, "wavelength_nm": {"type": "number"}},
         "required": ["n_channels", "channel_spacing_nm"]}},
    {"name": "build_foundry_demux",
     "description": "Lay out the demux on the Cornerstone Si220 foundry PDK: PDK ring_double cells on a shared bus, every port routed to grating couplers at 127 um fiber-array pitch. Returns radii, footprint and GDS path.",
     "input_schema": {"type": "object", "properties": {
         "n_channels": {"type": "integer"}, "channel_spacing_nm": {"type": "number"},
         "gap_um": {"type": "number", "description": "Ring coupling gap; defaults to the PDK value"}},
         "required": ["n_channels", "channel_spacing_nm"]}},
    {"name": "run_rule_checks",
     "description": "Run geometry rule checks (spacing, width, crossed routes) on a GDS file. Report the result honestly; foundry sign-off DRC is a separate GDSFactory+ step.",
     "input_schema": {"type": "object", "properties": {"gds": {"type": "string"}}, "required": ["gds"]}},
    {"name": "write_spec_sheet",
     "description": "Write the customer-facing technical summary. Pass the outputs of plan_wdm_demux, build_foundry_demux and run_rule_checks, plus open questions for the customer.",
     "input_schema": {"type": "object", "properties": {
         "customer": {"type": "string"}, "plan": {"type": "object"}, "layout": {"type": "object"}, "checks": {"type": "object"},
         "open_questions": {"type": "array", "items": {"type": "string"}}},
         "required": ["customer", "plan", "layout", "checks"]}},
    {"name": "write_poc_plan",
     "description": "Write a mutual proof-of-concept plan with measurable success criteria agreed before the trial, and the commercial next step if they are met.",
     "input_schema": {"type": "object", "properties": {
         "customer": {"type": "string"}, "current_pain": {"type": "string"},
         "success_criteria": {"type": "array", "items": {"type": "string"}},
         "trial_days": {"type": "integer"}, "seats": {"type": "integer"}},
         "required": ["customer", "current_pain", "success_criteria"]}},
]


def call_tool(name: str, args: dict) -> str:
    return json.dumps(TOOLS[name](**args))
