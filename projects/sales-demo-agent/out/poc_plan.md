# Proof of concept: a WDM demux team x GDSFactory+

**Why now:** Layouts are stitched together in KLayout and Python scripts, and DRC errors are fixed by hand before every tape-out.

**Trial:** 30 days, Nov 19 to Dec 19

## Success criteria (agreed before the trial starts)
1. Port the 4-channel demux onto the Cornerstone Si220 PDK in GDSFactory+
2. Pass foundry DRC with 0 errors
3. Simulated drop-port spectra match the channel plan within 0.5 nm
4. One designer reproduces the flow from the shared workspace without help

## Milestones
- Week 1: port the reference design onto the customer's foundry PDK; first DRC run
- Week 2: close DRC to zero; circuit simulation against measured or expected spectra
- Week 3: hand-off session with the CAD/PDK owner (version control, PDK update path)
- Week 4: results review with the engineering lead

## If the criteria are met
Move forward with a 5-seat GDSFactory+ license, with PDK updates and support included.
