import json
from pathlib import Path

import yaml

DEFAULTS = {
    "graphify_path": "./graphify-out/graph.json",
    "preferences": {
        "optimize_for": "balanced",
        "max_budget_per_task": None,
        "bfs_max_depth": 3,
    },
}


def load_model_library(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["models"]


def load_config(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    if "graphify_path" not in cfg:
        cfg["graphify_path"] = DEFAULTS["graphify_path"]

    defaults_prefs = DEFAULTS["preferences"].copy()
    user_prefs = cfg.get("preferences") or {}
    defaults_prefs.update({k: v for k, v in user_prefs.items() if v is not None})
    cfg["preferences"] = defaults_prefs

    return cfg


def get_available_models(all_models: list[dict], model_ids: list[str]) -> list[dict]:
    id_set = set(model_ids)
    return [m for m in all_models if m["id"] in id_set]
