import yaml
from pydantic import ValidationError

from sim.config.schema import SimConfig


def load_config(path: str) -> SimConfig:
    """Load and validate a YAML configuration file.

    Raises SystemExit with a descriptive message if validation fails (FR-013).
    """
    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        raise SystemExit(f"ERROR: Config file not found: {path}")
    except yaml.YAMLError as e:
        raise SystemExit(f"ERROR: Invalid YAML in {path}: {e}")

    if raw is None:
        raise SystemExit(f"ERROR: Config file is empty: {path}")

    try:
        return SimConfig.model_validate(raw)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"  [{loc}] {err['msg']}")
        msg = "ERROR: Configuration validation failed:\n" + "\n".join(errors)
        raise SystemExit(msg)
