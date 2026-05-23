"""CLI entry point: python -m sim <subcommand> [options]"""
import argparse
import json
import os
import sys

from sim.config.loader import load_config
from sim.engine.simulator import Simulator
from sim.metrics.reporter import generate_report, write_csv, write_json, write_trace_jsonl


def cmd_validate(args: argparse.Namespace) -> None:
    load_config(args.config)
    print("Configuration valid.")


def cmd_run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    seed = args.seed if args.seed is not None else config.simulation.seed
    trace_enabled = args.trace or config.output.event_log
    sim = Simulator(config, seed=seed, trace_enabled=trace_enabled)
    collector = sim.run()

    os.makedirs(args.output_dir, exist_ok=True)

    energy_rates = [
        config.stages.printing.energy_rate,
        config.stages.binding.energy_rate,
        config.stages.qa.energy_rate,
        config.stages.packaging.energy_rate,
    ]
    machine_counts = [
        config.stages.printing.machines,
        config.stages.binding.machines,
        config.stages.qa.machines,
        config.stages.packaging.machines,
    ]
    meta = {
        "config_file": args.config,
        "seed": seed,
        "orders_simulated": config.simulation.orders,
        "policy": config.sequencing.policy,
    }
    report = generate_report(collector, meta, energy_rates, machine_counts, sim.get_sim_time())

    fmt = args.format or config.output.format
    json_path = os.path.join(args.output_dir, "results.json")
    write_json(report, json_path)
    print(f"Results written to {json_path}")

    if trace_enabled:
        trace_path = os.path.join(args.output_dir, "trace.jsonl")
        write_trace_jsonl(collector.event_log, trace_path)
        print(f"Trace written to {trace_path}")

    if fmt in ("csv", "both"):
        csv_path = os.path.join(args.output_dir, "results.csv")
        write_csv(report, csv_path)
        print(f"Results written to {csv_path}")


def cmd_compare(args: argparse.Namespace) -> None:
    if not args.configs:
        print("ERROR: --configs requires at least one config file", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    comparison: dict[str, dict] = {}

    for config_path in args.configs:
        config = load_config(config_path)
        seed = args.seed if args.seed is not None else config.simulation.seed
        sim = Simulator(config, seed=seed)
        collector = sim.run()

        energy_rates = [
            config.stages.printing.energy_rate,
            config.stages.binding.energy_rate,
            config.stages.qa.energy_rate,
            config.stages.packaging.energy_rate,
        ]
        machine_counts = [
            config.stages.printing.machines,
            config.stages.binding.machines,
            config.stages.qa.machines,
            config.stages.packaging.machines,
        ]
        meta = {
            "config_file": config_path,
            "seed": seed,
            "orders_simulated": config.simulation.orders,
            "policy": config.sequencing.policy,
        }
        report = generate_report(collector, meta, energy_rates, machine_counts, sim.get_sim_time())
        label = config.sequencing.policy
        comparison[label] = report

    out_path = os.path.join(args.output_dir, "comparison.json")
    with open(out_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"Comparison written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="sim", description="Editorial Plant DES Simulator")
    sub = parser.add_subparsers(dest="command")

    p_val = sub.add_parser("validate", help="Validate a config file without running")
    p_val.add_argument("--config", required=True, help="Path to YAML config")

    p_run = sub.add_parser("run", help="Execute a simulation")
    p_run.add_argument("--config", required=True, help="Path to YAML config")
    p_run.add_argument("--seed", type=int, default=None, help="Random seed")
    p_run.add_argument("--output-dir", default="results", dest="output_dir")
    p_run.add_argument("--format", choices=["json", "csv", "both"], default=None)
    p_run.add_argument("--trace", action="store_true")

    p_cmp = sub.add_parser("compare", help="Compare multiple configs with same seed")
    p_cmp.add_argument("--configs", nargs="+", required=True)
    p_cmp.add_argument("--seed", type=int, default=None)
    p_cmp.add_argument("--output-dir", default="results", dest="output_dir")
    p_cmp.add_argument("--format", choices=["json", "csv", "both"], default="json")

    args = parser.parse_args()
    if args.command == "validate":
        cmd_validate(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "compare":
        cmd_compare(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
