# CLI Contract: sim

The simulation is invoked as a Python module from the command line.

## Command Structure

```
python -m sim <subcommand> [options]
```

### Subcommands

#### `run` — Execute a simulation

```
python -m sim run --config <path> [--seed <int>] [--output-dir <path>]
                  [--trace] [--format {json,csv,both}]
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `--config` | Yes | — | Path to YAML configuration file |
| `--seed` | No | random int | Master PRNG seed for reproducibility |
| `--output-dir` | No | `./results/` | Directory for output files |
| `--trace` | No | false | Enable full event log output |
| `--format` | No | `json` | Output format: `json`, `csv`, or `both` |

**Exit codes**:
- `0` — simulation completed successfully
- `1` — configuration validation error (printed to stderr)
- `2` — runtime error (printed to stderr with traceback)

**Stdout**: progress indicators (one line per N events, configurable)

**Stderr**: errors and warnings only

**Output files** (written to `--output-dir`):
- `results.json` — full metrics report
- `results.csv` — flat metrics (when `--format csv` or `both`)
- `trace.jsonl` — event log (when `--trace`, one JSON object per line)

---

#### `validate` — Validate a configuration file without running

```
python -m sim validate --config <path>
```

Prints validation errors to stdout and exits with code `1` if invalid,
`0` if valid.

---

#### `compare` — Run multiple configs and produce a comparison report

```
python -m sim compare --configs <path> [<path> ...] --seed <int>
                       [--output-dir <path>] [--format {json,csv,both}]
```

Runs each config with the same seed and outputs a side-by-side comparison
of all metrics. Useful for policy comparison (US2, US3, US4).

---

## Configuration File Schema (YAML)

```yaml
simulation:
  orders: 500           # Number of orders to simulate
  seed: 42              # Optional: overridden by --seed flag

arrival:
  distribution: exponential
  rate: 2.0             # orders per hour

order:
  page_count:
    distribution: discrete
    values: [100, 200, 300, 400]
    weights: [0.3, 0.4, 0.2, 0.1]
  units:
    distribution: uniform_int
    min: 100
    max: 500
  book_types: [A, B, C]            # Discrete type labels
  priority_range: [1, 5]           # Min/max priority values

lots:
  books_per_lot: 50     # CLPL

stages:
  printing:
    machines: 3         # CM[0]
    processing_time:
      distribution: exponential
      mean: 2.0         # hours per lot
    setup_time: 0.5     # TPM[0] hours
    energy_rate: 10.0   # CEM[0] cost/hour
    operating_windows:  # RHFM[0]
      - [8, 20]         # 08:00–20:00
    failure:
      mtbf: 40.0        # TEF[0] mean hours between failures
      repair_time:
        distribution: exponential
        mean: 2.0       # TDR[0]
    materials: [0, 1]   # SD indices consumed

  binding:
    machines: 2         # CM[1]
    processing_time:
      distribution: exponential
      mean: 1.5
    setup_time: 0.3
    energy_rate: 8.0
    operating_windows:
      - [8, 20]
    failure:
      mtbf: 60.0
      repair_time:
        distribution: exponential
        mean: 1.5
    materials: [2, 3]

  qa:
    machines: 1         # CM[2]
    processing_time:
      distribution: uniform
      min: 0.5
      max: 1.5
    setup_time: 0.0     # No setup for QA
    energy_rate: 2.0
    operating_windows:
      - [8, 20]
    defect_probability: 0.05    # PD
    defect_threshold: 0.05      # PQA: reject if sampled defect >= threshold
    failure:
      mtbf: 100.0
      repair_time:
        distribution: exponential
        mean: 1.0

  packaging:
    machines: 2         # CM[3]
    processing_time:
      distribution: normal
      mean: 0.8
      std: 0.1
    setup_time: 0.2
    energy_rate: 5.0
    operating_windows:
      - [8, 20]
    failure:
      mtbf: 80.0
      repair_time:
        distribution: exponential
        mean: 1.0
    materials: [4]

  dispatch:
    threshold: 20       # CPTD: dispatch when CLTA >= this

materials:
  - index: 0
    name: paper
    initial_stock: 10000
    reorder_point: 1000   # SPR[0]
    replenishment_quantity: 5000
    lead_time:
      distribution: uniform
      min: 1.0
      max: 3.0
  - index: 1
    name: ink
    initial_stock: 5000
    reorder_point: 500
    replenishment_quantity: 3000
    lead_time:
      distribution: uniform
      min: 0.5
      max: 2.0
  - index: 2
    name: binding_material
    initial_stock: 3000
    reorder_point: 300
    replenishment_quantity: 2000
    lead_time:
      distribution: uniform
      min: 1.0
      max: 2.0
  - index: 3
    name: adhesive
    initial_stock: 2000
    reorder_point: 200
    replenishment_quantity: 1500
    lead_time:
      distribution: uniform
      min: 0.5
      max: 1.5
  - index: 4
    name: packaging_material
    initial_stock: 4000
    reorder_point: 400
    replenishment_quantity: 2500
    lead_time:
      distribution: uniform
      min: 1.0
      max: 2.5

maintenance:
  frequency: 80.0       # FMP: hours of uptime between preventive maintenance
  # Per-stage duration overrides (optional; defaults to stage processing_time mean)
  durations:
    printing: 3.0       # TMM[0]
    binding: 2.0
    qa: 1.0
    packaging: 1.5

sequencing:
  policy: FIFO          # PS: FIFO | PRIORITY | BOOK_TYPE

output:
  event_log: false
  format: json
```

---

## Output Schema (results.json)

```json
{
  "meta": {
    "config_file": "config/default.yaml",
    "seed": 42,
    "orders_simulated": 500,
    "simulation_time": 1234.56,
    "policy": "FIFO",
    "run_timestamp": "2026-04-11T10:00:00"
  },
  "metrics": {
    "TPPT": 45.2,
    "TPPL": 4.3,
    "CxTP": 12.5,
    "TSP": [3.1, 2.4, 0.8, 1.2, 0.0],
    "TPE": [1.5, 0.8, 0.3, 0.6, 0.0],
    "PR": 0.048
  },
  "stage_utilization": {
    "printing": 0.87,
    "binding": 0.72,
    "qa": 0.45,
    "packaging": 0.68,
    "dispatch": 0.12
  },
  "bottleneck": "printing",
  "energy": {
    "total_cost": 6250.0,
    "by_stage": {
      "printing": 4300.0,
      "binding": 1200.0,
      "qa": 250.0,
      "packaging": 500.0
    }
  }
}
```
