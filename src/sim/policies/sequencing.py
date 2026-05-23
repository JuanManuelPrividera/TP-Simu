from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim.model.lot import Lot


class SequencingPolicy(ABC):
    @abstractmethod
    def sort_key(self, lot: "Lot") -> tuple:
        ...


class FIFOPolicy(SequencingPolicy):
    """First-in, first-out by queue entry time."""

    def sort_key(self, lot: "Lot") -> tuple:
        return (lot.entry_time,)


class PriorityPolicy(SequencingPolicy):
    """Higher priority first; ties broken by entry time."""

    def sort_key(self, lot: "Lot") -> tuple:
        return (-lot.priority, lot.entry_time)


class BookTypePolicy(SequencingPolicy):
    """Group by book_type to minimize setup changes; within group, FIFO."""

    def sort_key(self, lot: "Lot") -> tuple:
        return (lot.book_type, lot.entry_time)


def make_policy(name: str) -> SequencingPolicy:
    mapping = {
        "FIFO": FIFOPolicy,
        "PRIORITY": PriorityPolicy,
        "BOOK_TYPE": BookTypePolicy,
    }
    if name not in mapping:
        raise ValueError(f"Unknown sequencing policy: {name!r}")
    return mapping[name]()
