from copy import deepcopy
from pathlib import Path

import yaml

from sim.config.loader import load_config
from sim.engine.simulator import Simulator
from sim.metrics.reporter import generate_report


def _build_config() -> dict:
    with open("config/default.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config = deepcopy(config)
    config["simulation"]["orders"] = 8000
    config["arrival"]["rate"] = 20.0
    config["order"]["units"]["min"] = 50
    config["order"]["units"]["max"] = 50
    config["order"]["book_types"] = ["A"]
    config["stages"]["printing"]["machines"] = 2
    config["stages"]["binding"]["machines"] = 2
    config["stages"]["qa"]["machines"] = 2
    config["stages"]["packaging"]["machines"] = 2
    config["stages"]["printing"]["processing_time"]["mean"] = 0.05
    config["stages"]["binding"]["processing_time"]["mean"] = 0.05
    config["stages"]["qa"]["processing_time"]["min"] = 0.01
    config["stages"]["qa"]["processing_time"]["max"] = 0.02
    config["stages"]["packaging"]["processing_time"]["mean"] = 0.03
    config["stages"]["packaging"]["processing_time"]["std"] = 0.005
    config["stages"]["printing"]["setup_time"] = 0.0
    config["stages"]["binding"]["setup_time"] = 0.0
    config["stages"]["packaging"]["setup_time"] = 0.0
    config["stages"]["printing"]["failure"]["mtbf"] = 1e9
    config["stages"]["binding"]["failure"]["mtbf"] = 1e9
    config["stages"]["qa"]["failure"]["mtbf"] = 1e9
    config["stages"]["packaging"]["failure"]["mtbf"] = 1e9
    config["maintenance"]["frequency"] = 0
    config["stages"]["dispatch"]["threshold"] = 1
    config["stages"]["qa"]["defect_probability"] = 0.05
    config["stages"]["qa"]["defect_threshold"] = 0.05

    for stage in ("printing", "binding", "qa", "packaging"):
        config["stages"][stage]["operating_windows"] = [[0, 24]]

    for material in config["materials"]:
        material["initial_stock"] = 1_000_000
        material["reorder_point"] = 0

    return config


def test_rework_rate_tracks_configured_probability_within_ten_percent(tmp_path: Path) -> None:
    path = tmp_path / "rework_config.yaml"
    path.write_text(yaml.safe_dump(_build_config()), encoding="utf-8")

    config = load_config(str(path))
    sim = Simulator(config, seed=42)
    collector = sim.run()
    report = generate_report(
        collector,
        meta={"config_file": str(path), "seed": 42, "orders_simulated": config.simulation.orders},
        energy_rates=[
            config.stages.printing.energy_rate,
            config.stages.binding.energy_rate,
            config.stages.qa.energy_rate,
            config.stages.packaging.energy_rate,
        ],
        machine_counts=[
            config.stages.printing.machines,
            config.stages.binding.machines,
            config.stages.qa.machines,
            config.stages.packaging.machines,
        ],
        sim_time=sim.get_sim_time(),
    )

    observed_pr = report["metrics"]["PR"]
    expected_pd = config.stages.qa.defect_probability

    assert collector.total_lots >= 5000
    assert observed_pr is not None
    assert abs(observed_pr - expected_pd) <= expected_pd * 0.1
