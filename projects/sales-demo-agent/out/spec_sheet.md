# Design summary for a WDM demux team

PDK: Cornerstone Si220 C-band (cspdk)

## Channel plan
- 4 channels x 3.2 nm = 12.8 nm band at 1550 nm
- ring FSR 14.08 nm > band 12.8 nm, so each ring drops exactly one channel
- MZI FSR = 2 x 3.2 nm = 6.4 nm

## Layout
- Ring radii: 6.466, 6.489, 6.513, 6.536 um (step 23.4 nm)
- Coupling gap: 0.27 um
- 6 grating couplers at 127 um fiber-array pitch
- Footprint: 636.0 x 508.0 um
- GDS: out/demux_4ch_gap270nm.gds

## Verification
- WG.S spacing < 0.27 um: 0
- WG.W width < 0.15 um: 0
- WG.X crossed or overlapping routes: 0
- Result: PASS, 0 violations

## Assumptions
- n_g = 4.2, n_eff = 2.4 for the PDK strip waveguide; confirm with the PDK's mode solver in GDSFactory+.

## Questions for your team
- How many engineer-hours per tape-out go into fixing DRC errors by hand today?
- When Cornerstone updates a PDK layer, who updates your scripts, and how long does it take?
- What did your last respin cost, in money and in schedule?
