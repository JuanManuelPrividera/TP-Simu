# Data Model: Simulación de Planta Editorial Industrial

## Entities

### Order (Pedido)

Represents an external demand entering the system.

| Field | Type | Description |
|---|---|---|
| `id` | int | Unique auto-incremented identifier |
| `arrival_time` | float | Simulation time when the order arrived |
| `page_count` | int | Number of pages (sampled from PCP) |
| `unit_count` | int | Total books ordered (sampled from CUL) |
| `book_type` | str | Discrete type used for BookType sequencing policy |
| `priority` | int | Priority level (higher = more urgent); used by Priority policy |
| `lots` | list[Lot] | Child lots created from this order |

**Derived**:
- `lot_count = ceil(unit_count / CLPL)`

---

### Lot (Lote)

The unit of work that flows through the production pipeline. Each order is
split into N lots of fixed size `CLPL`.

| Field | Type | Description |
|---|---|---|
| `id` | int | Unique identifier (e.g., `order_id-lot_seq`) |
| `order_id` | int | Parent order reference |
| `book_type` | str | Inherited from order; drives setup logic |
| `priority` | int | Inherited from order; drives Priority sequencing |
| `stage` | StageEnum | Current pipeline stage |
| `status` | LotStatus | WAITING \| IN_PROCESS \| DONE \| DISPATCHED |
| `rework_count` | int | Number of times this lot has failed QA (for PR metric) |
| `entry_time` | float | Time the lot entered its current queue |
| `start_time` | float | Time processing started on the current machine |
| `total_production_time` | float | Accumulated time from first entry to dispatch |

**StageEnum**: PRINTING | BINDING | QA | PACKAGING | DISPATCHED

**LotStatus**: WAITING | IN_PROCESS | SUSPENDED | DONE | DISPATCHED

Note: `SUSPENDED` is the status when the machine processing the lot fails
(the lot stays on the machine until repair completes).

---

### Machine (Máquina)

A processing resource at a given stage. Multiple machines of the same type
may exist in parallel.

| Field | Type | Description |
|---|---|---|
| `id` | int | Unique identifier within its type |
| `type_index` | int | Index into CM[6]: 0=printing, 1=binding, 2=QA, 3=packaging, 4=dispatch |
| `status` | MachineStatus | IDLE \| BUSY \| SETUP \| FAILED \| MAINTENANCE |
| `current_lot` | Lot \| None | The lot currently being processed (or suspended) |
| `last_lot_type` | str \| None | Book type of the last processed lot (setup detection) |
| `pending_maintenance` | bool | Whether maintenance is deferred until current lot finishes |
| `t_available` | float | Earliest time this machine can start a new lot |
| `operating_windows` | list[tuple] | `RHFM[i]`: list of (start_hour, end_hour) tuples |
| `energy_rate` | float | `CEM[i]`: energy cost per unit time when active |

**MachineStatus**: IDLE | BUSY | SETUP | FAILED | MAINTENANCE

**Immunity rule**: Failure events for a machine in SETUP or MAINTENANCE status
are discarded without effect (FR-016).

---

### StageQueue (Cola CLM[i])

The ordered waiting list of lots for each stage. The ordering is determined
by the active sequencing policy `PS`.

| Field | Type | Description |
|---|---|---|
| `stage` | StageEnum | Which stage this queue belongs to |
| `policy` | SequencingPolicy | FIFO \| PRIORITY \| BOOK_TYPE |
| `lots` | ordered collection | Lots waiting to be processed |

**Sequencing policies**:
- `FIFO`: lots ordered by arrival time in queue (earliest first)
- `PRIORITY`: lots ordered by `priority` descending, then by arrival time
- `BOOK_TYPE`: lots grouped by `book_type` to minimize setup changes; within
  a group, ordered by arrival time

---

### MaterialStock (SD[i])

Tracks available raw materials consumed by each stage.

| Index | Material | Consumed by |
|---|---|---|
| 0 | Paper (Papel) | Printing |
| 1 | Ink (Tinta) | Printing |
| 2 | Binding material (Encuadernado) | Binding |
| 3 | Binding adhesive (Adhesivo) | Binding |
| 4 | Packaging material (Embalaje) | Packaging |

