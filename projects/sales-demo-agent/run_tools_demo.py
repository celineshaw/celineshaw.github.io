"""Run the design tools directly, without the language model, for one sample request.

Sample request: "We're building a 4-channel WDM demux. We need a ring filter with
about 5 nm FSR at 1550 nm, and an MZI with 20 nm FSR to interleave channels."
"""
import json
from design_tools import design_ring, design_mzi, write_spec_sheet

ring = design_ring(target_fsr_nm=5.0)
mzi = design_mzi(target_fsr_nm=20.0)
sheet = write_spec_sheet("a WDM demux team", [ring, mzi], notes="Ring sized for 5 nm channel spacing; MZI interleaves every other channel.")
print(json.dumps({"ring": ring, "mzi": mzi, **sheet}, indent=2))
