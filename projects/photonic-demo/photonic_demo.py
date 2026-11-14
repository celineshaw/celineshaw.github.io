"""Ring resonator and Mach-Zehnder interferometer, laid out with gdsfactory.

Builds two silicon-photonic test structures, writes them to GDS, renders the
layouts, and plots their transmission spectra from compact analytic models.

Run:  python photonic_demo.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gdsfactory as gf

gf.gpdk.PDK.activate()

# ---- Waveguide model: 500 nm x 220 nm Si strip at 1550 nm (typical values)
LAMBDA0 = 1.55          # um
N_EFF = 2.44            # effective index at LAMBDA0
N_G = 4.18              # group index
DNDL = (N_EFF - N_G) / LAMBDA0   # dn_eff/dlambda from n_g = n_eff - lambda dn/dlambda
LOSS_DB_CM = 2.0        # propagation loss


def n_eff(lam):
    return N_EFF + DNDL * (lam - LAMBDA0)


def amplitude(length_um):
    alpha = LOSS_DB_CM / 4.343 / 1e4      # power loss per um
    return np.exp(-alpha * length_um / 2)


# ---- Layout 1: all-pass ring resonator
RADIUS = 10.0
GAP = 0.2
ring = gf.components.ring_single(gap=GAP, radius=RADIUS, length_x=4.0)
ring.write_gds("ring_single.gds")

# ---- Layout 2: unbalanced Mach-Zehnder interferometer
DELTA_L = 40.0
mzi = gf.components.mzi(delta_length=DELTA_L)
mzi.write_gds("mzi.gds")

for comp, name in [(ring, "ring_layout.png"), (mzi, "mzi_layout.png")]:
    fig = comp.plot(return_fig=True) if "return_fig" in comp.plot.__code__.co_varnames else None
    if fig is None:
        comp.plot()
        fig = plt.gcf()
    fig.savefig(name, dpi=220, bbox_inches="tight")
    plt.close("all")

# ---- Compact models
lam = np.linspace(1.53, 1.57, 200001)

ring_len = 2 * np.pi * RADIUS + 2 * 4.0        # circumference incl. straight sections
r = 0.998                                     # self-coupling, assumed near critical coupling
a = amplitude(ring_len)
phi = 2 * np.pi * n_eff(lam) * ring_len / lam
T_ring = (a**2 - 2 * r * a * np.cos(phi) + r**2) / (1 - 2 * a * r * np.cos(phi) + (r * a) ** 2)
fsr_ring = LAMBDA0**2 / (N_G * ring_len) * 1e3          # nm

dphi = 2 * np.pi * n_eff(lam) * DELTA_L / lam
T_mzi = np.cos(dphi / 2) ** 2
# loaded Q from the resonance nearest 1550 nm
i0 = np.argmin(np.where(np.abs(lam - LAMBDA0) < fsr_ring / 2e3, T_ring, 2))
half = (1 + T_ring[i0]) / 2
j = i0
while T_ring[j] < half: j += 1
k = i0
while T_ring[k] < half: k -= 1
q_loaded = lam[i0] / (lam[j] - lam[k])

fsr_mzi = LAMBDA0**2 / (N_G * DELTA_L) * 1e3

fig, ax = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
ax[0].plot(lam * 1e3, 10 * np.log10(T_ring + 1e-6), lw=1.2)
ax[0].set_ylabel("Ring thru (dB)")
ax[0].set_title(f"Ring R = {RADIUS:g} um: FSR ≈ {fsr_ring:.1f} nm, loaded Q ≈ {q_loaded:,.0f}   |   MZI ΔL = {DELTA_L:g} um: FSR ≈ {fsr_mzi:.1f} nm")
ax[1].plot(lam * 1e3, 10 * np.log10(T_mzi + 1e-6), lw=1.2, color="C3")
ax[1].set_ylabel("MZI out (dB)")
ax[1].set_xlabel("Wavelength (nm)")
for a_ in ax:
    a_.set_ylim(-30, 1)
    a_.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("spectra.png", dpi=200)

print(f"ring FSR {fsr_ring:.2f} nm, loaded Q {q_loaded:,.0f}, extinction {-10*np.log10(T_ring[i0]):.1f} dB, MZI FSR {fsr_mzi:.2f} nm")
print("ring ports:", [p.name for p in ring.ports], " mzi ports:", [p.name for p in mzi.ports])
