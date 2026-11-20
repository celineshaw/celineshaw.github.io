"""Circuit simulation of the gdsfactory MZI with sax.

Takes the netlist straight from the gdsfactory layout (every bend, straight and
splitter as placed) and simulates it, instead of using a hand-written formula.

Run:  pip install gdsfactory sax matplotlib && python simulate_mzi_sax.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gdsfactory as gf
import sax

gf.gpdk.PDK.activate()
NEFF, NG, LOSS = 2.44, 4.18, 2.0          # 500 x 220 nm Si strip near 1550 nm; dB/cm

mzi = gf.components.mzi(delta_length=40)
netlist = mzi.get_netlist()
bend_len = gf.components.bend_euler().info["length"]


def renamed(sdict, mapping):
    """Map sax's port names (in0, out0, ...) onto gdsfactory's (o1, o2, ...)."""
    return {(mapping[a], mapping[b]): v for (a, b), v in sdict.items()}


def wg(wl=1.55, length=10.0, **_):
    s = sax.models.straight(wl=wl, neff=NEFF, ng=NG, length=length, loss_dB_cm=LOSS)
    return renamed(s, {"in0": "o1", "out0": "o2"})


def mmi(wl=1.55, **_):
    return renamed(sax.models.mmi1x2(wl=wl), {"in0": "o1", "out0": "o2", "out1": "o3"})


models = {
    "straight": wg,
    "bend_euler": lambda wl=1.55, **_: wg(wl=wl, length=bend_len),
    "mmi1x2": mmi,
}
circuit, _ = sax.circuit(netlist=netlist, models=models)

wl = np.linspace(1.53, 1.57, 4001)
T = np.abs(circuit(wl=wl)["o1", "o2"]) ** 2
T_db = 10 * np.log10(T + 1e-9)

mins = wl[1:-1][(T_db[1:-1] < T_db[:-2]) & (T_db[1:-1] < T_db[2:]) & (T_db[1:-1] < -10)]
fsr_nm = float(np.mean(np.diff(mins)) * 1e3) if len(mins) > 1 else float("nan")
print(f"Simulated MZI FSR: {fsr_nm:.2f} nm  (analytic: {1.55**2 / (NG * 40) * 1e3:.2f} nm)")

fig, ax = plt.subplots(figsize=(8, 3.2))
ax.plot(wl * 1e3, T_db, lw=1.3)
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Transmission (dB)"); ax.set_ylim(-40, 1)
ax.set_title(f"sax circuit simulation of the gdsfactory MZI · FSR ≈ {fsr_nm:.1f} nm")
ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig("mzi_sax.png", dpi=200)
np.savetxt("mzi_sax.csv", np.c_[wl * 1e3, T_db], delimiter=",", header="wavelength_nm,transmission_dB", comments="")
