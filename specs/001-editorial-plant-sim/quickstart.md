# Quickstart: Simulación de Planta Editorial Industrial

## Prerequisites

- Python 3.11+
- `pip` or `uv`

## Installation

```bash
# Clone and enter the project
cd /path/to/Simulacion

# Install with pip (editable)
pip install -e ".[dev]"

# Or with uv
uv sync
```

## Run a simulation

```bash
# Run with default config and a fixed seed
python -m sim run --config config/default.yaml --seed 42

# Run with event trace enabled
python -m sim run --config config/default.yaml --seed 42 --trace

# Output to a specific directory
python -m sim run --config config/default.yaml --seed 42 --output-dir results/baseline/
```

## Compare sequencing policies

```bash
python -m sim compare \
  --configs config/fifo.yaml config/priority.yaml config/booktype.yaml \
  --seed 42 \
  --output-dir results/policy-comparison/
```

## Validate a config file

```bash
python -m sim validate --config config/default.yaml
# Output: "Configuration valid." or a list of errors
```

## Run tests

```bash
pytest                    # all tests
pytest tests/unit/        # unit tests only
pytest tests/scenario/    # full scenario tests
pytest -k "test_seed"     # run a specific test
```

## Expected output (results.json excerpt)

```json
{
  "metrics": {
    "TPPT": 45.2,
    "TPPL": 4.3,
    "PR": 0.048,
    "TSP": [3.1, 2.4, 0.8, 1.2, 0.0]
  },
  "bottleneck": "printing"
}
```

## Validation checklist (run after each simulation)

- [ ] `results.json` exists in output directory
- [ ] All 11 metrics present and non-null
- [ ] Same seed + same config → identical results on re-run
- [ ] `PR` value is close to configured `defect_probability` (within ±10%)
- [ ] `TSP` values sum to less than total simulation time per machine
- [ ] Timestamps in `trace.jsonl` are monotonically increasing (if `--trace` used)
