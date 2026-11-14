# Coupled quantum dots as neural electric-field sensors

First-order feasibility model from research with the Quantum Matters Group at UC Merced (NASA-funded, MACES), 2021.

It compares the field of a single firing neuron, modeled as a line charge, with the smallest field a coupled InAs
quantum-dot pair can resolve through the quantum-confined Stark effect.

| Quantity | Value |
| --- | --- |
| Neuron field at 4 mm | 2.2 × 10⁻³ kV/cm |
| CQD field resolution (10 e·nm dipole, 1.7 µeV resolvable shift) | 1.7 × 10⁻³ kV/cm |
| Detectable out to | ≈ 5.3 mm |

```bash
python cqd_field_model.py
```

This is a best-case bound: it ignores tissue screening, skull attenuation and spectral diffusion.
