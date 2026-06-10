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

VALID_MODES = {"quality", "balanced", "performance", "token-saver"}


def load_model_library(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    models = data.get("models", [])
    validated = []
    for m in models:
        if not m.get("id") or not m.get("cost"):
            continue
        m.setdefault("name", m["id"])
        m.setdefault("quality_score", 50)
        m.setdefault("speed", "medium")
        validated.append(m)
    return validated


def load_config(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}

    if "graphify_path" not in cfg:
        cfg["graphify_path"] = DEFAULTS["graphify_path"]

    if "available_models" not in cfg:
        cfg["available_models"] = []

    defaults_prefs = DEFAULTS["preferences"].copy()
    user_prefs = cfg.get("preferences") or {}
    defaults_prefs.update({k: v for k, v in user_prefs.items() if v is not None})

    mode = defaults_prefs["optimize_for"]
    if mode == "cost":
        defaults_prefs["optimize_for"] = "token-saver"
    elif mode not in VALID_MODES:
        defaults_prefs["optimize_for"] = "balanced"

    cfg["preferences"] = defaults_prefs
    return cfg


def get_available_models(all_models: list[dict], model_ids: list[str]) -> list[dict]:
    id_set = set(model_ids)
    return [m for m in all_models if m["id"] in id_set]
