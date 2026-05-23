from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim.model.lot import Lot
    from sim.policies.sequencing import SequencingPolicy


class StageQueue:
    """Ordered waiting list of lots for a production stage."""

    def __init__(self, stage_index: int, policy: "SequencingPolicy") -> None:
        self.stage_index = stage_index
        self.policy = policy
        self._lots: list["Lot"] = []

    def enqueue(self, lot: "Lot") -> None:
        self._lots.append(lot)
        self._lots.sort(key=self.policy.sort_key)

    def dequeue(self) -> "Lot | None":
        if not self._lots:
            return None
        return self._lots.pop(0)

    def peek(self) -> "Lot | None":
        return self._lots[0] if self._lots else None

    def __len__(self) -> int:
        return len(self._lots)

    def __bool__(self) -> bool:
        return bool(self._lots)
