from pathlib import Path

import yaml

from sim.config.loader import load_config
from sim.engine.simulator import Simulator


def _write_config(tmp_path: Path) -> Path:
    config = {
        "simulation": {"orders": 40, "seed": 42},
        "arrival": {"distribution": "exponential", "rate": 2.5},
        "order": {
            "page_count": {
                "distribution": "discrete",
                "values": [100, 200],
                "weights": [0.5, 0.5],
            },
            "units": {"distribution": "uniform_int", "min": 50, "max": 100},
            "book_types": ["A", "B"],
            "priority_range": [1, 3],
        },
        "lots": {"books_per_lot": 50},
        "stages": {
            "printing": {
                "machines": 1,
                "processing_time": {"distribution": "exponential", "mean": 0.6},
                "setup_time": 0.2,
                "energy_rate": 10.0,
                "operating_windows": [[8, 20]],
                "failure": {
                    "mtbf": 1.5,
                    "repair_time": {"distribution": "exponential", "mean": 0.3},
                },
                "materials": [0, 1],
            },
            "binding": {
                "machines": 1,
                "processing_time": {"distribution": "exponential", "mean": 0.5},
                "setup_time": 0.1,
                "energy_rate": 8.0,
                "operating_windows": [[8, 20]],
                "failure": {
                    "mtbf": 2.0,
                    "repair_time": {"distribution": "exponential", "mean": 0.2},
                },
                "materials": [2, 3],
            },
            "qa": {
                "machines": 1,
                "processing_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
                "setup_time": 0.0,
                "energy_rate": 2.0,
                "operating_windows": [[8, 20]],
                "defect_probability": 0.15,
                "defect_threshold": 0.15,
                "failure": {
                    "mtbf": 3.0,
                    "repair_time": {"distribution": "exponential", "mean": 0.1},
                },
                "materials": [],
            },
            "packaging": {
                "machines": 1,
                "processing_time": {"distribution": "normal", "mean": 0.4, "std": 0.05},
                "setup_time": 0.1,
                "energy_rate": 5.0,
                "operating_windows": [[8, 20]],
                "failure": {
                    "mtbf": 2.5,
                    "repair_time": {"distribution": "exponential", "mean": 0.2},
                },
                "materials": [4],
            },
            "dispatch": {"threshold": 1},
        },
        "materials": [
            {
                "index": 0,
                "name": "paper",
                "initial_stock": 20,
                "reorder_point": 15,
                "replenishment_quantity": 50,
                "consumption_per_lot": 10,
                "lead_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
            },
            {
                "index": 1,
                "name": "ink",
                "initial_stock": 10,
                "reorder_point": 8,
                "replenishment_quantity": 30,
                "consumption_per_lot": 5,
                "lead_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
            },
            {
                "index": 2,
                "name": "binding_material",
                "initial_stock": 16,
                "reorder_point": 12,
                "replenishment_quantity": 40,
                "consumption_per_lot": 8,
                "lead_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
            },
            {
                "index": 3,
                "name": "adhesive",
                "initial_stock": 8,
                "reorder_point": 6,
                "replenishment_quantity": 20,
                "consumption_per_lot": 3,
                "lead_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
            },
            {
                "index": 4,
                "name": "packaging_material",
                "initial_stock": 12,
                "reorder_point": 9,
                "replenishment_quantity": 25,
                "consumption_per_lot": 6,
                "lead_time": {"distribution": "uniform", "min": 0.1, "max": 0.2},
            },
        ],
        "maintenance": {
            "frequency": 2.0,
            "durations": {"printing": 0.3, "binding": 0.2, "qa": 0.1, "packaging": 0.15},
        },
        "sequencing": {"policy": "FIFO"},
        "output": {"event_log": True, "format": "json"},
    }
    path = tmp_path / "trace_config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_event_trace_contains_all_required_types_and_is_monotonic(tmp_path: Path) -> None:
    config = load_config(str(_write_config(tmp_path)))
    collector = Simulator(config, seed=42, trace_enabled=True).run()

    trace = collector.event_log
    assert trace

    observed_types = {entry["type"] for entry in trace}
    expected_types = {
        "ORDER_ARRIVAL",
        "STAGE_START",
        "STAGE_END",
        "SETUP_START",
        "SETUP_END",
        "MACHINE_FAILURE",
        "REPAIR_END",
        "MAINTENANCE_DUE",
        "MAINTENANCE_END",
        "STOCK_REPLENISHMENT",
        "DISPATCH",
        "WINDOW_OPEN",
        "WINDOW_CLOSE",
    }

    assert expected_types.issubset(observed_types)

    event_order = [(entry["time"], entry["seq"]) for entry in trace]
    assert event_order == sorted(event_order)
