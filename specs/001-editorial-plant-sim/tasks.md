---
description: "Task list for Simulación de Planta Editorial Industrial"
---

# Tasks: Simulación de Planta Editorial Industrial

**Input**: Design documents from `specs/001-editorial-plant-sim/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/cli.md ✅ quickstart.md ✅

**Tests**: Not explicitly requested — test tasks are NOT included.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- All time values in hours (floats). No datetime objects.
- `sim_time % 24` for hour-of-day RHFM checks.

## Path Conventions

Single project: `src/sim/`, `tests/` at repository root.

---

## Phase 1: Setup

**Purpose**: Initialize Python project, directory skeleton, and tooling.

- [x] T001 Create `pyproject.toml` with dependencies (numpy, pyyaml, pydantic>=2, pytest, ruff), `[project.scripts]` entry `sim = "sim.__main__:main"`, and `[tool.ruff]` config
- [x] T002 Create full directory skeleton with empty `__init__.py` files: `src/sim/engine/`, `src/sim/model/`, `src/sim/events/`, `src/sim/policies/`, `src/sim/config/`, `src/sim/metrics/`, `src/sim/distributions/`, `tests/unit/`, `tests/integration/`, `tests/scenario/`, `config/`, `docs/`
- [x] T003 [P] Create `config/default.yaml` matching the full YAML schema from `specs/001-editorial-plant-sim/contracts/cli.md` with all five stages, five materials, maintenance, and sequencing sections
- [x] T004 [P] Create `docs/distributions.md` listing all random variables (IA, PCP, CUL, PD, TEF[i], TDR[i], TMM[i], lead times) with distribution type and parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core engine infrastructure that ALL user stories depend on.
Event queue, PRNG, config loader, metrics collector, domain model, and policies
must be complete before any production pipeline code can be written.

**⚠️ CRITICAL**: No event handler or stage code until this phase completes.

- [x] T005 Implement `src/sim/engine/event_queue.py`: `EventQueue` wrapping `heapq` with items `(time, seq, event)`, monotonic `_counter` for tie-breaking, methods `push(event)`, `pop() → Event`, `is_empty() → bool`

- [x] T006 Implement `src/sim/distributions/prng.py`: `PRNGFactory(master_seed)` using `numpy.random.SeedSequence`; `get_stream(name: str) → numpy.random.Generator` with cached named generators; helper methods `exponential(name, mean)`, `normal(name, mean, std)`, `uniform(name, lo, hi)`, `uniform_int(name, lo, hi)`, `discrete(name, values, weights)`

- [x] T007 Implement `src/sim/config/schema.py`: Pydantic v2 models for full YAML schema from `specs/001-editorial-plant-sim/contracts/cli.md` — `SimConfig`, `StageConfig`, `MaterialConfig`, `MaintenanceConfig`, `SequencingConfig`, `DistributionConfig`

- [x] T008 Implement `src/sim/config/loader.py`: `load_config(path: str) → SimConfig` using PyYAML + pydantic validation; collect all validation errors before raising; FR-013

- [x] T009 [P] Implement `src/sim/model/lot.py`: `LotStatus` enum (WAITING | IN_PROCESS | SUSPENDED | DONE | DISPATCHED), `StageEnum` (PRINTING | BINDING | QA | PACKAGING | DISPATCHED), `Lot` dataclass with fields: `id`, `order_id`, `book_type`, `priority`, `stage`, `status`, `rework_count`, `entry_time`, `start_time`, `total_production_time`, `remaining_process_time`

- [x] T010 [P] Implement `src/sim/model/order.py`: `Order` dataclass with fields: `id`, `arrival_time`, `page_count`, `unit_count`, `book_type`, `priority`; method `create_lots(clpl: int) → list[Lot]` using `math.ceil(unit_count / clpl)` lot count

- [x] T011 [P] Implement `src/sim/model/machine.py`: `MachineStatus` enum (IDLE | BUSY | SETUP | FAILED | MAINTENANCE), `Machine` dataclass with fields: `id`, `type_index`, `status`, `current_lot`, `last_lot_type`, `pending_maintenance`, `t_repair_done`, `operating_windows`, `energy_rate`; methods `is_available(sim_time) → bool`, `in_window(sim_time) → bool` using `sim_time % 24`

- [x] T012 [P] Implement `src/sim/model/stage_queue.py`: `StageQueue(stage, policy)` with internal list; `enqueue(lot)` inserts according to policy sort key; `dequeue() → Lot | None`; `peek() → Lot | None`; `__len__()`

- [x] T013 [P] Implement `src/sim/model/stock.py`: `MaterialStock(index, quantity, reorder_point, consumption_per_lot, replenishment_pending)` dataclass; `consume(amount) → bool` (returns False if insufficient, does NOT deduct on failure); `replenish(amount)`; `needs_reorder() → bool`

- [x] T014 [P] Implement `src/sim/policies/sequencing.py`: abstract `SequencingPolicy` with `sort_key(lot) → tuple`; `FIFOPolicy` (key: `entry_time`); `PriorityPolicy` (key: `(-priority, entry_time)`); `BookTypePolicy` (key: `(book_type, entry_time)` — groups same type to minimize setup changes); factory `make_policy(name: str) → SequencingPolicy`

- [x] T015 [P] Implement `src/sim/metrics/collector.py`: `MetricsCollector` with accumulators `tppt_samples`, `tppl_samples`, `tsp[5]`, `tpe_samples[5]`, `rework_count`, `total_lots`, `energy_active_time[5]`; methods `record_lot_done(lot, sim_time)`, `record_queue_wait(stage_idx, duration)`, `record_downtime(stage_idx, duration)`, `record_energy(stage_idx, duration)`, `record_rework()`

- [x] T016 [P] Implement `src/sim/metrics/reporter.py`: `generate_report(collector, meta, config) → dict` computing TPPT, TPPL, TSP[i], TPE[i], PR, CxTP, stage_utilization, bottleneck (stage with max TPE); `write_json(report, path)`; `write_csv(report, path)` (flat key-value pairs)

- [x] T017 Implement `src/sim/events/base.py`: `EventType` enum with all types from `specs/001-editorial-plant-sim/data-model.md` (ORDER_ARRIVAL, STAGE_START, STAGE_END, SETUP_START, SETUP_END, MACHINE_FAILURE, REPAIR_END, MAINTENANCE_DUE, MAINTENANCE_END, STOCK_REPLENISHMENT, DISPATCH, WINDOW_OPEN, WINDOW_CLOSE); `Event` dataclass with `time: float`, `seq: int`, `type: EventType`, `payload: dict`; comparison by `(time, seq)`

**Checkpoint**: Engine, model, policies, and metrics all in place. Can be unit-tested
in full isolation before any production pipeline is written.

---

## Phase 3: User Story 1 — Baseline Simulation Run (Priority: P1) 🎯 MVP

**Goal**: Full five-stage pipeline (printing → binding → QA → packaging → dispatch)
running end-to-end with config, PRNG, metrics, and CLI output.

**Independent Test**: `python -m sim run --config config/default.yaml --seed 42` completes
without error and writes `results/results.json` with all 11 metrics populated and non-null.
Running again with the same seed produces an identical file (SC-001, SC-002).

### Implementation for User Story 1

- [x] T018 [US1] Implement `src/sim/events/arrival.py` — `handle_order_arrival(event, state)`: sample `page_count` (PCP stream), `unit_count` (CUL stream), `book_type`, `priority`; create `Order` and call `create_lots(clpl)`; enqueue each lot in `state.queues[PRINTING]`; schedule next ORDER_ARRIVAL at `t + prng.exponential("IA", rate)`; for each available printing machine check `is_available` → schedule STAGE_START or SETUP_START; check SD[0]/SD[1] reorder → schedule STOCK_REPLENISHMENT

- [x] T019 [US1] Implement `src/sim/events/replenishment.py` — `handle_stock_replenishment(event, state)`: call `stock.replenish(quantity)`; clear `replenishment_pending`; for the stage(s) that use this material, check if any machine is IDLE with lots waiting and materials now available → schedule STAGE_START

- [x] T020 [US1] Implement `src/sim/events/processing.py` — `handle_setup_start` and `handle_setup_end`: SETUP_START sets `machine.status = SETUP`, `machine.last_lot_type = new_type`; schedules SETUP_END at `t + TPM[i]`; SETUP_END sets `machine.status = BUSY`; schedules STAGE_END at `t + processing_time`

- [x] T021 [US1] Implement `src/sim/events/processing.py` — `handle_stage_start(event, state)`: dequeue next lot from `state.queues[stage]` per policy; assign to machine; check if `lot.book_type != machine.last_lot_type` → schedule SETUP_START else directly STAGE_END; set `lot.status = IN_PROCESS`, `lot.start_time = t`; record `machine.status = BUSY`

- [x] T022 [US1] Implement `src/sim/events/processing.py` — `handle_stage_end(event, state)`: set `machine.status = IDLE`; consume materials for stage; route lot: if stage == QA → sample defect (`prng.uniform("PD", 0, 1) < PD`) → rework path or forward; if stage == PACKAGING → increment `CLTA`; check `CLTA >= CPTD` → schedule DISPATCH; check `pending_maintenance` flag → schedule MAINTENANCE_DUE if set; check CLM[stage] for next lot → schedule STAGE_START or SETUP_START; check material reorder → schedule STOCK_REPLENISHMENT; record `collector.record_queue_wait` for dequeued lot

- [x] T023 [US1] Implement `src/sim/events/dispatch.py` — `handle_dispatch(event, state)`: move all DONE lots in storage to DISPATCHED; call `collector.record_lot_done` for each; reset `state.clta = 0`

- [x] T024 [US1] Implement `src/sim/engine/simulator.py` — `Simulator(config, seed)`: initialise `EventQueue`, `PRNGFactory(seed)`, queues (`StageQueue` per stage), machines (one `Machine` per `CM[i]` per stage), stocks (`MaterialStock` per material), `MetricsCollector`; schedule initial ORDER_ARRIVAL, initial MACHINE_FAILURE for each machine, initial MAINTENANCE_DUE for each machine; `run() → MetricsCollector` dispatches events by `EventType` until `state.orders_completed >= config.simulation.orders`

- [x] T025 [US1] Implement `src/sim/__main__.py`: `argparse` with subcommands `run`, `validate`, `compare`; `run`: `load_config → Simulator(config, seed).run() → generate_report → write_json/csv`; `validate`: `load_config` and print "Configuration valid." or errors; `compare`: run each config with same seed and write side-by-side comparison dict

- [ ] T026 [US1] Implement optional event trace capture/export: persist one ordered record per processed event with `time`, `seq`, `type`, and relevant entity IDs; expose via `--trace` / trace output file so SC-004 can be verified

**Checkpoint**: `python -m sim run --config config/default.yaml --seed 42` produces
`results/results.json` with TPPT, TPPL, CxTP, TSP[0..4], TPE[0..4], PR all non-null.
Same command run twice produces identical output. SC-001 ✅ SC-002 ✅

---

## Phase 4: User Story 3 — Maintenance Strategy Analysis (Priority: P2)

**Goal**: Machine failures (corrective) and preventive maintenance fully modelled.
TSP[i] values reflect downtime broken down by repair, idle, and setup.

**Independent Test**: Run with `maintenance.frequency: 80.0` vs `maintenance.frequency: 0`
(disable preventive). `TSP[i]` values differ between runs. Machine failure events appear
in trace log when `--trace` is used.

### Implementation for User Story 3

- [x] T027 [US3] Implement `src/sim/events/failure.py` — `handle_machine_failure(event, state)`: guard — discard event if `machine.status in (SETUP, MAINTENANCE)` (FR-016); set `machine.status = FAILED`; if `machine.current_lot` is not None set `lot.status = SUSPENDED`, store `lot.remaining_process_time = t_stage_end - t`; cancel pending MAINTENANCE_DUE for this machine if it falls within repair window; schedule REPAIR_END at `t + prng.exponential("TDR_i", TDR[i])`; schedule next MACHINE_FAILURE at `t_repair_end + prng.exponential("TEF_i", TEF[i])`; evaluate FR-015: if all machines of type i unavailable, compare `remaining_repair_time` vs `TPM[compatible]` for each waiting lot → redirect or leave in queue; call `collector.record_downtime(i, repair_duration)`

- [x] T028 [US3] Implement `src/sim/events/failure.py` — `handle_repair_end(event, state)`: set `machine.status = IDLE`; if `machine.current_lot` has `status == SUSPENDED` → reschedule STAGE_END at `t + lot.remaining_process_time`, set `lot.status = IN_PROCESS`; else check `state.queues[stage]` → schedule STAGE_START if lots waiting and materials available; reschedule MAINTENANCE_DUE at `t + FMP` (reset maintenance clock after repair)

- [x] T029 [US3] Implement `src/sim/events/maintenance.py` — `handle_maintenance_due(event, state)`: if `machine.status == BUSY` → set `machine.pending_maintenance = True`; return (Option A — deferred); if `machine.status == IDLE` → set `machine.status = MAINTENANCE`; schedule MAINTENANCE_END at `t + prng.normal("TMM_i", TMM[i], std)`; discard if `machine.status == FAILED`

- [x] T030 [US3] Implement `src/sim/events/maintenance.py` — `handle_maintenance_end(event, state)`: set `machine.status = IDLE`; clear `machine.pending_maintenance`; schedule MAINTENANCE_DUE at `t + FMP`; reschedule MACHINE_FAILURE at `t + prng.exponential("TEF_i", TEF[i])` (reset failure clock); check `state.queues[stage]` → schedule STAGE_START if lots waiting; call `collector.record_downtime(i, TMM_duration)`

**Checkpoint**: Two scenario runs (FMP=80 vs FMP=0) produce different `TSP[i]`. Lots
remain SUSPENDED (not requeued) during machine repair. US3 independent test passes.

---

## Phase 5: User Story 4 — Energy-Constrained Scheduling (Priority: P3)

**Goal**: Machine operating windows (RHFM) enforced. Lots queue during off-hours.
Energy cost (CxTP) reflects only active machine time.

**Independent Test**: Configure all machines with `operating_windows: [[8, 20]]`.
No STAGE_START event fires outside hours 8–20 (verified via `--trace`). Queue size
grows during off-hours and drains on window open. CxTP is lower than unrestricted run.

### Implementation for User Story 4

- [x] T031 [US4] Update `src/sim/engine/simulator.py` — schedule WINDOW_OPEN / WINDOW_CLOSE events at init: for each machine type i, for each `(start_h, end_h)` in `RHFM[i]`, schedule recurring events for each 24-hour cycle within the simulation horizon; use `math.floor(horizon / 24) + 1` cycles

- [x] T032 [US4] Implement `src/sim/events/window.py` — `handle_window_open(event, state)`: for each IDLE machine of this type, if `state.queues[stage]` has lots and materials available → schedule STAGE_START immediately; `handle_window_close` is a no-op (machines already check `in_window` before starting new lots)

- [x] T033 [US4] Update `src/sim/events/arrival.py` and `handle_stage_end` in `processing.py`: wrap every STAGE_START/SETUP_START scheduling decision with `machine.is_available(t)` guard — machines outside their window are skipped; lot stays in queue until WINDOW_OPEN fires

- [x] T034 [US4] Update `src/sim/metrics/collector.py` — `record_energy(stage_idx, duration)`: accumulate `energy_active_time[stage_idx] += duration`; update `reporter.py` to compute `CxTP = sum(CEM[i] * energy_active_time[i] for all i) / total_simulation_time`

**Checkpoint**: `python -m sim run --config config/8h-windows.yaml --seed 42` produces
lower CxTP than `config/default.yaml` (unrestricted). Trace shows no STAGE_START outside
window hours. SC-006 ✅

---

## Phase 6: User Story 2 — Sequencing Policy Comparison (Priority: P1) ✅

**Goal**: All three PS policies (FIFO, PRIORITY, BOOK_TYPE) verified end-to-end via
the `compare` subcommand. Policies already implemented in Phase 2 (T014); this phase
validates correctness in full simulation runs.

**Independent Test**: `python -m sim compare --configs config/fifo.yaml config/priority.yaml config/booktype.yaml --seed 42` produces three distinct TPPT values. BookType config produces fewer SETUP_START events than FIFO config.

### Implementation for User Story 2

- [x] T035 [P] [US2] Create `config/fifo.yaml`, `config/priority.yaml`, `config/booktype.yaml` — copies of `default.yaml` with only `sequencing.policy` changed to `FIFO`, `PRIORITY`, `BOOK_TYPE` respectively

- [x] T036 [US2] Update `src/sim/events/processing.py` — `handle_stage_end`: when checking `pending_maintenance`, also record setup event count in `collector` for BookType verification; add `collector.record_setup()` call inside `handle_setup_start`

- [x] T037 [US2] Add `setup_count` accumulator to `src/sim/metrics/collector.py` and expose in `reporter.py` output under `metrics.setup_count`

**Checkpoint**: `python -m sim compare` outputs three reports with distinct TPPT.
`booktype` report has lower `setup_count` than `fifo` report. SC-003 ✅

---

## Phase 7: Traceability & Statistical Validation

**Purpose**: Cubrir explícitamente SC-004 y SC-005 antes del cierre final.

- [x] T038 [P] [US1] Add `tests/scenario/test_event_trace.py`: run simulation with trace enabled; assert the trace contains ORDER_ARRIVAL, STAGE_START, STAGE_END, SETUP_START, SETUP_END, MACHINE_FAILURE, REPAIR_END, MAINTENANCE_DUE, MAINTENANCE_END, STOCK_REPLENISHMENT, DISPATCH, WINDOW_OPEN, WINDOW_CLOSE; assert `(time, seq)` is monotonic throughout (SC-004)

- [x] T039 [P] [US3] Add `tests/scenario/test_rework_rate.py`: run a long workload generating 1000+ lots with fixed seed; compare observed `PR` against configured `PD`; assert deviation is within ±10% of expected value (SC-005)

**Checkpoint**: SC-004 and SC-005 have explicit automated coverage and no longer depend on implied manual verification.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, lint, reproducibility check, and documentation.

- [x] T040 [P] Run `ruff check src/ tests/` and fix all reported issues; run `ruff format src/ tests/`
- [x] T041 [P] Run `python -m sim run --config config/default.yaml --seed 42 --output-dir results/run1/` then same with `--output-dir results/run2/`; diff `run1/results.json` vs `run2/results.json` — must be identical (SC-002)
- [x] T042 [P] Run `python -m sim validate --config config/default.yaml` — must print "Configuration valid." with exit code 0
- [x] T043 [P] Run `python -m sim validate --config /dev/null` — must print validation errors with exit code 1 (FR-013)
- [x] T044 [P] Complete `docs/distributions.md` with final distribution types and parameters for all random variables (IA, PCP, CUL, PD, TEF[0..4], TDR[0..4], TMM[0..4], lead times)
- [x] T045 Run quickstart.md validation checklist end-to-end and confirm all six items pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 / Phase 3**: Depends on Phase 2 — delivers MVP
- **US3 / Phase 4**: Depends on Phase 3 (simulator.py must exist) — independent of US4
- **US4 / Phase 5**: Depends on Phase 3 — independent of US3
- **US2 / Phase 6**: Depends on Phase 3 (policies already wired in Phase 2) — independent of US3/US4
- **Traceability & Validation (Phase 7)**: Depends on Phases 3-6
- **Polish (Phase 8)**: Depends on all user story phases complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies — first deliverable
- **US2 (P1)**: Depends only on US1 infrastructure; policies implemented in Phase 2
- **US3 (P2)**: Depends on US1 (simulator loop); no dependency on US2 or US4
- **US4 (P3)**: Depends on US1 (simulator loop and `is_available`); no dependency on US2 or US3

### Within Each Phase

- All `[P]`-marked tasks have no file conflicts — safe to run in parallel
- T018–T024 must complete in order (each builds on the previous handler)
- T026–T029 must complete in order within Phase 4
- T031–T034 must complete in order within Phase 5

### Parallel Opportunities

```bash
# Phase 2 — all [P] tasks are independent files:
T009 lot.py  |  T010 order.py  |  T011 machine.py
T012 stage_queue.py  |  T013 stock.py  |  T014 sequencing.py
T015 collector.py  |  T016 reporter.py

