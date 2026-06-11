from __future__ import annotations

from l4_smartroute.task_classifier import classify_task

SPEED_ORDER = {"fast": 0, "medium": 1, "slow": 2}
SPEED_SCORE = {"fast": 90, "medium": 70, "slow": 45}
TIER_LEVEL = {"low": 1, "medium": 2, "high": 3, "ultra": 4}

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

TASK_WEIGHTS: dict[str, dict[str, float]] = {
    "simple_edit": {
        "cost_efficiency": 0.35,
        "speed": 0.25,
        "coding": 0.15,
        "instruction_following": 0.25,
    },
    "docs": {
        "cost_efficiency": 0.30,
        "speed": 0.20,
        "long_context": 0.15,
        "instruction_following": 0.25,
        "structured_output": 0.10,
    },
    "bugfix": {
        "debugging": 0.35,
        "coding": 0.25,
        "instruction_following": 0.15,
        "refactoring": 0.15,
        "cost_efficiency": 0.10,
    },
    "debugging": {
        "debugging": 0.45,
        "coding": 0.20,
        "architecture": 0.15,
        "instruction_following": 0.15,
        "cost_efficiency": 0.05,
    },
    "multi_file_refactor": {
        "refactoring": 0.35,
        "coding": 0.20,
        "architecture": 0.15,
        "long_context": 0.15,
        "instruction_following": 0.15,
    },
    "architecture": {
        "architecture": 0.40,
        "agentic_work": 0.20,
        "refactoring": 0.15,
        "instruction_following": 0.15,
        "cost_efficiency": 0.10,
    },
    "test_generation": {
        "coding": 0.30,
        "debugging": 0.25,
        "structured_output": 0.20,
        "instruction_following": 0.15,
        "cost_efficiency": 0.10,
    },
    "review": {
        "debugging": 0.30,
        "refactoring": 0.20,
        "long_context": 0.15,
        "instruction_following": 0.20,
        "architecture": 0.15,
    },
    "long_context_analysis": {
        "long_context": 0.40,
        "instruction_following": 0.20,
        "structured_output": 0.15,
        "speed": 0.10,
        "cost_efficiency": 0.15,
    },
    "agentic_implementation": {
        "agentic_work": 0.35,
        "coding": 0.25,
        "debugging": 0.15,
        "refactoring": 0.15,
        "instruction_following": 0.10,
    },
    "frontend_ui": {
        "frontend": 0.50,
        "coding": 0.15,
        "instruction_following": 0.20,
        "structured_output": 0.10,
        "cost_efficiency": 0.05,
    },
    "backend_systems": {
        "backend": 0.35,
        "debugging": 0.20,
        "architecture": 0.15,
        "refactoring": 0.15,
        "instruction_following": 0.10,
        "cost_efficiency": 0.05,
    },
    "math_science": {
        "math_science": 0.45,
        "architecture": 0.15,
        "instruction_following": 0.15,
        "structured_output": 0.10,
        "cost_efficiency": 0.15,
    },
}

MODE_MULTIPLIERS = {
    "quality": {"fit": 0.82, "tier": 0.18, "cost": 0.00, "speed": 0.00},
    "balanced": {"fit": 0.72, "tier": 0.16, "cost": 0.08, "speed": 0.04},
    "performance": {"fit": 0.60, "tier": 0.12, "cost": 0.10, "speed": 0.18},
    "token-saver": {"fit": 0.55, "tier": 0.10, "cost": 0.30, "speed": 0.05},
}

STATUS_PENALTY = {
    "active": 0,
    "preview": 2,
    "unknown": 4,
    "deprecated": 18,
    "retired": 40,
}

AI_REVIEW_TASKS = {
    "architecture",
    "debugging",
    "multi_file_refactor",
    "review",
    "agentic_implementation",
    "backend_systems",
    "frontend_ui",
    "math_science",
}

VALID_ROUTER_MODES = {"deterministic", "hybrid", "ai-review"}


