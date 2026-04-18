import numpy as np


class PRNGFactory:
    """
    Manages named, independent random streams derived from a master seed.

    Each named stream is a separate numpy Generator spawned from a
    SeedSequence. Adding or removing streams does not shift other streams.
    """

    def __init__(self, master_seed: int) -> None:
        self._seed_seq = np.random.SeedSequence(master_seed)
        self._streams: dict[str, np.random.Generator] = {}
        self._stream_index: dict[str, int] = {}
        self._next_index = 0

    def get_stream(self, name: str) -> np.random.Generator:
        if name not in self._streams:
            # Use a deterministic sub-seed based on stream registration order
            # We create a new SeedSequence from a hash of the name for stability
            named_seed = np.random.SeedSequence(
                int.from_bytes(name.encode(), "big") & 0xFFFFFFFF
                ^ (self._seed_seq.entropy & 0xFFFFFFFF)  # type: ignore[operator]
            )
            self._streams[name] = np.random.default_rng(named_seed)
        return self._streams[name]

    # ── Convenience samplers ──────────────────────────────────────────────────

    def exponential(self, stream: str, mean: float) -> float:
        return float(self.get_stream(stream).exponential(scale=mean))

    def normal(self, stream: str, mean: float, std: float) -> float:
        return max(0.0, float(self.get_stream(stream).normal(loc=mean, scale=std)))

    def uniform(self, stream: str, lo: float, hi: float) -> float:
        return float(self.get_stream(stream).uniform(low=lo, high=hi))

    def uniform_int(self, stream: str, lo: int, hi: int) -> int:
        return int(self.get_stream(stream).integers(low=lo, high=hi + 1))

    def discrete(self, stream: str, values: list, weights: list) -> object:
        probs = np.array(weights, dtype=float)
        probs /= probs.sum()
        idx = int(self.get_stream(stream).choice(len(values), p=probs))
        return values[idx]

    def random(self, stream: str) -> float:
        """Uniform [0, 1)."""
        return float(self.get_stream(stream).random())
