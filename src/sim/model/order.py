import math
from dataclasses import dataclass, field

from sim.model.lot import Lot, LotStatus, StageEnum


@dataclass
class Order:
    id: int
    arrival_time: float
    page_count: int
    unit_count: int
    book_type: str
    priority: int
    material_profile: dict[int, float] = field(default_factory=dict)
    lots: list[Lot] = field(default_factory=list)

    def create_lots(self, clpl: int) -> list[Lot]:
        """Split order into lots that share the same book configuration."""
        n = math.ceil(self.unit_count / clpl)
        self.lots = []
        remaining_units = self.unit_count

        for i in range(n):
            units_in_lot = min(clpl, remaining_units)
            remaining_units -= units_in_lot
            material_requirements = {
                mat_idx: per_unit_amount * units_in_lot
                for mat_idx, per_unit_amount in self.material_profile.items()
            }
            self.lots.append(
                Lot(
                    id=f"{self.id}-{i}",
                    order_id=self.id,
                    book_type=self.book_type,
                    priority=self.priority,
                    page_count=self.page_count,
                    units_in_lot=units_in_lot,
                    material_requirements=material_requirements,
                    stage=StageEnum.PRINTING,
                    status=LotStatus.WAITING,
                    arrival_time=self.arrival_time,
                    entry_time=self.arrival_time,
                )
            )
        return self.lots