def _cost_per_1m(model: dict) -> float:
    return float(model["cost"]["input_per_1m"]) + float(model["cost"]["output_per_1m"])


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
            _cost_per_1m(m),
        ))
    elif optimize_for == "token-saver":
        tier_models.sort(key=lambda m: (
            _cost_per_1m(m),
            -m.get("quality_score", 50),
        ))
    elif optimize_for == "quality":
        tier_models.sort(key=lambda m: -m.get("quality_score", 50))
    else:
        tier_models.sort(key=lambda m: (
            -m.get("quality_score", 50),
            _cost_per_1m(m),
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


def _context_score(context_window: int) -> int:
    if context_window >= 1_000_000:
        return 96
    if context_window >= 400_000:
        return 88
    if context_window >= 200_000:
        return 76
    if context_window >= 128_000:
        return 66
    return 50


def _infer_capabilities(model: dict) -> dict[str, float]:
    base = float(model.get("quality_score", 50))
    strengths = set(model.get("strengths") or [])
    model_id = model.get("id", "").lower()
    provider = model.get("provider", "").lower()
    caps = {
        "coding": base,
        "debugging": base - 4,
        "refactoring": base - 5,
        "architecture": base - 6,
        "agentic_work": base - 6,
        "long_context": _context_score(int(model.get("context_window", 0))),
        "instruction_following": base,
        "structured_output": base - 2,
        "speed": SPEED_SCORE.get(model.get("speed", "medium"), 70),
        "frontend": base - 3,
        "backend": base,
        "math_science": base - 8,
    }
    boosts = {
        "code-generation": ("coding", 8),
        "ultra-coding": ("coding", 12),
        "bug-fixes": ("debugging", 10),
        "debugging": ("debugging", 12),
        "moderate-refactoring": ("refactoring", 8),
        "multi-file-refactoring": ("refactoring", 12),
        "cross-cutting-changes": ("refactoring", 8),
        "architecture-decisions": ("architecture", 12),
        "complex-reasoning": ("architecture", 8),
        "agentic-tasks": ("agentic_work", 12),
        "long-context": ("long_context", 12),
        "documentation": ("instruction_following", 6),
        "boilerplate": ("structured_output", 6),
        "simple-fixes": ("speed", 4),
    }
    for strength in strengths:
        if strength in boosts:
            key, boost = boosts[strength]
            caps[key] = caps.get(key, base) + boost

    if "claude" in model_id:
        caps["frontend"] += 12
        caps["instruction_following"] += 4
    if "gemini" in model_id:
        caps["frontend"] += 8
        caps["long_context"] += 2
    if provider == "openai":
        caps["frontend"] += 4
    if any(token in model_id for token in ("coder", "codestral")):
        caps["coding"] += 10
        caps["backend"] += 8
        caps["structured_output"] += 4
    if any(token in model_id for token in ("o3", "o4", "gpt")) or provider == "openai":
        caps["math_science"] += 8
        caps["structured_output"] += 4
    if any(token in model_id for token in ("gemini", "grok")):
        caps["math_science"] += 5
    if any(token in model_id for token in ("deepseek", "qwen", "kimi")):
        caps["backend"] += 6
        caps["coding"] += 5
        caps["frontend"] -= 8

    for key, value in model.get("capabilities", {}).items():
        caps[key] = float(value)

    return {key: max(0, min(100, value)) for key, value in caps.items()}


def _cost_efficiency(model: dict, min_cost: float, max_cost: float) -> float:
    cost = _cost_per_1m(model)
    if max_cost <= min_cost:
        return 75
    return 100 - ((cost - min_cost) / (max_cost - min_cost) * 100)


def _tier_fit(model: dict, target_tier: str, complexity: str) -> float:
    model_level = TIER_LEVEL.get(model.get("tier", "medium"), 2)
    target_level = TIER_LEVEL.get(target_tier, 2)
    distance = abs(model_level - target_level)
    fit = 100 - (distance * 18)
    if complexity in {"high", "critical"} and model_level < target_level:
        fit -= (target_level - model_level) * 14
    return max(0, fit)


def _task_fit(model: dict, task_type: str, min_cost: float, max_cost: float) -> tuple[float, dict[str, float]]:
    caps = _infer_capabilities(model)
    caps["cost_efficiency"] = _cost_efficiency(model, min_cost, max_cost)
    weights = TASK_WEIGHTS.get(task_type, TASK_WEIGHTS["agentic_implementation"])
    score = sum(caps.get(cap, 50) * weight for cap, weight in weights.items())
    return score, caps


def _score_model(
    model: dict,
    *,
    task_type: str,
    complexity: str,
    target_tier: str,
    optimize_for: str,
    min_cost: float,
    max_cost: float,
) -> dict:
    fit, caps = _task_fit(model, task_type, min_cost, max_cost)
    mode = MODE_MULTIPLIERS.get(optimize_for, MODE_MULTIPLIERS["balanced"])
    tier = _tier_fit(model, target_tier, complexity)
    cost = caps["cost_efficiency"]
    speed = caps.get("speed", SPEED_SCORE.get(model.get("speed", "medium"), 70))
    status = model.get("status", "active")
    score = (
        fit * mode["fit"]
        + tier * mode["tier"]
        + cost * mode["cost"]
        + speed * mode["speed"]
        - STATUS_PENALTY.get(status, STATUS_PENALTY["unknown"])
    )
    return {
        "model": model,
        "score": score,
        "fit": fit,
        "tier_fit": tier,
        "cost_efficiency": cost,
        "speed": speed,
    }


def _build_reason(complexity: str, optimize_for: str, model: dict, task_type: str, candidate: dict) -> str:
    mode_labels = {
        "quality": "Quality",
        "balanced": "Balanced",
        "performance": "Performance (DLSS)",
        "token-saver": "Token-Saver",
    }
    mode = mode_labels.get(optimize_for, optimize_for)
    cost_total = _cost_per_1m(model)
    return (
        f"Task: {task_type} | Complexity: {complexity} | Mode: {mode} | "
        f"fit {candidate['fit']:.0f}/100 | ${cost_total:.2f}/1M tokens"
    )


def _candidate_payload(candidate: dict) -> dict:
    model = candidate["model"]
    return {
        "model": model["id"],
        "score": round(candidate["score"], 1),
        "fit": round(candidate["fit"], 1),
        "cost_per_1m": round(_cost_per_1m(model), 4),
        "provider": model.get("provider"),
        "tier": model.get("tier"),
        "status": model.get("status", "active"),
    }


def _review_candidate_payload(candidate: dict, desired_effort: str | None, task_type: str) -> dict:
    model = candidate["model"]
    caps = _infer_capabilities(model)
    relevant_caps = sorted(
        TASK_WEIGHTS.get(task_type, {}).keys(),
        key=lambda cap: TASK_WEIGHTS.get(task_type, {}).get(cap, 0),
        reverse=True,
    )
    return {
        "model": model["id"],
        "provider": model.get("provider"),
        "name": model.get("name", model["id"]),
        "score": round(candidate["score"], 1),
        "fit": round(candidate["fit"], 1),
        "cost_per_1m": round(_cost_per_1m(model), 4),
        "context_window": model.get("context_window"),
        "speed": model.get("speed"),
        "tier": model.get("tier"),
        "status": model.get("status", "active"),
        "best_for": model.get("best_for", [])[:4],
        "avoid_for": model.get("avoid_for", [])[:4],
        "suggested_effort": _resolve_effort(model, desired_effort),
        "capabilities": {
            cap: round(caps.get(cap, 50), 1)
            for cap in relevant_caps
            if cap != "cost_efficiency"
        },
    }


def _budget_alternative(scored: list[dict], primary: dict, primary_effort: str | None) -> dict | None:
    primary_model = primary["model"]
    primary_cost = _cost_per_1m(primary_model)
    minimum_score = primary["score"] * 0.78
    cheaper = [
        c for c in scored
        if c["model"]["id"] != primary_model["id"]
        and _cost_per_1m(c["model"]) < primary_cost
        and c["score"] >= minimum_score
    ]
    if not cheaper:
        return None
    cheaper.sort(key=lambda c: (_cost_per_1m(c["model"]), -c["score"]))
    alt = cheaper[0]
    alt_effort = _resolve_effort(alt["model"], primary_effort)
    return {
        "model": alt["model"]["id"],
        "effort_level": alt_effort,
        "reason": f"Cheaper option with {alt['fit']:.0f}/100 task fit",
    }


def _primary_candidate(scored: list[dict], optimize_for: str) -> dict:
    best = scored[0]
    if optimize_for != "token-saver":
        return best
    good_enough = [candidate for candidate in scored if candidate["score"] >= best["score"] * 0.96]
    good_enough.sort(key=lambda candidate: (_cost_per_1m(candidate["model"]), -candidate["score"]))
    return good_enough[0]


def _review_reason(
    *,
    router_mode: str,
    complexity: str,
    task_type: str,
    scored: list[dict],
    blast_radius: dict | None,
) -> str | None:
    if router_mode == "deterministic":
        return None
    if router_mode == "ai-review":
        return "router_mode=ai-review"
    if router_mode != "hybrid":
        return None
    if complexity == "low" and task_type in {"docs", "simple_edit"}:
        return None
    if len(scored) < 2:
        return None

    gap = scored[0]["score"] - scored[1]["score"]
    files_affected = int((blast_radius or {}).get("files_affected", 0))
    communities_crossed = int((blast_radius or {}).get("communities_crossed", 0))
    if complexity in {"high", "critical"}:
        return f"{complexity} complexity"
    if task_type in AI_REVIEW_TASKS:
        return f"task_type={task_type}"
    if gap <= 4:
        return f"close candidates, top gap {gap:.1f}"
    if files_affected >= 8 or communities_crossed >= 3:
        return "large Graphify blast radius"
    return None


def _ai_review_payload(
    *,
    required: bool,
    reason: str | None,
    prompt: str,
    complexity: str,
    optimize_for: str,
    task_type: str,
    router_mode: str,
    target_tier: str,
    effort: str | None,
    blast_radius: dict | None,
    candidates: list[dict],
) -> dict:
    prompt_excerpt = " ".join(prompt.split())[:700]
    policy = [
        "Select exactly one model from candidates.",
        "Never select deprecated or retired models unless every active candidate is clearly worse.",
        "Respect optimize_for: token-saver favors cheaper good-enough models; quality favors best task fit; performance favors speed; balanced favors fit per cost.",
        "Use Graphify blast radius to avoid underpowered models for high-risk cross-module work.",
        "Return JSON only with model, effort_level, confidence, and one short reason.",
    ]
    return {
        "required": required,
        "reason": reason,
        "router_mode": router_mode,
        "context": {
            "prompt_excerpt": prompt_excerpt,
            "complexity": complexity,
            "task_type": task_type,
            "optimize_for": optimize_for,
            "target_tier": target_tier,
            "blast_radius": {
                "files_affected": int((blast_radius or {}).get("files_affected", 0)),
                "communities_crossed": int((blast_radius or {}).get("communities_crossed", 0)),
                "avg_centrality": (blast_radius or {}).get("avg_centrality", 0),
                "max_edge_depth": int((blast_radius or {}).get("max_edge_depth", 0)),
            },
        },
        "policy": policy,
        "candidates": [
            _review_candidate_payload(candidate, effort, task_type)
            for candidate in candidates[:5]
        ],
    }


def _legacy_reason(complexity: str, optimize_for: str, model: dict) -> str:
    mode_labels = {
        "quality": "Quality",
        "balanced": "Balanced",
        "performance": "Performance (DLSS)",
        "token-saver": "Token-Saver",
    }
    mode = mode_labels.get(optimize_for, optimize_for)
    cost_total = _cost_per_1m(model)
    return f"Complexity: {complexity} | Mode: {mode} | ${cost_total:.2f}/1M tokens"


def _legacy_recommend(complexity: str, available_models: list[dict], optimize_for: str) -> dict:
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
            "reason": _legacy_reason(complexity, optimize_for, primary_model),
        },
        "budget_alternative": budget_alt,
        "estimated_cost": {
            "primary": _estimate_cost(primary_model),
            "alternative": _estimate_cost(alt_cost_model),
        },
        "routing": {
            "task_type": None,
            "target_tier": tier,
            "router_mode": "deterministic",
            "scored_candidates": [],
            "ai_review": {
                "required": False,
                "reason": None,
                "router_mode": "deterministic",
                "context": {},
                "policy": [],
                "candidates": [],
            },
        },
    }


