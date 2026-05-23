from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim.events.base import Event
    from sim.model.lot import Lot

NUM_STAGES = 4  # printing, binding, qa, packaging (dispatch is not a machine stage)


@dataclass
class MetricsCollector:
    tppt_samples: list[float] = field(default_factory=list)   # per order
    tppl_samples: list[float] = field(default_factory=list)   # per lot
    tsp: list[float] = field(default_factory=lambda: [0.0] * NUM_STAGES)
    tpe_samples: list[list[float]] = field(
        default_factory=lambda: [[] for _ in range(NUM_STAGES)]
    )
    rework_count: int = 0
    total_lots: int = 0
    energy_active_time: list[float] = field(default_factory=lambda: [0.0] * NUM_STAGES)
    setup_count: int = 0
    event_log: list[dict] = field(default_factory=list)
    dispatched_orders: set[int] = field(default_factory=set)
    # Per order: order_id -> lot completion times
    _order_lot_times: dict[int, list[float]] = field(default_factory=dict)

    def record_lot_done(self, lot: "Lot", sim_time: float) -> None:
        production_time = sim_time - lot.arrival_time
        self.tppl_samples.append(production_time)
        self.total_lots += 1

        order_id = lot.order_id
        if order_id not in self._order_lot_times:
            self._order_lot_times[order_id] = []
        self._order_lot_times[order_id].append(sim_time)

    def record_order_done(self, order_id: int, arrival_time: float, sim_time: float) -> None:
        """Called when all lots of an order are dispatched."""
        if order_id not in self.dispatched_orders:
            self.dispatched_orders.add(order_id)
            self.tppt_samples.append(sim_time - arrival_time)

    def record_queue_wait(self, stage_idx: int, duration: float) -> None:
        if 0 <= stage_idx < NUM_STAGES:
            self.tpe_samples[stage_idx].append(duration)

    def record_downtime(self, stage_idx: int, duration: float) -> None:
        if 0 <= stage_idx < NUM_STAGES:
            self.tsp[stage_idx] += duration

    def record_energy(self, stage_idx: int, duration: float) -> None:
        if 0 <= stage_idx < NUM_STAGES:
            self.energy_active_time[stage_idx] += duration

    def record_rework(self) -> None:
        self.rework_count += 1

    def record_setup(self) -> None:
        self.setup_count += 1

    def record_event(self, event: "Event") -> None:
        self.event_log.append(
            {
                "time": event.time,
                "seq": event.seq,
                "type": event.type.name,
                "payload": event.payload,
            }
        )
