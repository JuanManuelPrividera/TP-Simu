from dataclasses import dataclass
from enum import Enum, auto


class StageEnum(Enum):
    PRINTING = 0
    BINDING = 1
    QA = 2
    PACKAGING = 3
    DISPATCHED = 4


class LotStatus(Enum):
    WAITING = auto()
    IN_PROCESS = auto()
    SUSPENDED = auto()  # machine failed while processing
    DONE = auto()       # finished packaging, in storage
    DISPATCHED = auto()


@dataclass
class Lot:
    id: str                          # e.g. "42-3" (order 42, lot 3)
    order_id: int
    book_type: str
    priority: int
    page_count: int
    units_in_lot: int
    material_requirements: dict[int, float]
    stage: StageEnum = StageEnum.PRINTING
    status: LotStatus = LotStatus.WAITING
    rework_count: int = 0
    entry_time: float = 0.0          # time lot entered current queue
    start_time: float = 0.0          # time processing started on current machine
    total_production_time: float = 0.0
    remaining_process_time: float = 0.0  # used when machine fails mid-process
    arrival_time: float = 0.0        # time the parent order arrived
