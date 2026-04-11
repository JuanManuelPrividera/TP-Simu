"""Main simulation engine."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from sim.config.schema import SimConfig
from sim.distributions.prng import PRNGFactory
from sim.engine.event_queue import EventQueue
from sim.events.base import Event, EventType
from sim.metrics.collector import MetricsCollector
from sim.model.lot import Lot, LotStatus, StageEnum
from sim.model.machine import Machine, MachineStatus
from sim.model.order import Order
from sim.model.stage_queue import StageQueue
from sim.model.stock import MaterialStock
from sim.policies.sequencing import make_policy

STAGE_NAMES = ["printing", "binding", "qa", "packaging"]
STAGE_ENUM = [StageEnum.PRINTING, StageEnum.BINDING, StageEnum.QA, StageEnum.PACKAGING]
NEXT_STAGE = {
    StageEnum.PRINTING: StageEnum.BINDING,
    StageEnum.BINDING: StageEnum.QA,
    StageEnum.QA: StageEnum.PACKAGING,
}


@dataclass
class SimState:
    config: SimConfig
    prng: PRNGFactory
    eq: EventQueue
    collector: MetricsCollector
    queues: list[StageQueue]           # index 0..3 = printing..packaging
    machines: list[list[Machine]]      # machines[stage_idx][machine_id]
    stocks: list[MaterialStock]        # index 0..4
    storage: list[Lot] = field(default_factory=list)  # finished lots
    clta: int = 0                      # finished lots in storage
    orders_completed: int = 0
    orders_created: int = 0
    _seq: int = 0
    orders_map: dict[int, Order] = field(default_factory=dict)

    def next_event(self, time: float, etype: EventType, payload: dict) -> Event:
        self._seq += 1
        return Event(time=time, seq=self._seq, type=etype, payload=payload)

    def push(self, time: float, etype: EventType, payload: dict | None = None) -> None:
        self.eq.push(self.next_event(time, etype, payload or {}))


class Simulator:
    def __init__(self, config: SimConfig, seed: int | None = None) -> None:
        self.config = config
        effective_seed = seed if seed is not None else config.simulation.seed
        prng = PRNGFactory(effective_seed)
        policy = make_policy(config.sequencing.policy)
        queues = [StageQueue(i, policy) for i in range(4)]
        machines = self._build_machines(config)
        stocks = self._build_stocks(config)
        self.state = SimState(
            config=config,
            prng=prng,
            eq=EventQueue(),
            collector=MetricsCollector(),
            queues=queues,
            machines=machines,
            stocks=stocks,
        )
        self._sim_time = 0.0

    # ── Initialisation helpers ────────────────────────────────────────────────

    @staticmethod
    def _build_machines(config: SimConfig) -> list[list[Machine]]:
        stage_cfgs = [
            config.stages.printing,
            config.stages.binding,
            config.stages.qa,
            config.stages.packaging,
        ]
        result = []
        for i, sc in enumerate(stage_cfgs):
            windows = [(w[0], w[1]) for w in sc.operating_windows]
            stage_machines = [
                Machine(id=j, type_index=i, operating_windows=windows, energy_rate=sc.energy_rate)
                for j in range(sc.machines)
            ]
            result.append(stage_machines)
        return result

    @staticmethod
    def _build_stocks(config: SimConfig) -> list[MaterialStock]:
        stocks = [None] * 5
        for mc in config.materials:
            stocks[mc.index] = MaterialStock(
                index=mc.index,
                name=mc.name,
                quantity=mc.initial_stock,
                reorder_point=mc.reorder_point,
                replenishment_quantity=mc.replenishment_quantity,
                consumption_per_lot=mc.consumption_per_lot,
            )
        return stocks  # type: ignore[return-value]

    def _schedule_initial_events(self) -> None:
        st = self.state
        # First order arrival
        ia = 1.0 / st.config.arrival.rate
        t_arrive = st.prng.exponential("IA", ia)
        st.push(t_arrive, EventType.ORDER_ARRIVAL)

        # Machine failures and maintenance for each machine
        fmp = st.config.maintenance.frequency
        maint_durations = st.config.maintenance.durations
        dur_map = {
            0: maint_durations.printing,
            1: maint_durations.binding,
            2: maint_durations.qa,
            3: maint_durations.packaging,
        }
        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        for i, machines in enumerate(st.machines):
            mtbf = stage_cfgs[i].failure.mtbf
            for m in machines:
                t_fail = st.prng.exponential(f"TEF_{i}", mtbf)
                st.push(t_fail, EventType.MACHINE_FAILURE, {"machine_type": i, "machine_id": m.id})
                if fmp > 0:
                    st.push(fmp, EventType.MAINTENANCE_DUE, {"machine_type": i, "machine_id": m.id})

        # Energy window events
        self._schedule_window_events()

    def _schedule_window_events(self) -> None:
        """Schedule WINDOW_OPEN/CLOSE for the simulation horizon."""
        st = self.state
        # Estimate horizon as orders * mean inter-arrival * some factor
        ia_mean = 1.0 / st.config.arrival.rate
        horizon = st.config.simulation.orders * ia_mean * 3
        cycles = math.floor(horizon / 24) + 2
        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        for i, sc in enumerate(stage_cfgs):
            for start_h, end_h in sc.operating_windows:
                if start_h == 0 and end_h == 24:
                    continue  # unrestricted — no events needed
                for cycle in range(cycles):
                    t_open = cycle * 24 + start_h
                    t_close = cycle * 24 + end_h
                    st.push(t_open, EventType.WINDOW_OPEN, {"machine_type": i})
                    st.push(t_close, EventType.WINDOW_CLOSE, {"machine_type": i})

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> MetricsCollector:
        self._schedule_initial_events()
        st = self.state

        while not st.eq.is_empty():
            event = st.eq.pop()
            self._sim_time = event.time

            if st.orders_completed >= st.config.simulation.orders:
                break

            self._dispatch(event)

        return st.collector

    def get_sim_time(self) -> float:
        return self._sim_time

    def _dispatch(self, event: Event) -> None:
        handlers = {
            EventType.ORDER_ARRIVAL: self._handle_order_arrival,
            EventType.STAGE_START: self._handle_stage_start,
            EventType.STAGE_END: self._handle_stage_end,
            EventType.SETUP_START: self._handle_setup_start,
            EventType.SETUP_END: self._handle_setup_end,
            EventType.MACHINE_FAILURE: self._handle_machine_failure,
            EventType.REPAIR_END: self._handle_repair_end,
            EventType.MAINTENANCE_DUE: self._handle_maintenance_due,
            EventType.MAINTENANCE_END: self._handle_maintenance_end,
            EventType.STOCK_REPLENISHMENT: self._handle_stock_replenishment,
            EventType.DISPATCH: self._handle_dispatch,
            EventType.WINDOW_OPEN: self._handle_window_open,
            EventType.WINDOW_CLOSE: self._handle_window_close,
        }
        handler = handlers.get(event.type)
        if handler:
            handler(event)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _handle_order_arrival(self, event: Event) -> None:
        st = self.state
        t = event.time
        order_id = st.orders_created
        st.orders_created += 1

        cfg = st.config
        page_count = int(st.prng.discrete("PCP", cfg.order.page_count.values, cfg.order.page_count.weights))
        unit_count = st.prng.uniform_int("CUL", cfg.order.units.min, cfg.order.units.max)
        book_type = st.prng.discrete("BOOK_TYPE", cfg.order.book_types, [1] * len(cfg.order.book_types))
        priority = st.prng.uniform_int("PRIORITY", cfg.order.priority_range[0], cfg.order.priority_range[1])

        order = Order(
            id=order_id,
            arrival_time=t,
            page_count=page_count,
            unit_count=unit_count,
            book_type=str(book_type),
            priority=priority,
        )
        st.orders_map[order_id] = order
        lots = order.create_lots(cfg.lots.books_per_lot)

        for lot in lots:
            lot.entry_time = t
            st.queues[0].enqueue(lot)

        # Schedule next arrival
        ia_mean = 1.0 / cfg.arrival.rate
        st.push(t + st.prng.exponential("IA", ia_mean), EventType.ORDER_ARRIVAL)

        # Try to start printing
        self._try_start_stage(0, t)

        # Check material reorder
        for mat_idx in [0, 1]:
            self._check_reorder(mat_idx, t)

    def _try_start_stage(self, stage_idx: int, t: float) -> None:
        """Try to start processing on any available machine at this stage."""
        st = self.state
        if not st.queues[stage_idx]:
            return

        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        sc = stage_cfgs[stage_idx]

        # Check material availability
        for mat_idx in sc.materials:
            stock = st.stocks[mat_idx]
            if stock.quantity < stock.consumption_per_lot:
                return  # not enough material

        for machine in st.machines[stage_idx]:
            if machine.is_available(t):
                lot = st.queues[stage_idx].peek()
                if lot is None:
                    break
                # Check if setup needed
                if machine.last_lot_type is not None and machine.last_lot_type != lot.book_type:
                    st.push(t, EventType.SETUP_START, {
                        "stage": stage_idx, "machine_id": machine.id,
                        "from_type": machine.last_lot_type, "to_type": lot.book_type,
                    })
                else:
                    st.push(t, EventType.STAGE_START, {"stage": stage_idx, "machine_id": machine.id})
                return  # one machine at a time per call

    def _handle_stage_start(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["stage"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        if not machine.is_available(t):
            return

        lot = st.queues[stage_idx].dequeue()
        if lot is None:
            return

        # Record queue wait time
        wait = t - lot.entry_time
        st.collector.record_queue_wait(stage_idx, wait)

        machine.status = MachineStatus.BUSY
        machine.current_lot = lot
        lot.status = LotStatus.IN_PROCESS
        lot.start_time = t

        # Sample processing time
        proc_time = self._sample_processing_time(stage_idx, t)
        lot.remaining_process_time = proc_time

        st.push(t + proc_time, EventType.STAGE_END, {"stage": stage_idx, "machine_id": machine_id})

    def _sample_processing_time(self, stage_idx: int, t: float) -> float:
        st = self.state
        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        sc = stage_cfgs[stage_idx]
        dist = sc.processing_time
        stream = f"PROC_{stage_idx}"
        if dist.distribution == "exponential":
            return st.prng.exponential(stream, dist.mean)
        elif dist.distribution == "normal":
            return st.prng.normal(stream, dist.mean, dist.std)
        elif dist.distribution == "uniform":
            return st.prng.uniform(stream, dist.min, dist.max)
        return dist.mean or 1.0

    def _handle_setup_start(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["stage"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        if machine.status != MachineStatus.IDLE:
            return

        lot = st.queues[stage_idx].peek()
        if lot is None:
            return

        machine.status = MachineStatus.SETUP
        st.collector.record_setup()

        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        setup_time = stage_cfgs[stage_idx].setup_time
        st.push(t + setup_time, EventType.SETUP_END, {"stage": stage_idx, "machine_id": machine_id})

    def _handle_setup_end(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["stage"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        machine.status = MachineStatus.IDLE
        # Now start the actual processing
        st.push(t, EventType.STAGE_START, {"stage": stage_idx, "machine_id": machine_id})

    def _handle_stage_end(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["stage"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]
        lot = machine.current_lot

        if lot is None:
            return

        # Record energy usage
        proc_duration = t - lot.start_time
        st.collector.record_energy(stage_idx, proc_duration)

        # Consume materials
        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        sc = stage_cfgs[stage_idx]
        for mat_idx in sc.materials:
            st.stocks[mat_idx].consume(st.stocks[mat_idx].consumption_per_lot)
            self._check_reorder(mat_idx, t)

        machine.status = MachineStatus.IDLE
        machine.current_lot = None
        machine.last_lot_type = lot.book_type

        # QA defect check
        if stage_idx == 2:  # QA
            qa_cfg = st.config.stages.qa
            pd = qa_cfg.defect_probability or 0.05
            pqa = qa_cfg.defect_threshold or 0.05
            sample = st.prng.random("PD")
            if sample < pd:
                # Lot fails QA — rework
                lot.rework_count += 1
                lot.stage = StageEnum.PRINTING
                lot.status = LotStatus.WAITING
                lot.entry_time = t
                st.collector.record_rework()
                st.queues[0].enqueue(lot)
                self._try_start_stage(0, t)
                self._check_reorder(0, t)
                self._check_reorder(1, t)
            else:
                # Lot passes — move to packaging
                lot.stage = StageEnum.PACKAGING
                lot.status = LotStatus.WAITING
                lot.entry_time = t
                st.queues[3].enqueue(lot)
                self._try_start_stage(3, t)
        elif stage_idx == 3:  # Packaging done
            lot.status = LotStatus.DONE
            lot.stage = StageEnum.DISPATCHED
            st.storage.append(lot)
            st.clta += 1
            st.collector.record_lot_done(lot, t)

            if st.clta >= st.config.stages.dispatch.threshold:
                st.push(t, EventType.DISPATCH)
        else:
            # Move to next stage
            next_stage = NEXT_STAGE[STAGE_ENUM[stage_idx]]
            next_idx = next_stage.value
            lot.stage = next_stage
            lot.status = LotStatus.WAITING
            lot.entry_time = t
            st.queues[next_idx].enqueue(lot)
            self._try_start_stage(next_idx, t)

        # Check pending maintenance (Option A)
        if machine.pending_maintenance:
            machine.pending_maintenance = False
            st.push(t, EventType.MAINTENANCE_DUE, {"machine_type": stage_idx, "machine_id": machine_id})
        else:
            # Try next lot on same machine
            self._try_start_stage(stage_idx, t)

    def _check_reorder(self, mat_idx: int, t: float) -> None:
        stock = self.state.stocks[mat_idx]
        if stock.needs_reorder():
            stock.replenishment_pending = True
            cfg = self.state.config.materials[mat_idx]
            lead = self._sample_lead_time(mat_idx)
            self.state.push(t + lead, EventType.STOCK_REPLENISHMENT, {"material_index": mat_idx})

    def _sample_lead_time(self, mat_idx: int) -> float:
        st = self.state
        cfg = st.config.materials[mat_idx]
        lt = cfg.lead_time
        stream = f"LT_{mat_idx}"
        if lt.distribution == "uniform":
            return st.prng.uniform(stream, lt.min, lt.max)
        return lt.min or 1.0

    def _handle_stock_replenishment(self, event: Event) -> None:
        st = self.state
        t = event.time
        mat_idx: int = event.payload["material_index"]
        cfg = st.config.materials[mat_idx]
        st.stocks[mat_idx].replenish(cfg.replenishment_quantity)

        # Try to restart any stages that use this material
        stage_cfgs = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ]
        for i, sc in enumerate(stage_cfgs):
            if mat_idx in sc.materials:
                self._try_start_stage(i, t)

    def _handle_dispatch(self, event: Event) -> None:
        st = self.state
        t = event.time
        dispatched = list(st.storage)
        st.storage.clear()
        st.clta = 0

        # Track order completions
        order_lots: dict[int, list[Lot]] = {}
        for lot in dispatched:
            lot.status = LotStatus.DISPATCHED
            order_lots.setdefault(lot.order_id, []).append(lot)

        for order_id, lots in order_lots.items():
            order = st.orders_map.get(order_id)
            if order and order_id not in st.collector.dispatched_orders:
                st.collector.record_order_done(order_id, order.arrival_time, t)
                st.orders_completed += 1

    def _handle_machine_failure(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["machine_type"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        # FR-016: ignore if immune
        if machine.is_failure_immune():
            return

        machine.status = MachineStatus.FAILED

        # Lot stays suspended
        if machine.current_lot:
            machine.current_lot.status = LotStatus.SUSPENDED
            elapsed = t - machine.current_lot.start_time
            machine.current_lot.remaining_process_time = max(
                0.0, machine.current_lot.remaining_process_time - elapsed
            )

        # Sample repair time
        sc = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ][stage_idx]
        repair_dist = sc.failure.repair_time
        repair_time = st.prng.exponential(f"TDR_{stage_idx}", repair_dist.mean)
        machine.t_repair_done = t + repair_time

        st.push(t + repair_time, EventType.REPAIR_END, {"machine_type": stage_idx, "machine_id": machine_id})
        # Next failure scheduled after repair
        st.push(t + repair_time + st.prng.exponential(f"TEF_{stage_idx}", sc.failure.mtbf),
                EventType.MACHINE_FAILURE, {"machine_type": stage_idx, "machine_id": machine_id})

        st.collector.record_downtime(stage_idx, repair_time)

        # FR-015: if all machines of this type are unavailable, evaluate redirect
        self._evaluate_redirect(stage_idx, t)

    def _evaluate_redirect(self, unavailable_stage: int, t: float) -> None:
        """FR-015: redirect lots if setup time on compatible machine < remaining repair time."""
        # For this model, stages are linear and not cross-compatible by default.
        # This hook point exists for future extension; currently no cross-type redirect.
        pass

    def _handle_repair_end(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["machine_type"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        machine.status = MachineStatus.IDLE

        if machine.current_lot and machine.current_lot.status == LotStatus.SUSPENDED:
            lot = machine.current_lot
            lot.status = LotStatus.IN_PROCESS
            lot.start_time = t
            st.push(t + lot.remaining_process_time, EventType.STAGE_END,
                    {"stage": stage_idx, "machine_id": machine_id})
            machine.status = MachineStatus.BUSY
        else:
            machine.current_lot = None
            # Reschedule maintenance from now
            if st.config.maintenance.frequency > 0:
                st.push(t + st.config.maintenance.frequency, EventType.MAINTENANCE_DUE,
                        {"machine_type": stage_idx, "machine_id": machine_id})
            self._try_start_stage(stage_idx, t)

    def _handle_maintenance_due(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["machine_type"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        if machine.status == MachineStatus.FAILED:
            return  # discard

        if machine.status == MachineStatus.BUSY:
            machine.pending_maintenance = True  # Option A: defer
            return

        if machine.status == MachineStatus.MAINTENANCE:
            return  # already in maintenance

        # IDLE or SETUP — start maintenance
        machine.status = MachineStatus.MAINTENANCE

        dur_map = {
            0: st.config.maintenance.durations.printing,
            1: st.config.maintenance.durations.binding,
            2: st.config.maintenance.durations.qa,
            3: st.config.maintenance.durations.packaging,
        }
        maint_duration = st.prng.normal(f"TMM_{stage_idx}", dur_map[stage_idx], dur_map[stage_idx] * 0.1)
        st.push(t + maint_duration, EventType.MAINTENANCE_END,
                {"machine_type": stage_idx, "machine_id": machine_id, "duration": maint_duration})
        st.collector.record_downtime(stage_idx, maint_duration)

    def _handle_maintenance_end(self, event: Event) -> None:
        st = self.state
        t = event.time
        stage_idx: int = event.payload["machine_type"]
        machine_id: int = event.payload["machine_id"]
        machine = st.machines[stage_idx][machine_id]

        machine.status = MachineStatus.IDLE
        machine.pending_maintenance = False
        machine.current_lot = None

        # Schedule next maintenance and reset failure clock
        fmp = st.config.maintenance.frequency
        if fmp > 0:
            st.push(t + fmp, EventType.MAINTENANCE_DUE,
                    {"machine_type": stage_idx, "machine_id": machine_id})

        sc = [
            st.config.stages.printing,
            st.config.stages.binding,
            st.config.stages.qa,
            st.config.stages.packaging,
        ][stage_idx]
        st.push(t + st.prng.exponential(f"TEF_{stage_idx}", sc.failure.mtbf),
                EventType.MACHINE_FAILURE, {"machine_type": stage_idx, "machine_id": machine_id})

        self._try_start_stage(stage_idx, t)

    def _handle_window_open(self, event: Event) -> None:
        stage_idx: int = event.payload["machine_type"]
        t = event.time
        self._try_start_stage(stage_idx, t)

    def _handle_window_close(self, event: Event) -> None:
        # No-op: machines check is_available before starting new lots
        pass
