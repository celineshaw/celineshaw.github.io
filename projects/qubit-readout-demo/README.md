# Frequency-multiplexed qubit readout on GDSFactory's quantum PDK

Four readout resonators share one probe line, each tuned to its own frequency: the microwave version of a WDM demux.

`qubit_readout_demo.py` uses [qpdk](https://gdsfactory.github.io/quantum-rf-pdk/), GDSFactory's superconducting PDK, to:

1. simulate a quarter-wave CPW resonator coupled to a probe line with the PDK's S-parameter model (sax/JAX),
2. solve (by bisection) for the resonator length that lands on each target frequency,
3. resolve each resonance's depth, linewidth and loaded Q,
4. lay out a transmon qubit with its readout resonator and probe line, and write the GDS.

| Target | Length | Simulated f₀ | Linewidth | Loaded Q |
| --- | --- | --- | --- | --- |
| 6.8 GHz | 4,462 µm | 6.7999 GHz | 111 kHz | 61,500 |
| 7.0 GHz | 4,334 µm | 6.9999 GHz | 120 kHz | 58,500 |
| 7.2 GHz | 4,214 µm | 7.2000 GHz | 129 kHz | 55,800 |
| 7.4 GHz | 4,099 µm | 7.3999 GHz | 139 kHz | 53,200 |

```bash
pip install qpdk polars matplotlib
python qubit_readout_demo.py      # about a minute
```
