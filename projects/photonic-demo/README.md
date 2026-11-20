# Ring resonator and MZI in gdsfactory

Two silicon-photonics test structures built with [gdsfactory](https://github.com/gdsfactory/gdsfactory):

- an all-pass ring resonator (R = 10 µm, 200 nm gap)
- an unbalanced Mach-Zehnder interferometer (ΔL = 40 µm)

`photonic_demo.py` writes both to GDSII (`ring_single.gds`, `mzi.gds`), renders the layouts, and plots
transmission from compact analytic models for a 500 × 220 nm Si strip at 1550 nm
(n_eff 2.44, n_g 4.18, 2 dB/cm loss).

| Result | Value |
| --- | --- |
| Ring FSR | 8.1 nm |
| Ring loaded Q (near critical coupling) | ≈ 1.6 × 10⁵ |
| MZI FSR | 14.4 nm |

```bash
pip install gdsfactory matplotlib
python photonic_demo.py
```

`simulate_mzi_sax.py` checks the MZI against a [sax](https://github.com/flaport/sax) circuit simulation of the netlist gdsfactory extracts from the layout itself: simulated FSR 14.36 nm vs 14.37 nm analytic.
