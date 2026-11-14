# Design summary for a WDM demux team

Platform: 220 nm SOI, 500 nm strip waveguide, C-band (n_g = 4.18).

## All-pass ring resonator
- **radius_um**: 18.3
- **gap_um**: 0.2
- **fsr_nm**: 5.0
- **intrinsic_q_estimate**: 368000
- **footprint_um**: [42.6, 38.4]
- **ports**: ['o2', 'o1']
- **gds**: out/ring_R18.3um.gds

## Unbalanced mach-zehnder interferometer
- **delta_length_um**: 28.74
- **fsr_nm**: 20.0
- **footprint_um**: [91.1, 60.1]
- **ports**: ['o1', 'o2']
- **gds**: out/mzi_dL28.74um.gds

## Notes
Ring sized for 5 nm channel spacing; MZI interleaves every other channel.

Next step: run these on your foundry PDK in GDSFactory+ for DRC and circuit simulation.