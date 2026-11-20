"""Frequency-multiplexed qubit readout on GDSFactory's superconducting quantum PDK (qpdk).

1. Simulate a quarter-wave CPW resonator coupled to a probeline with the PDK's
   S-parameter model (sax/JAX), and solve for the length that lands each
   resonator on its target readout frequency.
2. Resolve each resonance's depth, linewidth and loaded Q.
3. Lay out a transmon qubit with its readout resonator and probeline.

Run:  pip install qpdk polars matplotlib && python qubit_readout_demo.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qpdk import PDK
PDK.activate()
resonator_model = PDK.models["quarter_wave_resonator_coupled"]

OUT = Path("out")
OUT.mkdir(exist_ok=True)


def s21(f_hz, length_um, gap_um=20.0):
    s = resonator_model(f=f_hz, length=length_um, coupling_gap=gap_um)
    key = next(k for k in s if k[0] != k[1])          # the probeline through-path
    return np.asarray(s[key])


def resonance_ghz(length_um, f_lo=3e9, f_hi=12e9, n=40001):
    f = np.linspace(f_lo, f_hi, n)
    return f[np.argmin(np.abs(s21(f, length_um)))] / 1e9


def length_for(f_target_ghz, lo=2500.0, hi=9000.0):
    """Bisection on length: longer resonator -> lower frequency."""
    for _ in range(40):
        mid = (lo + hi) / 2
        if resonance_ghz(mid) > f_target_ghz:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 1)


targets = [6.8, 7.0, 7.2, 7.4]                       # GHz, one readout tone per qubit
plan = []
for ft in targets:
    L = length_for(ft)
    plan.append({"target_GHz": ft, "length_um": L, "simulated_GHz": round(resonance_ghz(L), 4)})

# --- Resolve each resonance: depth, linewidth and loaded Q
for p in plan:
    f0 = p["simulated_GHz"] * 1e9
    for span in (20e6, 2e6):                          # coarse, then fine
        f = np.linspace(f0 - span, f0 + span, 40001)
        mag = np.abs(s21(f, p["length_um"]))
        f0 = f[np.argmin(mag)]
    half = np.sqrt((1 + mag.min() ** 2) / 2)          # half-power level
    below = np.where(mag < half)[0]
    fwhm = f[below[-1]] - f[below[0]]
    p.update(f0_GHz=round(f0 / 1e9, 5), depth_dB=round(20 * np.log10(mag.min()), 1),
             linewidth_kHz=round(fwhm / 1e3, 1), loaded_Q=int(round(f0 / fwhm, -2)))

# --- S21 of the four readout resonators (dense sampling around each dip)
f = np.concatenate([np.linspace(6.6e9, 7.6e9, 4001)] +
                   [np.linspace(p["f0_GHz"] * 1e9 - 1e6, p["f0_GHz"] * 1e9 + 1e6, 2001) for p in plan])
f.sort()
fig, ax = plt.subplots(figsize=(8, 3.6))
for p in plan:
    ax.plot(f / 1e9, 20 * np.log10(np.abs(s21(f, p["length_um"])) + 1e-12), lw=1.3,
            label=f'{p["target_GHz"]} GHz · L = {p["length_um"]:.0f} µm · Q ≈ {p["loaded_Q"]:,}')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("|S21| (dB)")
ax.legend(fontsize=8, frameon=False, loc="lower left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "readout_s21.png", dpi=200)
plt.close(fig)

# --- Layout: transmon + readout resonator + probeline, at the first channel's length
L0 = plan[0]["length_um"]
chip = PDK.cells["transmon_with_resonator_and_probeline"](resonator_length=L0)
chip.write_gds(OUT / "transmon_readout.gds")

(OUT / "readout_plan.json").write_text(json.dumps(plan, indent=2))
print(json.dumps(plan, indent=2))
