import json
from pathlib import Path

import yaml

from l4_smartroute.recommender import _infer_capabilities

DEFAULTS = {
    "graphify_path": "./graphify-out/graph.json",
    "preferences": {
        "optimize_for": "balanced",
        "router_mode": "hybrid",
        "max_budget_per_task": None,
        "bfs_max_depth": 3,
    },
}

VALID_MODES = {"quality", "balanced", "performance", "token-saver"}
VALID_ROUTER_MODES = {"deterministic", "hybrid", "ai-review"}


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
        m.setdefault("status", "active")
        m.setdefault("confidence", "curated")
        m.setdefault("source", "models.json")
        validated.append(m)
    for m in validated:
        m.setdefault("capabilities", _infer_capabilities(m))
        m.setdefault("best_for", _best_for(m))
        m.setdefault("avoid_for", _avoid_for(m))
    return validated


def _best_for(model: dict) -> list[str]:
    strengths = set(model.get("strengths") or [])
    best = []
    if {"multi-file-refactoring", "cross-cutting-changes", "architecture-decisions"} & strengths:
        best.append("multi_file_refactor")
    if {"debugging", "bug-fixes"} & strengths:
        best.append("debugging")
    if "long-context" in strengths or int(model.get("context_window", 0)) >= 1_000_000:
        best.append("long_context_analysis")
    if {"documentation", "simple-fixes", "typo-corrections"} & strengths:
        best.append("simple_edit")
    if {"agentic-tasks", "ultra-coding"} & strengths:
        best.append("agentic_implementation")
    if not best:
        best.append("agentic_implementation")
    return best


def _avoid_for(model: dict) -> list[str]:
    tier = model.get("tier", "medium")
    avoid = []
    if tier == "low":
        avoid.extend(["architecture", "multi_file_refactor"])
    if model.get("status") in {"deprecated", "retired"}:
        avoid.append("new_work")
    return avoid


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

    router_mode = defaults_prefs.get("router_mode", "hybrid")
    if router_mode not in VALID_ROUTER_MODES:
        defaults_prefs["router_mode"] = "hybrid"

    cfg["preferences"] = defaults_prefs
    return cfg


def get_available_models(all_models: list[dict], model_ids: list[str]) -> list[dict]:
    id_set = set(model_ids)
    return [m for m in all_models if m["id"] in id_set]
