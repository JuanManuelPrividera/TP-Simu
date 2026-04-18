# Implementation Plan: Simulación de Planta Editorial Industrial

**Branch**: `001-editorial-plant-sim` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-editorial-plant-sim/spec.md`

## Summary

Discrete-event simulation of an industrial book publishing plant with five
production stages (printing → binding → QA → packaging → dispatch), multiple
parallel machines per stage, random failures, preventive maintenance, raw
material inventory, configurable sequencing policies, and energy operating
windows. The simulation engine uses a custom event-to-event loop (heapq
priority queue), NumPy seeded random streams, and a YAML-based parametric
configuration. Outputs include per-run JSON/CSV metric reports and an optional
full event trace.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `numpy` — seeded random number generation (named streams via SeedSequence)
- `pyyaml` — YAML configuration parsing
- `pydantic` v2 — configuration schema validation (FR-013)
- `pytest` — test suite
- `ruff` — linting and formatting

**Storage**: File I/O only — YAML config in, JSON/CSV results out. No database.
**Testing**: `pytest`; unit, integration, and scenario test suites.
**Target Platform**: Linux/macOS/Windows (CLI, single-threaded)
**Project Type**: CLI simulation tool
**Performance Goals**: Complete a 500-order simulation in < 60 seconds on a
standard laptop. No concurrency required.
**Constraints**: Single-threaded; identical seed + config → identical output
(FR-012); all parameters configurable via YAML (Constitution IV).
**Scale/Scope**: Academic project; 5 stages; up to ~6 machine types; no
multi-user or persistence requirements.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Event-Driven Model | All behavior expressed as discrete events; heapq priority queue; no step-based loops | ✅ PASS |
| II. Modular Stage Design | Each stage owns its queue, machines, and event handlers; coupled only via queue enqueue | ✅ PASS |
| III. Seed-Controlled Reproducibility | NumPy SeedSequence with named streams; seed is top-level CLI arg | ✅ PASS |
| IV. Fully Parametric Control | All PS, FMP, PQA, RHFM, CPTD, CLPL, CM, SPR configurable via YAML | ✅ PASS |
| V. Structured Result Collection | MetricsCollector class separate from simulation logic; JSON/CSV export | ✅ PASS |

No violations. Proceeding to implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-editorial-plant-sim/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technology decisions
├── data-model.md        # Entities, state machines, event catalogue
├── quickstart.md        # How to run and validate
├── contracts/
│   └── cli.md           # CLI and config schema contract
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code

```text
src/
└── sim/
    ├── __init__.py
    ├── __main__.py              # CLI entry point (argparse)
    ├── engine/
    │   ├── __init__.py
    │   ├── event_queue.py       # heapq wrapper with tie-break counter
    │   └── simulator.py         # Main simulation loop
    ├── model/
    │   ├── __init__.py
    │   ├── order.py             # Order entity
    │   ├── lot.py               # Lot entity + LotStatus enum
    │   ├── machine.py           # Machine entity + MachineStatus enum
    │   ├── stage_queue.py       # CLM[i] with sequencing policy support
    │   └── stock.py             # MaterialStock SD[i]
    ├── events/
    │   ├── __init__.py
    │   ├── base.py              # Event base class + EventType enum
    │   ├── arrival.py           # ORDER_ARRIVAL handler
    │   ├── processing.py        # STAGE_START / STAGE_END / SETUP_START / SETUP_END
    │   ├── failure.py           # MACHINE_FAILURE / REPAIR_END
    │   ├── maintenance.py       # MAINTENANCE_START / MAINTENANCE_END
    │   ├── replenishment.py     # STOCK_REPLENISHMENT
    │   ├── dispatch.py          # DISPATCH
    │   └── window.py            # WINDOW_OPEN / WINDOW_CLOSE
    ├── policies/
    │   ├── __init__.py
    │   └── sequencing.py        # FIFO, Priority, BookType queue ordering
    ├── config/
    │   ├── __init__.py
    │   ├── schema.py            # Pydantic config model
    │   └── loader.py            # YAML load + validate
    ├── metrics/
    │   ├── __init__.py
    │   ├── collector.py         # MetricsCollector (accumulates during run)
    │   └── reporter.py          # JSON/CSV report generation
    └── distributions/
        ├── __init__.py
        └── prng.py              # SeedSequence + named Generator streams

