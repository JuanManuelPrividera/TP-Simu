from dataclasses import dataclass, field
from enum import Enum, auto
from functools import total_ordering


class EventType(Enum):
    ORDER_ARRIVAL = auto()
    STAGE_START = auto()
    STAGE_END = auto()
    SETUP_START = auto()
    SETUP_END = auto()
    MACHINE_FAILURE = auto()
    REPAIR_END = auto()
    MAINTENANCE_DUE = auto()
    MAINTENANCE_END = auto()
    STOCK_REPLENISHMENT = auto()
    DISPATCH = auto()
    WINDOW_OPEN = auto()
    WINDOW_CLOSE = auto()


@total_ordering
@dataclass
class Event:
    time: float
    seq: int
    type: EventType
    payload: dict = field(default_factory=dict)

    def __lt__(self, other: "Event") -> bool:
        return (self.time, self.seq) < (other.time, other.seq)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return (self.time, self.seq) == (other.time, other.seq)

    def __hash__(self) -> int:
        return hash((self.time, self.seq))
