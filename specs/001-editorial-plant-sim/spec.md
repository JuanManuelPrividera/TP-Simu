# Feature Specification: Simulación de Planta Editorial Industrial

**Feature Branch**: `001-editorial-plant-sim`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: Discrete-event simulation of an industrial book publishing plant (TPSimulacion.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Baseline Plant Simulation Run (Priority: P1)

An analyst configures the simulation with a set of parameters (machine counts,
lot sizes, arrival rates, material reorder points, maintenance schedule, QA
threshold, sequencing policy, energy windows) and runs a single full simulation.
At the end of the run, the system produces a complete report of all operational
metrics so the analyst can understand the current plant behavior.

**Why this priority**: All comparative analyses depend on the ability to run a
single, fully-instrumented simulation and collect accurate results. Without this
foundation nothing else is testable.

**Independent Test**: Run the simulation with default parameters for a fixed
random seed. Verify that the output report contains values for every required
metric (TPPT, TPPL, CxTP, TSP per stage, TPE per machine type, PR) and that
re-running with the same seed produces identical results.

**Acceptance Scenarios**:

1. **Given** a valid configuration file and a random seed,
   **When** the analyst runs the simulation,
   **Then** the system produces a metrics report with all required output
   variables and no errors.

2. **Given** the same configuration file and the same seed run twice,
   **When** both runs complete,
   **Then** all metric values are identical (reproducibility guarantee).

3. **Given** a configuration file where `CM[i]` for some stage is zero,
   **When** the analyst runs the simulation,
   **Then** the system rejects the configuration with a clear error message
   before starting.

4. **Given** a simulation run where raw material stock for stage i reaches zero,
   **When** the reorder point `SPR[i]` is crossed,
   **Then** a replenishment event is scheduled and production resumes once
   materials arrive.

---

### User Story 2 — Sequencing Policy Comparison (Priority: P1)

An analyst configures three simulation runs — one per sequencing policy (FIFO,
Priority-based, Book-type-based) — using identical parameters and the same
random seed, then compares average production times, queue wait times, and
bottleneck locations across runs.

**Why this priority**: The primary study objective is evaluating sequencing
criteria. This is the core analytical deliverable of the assignment.

**Independent Test**: Run simulations with `PS=FIFO`, `PS=Priority`, and
`PS=BookType` using the same seed. Verify that the metric report for each run
contains distinct values and that the system correctly applies the specified
ordering rule to the lot queue at each stage.

**Acceptance Scenarios**:

1. **Given** three configurations identical except for `PS`,
   **When** all three runs complete,
   **Then** the system produces one report per configuration, each clearly
   labeled with the policy used.

2. **Given** a queue with lots of different priorities and types,
   **When** `PS=Priority` is active,
   **Then** higher-priority lots are always processed before lower-priority
   lots at each stage (verified in trace log).

3. **Given** a queue with lots of different book types,
   **When** `PS=BookType` is active,
   **Then** lots are grouped by type to minimize setup changes between
   consecutive lots at each machine.

4. **Given** three policy comparison runs,
   **When** results are reviewed,
   **Then** the report includes `TPPT`, `TPPL`, `TPE` per stage, and
   bottleneck identification for each policy.

---

### User Story 3 — Maintenance Strategy Analysis (Priority: P2)

An analyst compares two maintenance strategies — preventive-only and
corrective-only — by running the simulation with the same random seed and
measuring downtime per stage, rework rates, and total throughput under each
strategy.

**Why this priority**: Maintenance policy (planned vs. reactive) is an explicit
analysis target of the study.

**Independent Test**: Run with `FMP > 0` (preventive maintenance enabled) and
`FMP = 0` (corrective only). Verify that `TSP[i]` values differ between runs
and that machine failure/repair events appear correctly in the event trace.

**Acceptance Scenarios**:

1. **Given** preventive maintenance is enabled with frequency `FMP`,
   **When** a machine's uptime exceeds `FMP`,
   **Then** a scheduled maintenance event is generated before the next
   failure event for that machine.

2. **Given** a machine failure event occurs,
   **When** corrective maintenance begins,
   **Then** the machine is removed from active processing for duration `TDR[i]`
   and queued lots accumulate until repair completes.

3. **Given** both strategies are compared,
   **When** the analyst reviews results,
   **Then** the report shows per-stage downtime (`TSP[i]`) broken down into
   repair time, idle time, and setup time.

---

### User Story 4 — Energy-Constrained Scheduling Analysis (Priority: P3)

An analyst configures machine operating windows (`RHFM`) to restrict which hours
each machine type may run, then evaluates the impact on production throughput,
queue buildup during off-peak hours, and total energy cost.

**Why this priority**: Energy constraints add operational complexity and are an
explicit variable in the study, but they are secondary to sequencing and
maintenance comparisons.

**Independent Test**: Configure `RHFM` to restrict all machines to 8-hour
daytime windows. Verify that no lot processing begins outside the configured
window, that lots accumulate in queues during off-hours, and that energy cost
tracking accumulates only during active periods.

**Acceptance Scenarios**:

1. **Given** an operating window `RHFM[i]` defined for machine type i,
   **When** the simulation clock is outside that window,
   **Then** no new lot processing starts on machines of type i, and the
   queue holds pending lots.

2. **Given** a machine resumes operation at the start of its window,
   **When** lots are waiting in the queue,
   **Then** processing resumes immediately according to the active sequencing
   policy.

3. **Given** a completed simulation run with energy constraints,
   **When** the analyst reviews the report,
   **Then** the report includes total energy cost (`CxTP`) computed as
   active machine time × energy rate per time slot.

---

### Edge Cases

- **QA rework with insufficient raw material**: A lot that fails QA and must
  be reprinted waits in the printing queue until sufficient raw materials
  (`SD[0]`, `SD[1]`) are available. Replenishment events are triggered
  normally; the lot does not skip the queue once materials arrive.

- **All machines of a type simultaneously under maintenance**: If the
  remaining maintenance time for all machines of type i exceeds the time
  required to reconfigure a machine of a different compatible type, the lot
  is redirected to that reconfigured machine. Otherwise the lot waits in the
  queue until at least one machine of type i becomes available.

- **Dispatch threshold reached during an ongoing dispatch**: Whenever `CLTA`
  reaches `CPTD`, a dispatch event is triggered immediately and
  unconditionally, regardless of whether a prior dispatch is already in
  progress. All finished lots at that moment are dispatched.

- **Machine failure during setup**: This scenario is excluded from the model.
  Machines are considered immune to failure while in setup state. Failures
  can only occur during active processing or idle state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST simulate the full five-stage production pipeline
  (printing → binding → QA → packaging → dispatch) as discrete events in
  the correct sequence.
- **FR-002**: The system MUST support multiple parallel machines per stage,
  with machine count per stage configurable via `CM[i]`.
- **FR-003**: The system MUST model random machine failures using inter-failure
  time distribution `TEF[i]` and repair duration `TDR[i]` per machine type.
- **FR-004**: The system MUST support scheduled preventive maintenance with
  configurable frequency `FMP` and duration `TMM[i]` per machine type.
- **FR-005**: The system MUST apply per-stage setup times `TPM[i]` when a
  machine switches between lot types or configurations.
- **FR-006**: The system MUST support three lot sequencing policies selectable
  via `PS`: FIFO, Priority, and Book-type grouping.
- **FR-007**: The system MUST enforce machine operating windows `RHFM[i]` and
  prevent lot processing outside those windows.
- **FR-008**: The system MUST track five raw material stocks `SD[0..4]`, trigger
  replenishment events when stock falls to or below `SPR[i]`, and block
  stage processing when required materials are unavailable. Lots blocked by
  material shortage MUST wait in the queue and resume when stock is restored.
- **FR-009**: The system MUST route lots failing QA (defect probability `PD ≥
  PQA`) back to the printing stage for rework; if raw materials are
  insufficient at that moment, the rework lot MUST wait in the printing
  queue until replenishment completes.
- **FR-010**: The system MUST dispatch all finished lots whenever storage count
  `CLTA` reaches the configured dispatch threshold `CPTD`, triggering
  immediately and unconditionally even if a prior dispatch is in progress.
- **FR-015**: When all machines of a given type are under maintenance, the
  system MUST compare remaining maintenance time against the setup time
  required to redirect the lot to a compatible machine of a different type.
  If setup time is shorter, the lot MUST be redirected; otherwise it MUST
  wait for the original machine type to become available.
- **FR-016**: Machine failures MUST only occur during active processing or idle
  state. Machines in setup state MUST be immune to failure events.
- **FR-011**: The system MUST collect and report all output metrics: `TPPT`,
  `TPPL`, `CxTP`, `TSP[5]`, `TPE[5]`, `PR`.
- **FR-012**: The system MUST produce identical results when run with the same
  configuration and random seed (deterministic replay).
- **FR-013**: The system MUST validate the configuration file before starting
  and report all invalid or missing parameters.
- **FR-014**: The system MUST export results to a structured format (JSON or
  CSV) for post-simulation analysis.

### Key Entities

- **Order (Pedido)**: An external demand for a book; characterized by page
  count, unit quantity, arrival time, and priority.
- **Lot (Lote)**: A subdivision of an order; the unit that moves through the
  production pipeline; has a type (book type), current stage, and status.
- **Machine (Máquina)**: A processing resource at a given stage; has a type,
  status (idle | busy | setup | failed | maintenance), and current
  configuration.
- **Queue (Cola CLM[i])**: The ordered waiting list of lots for a stage;
  ordering determined by active sequencing policy.
- **Material Stock (SD[i])**: The available quantity of a raw material consumed
  by a stage; triggers replenishment events when it falls to the reorder point.
- **Event**: A timestamped occurrence that changes system state and may
  schedule future events (e.g., LotArrived, ProcessingComplete, MachineFailed,
  MaintenanceScheduled, StockReplenished, Dispatched).
- **Metrics Collector**: A stateful recorder that accumulates running statistics
  throughout the simulation and produces the final report.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single simulation run with 500 orders completes without errors
  and produces a report covering all 11 required metrics.
- **SC-002**: Two runs with identical configuration and seed produce
  byte-for-byte identical metric reports.
- **SC-003**: Policy comparison runs (US2) produce distinct `TPPT` values
  across all three sequencing policies, demonstrating the model's sensitivity
  to the policy variable.
- **SC-004**: The event trace correctly records all event types (arrival,
  processing start/end, failure, repair, maintenance, replenishment,
  dispatch) with monotonically increasing timestamps.
- **SC-005**: Rework rate `PR` reported by the simulation is statistically
  consistent with the configured defect probability `PD` over long runs
  (within ±10% of expected value for 1000+ lots).
- **SC-006**: Configuring restrictive energy windows reduces total active
  machine time compared to unrestricted runs, and the difference is
  reflected in the energy cost metric `CxTP`.

## Assumptions

- Orders arrive following the inter-arrival distribution `IA`; order
  generation begins at simulation time 0.
- Each order is divided into lots of fixed size `CLPL` (books per lot);
  fractional lots are rounded up.
- The simulation horizon is defined by total number of orders to simulate
  (not wall-clock time), unless explicitly configured otherwise.
- Book priority for the Priority sequencing policy is derived from order
  attributes; the priority scale and mapping are defined in configuration.
- Book type grouping for the BookType policy groups lots by a discrete
  type attribute to minimize machine setup changes.
- Replenishment lead time is assumed to follow a configurable distribution;
  materials arrive after the lead time elapses.
- Machine failures cannot occur during the setup phase; only during active
  processing or idle state. This simplification is a model boundary decision.
- Energy cost is computed as a flat rate per machine type per active time
  unit, with no demand-charge modeling.
- Simulation results are intended for academic analysis, not production
  deployment; no authentication, multi-user, or persistence requirements
  apply.
- A single simulation run is single-threaded; no distributed or parallel
  execution is required.
