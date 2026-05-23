# Research: Simulación de Planta Editorial Industrial

## 1. Event Queue Implementation

**Decision**: Custom event loop using Python's `heapq` (stdlib priority queue).

**Rationale**: The assignment mandates "Metodología: Evento a Evento" as an
academic exercise — the point is to demonstrate understanding of the event
scheduling mechanism. Using a framework like SimPy would abstract away the
core mechanics that must be implemented. `heapq` provides O(log n) push/pop,
is deterministic, and requires no external dependencies.

**Alternatives considered**:
- **SimPy**: Full-featured DES library, would satisfy all requirements, but
  hides the event queue and coroutine dispatch — inappropriate for an
  academic model that must expose these mechanics.
- `sortedcontainers.SortedList`: O(log n) insertion with stable ordering,
  but adds a dependency for no meaningful gain over heapq.
- **Custom doubly-linked list**: O(1) ordered insert but O(n) worst case
  rebuild; overkill for this scale.

**Event ordering tie-break**: When two events share the same timestamp, use
a monotonic integer counter as secondary sort key to ensure FIFO ordering
among simultaneous events (Python heapq is not stable on equal keys).

---

## 2. Random Number Generation & Named Streams

**Decision**: `numpy.random.default_rng(seed)` with one `Generator` per
random variable stream.

**Rationale**: NumPy's `default_rng` uses PCG64, which is high-quality,
seedable, and supports independent streams via `SeedSequence.spawn()`. Each
named stream (IA, PCP, TEF[i], TDR[i], etc.) gets its own generator derived
from the master seed — this ensures adding or removing one variable does not
shift the random sequence of all others, making policy comparisons valid.

**Stream assignment**:
```
master_seed → SeedSequence → spawn N child sequences
  stream["IA"]      → inter-arrival times
  stream["PCP"]     → page count distribution
  stream["CUL"]     → units per order
  stream["PD"]      → defect sampling at QA
  stream["TEF"][i]  → failure times per machine type
  stream["TDR"][i]  → repair durations per machine type
  stream["TMM"][i]  → maintenance durations per machine type
  stream["REPR"][i] → replenishment lead times per material
```

**Alternatives considered**:
- `random` (stdlib): No SeedSequence, streams must be faked with offset seeds
  — fragile and not reproducible across Python versions.
- `scipy.stats`: Adds heavy dependency; NumPy distributions are sufficient.

---

## 3. Configuration Format

**Decision**: YAML via `PyYAML`, validated with `pydantic` v2 models.

**Rationale**: YAML is human-readable and standard for configuration files.
Pydantic provides declarative validation with descriptive error messages —
required by FR-013. The schema model also serves as the authoritative
documentation of all parameters.

**Alternatives considered**:
- JSON: No comments, less readable for a configuration-heavy academic project.
- TOML: Good choice but less tooling support in academic environments.
- `.ini` / configparser: Cannot represent nested structures like `RHFM[5][CM]`.

---

## 4. Probability Distributions

All distributions are parameterized in configuration. Recommended defaults
for the editorial plant model (to be validated/adjusted by the analyst):

| Variable | Distribution | Parameters |
|---|---|---|
| IA (inter-arrival) | Exponential | rate λ (orders/hour) |
| PCP (page count) | Discrete (weights) | {pages: probability} map |
| CUL (units/order) | Discrete uniform | min, max |
| TPI (printing time) | Normal or Exponential | mean, std |
| TPE (binding time) | Normal or Exponential | mean, std |
| TPQA (QA time) | Uniform | min, max |
| TPE_emb (packaging time) | Normal | mean, std |
| TEF[i] (failure interval) | Exponential | MTBF per type |
| TDR[i] (repair duration) | Exponential | mean repair time |
| TMM[i] (maintenance duration) | Deterministic or Normal | duration |
| Lead time replenishment | Uniform | min, max |

All documented in `docs/distributions.md` per Constitution Principle III.

---

## 5. Output & Reporting

**Decision**: JSON primary export (human-readable + machine-parseable),
optional CSV for spreadsheet analysis.

**Rationale**: JSON maps naturally to the nested metric structure
(TSP[5], TPE[5] as arrays). CSV is flat but useful for quick analysis in
tools like Excel or pandas. Both are generated after every run.

---

## 6. CLI Design

**Decision**: `python -m sim run --config <file> [--seed N] [--output-dir DIR]`

Uses Python's `argparse` (stdlib) — no external CLI framework needed for a
single-command tool.
