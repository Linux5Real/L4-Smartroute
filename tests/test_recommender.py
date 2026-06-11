import pytest

from l4_smartroute.recommender import recommend
from l4_smartroute.task_classifier import classify_task

MODELS = [
    {
        "id": "claude-fable-5",
        "provider": "anthropic",
        "tier": "ultra",
        "cost": {"input_per_1m": 20.0, "output_per_1m": 100.0},
        "context_window": 200000,
        "quality_score": 98,
        "speed": "medium",
        "strengths": ["ultra-coding", "complex-reasoning"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    {
        "id": "claude-opus-4-8",
        "provider": "anthropic",
        "tier": "high",
        "cost": {"input_per_1m": 15.0, "output_per_1m": 75.0},
        "context_window": 200000,
        "quality_score": 94,
        "speed": "slow",
        "strengths": ["complex-reasoning", "multi-file-refactoring", "architecture-decisions", "cross-cutting-changes"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "tier": "medium",
        "cost": {"input_per_1m": 3.0, "output_per_1m": 15.0},
        "context_window": 200000,
        "quality_score": 85,
        "speed": "fast",
        "strengths": ["code-generation", "moderate-refactoring", "bug-fixes", "single-module-changes"],
        "effort_levels": ["low", "medium", "high"],
    },
    {
        "id": "claude-haiku-4-5",
        "provider": "anthropic",
        "tier": "low",
        "cost": {"input_per_1m": 0.25, "output_per_1m": 1.25},
        "context_window": 200000,
        "quality_score": 72,
        "speed": "fast",
        "strengths": ["simple-fixes", "typo-corrections", "single-file-edits", "boilerplate", "documentation"],
        "effort_levels": None,
    },
]


class TestRecommendBalanced:
    def test_low_complexity(self):
        rec = recommend("low", MODELS, "balanced")
        assert rec["primary"]["model"] == "claude-haiku-4-5"
        assert rec["primary"]["effort_level"] is None

    def test_medium_complexity(self):
        rec = recommend("medium", MODELS, "balanced")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "high"

    def test_high_complexity(self):
        rec = recommend("high", MODELS, "balanced")
        assert rec["primary"]["model"] == "claude-opus-4-8"
        assert rec["primary"]["effort_level"] == "high"

    def test_critical_complexity(self):
        rec = recommend("critical", MODELS, "balanced")
        assert rec["primary"]["model"] == "claude-fable-5"
        assert rec["primary"]["effort_level"] == "high"


class TestRecommendQuality:
    def test_low_uses_medium_tier(self):
        rec = recommend("low", MODELS, "quality")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "low"

    def test_high_uses_ultra(self):
        rec = recommend("high", MODELS, "quality")
        assert rec["primary"]["model"] == "claude-fable-5"
        assert rec["primary"]["effort_level"] == "high"

    def test_critical_uses_ultra_max(self):
        rec = recommend("critical", MODELS, "quality")
        assert rec["primary"]["model"] == "claude-fable-5"
        assert rec["primary"]["effort_level"] == "max"


class TestRecommendPerformanceDLSS:
    """Performance mode drops tier, boosts effort — like NVIDIA DLSS."""

    def test_low_stays_low(self):
        rec = recommend("low", MODELS, "performance")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_medium_drops_to_low_boosts_effort(self):
        rec = recommend("medium", MODELS, "performance")
        assert rec["primary"]["model"] == "claude-haiku-4-5"
        assert rec["primary"]["effort_level"] is None

    def test_high_drops_to_medium_boosts_effort(self):
        rec = recommend("high", MODELS, "performance")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "high"

    def test_critical_drops_to_high_boosts_effort(self):
        rec = recommend("critical", MODELS, "performance")
        assert rec["primary"]["model"] == "claude-opus-4-8"
        assert rec["primary"]["effort_level"] == "max"


class TestRecommendTokenSaver:
    def test_low_uses_cheapest(self):
        rec = recommend("low", MODELS, "token-saver")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_medium_stays_cheap(self):
        rec = recommend("medium", MODELS, "token-saver")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_high_still_cheap(self):
        rec = recommend("high", MODELS, "token-saver")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_critical_bumps_to_medium(self):
        rec = recommend("critical", MODELS, "token-saver")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "high"


class TestBudgetAlternative:
    def test_has_budget_alternative(self):
        rec = recommend("high", MODELS, "balanced")
        assert "budget_alternative" in rec
        alt = rec["budget_alternative"]
        assert alt is not None
        assert alt["model"] != rec["primary"]["model"] or alt["effort_level"] != rec["primary"]["effort_level"]

    def test_low_complexity_no_cheaper_alternative(self):
        rec = recommend("low", MODELS, "balanced")
        assert rec["budget_alternative"] is None

    def test_performance_low_no_alternative(self):
        rec = recommend("low", MODELS, "performance")
        assert rec["budget_alternative"] is None

    def test_token_saver_low_no_alternative(self):
        rec = recommend("low", MODELS, "token-saver")
        assert rec["budget_alternative"] is None


class TestEstimatedCost:
    def test_has_cost_estimate(self):
        rec = recommend("high", MODELS, "balanced")
        assert "estimated_cost" in rec
        assert "primary" in rec["estimated_cost"]
        assert "alternative" in rec["estimated_cost"]


class TestReasonString:
    def test_includes_mode_and_complexity(self):
        rec = recommend("high", MODELS, "performance")
        reason = rec["primary"]["reason"]
        assert "high" in reason
        assert "DLSS" in reason

    def test_includes_cost_info(self):
        rec = recommend("medium", MODELS, "token-saver")
        reason = rec["primary"]["reason"]
        assert "$" in reason


class TestMissingModels:
    def test_fallback_when_only_haiku(self):
        haiku_only = [m for m in MODELS if m["tier"] == "low"]
        rec = recommend("critical", haiku_only, "balanced")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_fallback_when_only_opus(self):
        opus_only = [m for m in MODELS if m["tier"] == "high"]
        rec = recommend("low", opus_only, "balanced")
        assert rec["primary"]["model"] == "claude-opus-4-8"

    def test_fallback_when_no_ultra(self):
        no_ultra = [m for m in MODELS if m["tier"] != "ultra"]
        rec = recommend("critical", no_ultra, "quality")
        assert rec["primary"]["model"] == "claude-opus-4-8"


class TestMultiProviderSelection:
    """When multiple models share a tier, mode determines which is picked."""

    MULTI = MODELS + [
        {
            "id": "gemini-2.5-flash",
            "provider": "google",
            "tier": "medium",
            "cost": {"input_per_1m": 0.15, "output_per_1m": 0.60},
            "context_window": 1048576,
            "quality_score": 80,
            "speed": "fast",
            "strengths": ["code-generation", "fast-iteration"],
            "effort_levels": ["low", "medium", "high"],
        },
    ]

    def test_quality_prefers_higher_score(self):
        rec = recommend("medium", self.MULTI, "quality")
        # high tier → opus has highest quality_score among high-tier
        assert rec["primary"]["model"] == "claude-opus-4-8"

    def test_token_saver_prefers_cheapest(self):
        rec = recommend("medium", self.MULTI, "token-saver")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_performance_prefers_fastest(self):
        rec = recommend("high", self.MULTI, "performance")
        # medium tier, fastest → gemini flash or sonnet (both fast, but gemini is cheaper)
        result = rec["primary"]["model"]
        assert result in ("gemini-2.5-flash", "claude-sonnet-4-6")


class TestTaskClassification:
    def test_refactor_prompt_routes_to_multi_file_refactor(self):
        task = classify_task(
            "Refactor auth and billing across multiple files",
            complexity="high",
            files_affected=12,
            communities_crossed=4,
        )
        assert task == "multi_file_refactor"

    def test_debug_prompt_routes_to_debugging(self):
        task = classify_task("Diagnose this traceback and find the root cause", complexity="medium")
        assert task == "debugging"

    def test_empty_diff_analysis_routes_to_review(self):
        task = classify_task("", files_affected=3)
        assert task == "review"

    def test_frontend_prompt_routes_to_frontend_ui(self):
        task = classify_task("Build a responsive React component with CSS polish")
        assert task == "frontend_ui"

    def test_backend_prompt_routes_to_backend_systems(self):
        task = classify_task("Fix the backend API middleware and Postgres auth flow")
        assert task == "backend_systems"

    def test_physics_prompt_routes_to_math_science(self):
        task = classify_task("Solve a physics optimization problem with probability math")
        assert task == "math_science"


class TestCapabilityRouting:
    MODELS = [
        {
            "id": "cheap-docs",
            "provider": "test",
            "tier": "low",
            "cost": {"input_per_1m": 0.05, "output_per_1m": 0.10},
            "context_window": 128000,
            "quality_score": 62,
            "speed": "fast",
            "strengths": ["documentation", "simple-fixes"],
            "capabilities": {
                "coding": 50,
                "debugging": 45,
                "refactoring": 35,
                "architecture": 30,
                "agentic_work": 35,
                "long_context": 55,
                "instruction_following": 70,
                "structured_output": 60,
            },
            "effort_levels": None,
        },
        {
            "id": "long-context-fast",
            "provider": "test",
            "tier": "medium",
            "cost": {"input_per_1m": 0.20, "output_per_1m": 0.80},
            "context_window": 1048576,
            "quality_score": 78,
            "speed": "fast",
            "strengths": ["long-context", "code-generation"],
            "capabilities": {
                "coding": 74,
                "debugging": 68,
                "refactoring": 66,
                "architecture": 62,
                "agentic_work": 64,
                "long_context": 96,
                "instruction_following": 76,
                "structured_output": 72,
            },
            "effort_levels": ["low", "medium", "high"],
        },
        {
            "id": "refactor-pro",
            "provider": "test",
            "tier": "high",
            "cost": {"input_per_1m": 3.0, "output_per_1m": 12.0},
            "context_window": 200000,
            "quality_score": 90,
            "speed": "medium",
            "strengths": ["multi-file-refactoring", "debugging", "architecture-decisions"],
            "capabilities": {
                "coding": 90,
                "debugging": 92,
                "refactoring": 95,
                "architecture": 90,
                "agentic_work": 88,
                "long_context": 72,
                "instruction_following": 88,
                "structured_output": 86,
            },
            "effort_levels": ["low", "medium", "high", "max"],
        },
    ]

    def test_long_context_task_prefers_long_context_model(self):
        rec = recommend(
            "medium",
            self.MODELS,
            "balanced",
            task_type="long_context_analysis",
            prompt="Summarize the whole codebase",
        )
        assert rec["primary"]["model"] == "long-context-fast"
        assert rec["routing"]["task_type"] == "long_context_analysis"

    def test_refactor_task_prefers_refactor_capability(self):
        rec = recommend(
            "high",
            self.MODELS,
            "balanced",
            task_type="multi_file_refactor",
            prompt="Refactor auth across modules",
        )
        assert rec["primary"]["model"] == "refactor-pro"

    def test_token_saver_docs_prefers_cheapest_good_enough_model(self):
        rec = recommend(
            "low",
            self.MODELS,
            "token-saver",
            task_type="docs",
            prompt="Update README docs",
        )
        assert rec["primary"]["model"] == "cheap-docs"

    def test_returns_scored_candidates_without_full_model_payloads(self):
        rec = recommend("high", self.MODELS, "balanced", task_type="debugging")
        candidates = rec["routing"]["scored_candidates"]
        assert 1 <= len(candidates) <= 5
        assert {"model", "score", "fit", "cost_per_1m"} <= set(candidates[0])
        assert "capabilities" not in candidates[0]

    def test_hybrid_adds_ai_review_for_high_risk_refactor(self):
        rec = recommend(
            "high",
            self.MODELS,
            "balanced",
            task_type="multi_file_refactor",
            prompt="Refactor auth across modules",
            blast_radius={"files_affected": 12, "communities_crossed": 3},
            router_mode="hybrid",
        )
        review = rec["routing"]["ai_review"]
        assert review["required"] is True
        assert len(review["candidates"]) == 3
        assert review["candidates"][0]["model"] == rec["primary"]["model"]
        assert "capabilities" in review["candidates"][0]

    def test_deterministic_router_skips_ai_review(self):
        rec = recommend(
            "critical",
            self.MODELS,
            "quality",
            task_type="architecture",
            prompt="Design a migration",
            blast_radius={"files_affected": 20, "communities_crossed": 5},
            router_mode="deterministic",
        )
        assert rec["routing"]["ai_review"]["required"] is False

    def test_ai_review_router_always_requests_ai_review(self):
        rec = recommend(
            "low",
            self.MODELS,
            "balanced",
            task_type="docs",
            prompt="Update README",
            router_mode="ai-review",
        )
        assert rec["routing"]["ai_review"]["required"] is True

    def test_hybrid_skips_ai_review_for_low_risk_docs(self):
        rec = recommend(
            "low",
            self.MODELS,
            "token-saver",
            task_type="docs",
            prompt="Update README copy",
            blast_radius={"files_affected": 1, "communities_crossed": 0},
            router_mode="hybrid",
        )
        assert rec["routing"]["ai_review"]["required"] is False

    def test_frontend_task_can_prefer_frontend_capability(self):
        frontend = {
            **self.MODELS[1],
            "id": "frontend-specialist",
            "cost": {"input_per_1m": 1.0, "output_per_1m": 3.0},
            "capabilities": {**self.MODELS[1]["capabilities"], "frontend": 98, "backend": 65},
        }
        backend = {
            **self.MODELS[1],
            "id": "backend-specialist",
            "cost": {"input_per_1m": 1.0, "output_per_1m": 3.0},
            "capabilities": {**self.MODELS[1]["capabilities"], "frontend": 60, "backend": 98},
        }
        rec = recommend("medium", [backend, frontend], "balanced", task_type="frontend_ui", prompt="Build UI")
        assert rec["primary"]["model"] == "frontend-specialist"

    def test_backend_task_can_prefer_backend_capability(self):
        frontend = {
            **self.MODELS[1],
            "id": "frontend-specialist",
            "cost": {"input_per_1m": 1.0, "output_per_1m": 3.0},
            "capabilities": {**self.MODELS[1]["capabilities"], "frontend": 98, "backend": 65},
        }
        backend = {
            **self.MODELS[1],
            "id": "backend-specialist",
            "cost": {"input_per_1m": 1.0, "output_per_1m": 3.0},
            "capabilities": {**self.MODELS[1]["capabilities"], "frontend": 60, "backend": 98},
        }
        rec = recommend("medium", [frontend, backend], "balanced", task_type="backend_systems", prompt="Build API")
        assert rec["primary"]["model"] == "backend-specialist"
