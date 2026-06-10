import pytest

from model_selector.recommender import recommend

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
