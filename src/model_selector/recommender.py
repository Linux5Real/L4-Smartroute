SPEED_ORDER = {"fast": 0, "medium": 1, "slow": 2}

MAPPING = {
    ("low", "quality"):        ("medium", "low"),
    ("low", "balanced"):       ("low", None),
    ("low", "performance"):    ("low", None),
    ("low", "token-saver"):    ("low", None),

    ("medium", "quality"):     ("high", "medium"),
    ("medium", "balanced"):    ("medium", "high"),
    ("medium", "performance"): ("low", "high"),
    ("medium", "token-saver"): ("low", "medium"),

    ("high", "quality"):       ("ultra", "high"),
    ("high", "balanced"):      ("high", "high"),
    ("high", "performance"):   ("medium", "xhigh"),
    ("high", "token-saver"):   ("low", "high"),

    ("critical", "quality"):    ("ultra", "max"),
    ("critical", "balanced"):   ("ultra", "high"),
    ("critical", "performance"): ("high", "max"),
    ("critical", "token-saver"): ("medium", "high"),
}

BUDGET_ALT_MAPPING = {
    ("low", "quality"):        ("low", None),
    ("low", "balanced"):       None,
    ("low", "performance"):    None,
    ("low", "token-saver"):    None,

    ("medium", "quality"):     ("medium", "medium"),
    ("medium", "balanced"):    ("low", None),
    ("medium", "performance"): ("low", "medium"),
    ("medium", "token-saver"): None,

    ("high", "quality"):       ("high", "high"),
    ("high", "balanced"):      ("medium", "high"),
    ("high", "performance"):   ("low", "high"),
    ("high", "token-saver"):   ("low", "medium"),

    ("critical", "quality"):    ("high", "max"),
    ("critical", "balanced"):   ("high", "high"),
    ("critical", "performance"): ("medium", "high"),
    ("critical", "token-saver"): ("low", "high"),
}


def _models_of_tier(models: list[dict], tier: str) -> list[dict]:
    return [m for m in models if m["tier"] == tier]


def _best_for_mode(models: list[dict], tier: str, optimize_for: str) -> dict:
    tier_models = _models_of_tier(models, tier)
    if not tier_models:
        for fallback in ("ultra", "high", "medium", "low"):
            tier_models = _models_of_tier(models, fallback)
            if tier_models:
                break
    if not tier_models:
        return models[0]

    if optimize_for == "performance":
        tier_models.sort(key=lambda m: (
            SPEED_ORDER.get(m.get("speed", "medium"), 1),
            -m.get("quality_score", 50),
        ))
    elif optimize_for == "token-saver":
        tier_models.sort(key=lambda m: (
            m["cost"]["input_per_1m"] + m["cost"]["output_per_1m"],
            -m.get("quality_score", 50),
        ))
    elif optimize_for == "quality":
        tier_models.sort(key=lambda m: -m.get("quality_score", 50))
    else:
        tier_models.sort(key=lambda m: (
            -m.get("quality_score", 50),
            m["cost"]["input_per_1m"] + m["cost"]["output_per_1m"],
        ))

    return tier_models[0]


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


def _build_reason(complexity: str, optimize_for: str, model: dict) -> str:
    mode_labels = {
        "quality": "Quality",
        "balanced": "Balanced",
        "performance": "Performance (DLSS)",
        "token-saver": "Token-Saver",
    }
    mode = mode_labels.get(optimize_for, optimize_for)
    cost_total = model["cost"]["input_per_1m"] + model["cost"]["output_per_1m"]
    return f"Complexity: {complexity} | Mode: {mode} | ${cost_total:.2f}/1M tokens"


def recommend(complexity: str, available_models: list[dict], optimize_for: str) -> dict:
    tier, effort = MAPPING.get((complexity, optimize_for), ("high", "medium"))
    primary_model = _best_for_mode(available_models, tier, optimize_for)
    primary_effort = _resolve_effort(primary_model, effort)

    budget_alt = None
    budget_entry = BUDGET_ALT_MAPPING.get((complexity, optimize_for))
    if budget_entry:
        alt_tier, alt_effort = budget_entry
        alt_model = _best_for_mode(available_models, alt_tier, optimize_for)
        alt_effort_resolved = _resolve_effort(alt_model, alt_effort)
        if alt_model["id"] != primary_model["id"] or alt_effort_resolved != primary_effort:
            budget_alt = {
                "model": alt_model["id"],
                "effort_level": alt_effort_resolved,
                "reason": "Cheaper option, may need more iterations",
            }

    alt_cost_model = primary_model
    if budget_entry:
        alt_cost_model = _best_for_mode(available_models, budget_entry[0], optimize_for)

    return {
        "optimize_for": optimize_for,
        "primary": {
            "model": primary_model["id"],
            "effort_level": primary_effort,
            "reason": _build_reason(complexity, optimize_for, primary_model),
        },
        "budget_alternative": budget_alt,
        "estimated_cost": {
            "primary": _estimate_cost(primary_model),
            "alternative": _estimate_cost(alt_cost_model),
        },
    }
