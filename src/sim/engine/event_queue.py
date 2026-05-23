import heapq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim.events.base import Event


class EventQueue:
    """Priority queue for simulation events ordered by (time, sequence_num)."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, "Event"]] = []
        self._counter = 0

    def push(self, event: "Event") -> None:
        heapq.heappush(self._heap, (event.time, self._counter, event))
        self._counter += 1

    def pop(self) -> "Event":
        if self.is_empty():
            raise IndexError("pop from empty EventQueue")
        _, _, event = heapq.heappop(self._heap)
        return event

    def peek(self) -> "Event":
        if self.is_empty():
            raise IndexError("peek at empty EventQueue")
        return self._heap[0][2]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)
