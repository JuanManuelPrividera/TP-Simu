from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim.model.lot import Lot


class MachineStatus(Enum):
    IDLE = auto()
    BUSY = auto()
    SETUP = auto()
    FAILED = auto()
    MAINTENANCE = auto()


# Statuses immune to failure events (FR-016)
FAILURE_IMMUNE = {MachineStatus.SETUP, MachineStatus.MAINTENANCE}


@dataclass
class Machine:
    id: int                          # unique within its type
    type_index: int                  # 0=printing, 1=binding, 2=qa, 3=packaging
    status: MachineStatus = MachineStatus.IDLE
    current_lot: "Lot | None" = None
    last_lot_type: str | None = None
    pending_maintenance: bool = False
    t_repair_done: float = 0.0       # used to evaluate FR-015 redirect logic
    operating_windows: list[tuple[float, float]] = field(default_factory=lambda: [(0.0, 24.0)])
    energy_rate: float = 0.0         # CEM[i]

    def in_window(self, sim_time: float) -> bool:
        """Return True if sim_time falls within any operating window."""
        hour = sim_time % 24.0
        for start, end in self.operating_windows:
            if start <= hour < end:
                return True
            # handle windows that wrap midnight (e.g. 22–6)
            if start > end and (hour >= start or hour < end):
                return True
        return False

    def is_available(self, sim_time: float) -> bool:
        """True if machine can accept a new lot right now."""
        return self.status == MachineStatus.IDLE and self.in_window(sim_time)

    def is_failure_immune(self) -> bool:
        return self.status in FAILURE_IMMUNE