tests/
├── unit/
│   ├── test_event_queue.py      # Ordering, tie-break, empty queue
│   ├── test_machine.py          # State transitions, immunity rules
│   ├── test_lot.py              # Status transitions, rework counting
│   ├── test_sequencing.py       # FIFO/Priority/BookType ordering
│   ├── test_metrics.py          # MetricsCollector accumulation
│   └── test_config.py           # Validation errors, defaults
├── integration/
│   ├── test_arrival_to_printing.py
│   ├── test_printing_to_binding.py
│   ├── test_qa_rework.py
│   ├── test_replenishment.py
│   ├── test_failure_and_repair.py
│   ├── test_maintenance.py
│   └── test_dispatch.py
└── scenario/
    ├── test_baseline.py         # SC-001, SC-002
    ├── test_policy_comparison.py # SC-003 (US2)
    ├── test_maintenance_strategies.py # US3
    └── test_energy_windows.py   # SC-006 (US4)

config/
└── default.yaml                 # Default configuration (matches contract schema)

docs/
└── distributions.md             # All distributions with type + parameters

pyproject.toml
```

**Structure Decision**: Single project. All simulation code under `src/sim/`.
Subpackages by concern: engine, model, events, policies, config, metrics,
distributions. Tests mirror source structure with scenario tests as top-level
integration runs.

## Complexity Tracking

No constitution violations to justify.

---

## Phase 1: Project Setup

**Purpose**: Initialize Python project, directory structure, and tooling.

- [ ] T001 Create `pyproject.toml` with dependencies: numpy, pyyaml, pydantic,
       pytest, ruff; configure `[project.scripts]` entry point for `sim`
- [ ] T002 Create directory skeleton: `src/sim/` subpackages with `__init__.py`
       files, `tests/unit/`, `tests/integration/`, `tests/scenario/`,
       `config/`, `docs/`
- [ ] T003 [P] Create `config/default.yaml` matching the CLI contract schema
- [ ] T004 [P] Create `docs/distributions.md` documenting all distributions
       with type and parameters per Constitution III

---

## Phase 2: Core Engine (Blocking — required by all stages)

**Purpose**: Event queue, PRNG abstraction, config loader, and metrics
collector. Nothing else can be built without these.

**⚠️ CRITICAL**: No stage or event code until this phase completes.

- [ ] T005 Implement `src/sim/engine/event_queue.py`:
       - `EventQueue` wrapping heapq
       - Items: `(time, sequence_num, event)` tuples
       - Methods: `push(event)`, `pop() → event`, `is_empty() → bool`
       - Monotonic sequence counter for tie-breaking

- [ ] T006 Implement `src/sim/distributions/prng.py`:
       - `PRNGFactory(master_seed)` using `numpy.random.SeedSequence`
       - `get_stream(name: str) → numpy.random.Generator`
       - Named streams cached after first call
       - Supported distributions: exponential, normal, uniform, uniform_int,
         discrete (weighted choice)

- [ ] T007 Implement `src/sim/config/schema.py` + `loader.py`:
       - Pydantic v2 model covering full YAML schema (see contracts/cli.md)
       - `load_config(path) → SimConfig` with validation errors on failure
       - FR-013: all validation errors collected and reported before run starts

- [ ] T008 Implement `src/sim/metrics/collector.py`:
       - `MetricsCollector` class with methods:
         `record_lot_done(lot)`, `record_queue_wait(stage, duration)`,
         `record_downtime(stage, duration, reason)`, `record_energy(stage, duration)`,
         `record_rework(lot_id)`
       - Accumulators for all FR-011 metrics
       - No simulation logic — pure data collection

- [ ] T009 Implement `src/sim/metrics/reporter.py`:
       - `generate_report(collector, meta) → dict`
       - `write_json(report, path)`, `write_csv(report, path)`
       - Derived metric calculations (TPPT, TPPL, TSP, TPE, PR, CxTP)
       - Include trace metadata in report output when event tracing is enabled

**Checkpoint**: Engine ready — event queue testable, PRNG produces seeded
streams, config loads and validates, metrics collector accumulates.

---

## Phase 3: Domain Model

**Purpose**: Entities that the event handlers will create and mutate.

- [ ] T010 [P] Implement `src/sim/model/lot.py`:
       - `Lot` dataclass with all fields from data-model.md
       - `LotStatus` enum: WAITING | IN_PROCESS | SUSPENDED | DONE | DISPATCHED
       - `StageEnum`: PRINTING | BINDING | QA | PACKAGING | DISPATCHED

- [ ] T011 [P] Implement `src/sim/model/order.py`:
       - `Order` dataclass; `create_lots(clpl) → list[Lot]` method

- [ ] T012 [P] Implement `src/sim/model/machine.py`:
       - `Machine` dataclass with all fields from data-model.md
       - `MachineStatus` enum: IDLE | BUSY | SETUP | FAILED | MAINTENANCE
       - `is_available(sim_time) → bool` — checks status and operating window
       - `in_window(sim_time) → bool` — checks RHFM against `sim_time % 24`

- [ ] T013 [P] Implement `src/sim/model/stage_queue.py`:
       - `StageQueue(policy: SequencingPolicy)`
       - `enqueue(lot)`, `dequeue() → Lot | None`, `peek() → Lot | None`
       - Delegates ordering to policy module

- [ ] T014 [P] Implement `src/sim/model/stock.py`:
       - `MaterialStock(index, quantity, reorder_point, ...)`
       - `consume(amount) → bool` — returns False if insufficient
       - `replenish(amount)`, `needs_reorder() → bool`

- [ ] T015 [P] Implement `src/sim/policies/sequencing.py`:
       - `SequencingPolicy` ABC with `sort_key(lot) → tuple`
       - `FIFOPolicy`, `PriorityPolicy`, `BookTypePolicy` implementations
       - BookType: group by type, within group by arrival_time

**Checkpoint**: All model classes in place and unit-testable in isolation.

---

## Phase 4: Event Handlers — Core Production Flow (US1)

**Purpose**: The five-stage production pipeline end-to-end, without failures
or maintenance. This delivers User Story 1 (baseline simulation run).

- [ ] T016 Implement `src/sim/events/base.py`:
       - `Event` dataclass: `time`, `sequence_num`, `type: EventType`, `payload: dict`
       - `EventType` enum with all types from data-model.md

- [ ] T017 Implement `src/sim/events/arrival.py` — `handle_order_arrival`:
       - Sample order attributes from PRNG streams
       - Create lots → enqueue in CLM[printing]
       - Schedule next ORDER_ARRIVAL
       - Conditionally schedule STAGE_START for printing if machine available
       - Conditionally schedule STOCK_REPLENISHMENT if SD[0] or SD[1] at reorder

- [ ] T018 Implement `src/sim/events/processing.py` — `handle_stage_end`:
       - Release machine → IDLE
       - Consume stage materials from SD[i]
       - Route lot to next stage queue (or storage if packaging done)
       - If `CLTA >= CPTD` → schedule DISPATCH
       - Conditionally schedule next STAGE_START on same machine
       - Conditionally schedule STOCK_REPLENISHMENT if materials at reorder
       - Check `pending_maintenance` flag → enter MAINTENANCE if set

- [ ] T019 Implement `src/sim/events/processing.py` — `handle_setup_end`:
       - Machine SETUP → BUSY
       - Schedule STAGE_END at `t + processing_time`

- [ ] T020 Implement `src/sim/events/dispatch.py` — `handle_dispatch`:
       - Move all DONE lots from storage → DISPATCHED
       - Reset CLTA to 0
       - Record dispatch in metrics

- [ ] T021 Implement `src/sim/engine/simulator.py` — main loop:
       - `Simulator(config, seed)` constructor initializes all state
       - `run() → MetricsCollector` — processes events until termination
       - Termination: N orders completed (configurable in config)
       - Dispatches events to correct handler by EventType
       - Optionally capture a full event trace with monotonic timestamps for
         every processed event type (SC-004)

- [ ] T022 Implement `src/sim/__main__.py` — CLI:
       - `run` subcommand: load config → create Simulator → run → report
       - `validate` subcommand: load config and exit
       - `compare` subcommand: run multiple configs with same seed → compare report

**Checkpoint**: `python -m sim run --config config/default.yaml --seed 42`
completes and writes `results.json` with all metrics. SC-001 and SC-002 pass.

---

## Phase 5: Event Handlers — Failures & Maintenance (US3)

**Purpose**: Machine failures (corrective) and preventive maintenance.

- [ ] T023 Implement `src/sim/events/failure.py` — `handle_machine_failure`:
       - Guard: ignore if machine in SETUP or MAINTENANCE (FR-016)
       - Machine → FAILED; lot stays SUSPENDED (not requeued)
       - Cancel/ignore pending MAINTENANCE_DUE if within repair window
       - Schedule REPAIR_END at `t + TDR[i]`
       - Schedule next MACHINE_FAILURE at `t + TDR[i] + TEF[i]`
       - FR-015: if all machines of type unavailable, evaluate redirect vs wait

- [ ] T024 Implement `src/sim/events/failure.py` — `handle_repair_end`:
       - Machine → IDLE
       - If lot was SUSPENDED → reschedule STAGE_END at `t + remaining_time`
       - Else → check CLM[i] and schedule STAGE_START if lots waiting
       - Reschedule next MAINTENANCE_DUE at `t + FMP`
       - Record downtime in metrics

- [ ] T025 Implement `src/sim/events/maintenance.py` — `handle_maintenance_due`:
       - If machine BUSY: set `pending_maintenance = True`; return (Option A)
       - If machine IDLE: machine → MAINTENANCE; schedule MAINTENANCE_END
       - Discard if machine FAILED

- [ ] T026 Implement `src/sim/events/maintenance.py` — `handle_maintenance_end`:
       - Machine → IDLE; clear `pending_maintenance`
       - Check CLM[i] → schedule STAGE_START if lots waiting
       - Schedule next MAINTENANCE_DUE at `t + FMP`
       - Reschedule next MACHINE_FAILURE at `t + TEF[i]`
       - Record maintenance downtime in metrics

**Checkpoint**: Run with `FMP > 0` vs `FMP = 0`; TSP[i] values differ.
Failure/repair events appear in trace. US3 scenario tests pass.

---

## Phase 6: Event Handlers — Energy Windows (US4)

**Purpose**: Operating window enforcement (RHFM).

- [ ] T027 Schedule WINDOW_OPEN / WINDOW_CLOSE events at simulator init:
       - For each machine type, for each window in RHFM[i], schedule recurring
         events across the simulation horizon

- [ ] T028 Implement `src/sim/events/window.py` — `handle_window_open`:
       - For each idle machine of this type with lots waiting → schedule
         STAGE_START immediately

- [ ] T029 Update `handle_stage_end` and `handle_order_arrival`:
       - Call `machine.is_available(sim_time)` before scheduling STAGE_START
       - Machines outside window do not start new lots

- [ ] T030 Update `MetricsCollector` to track active time per stage per
       time slot for energy cost calculation

**Checkpoint**: Machines block outside RHFM windows. SC-006 passes.

---

## Phase 7: Sequencing Policies (US2)

**Purpose**: Verify all three PS options work end-to-end.

- [ ] T031 Write `tests/scenario/test_policy_comparison.py`:
       - Run FIFO, PRIORITY, BOOK_TYPE with same seed
       - Assert distinct TPPT values (SC-003)
       - Assert lot order in trace matches declared policy

- [ ] T032 Verify BookType minimizes setups: count SETUP_START events in trace;
       BOOK_TYPE should produce fewer setups than FIFO for mixed workloads

**Checkpoint**: US2 scenario tests pass. SC-003 verified.

---

## Phase 8: Traceability & Statistical Validation

**Purpose**: Close the remaining measurable-outcome gaps for event trace
correctness (SC-004) and QA rework-rate calibration (SC-005).

- [ ] T033 Implement event trace capture/export:
       - Add optional trace sink under `src/sim/metrics/` or `src/sim/engine/`
       - Persist one ordered record per processed event with `time`, `seq`,
         `type`, and minimal entity identifiers
       - Expose trace output through CLI flag and structured file output

- [ ] T034 Add scenario test for SC-004:
       - Run simulation with trace enabled
       - Assert all required event types appear in trace
       - Assert timestamps are monotonically non-decreasing and ties preserve
         event queue sequence order

- [ ] T035 Add scenario/statistical validation for SC-005:
       - Run long simulation workload (1000+ lots) with fixed seed
       - Compare observed `PR` against configured `PD`
       - Assert deviation remains within the specified ±10% tolerance

**Checkpoint**: Trace export is available and SC-004/SC-005 are explicitly
verified by automated tests.

---

## Phase 9: Polish & Cross-Cutting

- [ ] T036 [P] Write `docs/distributions.md` with final parameterization
- [ ] T037 [P] Run `ruff check src/ tests/` and fix all lint errors
- [ ] T038 [P] Run full `pytest` suite; all tests must pass
- [ ] T039 [P] Run simulation twice with same seed; diff results → identical
- [ ] T040 Run quickstart.md validation checklist

---

## Dependencies & Execution Order

```
Phase 1 (Setup) → Phase 2 (Engine) → Phase 3 (Model)
                                          │
                            Phase 4 (Core Flow / US1) ── MVP
                                          │
                    ┌─────────────────────┼──────────────────┐
                    ▼                     ▼                  ▼
            Phase 5 (Failures)   Phase 6 (Windows)  Phase 7 (Policies)
                    │                     │                  │
                    └─────────────────────┴──────────────────┘
                                          │
                         Phase 8 (Traceability & Validation)
                                          │
                                  Phase 9 (Polish)
```

Phases 5, 6, 7 are independent of each other and can proceed in parallel
after Phase 4 completes.

## Notes

- All time values are in **hours** (fractional floats). No datetime objects.
- `sim_time % 24` converts simulation time to hour-of-day for RHFM checks.
- Event handlers communicate only through the shared EventQueue — no direct
  method calls between stage handlers.
- The `pending_maintenance` flag on Machine is the key mechanism for Option A
  non-interrupting preventive maintenance.
- FR-015 redirect logic lives in `handle_machine_failure` and
  `handle_maintenance_due`; both check if all machines of a type are
  unavailable before evaluating redirect vs wait.
- QA stage has no materials (SD indices) and no setup time.
