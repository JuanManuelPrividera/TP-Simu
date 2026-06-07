<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0
This is the initial ratification of the constitution from template.

Modified principles: N/A (first ratification)

Added sections:
  - Core Principles (5 principles)
  - Model Architecture
  - Development Workflow
  - Governance

Removed sections: N/A

Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check section present)
  - .specify/templates/spec-template.md ✅ aligned (FR/SC structure compatible)
  - .specify/templates/tasks-template.md ✅ aligned (phase structure compatible)

Deferred TODOs: None
-->

# Simulación Editorial Industrial — Constitution

## Core Principles

### I. Event-Driven Simulation Model

Every behavior in the system MUST be expressed as a discrete event with an
explicit timestamp, type, and state transition. No continuous-time or
step-based logic is permitted.

- The simulation clock advances event-to-event (not fixed time steps).
- All events MUST be placed on a global priority queue ordered by time.
- Each event handler MUST update system state and conditionally schedule
  follow-up events.
- The simulation engine MUST be decoupled from domain logic (stages, machines,
  policies).

Rationale: The assignment specifies "Metodología: Evento a Evento". Mixing
paradigms would invalidate the analytical model.

### II. Modular Stage Design

Each production stage (Impresión, Encuadernación, QA, Embalaje, Despacho) MUST
be implemented as an independent, self-contained module.

- Each stage module owns its queue (`CLM[i]`), its machines, and its event
  handlers.
- Inter-stage coupling is limited to: enqueuing the next stage's queue upon
  batch completion.
- Stages MUST be independently testable with a stub clock and stub queues.
- New stages MUST be addable without modifying existing stage modules.

Rationale: Bottlenecks shift dynamically across stages; isolation ensures each
can be analyzed, parameterized, and replaced independently.

### III. Seed-Controlled Reproducibility

Every stochastic element MUST use a seeded pseudo-random number generator
(PRNG). The same seed MUST always produce the same simulation trace.

- Random variables (inter-arrival times, page counts, defect probability,
  failure times, repair times) MUST draw from named, seedable streams.
- No calls to `random.random()` or `time.time()` for stochastic sampling are
  permitted; use the project's PRNG abstraction.
- The seed MUST be a top-level control parameter (not buried in module state).

Rationale: Reproducibility is mandatory for comparing policies (sequencing,
maintenance, QA) under identical stochastic conditions.

### IV. Fully Parametric Control

All control variables MUST be externalizable as configuration — no policy or
capacity value may be hard-coded.

Control parameters that MUST be configurable:
- `PS` — sequencing policy (FIFO | Priority | BookType)
- `FMP` — preventive maintenance frequency
- `PQA` — QA defect threshold
- `RHFM[5][CM]` — machine operating time windows (energy constraints)
- `CPTD` — finished-lot dispatch threshold
- `CLPL` — lot size (books per lot)
- `CM[5]` — machine counts per stage
- `SPR[5]` — reorder points per raw material

Rationale: The study objective is to compare alternative management policies;
hard-coded values make comparison impossible without code changes.

### V. Structured Result Collection

All output metrics MUST be recorded through a dedicated collector that is
separate from simulation logic.

Metrics MUST include:
- `TPPT` — average total production time
- `TPPL` — average production time per lot
- `CxTP` — cost per production time unit
- `TSP[5]` — average non-production time per stage (repair + idle + setup)
- `TPE[5]` — average queue wait time per machine type
- `PR` — average rework rate

The collector MUST support export to structured formats (JSON or CSV) for
post-simulation analysis. Raw event logs MUST be preserved optionally.

Rationale: Results are the primary deliverable of the study; coupling metric
collection to simulation logic makes it impossible to extend or audit outputs.

## Model Architecture

### State Variables

The simulation state MUST track:

- `CLM[5]` — lot queue per machine type
- `CxM[5][CM]` — per-machine configuration/status
- `SD[5]` — available stock of each raw material (paper, ink, binding
  material, packaging, labels)
- `CLTA` — count of finished lots in storage

### Random Variables (Inputs)

- `IA` — inter-arrival time of orders
- `PCP` — page count probability distribution
- `CUL` — number of book units per order
- `PD` — defect probability per lot at QA
- `TEF[5]` — time-between-failures per machine type
- `TDR[5]` — repair duration per machine type
- `TMM[5]` — preventive maintenance duration per machine type
- `CEM[5]` — energy consumption per machine type
- `TPM[5]` — setup time per machine type

All distributions MUST be documented (type + parameters) in `docs/distributions.md`.

### Energy Constraints

Operating time windows (`RHFM`) MUST gate machine availability. A machine
outside its permitted window MUST NOT process new lots. Energy cost tracking
MUST accumulate `CEM[i] × active_time` per time slot.

## Development Workflow

- Language: Python 3.11+
- Project layout: single-project (`src/`, `tests/`)
- Dependency management: `pyproject.toml` with pinned versions
- Testing: `pytest`; unit tests for event handlers, integration tests for
  stage-to-stage flows, scenario tests for full policy comparisons
- Linting: `ruff` (formatting + lint); CI MUST pass before merge
- Simulation runs: invoked via CLI (`python -m sim run --config <file>`)
- Configuration: YAML or JSON config files; no runtime mutation of config

## Governance

This constitution supersedes all other practices for this project. Amendments
require:

1. A written rationale explaining why the change is necessary.
2. Version increment following semantic versioning:
   - MAJOR — principle removed or its non-negotiable rules redefined.
   - MINOR — new principle or section added.
   - PATCH — clarification, wording, or non-semantic fix.
3. Updates to all affected template files (plan, spec, tasks).
4. Compliance review: all implementation PRs MUST pass Constitution Check
   gates in the plan template before merge.

**Version**: 1.0.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-11