# Phase 1 — parallel after T001, T002:
T003 default.yaml  |  T004 distributions.md

# After Phase 3 MVP is done, US3/US4/US2 can run in parallel:
Phase 4 (US3)  |  Phase 5 (US4)  |  Phase 6 (US2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T017) — CRITICAL
3. Complete Phase 3: User Story 1 (T018–T025)
4. **STOP and VALIDATE**: `python -m sim run --config config/default.yaml --seed 42` → check results.json
5. Run twice with same seed → diff output → must be identical

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready
2. Phase 3 (US1) → Baseline simulation running → **MVP**
3. Phase 4 (US3) + Phase 5 (US4) + Phase 6 (US2) in parallel → Full feature set
4. Phase 7 → Traceability and statistical validation
5. Phase 8 → Polish and validation

### Parallel Team Strategy

With multiple developers after Phase 3 completes:
- Developer A: Phase 4 — failure & maintenance handlers
- Developer B: Phase 5 — energy window handlers
- Developer C: Phase 6 — sequencing policy verification + config files
- Developer D: Phase 7 — trace export and statistical validation

---

## Notes

- `[P]` tasks touch different files — no conflicts
- `[Story]` label maps each task to a user story for traceability
- All time units: hours (float). `sim_time % 24` = hour of day for RHFM.
- `pending_maintenance` flag on `Machine` is the key for Option A maintenance.
- FR-015 redirect logic lives in `handle_machine_failure` — compare `remaining_repair_time` vs `TPM[compatible_type]`.
- FR-016: discard MACHINE_FAILURE if `machine.status in (SETUP, MAINTENANCE)`.
- QA stage: no materials consumed, no setup time, no `SD` indices.
- Lot stays SUSPENDED on the machine during repair — not requeued.