| Field | Type | Description |
|---|---|---|
| `index` | int | 0–4 |
| `quantity` | float | Current available stock |
| `reorder_point` | float | `SPR[i]`: trigger replenishment below this level |
| `replenishment_pending` | bool | Prevents duplicate replenishment events |
| `consumption_per_lot` | float | Units consumed per lot processed |

---

### Event (Evento)

Base for all simulation events. Stored in the global priority queue ordered
by `(time, sequence_num)`.

| Field | Type | Description |
|---|---|---|
| `time` | float | Simulation time when the event fires |
| `sequence_num` | int | Monotonic counter for tie-breaking |
| `type` | EventType | See event catalogue below |
| `payload` | dict | Event-specific data |

**Event catalogue**:

| EventType | Payload | Description |
|---|---|---|
| `ORDER_ARRIVAL` | order_id | New order enters the system |
| `STAGE_START` | lot_id, machine_id | Machine begins processing a lot |
| `STAGE_END` | lot_id, machine_id | Machine finishes processing a lot |
| `SETUP_START` | machine_id, from_type, to_type | Setup begins |
| `SETUP_END` | machine_id | Setup completes; processing can begin |
| `MACHINE_FAILURE` | machine_id | Machine breaks down |
| `REPAIR_END` | machine_id | Corrective repair completes |
| `MAINTENANCE_START` | machine_id | Preventive maintenance begins |
| `MAINTENANCE_END` | machine_id | Preventive maintenance completes |
| `STOCK_REPLENISHMENT` | material_index, quantity | Materials arrive |
| `DISPATCH` | lot_ids | Finished lots are dispatched |
| `WINDOW_OPEN` | machine_type | Energy window starts (machines may resume) |
| `WINDOW_CLOSE` | machine_type | Energy window ends (machines must stop) |

---

### MetricsCollector

Accumulates statistics throughout the simulation run.

| Field | Type | Description |
|---|---|---|
| `tppt_samples` | list[float] | Total production time per completed order |
| `tppl_samples` | list[float] | Production time per lot |
| `tsp` | float[5] | Accumulated non-production time per machine type |
| `tpe` | list[list[float]] | Queue wait time samples per machine type |
| `rework_count` | int | Total lots that failed QA at least once |
| `total_lots` | int | Total lots completed |
| `energy_cost` | float | Accumulated CEM[i] × active_time |
| `event_log` | list[dict] | Full event trace (optional, enabled by flag) |

**Derived metrics** (computed at report time):
- `TPPT = mean(tppt_samples)`
- `TPPL = mean(tppl_samples)`
- `TSP[i] = tsp[i] / machine_count[i]` (per machine average)
- `TPE[i] = mean(tpe[i])`
- `PR = rework_count / total_lots`
- `CxTP = energy_cost / TPPT`

---

## State Diagram: Machine

```
           init
            │
            ▼
          IDLE ◄──────────────────────────────────────────┐
            │                                             │
   lot available                               repair/maintenance done
   + materials ok                                         │
   + in window                                            │
            │                                             │
            ▼                                        FAILED / MAINTENANCE
    [same type?]                                          ▲
       │       │                                          │
      yes      no                              machine_failure / maintenance_due
       │       │                               (only from IDLE or BUSY)
       │       ▼                                          │
       │     SETUP ──── setup_done ──────────────────────┘
       │       │                                   │
       └───────┤                                   │
               ▼                                   │
             BUSY ──── lot_done ──────► IDLE       │
               │                                   │
               └───── failure/maintenance ──────────┘
                       (BUSY → FAILED/MAINTENANCE)
```

---

## State Diagram: Lot

```
created
   │
   ▼
WAITING (in CLM[stage])
   │
   └─── machine picks lot ──► IN_PROCESS
                                   │
                          ┌────────┴────────┐
                    machine fails      stage completes
                          │                 │
                          ▼                 ▼
                      SUSPENDED       [QA check?]
                          │            │         │
                    repair done      pass       fail
                          │            │         │
                          ▼            ▼         ▼
                      IN_PROCESS    WAITING   WAITING
                                  (next      (CLM[0]
                                   stage)    rework)
                                      │
                                  last stage
                                      │
                                      ▼
                                    DONE
                                      │
                               CLTA >= CPTD
                                      │
                                      ▼
                                 DISPATCHED
```
