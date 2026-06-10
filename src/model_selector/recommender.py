MAPPING = {
    ("low", "cost"):        ("low", None),
    ("low", "quality"):     ("medium", "low"),
    ("low", "balanced"):    ("low", None),
    ("medium", "cost"):     ("medium", "medium"),
    ("medium", "quality"):  ("high", "low"),
    ("medium", "balanced"): ("medium", "high"),
    ("high", "cost"):       ("medium", "high"),
    ("high", "quality"):    ("high", "high"),
    ("high", "balanced"):   ("high", "medium"),
    ("critical", "cost"):       ("high", "medium"),
    ("critical", "quality"):    ("high", "ultra"),
    ("critical", "balanced"):   ("high", "max"),
}

BUDGET_ALT_MAPPING = {
    ("low", "cost"):        None,
    ("low", "quality"):     ("low", None),
    ("low", "balanced"):    None,
    ("medium", "cost"):     ("low", None),
    ("medium", "quality"):  ("medium", "medium"),
    ("medium", "balanced"): ("low", None),
    ("high", "cost"):       ("low", None),
    ("high", "quality"):    ("medium", "high"),
    ("high", "balanced"):   ("medium", "high"),
    ("critical", "cost"):       ("medium", "high"),
    ("critical", "quality"):    ("high", "high"),
    ("critical", "balanced"):   ("medium", "high"),
}


def _find_model_by_tier(models: list[dict], tier: str) -> dict | None:
    for m in models:
        if m["tier"] == tier:
            return m
    return None


def _best_available(models: list[dict], tier: str) -> dict:
    model = _find_model_by_tier(models, tier)
    if model:
        return model
    tier_order = ["high", "medium", "low"]
    for t in tier_order:
        model = _find_model_by_tier(models, t)
        if model:
            return model
    return models[0]


def _resolve_effort(model: dict, desired_effort: str | None) -> str | None:
    if not model.get("effort_levels") or desired_effort is None:
        return None
    if desired_effort in model["effort_levels"]:
        return desired_effort
    return model["effort_levels"][-1]


def _estimate_cost(model: dict) -> str:
    input_cost = model["cost"]["input_per_1m"]
    output_cost = model["cost"]["output_per_1m"]
    low = round((input_cost * 0.005) + (output_cost * 0.002), 2)
    high = round((input_cost * 0.020) + (output_cost * 0.010), 2)
    return f"${low:.2f} - ${high:.2f}"


def recommend(complexity: str, available_models: list[dict], optimize_for: str) -> dict:
    tier, effort = MAPPING.get((complexity, optimize_for), ("high", "medium"))
    primary_model = _best_available(available_models, tier)
    primary_effort = _resolve_effort(primary_model, effort)

    budget_alt = None
    budget_entry = BUDGET_ALT_MAPPING.get((complexity, optimize_for))
    if budget_entry:
        alt_tier, alt_effort = budget_entry
        alt_model = _best_available(available_models, alt_tier)
        alt_effort_resolved = _resolve_effort(alt_model, alt_effort)
        if alt_model["id"] != primary_model["id"] or alt_effort_resolved != primary_effort:
            budget_alt = {
                "model": alt_model["id"],
                "effort_level": alt_effort_resolved,
                "reason": "Cheaper option, may need more iterations",
            }

    return {
        "optimize_for": optimize_for,
        "primary": {
            "model": primary_model["id"],
            "effort_level": primary_effort,
            "reason": f"Complexity: {complexity}",
        },
        "budget_alternative": budget_alt,
        "estimated_cost": {
            "primary": _estimate_cost(primary_model),
            "alternative": _estimate_cost(
                _best_available(available_models, budget_entry[0]) if budget_entry else primary_model
            ),
        },
    }
