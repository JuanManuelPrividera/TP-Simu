from dataclasses import dataclass


@dataclass
class MaterialStock:
    index: int
    name: str
    quantity: float
    reorder_point: float
    replenishment_quantity: float
    consumption_per_lot: float
    replenishment_pending: bool = False

    def consume(self, amount: float) -> bool:
        """Deduct amount if sufficient stock. Returns True on success."""
        if self.quantity >= amount:
            self.quantity -= amount
            return True
        return False

    def replenish(self, amount: float) -> None:
        self.quantity += amount
        self.replenishment_pending = False

    def needs_reorder(self) -> bool:
        return self.quantity <= self.reorder_point and not self.replenishment_pending
