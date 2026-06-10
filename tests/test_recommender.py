import pytest

from model_selector.recommender import recommend

MODELS = [
    {
        "id": "claude-opus-4-8",
        "provider": "anthropic",
        "tier": "high",
        "cost": {"input_per_1m": 15.0, "output_per_1m": 75.0},
        "context_window": 200000,
        "strengths": ["complex-reasoning", "multi-file-refactoring", "architecture-decisions", "cross-cutting-changes"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "tier": "medium",
        "cost": {"input_per_1m": 3.0, "output_per_1m": 15.0},
        "context_window": 200000,
        "strengths": ["code-generation", "moderate-refactoring", "bug-fixes", "single-module-changes"],
        "effort_levels": ["low", "medium", "high"],
    },
    {
        "id": "claude-haiku-4-5",
        "provider": "anthropic",
        "tier": "low",
        "cost": {"input_per_1m": 0.25, "output_per_1m": 1.25},
        "context_window": 200000,
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
        assert rec["primary"]["effort_level"] == "medium"

    def test_critical_complexity(self):
        rec = recommend("critical", MODELS, "balanced")
        assert rec["primary"]["model"] == "claude-opus-4-8"
        assert rec["primary"]["effort_level"] == "max"


class TestRecommendCost:
    def test_low_uses_haiku(self):
        rec = recommend("low", MODELS, "cost")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_high_uses_sonnet(self):
        rec = recommend("high", MODELS, "cost")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "high"


class TestRecommendQuality:
    def test_low_uses_sonnet(self):
        rec = recommend("low", MODELS, "quality")
        assert rec["primary"]["model"] == "claude-sonnet-4-6"
        assert rec["primary"]["effort_level"] == "low"

    def test_critical_uses_opus_ultra(self):
        rec = recommend("critical", MODELS, "quality")
        assert rec["primary"]["model"] == "claude-opus-4-8"
        assert rec["primary"]["effort_level"] == "ultra"


class TestBudgetAlternative:
    def test_has_budget_alternative(self):
        rec = recommend("high", MODELS, "balanced")
        assert "budget_alternative" in rec
        alt = rec["budget_alternative"]
        assert alt["model"] != rec["primary"]["model"] or alt["effort_level"] != rec["primary"]["effort_level"]

    def test_low_complexity_no_cheaper_alternative(self):
        rec = recommend("low", MODELS, "cost")
        assert rec["budget_alternative"] is None


class TestEstimatedCost:
    def test_has_cost_estimate(self):
        rec = recommend("high", MODELS, "balanced")
        assert "estimated_cost" in rec
        assert "primary" in rec["estimated_cost"]
        assert "alternative" in rec["estimated_cost"]


class TestMissingModels:
    def test_fallback_when_only_haiku(self):
        haiku_only = [m for m in MODELS if m["tier"] == "low"]
        rec = recommend("critical", haiku_only, "balanced")
        assert rec["primary"]["model"] == "claude-haiku-4-5"

    def test_fallback_when_only_opus(self):
        opus_only = [m for m in MODELS if m["tier"] == "high"]
        rec = recommend("low", opus_only, "balanced")
        assert rec["primary"]["model"] == "claude-opus-4-8"
