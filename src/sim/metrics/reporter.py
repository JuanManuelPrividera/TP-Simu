import csv
import json
from datetime import datetime

from sim.metrics.collector import MetricsCollector


STAGE_NAMES = ["printing", "binding", "qa", "packaging"]


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def generate_report(
    collector: MetricsCollector,
    meta: dict,
    energy_rates: list[float],
    machine_counts: list[int],
    sim_time: float,
) -> dict:
    tsp_per_machine = [
        collector.tsp[i] / machine_counts[i] if machine_counts[i] > 0 else 0.0
        for i in range(4)
    ]
    tpe = [_mean(samples) or 0.0 for samples in collector.tpe_samples]
    total_energy = sum(
        energy_rates[i] * collector.energy_active_time[i] for i in range(4)
    )
    energy_by_stage = {
        STAGE_NAMES[i]: round(energy_rates[i] * collector.energy_active_time[i], 4)
        for i in range(4)
    }
    tppt = _mean(collector.tppt_samples)
    cxtp = (total_energy / tppt) if tppt else None

    bottleneck = STAGE_NAMES[tpe.index(max(tpe))] if any(tpe) else None

    return {
        "meta": {
            **meta,
            "simulation_time": round(sim_time, 4),
            "run_timestamp": datetime.utcnow().isoformat(),
        },
        "metrics": {
            "TPPT": round(tppt, 4) if tppt is not None else None,
            "TPPL": round(_mean(collector.tppl_samples) or 0.0, 4),
            "CxTP": round(cxtp, 4) if cxtp is not None else None,
            "TSP": [round(v, 4) for v in tsp_per_machine],
            "TPE": [round(v, 4) for v in tpe],
            "PR": round(collector.rework_count / collector.total_lots, 4)
            if collector.total_lots
            else 0.0,
            "setup_count": collector.setup_count,
        },
        "bottleneck": bottleneck,
        "energy": {
            "total_cost": round(total_energy, 4),
            "by_stage": energy_by_stage,
        },
    }


def write_json(report: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def write_csv(report: dict, path: str) -> None:
    rows = []
    metrics = report.get("metrics", {})
    for key, val in metrics.items():
        if isinstance(val, list):
            for i, v in enumerate(val):
                rows.append({"metric": f"{key}[{i}]", "value": v})
        else:
            rows.append({"metric": key, "value": val})
    rows.append({"metric": "bottleneck", "value": report.get("bottleneck", "")})
    rows.append({"metric": "energy_total_cost", "value": report["energy"]["total_cost"]})
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
