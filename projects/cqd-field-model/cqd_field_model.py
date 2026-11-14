"""Coupled quantum dots as neural electric-field sensors: first-order estimate.

Python version of the 2021 feasibility calculation done with the Quantum Matters
Group at UC Merced (NASA-funded, MACES). Compares the field of a single firing
neuron with the smallest field a coupled-quantum-dot (CQD) pair can resolve
through the quantum-confined Stark effect.

Run:  python cqd_field_model.py
"""
import numpy as np

EPS0 = 8.854e-12        # F/m
E_CHARGE = 1.602e-19    # C

# --- Neuron as a line charge (Gauss's law)
I_NEURON = 1e-9         # A, current during an action potential
T_AP = 5e-3             # s, action-potential duration
L_AXON = 0.1            # m, modeled segment length
Q = I_NEURON * T_AP     # C
lam = Q / L_AXON        # C/m


def neuron_field_kv_cm(r_m):
    """Field of an infinite line charge at distance r, in kV/cm."""
    return lam / (2 * np.pi * EPS0 * r_m) / 1e5


# --- CQD sensor
D_DOTS = 10e-9                          # m, electron-hole separation (indirect exciton)
P_DIPOLE = E_CHARGE * D_DOTS            # C m  (10 e nm)
SHIFT_MEV_PER_KVCM = P_DIPOLE * 1e5 / E_CHARGE * 1e3   # Stark slope, meV per kV/cm
DELTA_E_MEV = 1.7e-3                    # meV, assumed resolvable PL energy shift (1.7 ueV)
SENSITIVITY_KV_CM = DELTA_E_MEV / SHIFT_MEV_PER_KVCM


def two_level_energies(F_kv_cm, e_direct=1300.0, F0=20.0, t=3.0):
    """Eigenvalues of h = [[e_h, -t], [-t, e_h + F d]] around an anticrossing (meV)."""
    e_ind = e_direct - SHIFT_MEV_PER_KVCM * (F_kv_cm - F0)
    mean = (e_direct + e_ind) / 2
    half = np.sqrt(((e_direct - e_ind) / 2) ** 2 + t**2)
    return mean - half, mean + half


if __name__ == "__main__":
    r = 4e-3
    print(f"Charge per action potential  Q   = {Q:.2e} C")
    print(f"Line charge density          lam = {lam:.2e} C/m")
    print(f"Neuron field at r = 4 mm         = {neuron_field_kv_cm(r):.2e} kV/cm")
    print(f"Dipole moment                p   = {P_DIPOLE:.2e} C m  (10 e nm)")
    print(f"Stark slope                      = {SHIFT_MEV_PER_KVCM:.2f} meV per kV/cm")
    print(f"CQD field resolution         dF  = {SENSITIVITY_KV_CM:.2e} kV/cm")
    r_max = lam / (2 * np.pi * EPS0 * SENSITIVITY_KV_CM * 1e5)
    print(f"Detectable out to                = {r_max * 1e3:.1f} mm (best case, vacuum, no tissue screening)")
