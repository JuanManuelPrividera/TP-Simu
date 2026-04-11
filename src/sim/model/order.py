import math
from dataclasses import dataclass, field

from sim.model.lot import Lot, StageEnum, LotStatus


@dataclass
class Order:
    id: int
    arrival_time: float
    page_count: int
    unit_count: int
    book_type: str
    priority: int
    lots: list[Lot] = field(default_factory=list)

    def create_lots(self, clpl: int) -> list[Lot]:
        """Split order into ceil(unit_count / clpl) lots."""
        n = math.ceil(self.unit_count / clpl)
        self.lots = [
            Lot(
                id=f"{self.id}-{i}",
                order_id=self.id,
                book_type=self.book_type,
                priority=self.priority,
                stage=StageEnum.PRINTING,
                status=LotStatus.WAITING,
                arrival_time=self.arrival_time,
                entry_time=self.arrival_time,
            )
            for i in range(n)
        ]
        return self.lots