def recommend(
    complexity: str,
    available_models: list[dict],
    optimize_for: str,
    *,
    task_type: str | None = None,
    prompt: str = "",
    blast_radius: dict | None = None,
    router_mode: str = "deterministic",
) -> dict:
    if not available_models:
        raise ValueError("available_models must contain at least one model")
    if task_type is None and not prompt and not blast_radius:
        return _legacy_recommend(complexity, available_models, optimize_for)
    if router_mode not in VALID_ROUTER_MODES:
        router_mode = "deterministic"

    files_affected = int((blast_radius or {}).get("files_affected", 0))
    communities_crossed = int((blast_radius or {}).get("communities_crossed", 0))
    resolved_task_type = task_type or classify_task(
        prompt,
        complexity=complexity,
        files_affected=files_affected,
        communities_crossed=communities_crossed,
    )
    target_tier, effort = MAPPING.get((complexity, optimize_for), ("high", "medium"))
    costs = [_cost_per_1m(model) for model in available_models]
    min_cost = min(costs)
    max_cost = max(costs)
    scored = [
        _score_model(
            model,
            task_type=resolved_task_type,
            complexity=complexity,
            target_tier=target_tier,
            optimize_for=optimize_for,
            min_cost=min_cost,
            max_cost=max_cost,
        )
        for model in available_models
    ]
    scored.sort(key=lambda c: (-c["score"], _cost_per_1m(c["model"])))

    primary_candidate = _primary_candidate(scored, optimize_for)
    primary_model = primary_candidate["model"]
    primary_effort = _resolve_effort(primary_model, effort)
    budget_alt = _budget_alternative(scored, primary_candidate, effort)
    alt_cost_model = primary_model
    if budget_alt:
        alt_cost_model = next(m for m in available_models if m["id"] == budget_alt["model"])
    else:
        budget_entry = BUDGET_ALT_MAPPING.get((complexity, optimize_for))
        if budget_entry:
            alt_cost_model = _best_for_mode(available_models, budget_entry[0], optimize_for)
    display_candidates = [primary_candidate] + [
        candidate for candidate in scored
        if candidate["model"]["id"] != primary_model["id"]
    ]
    review_reason = _review_reason(
        router_mode=router_mode,
        complexity=complexity,
        task_type=resolved_task_type,
        scored=scored,
        blast_radius=blast_radius,
    )

    return {
        "optimize_for": optimize_for,
        "primary": {
            "model": primary_model["id"],
            "effort_level": primary_effort,
            "reason": _build_reason(
                complexity,
                optimize_for,
                primary_model,
                resolved_task_type,
                primary_candidate,
            ),
        },
        "budget_alternative": budget_alt,
        "estimated_cost": {
            "primary": _estimate_cost(primary_model),
            "alternative": _estimate_cost(alt_cost_model),
        },
        "routing": {
            "task_type": resolved_task_type,
            "target_tier": target_tier,
            "router_mode": router_mode,
            "scored_candidates": [_candidate_payload(c) for c in display_candidates[:5]],
            "ai_review": _ai_review_payload(
                required=review_reason is not None,
                reason=review_reason,
                prompt=prompt,
                complexity=complexity,
                optimize_for=optimize_for,
                task_type=resolved_task_type,
                router_mode=router_mode,
                target_tier=target_tier,
                effort=effort,
                blast_radius=blast_radius,
                candidates=display_candidates,
            ),
        },
    }
