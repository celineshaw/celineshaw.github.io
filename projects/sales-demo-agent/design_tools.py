"""Design tools a technical-sales agent can call.

Each function turns a customer's spec into a real gdsfactory layout plus the
numbers a customer cares about. The agent (agent.py) decides which tool to call;
these functions do the engineering.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gdsfactory as gf

gf.gpdk.PDK.activate()

OUT = Path("out")
OUT.mkdir(exist_ok=True)

# 500 nm x 220 nm Si strip waveguide near 1550 nm (typical values)
N_G = 4.18
LOSS_DB_CM = 2.0


def _save_png(component, name: str) -> str:
    component.plot()
    path = OUT / f"{name}.png"
    plt.gcf().savefig(path, dpi=200, bbox_inches="tight")
    plt.close("all")
    return str(path)


def design_ring(target_fsr_nm: float, wavelength_nm: float = 1550.0, gap_um: float = 0.2) -> dict:
    """Size an all-pass ring for a target free spectral range and lay it out."""
    lam_um = wavelength_nm / 1e3
    length_um = lam_um**2 / (N_G * target_fsr_nm / 1e3)        # FSR = lambda^2 / (n_g L)
    radius = round(length_um / (2 * math.pi), 2)
    if radius < 5:
        return {"error": f"A {target_fsr_nm} nm FSR needs R = {radius} um, below the ~5 um bend limit of this platform."}
    ring = gf.components.ring_single(radius=radius, gap=gap_um, length_x=0)
    name = f"ring_R{radius:g}um"
    gds = OUT / f"{name}.gds"
    ring.write_gds(gds)
    actual_fsr = lam_um**2 / (N_G * 2 * math.pi * radius) * 1e3
    alpha = LOSS_DB_CM / 4.343 / 1e4
    q_intrinsic = 2 * math.pi * N_G / (lam_um * alpha)
    xmin, ymin, xmax, ymax = ring.bbox_np().flatten()
    return {
        "device": "all-pass ring resonator",
        "radius_um": radius,
        "gap_um": gap_um,
        "fsr_nm": round(actual_fsr, 2),
        "intrinsic_q_estimate": int(round(q_intrinsic, -3)),
        "footprint_um": [round(float(xmax - xmin), 1), round(float(ymax - ymin), 1)],
        "ports": [p.name for p in ring.ports],
        "gds": str(gds),
        "layout_png": _save_png(ring, name),
    }


def design_mzi(target_fsr_nm: float, wavelength_nm: float = 1550.0) -> dict:
    """Size an unbalanced MZI for a target free spectral range and lay it out."""
    lam_um = wavelength_nm / 1e3
    delta_l = round(lam_um**2 / (N_G * target_fsr_nm / 1e3), 2)
    mzi = gf.components.mzi(delta_length=delta_l)
    name = f"mzi_dL{delta_l:g}um"
    gds = OUT / f"{name}.gds"
    mzi.write_gds(gds)
    xmin, ymin, xmax, ymax = mzi.bbox_np().flatten()
    return {
        "device": "unbalanced Mach-Zehnder interferometer",
        "delta_length_um": delta_l,
        "fsr_nm": round(lam_um**2 / (N_G * delta_l) * 1e3, 2),
        "footprint_um": [round(float(xmax - xmin), 1), round(float(ymax - ymin), 1)],
        "ports": [p.name for p in mzi.ports],
        "gds": str(gds),
        "layout_png": _save_png(mzi, name),
    }


def write_spec_sheet(customer: str, designs: list[dict], notes: str = "") -> dict:
    """Write a one-page summary the customer can read after the call."""
    lines = [f"# Design summary for {customer}", "", "Platform: 220 nm SOI, 500 nm strip waveguide, C-band (n_g = 4.18).", ""]
    for d in designs:
        lines.append(f"## {d['device'].capitalize()}")
        for k, v in d.items():
            if k not in ("device", "layout_png"):
                lines.append(f"- **{k}**: {v}")
        lines.append("")
    if notes:
        lines += ["## Notes", notes, ""]
    lines.append("Next step: run these on your foundry PDK in GDSFactory+ for DRC and circuit simulation.")
    path = OUT / "spec_sheet.md"
    path.write_text("\n".join(lines))
    return {"spec_sheet": str(path)}


TOOLS = {"design_ring": design_ring, "design_mzi": design_mzi, "write_spec_sheet": write_spec_sheet}

TOOL_SCHEMAS = [
    {
        "name": "design_ring",
        "description": "Size and lay out an all-pass silicon ring resonator for a target free spectral range. Returns radius, FSR, Q estimate, footprint and the GDS path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_fsr_nm": {"type": "number", "description": "Desired free spectral range in nm"},
                "wavelength_nm": {"type": "number", "description": "Center wavelength in nm, default 1550"},
                "gap_um": {"type": "number", "description": "Bus-to-ring gap in um, default 0.2"},
            },
            "required": ["target_fsr_nm"],
        },
    },
    {
        "name": "design_mzi",
        "description": "Size and lay out an unbalanced Mach-Zehnder interferometer for a target free spectral range. Returns path difference, FSR, footprint and the GDS path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_fsr_nm": {"type": "number"},
                "wavelength_nm": {"type": "number"},
            },
            "required": ["target_fsr_nm"],
        },
    },
    {
        "name": "write_spec_sheet",
        "description": "Write a customer-facing markdown summary of the designs produced in this session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer": {"type": "string"},
                "designs": {"type": "array", "items": {"type": "object"}},
                "notes": {"type": "string"},
            },
            "required": ["customer", "designs"],
        },
    },
]


def call_tool(name: str, args: dict) -> str:
    return json.dumps(TOOLS[name](**args))
