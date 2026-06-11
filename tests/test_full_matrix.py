import pytest

from l4_smartroute.recommender import recommend

MODELS = [
    {
        "id": "claude-fable-5",
        "provider": "anthropic",
        "tier": "ultra",
        "cost": {"input_per_1m": 20.0, "output_per_1m": 100.0},
        "context_window": 200000,
        "quality_score": 98,
        "speed": "medium",
        "strengths": ["ultra-coding", "complex-reasoning", "architecture-decisions"],
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
        "strengths": ["complex-reasoning", "multi-file-refactoring", "architecture-decisions", "debugging"],
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
        "strengths": ["code-generation", "moderate-refactoring", "bug-fixes"],
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
        "strengths": ["simple-fixes", "typo-corrections", "documentation", "boilerplate"],
        "effort_levels": None,
    },
    {
        "id": "gemini-2.5-flash",
        "provider": "google",
        "tier": "medium",
        "cost": {"input_per_1m": 0.15, "output_per_1m": 0.60},
        "context_window": 1048576,
        "quality_score": 80,
        "speed": "fast",
        "strengths": ["code-generation", "long-context"],
        "effort_levels": ["low", "medium", "high"],
    },
]

ROUTER_MODES = ["deterministic", "hybrid", "ai-review"]
OPTIMIZE_MODES = ["quality", "balanced", "performance", "token-saver"]

SIMPLE_PROMPT = "fix a typo in the readme"
COMPLEX_PROMPT = "refactor the authentication system across multiple modules and update all tests"
SIMPLE_BLAST = {"files_affected": 1, "communities_crossed": 0, "avg_centrality": 0.01, "max_edge_depth": 0}
COMPLEX_BLAST = {"files_affected": 15, "communities_crossed": 4, "avg_centrality": 0.25, "max_edge_depth": 3}


def _rec(router_mode, optimize_for, prompt, blast_radius=None):
    complexity = "medium" if "typo" in prompt else "high"
    return recommend(
        complexity,
        MODELS,
        optimize_for,
        prompt=prompt,
        blast_radius=blast_radius,
        router_mode=router_mode,
    )


def _validate_structure(rec):
    assert "primary" in rec
    assert "model" in rec["primary"]
    assert "effort_level" in rec["primary"]
    assert "reason" in rec["primary"]
    assert "budget_alternative" in rec
    assert "estimated_cost" in rec
    assert "routing" in rec
    assert "task_type" in rec["routing"]
    assert "router_mode" in rec["routing"]
    assert "scored_candidates" in rec["routing"]
    assert "ai_review" in rec["routing"]
    model_ids = {m["id"] for m in MODELS}
    assert rec["primary"]["model"] in model_ids


class TestDeterministicQuality:
    def test_simple_task(self):
        rec = _rec("deterministic", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_task(self):
        rec = _rec("deterministic", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_recommends_strong_model(self):
        rec = _rec("deterministic", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert rec["primary"]["model"] in ("claude-fable-5", "claude-opus-4-8")


class TestDeterministicBalanced:
    def test_simple_task(self):
        rec = _rec("deterministic", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_task(self):
        rec = _rec("deterministic", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_complex_has_budget_alternative(self):
        rec = _rec("deterministic", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert rec["budget_alternative"] is not None


class TestDeterministicPerformance:
    def test_simple_task(self):
        rec = _rec("deterministic", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("deterministic", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_prefers_fast_models(self):
        rec = _rec("deterministic", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        assert model["speed"] in ("fast", "medium")


class TestDeterministicTokenSaver:
    def test_simple_task(self):
        rec = _rec("deterministic", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("deterministic", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_prefers_cheap_models(self):
        rec = _rec("deterministic", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        cost = model["cost"]["input_per_1m"] + model["cost"]["output_per_1m"]
        assert cost <= 20.0


class TestHybridQuality:
    def test_simple_task_no_ai_review(self):
        rec = _rec("hybrid", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task_triggers_ai_review(self):
        rec = _rec("hybrid", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True
        assert len(rec["routing"]["ai_review"]["candidates"]) >= 1

    def test_ai_review_candidates_have_capabilities(self):
        rec = _rec("hybrid", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        if rec["routing"]["ai_review"]["required"]:
            for c in rec["routing"]["ai_review"]["candidates"]:
                assert "capabilities" in c
                assert "model" in c


class TestHybridBalanced:
    def test_simple_task(self):
        rec = _rec("hybrid", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestHybridPerformance:
    def test_simple_task(self):
        rec = _rec("hybrid", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)


class TestHybridTokenSaver:
    def test_simple_task(self):
        rec = _rec("hybrid", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_complex_prefers_budget(self):
        rec = _rec("hybrid", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        assert model["tier"] in ("low", "medium")


class TestAiReviewQuality:
    def test_simple_task_always_reviews(self):
        rec = _rec("ai-review", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task_always_reviews(self):
        rec = _rec("ai-review", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_candidates_include_policy(self):
        rec = _rec("ai-review", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert len(rec["routing"]["ai_review"]["policy"]) >= 1


class TestAiReviewBalanced:
    def test_simple_task(self):
        rec = _rec("ai-review", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestAiReviewPerformance:
    def test_simple_task(self):
        rec = _rec("ai-review", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestAiReviewTokenSaver:
    def test_simple_task(self):
        rec = _rec("ai-review", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestEdgeCases:
    def test_no_graphify_graph_still_works(self):
        rec = recommend(
            "medium", MODELS, "balanced",
            prompt="fix a bug",
            blast_radius=None,
            router_mode="hybrid",
        )
        _validate_structure(rec)

    def test_empty_prompt_with_blast_radius(self):
        rec = recommend(
            "high", MODELS, "balanced",
            prompt="",
            blast_radius=COMPLEX_BLAST,
            router_mode="deterministic",
        )
        _validate_structure(rec)
        assert rec["routing"]["task_type"] == "review"

    def test_single_model_available(self):
        rec = recommend(
            "critical", [MODELS[0]], "quality",
            prompt="refactor everything",
            router_mode="hybrid",
        )
        _validate_structure(rec)
        assert rec["primary"]["model"] == "claude-fable-5"

    def test_all_modes_return_scored_candidates(self):
        for router in ROUTER_MODES:
            for opt in OPTIMIZE_MODES:
                rec = _rec(router, opt, COMPLEX_PROMPT, COMPLEX_BLAST)
                assert len(rec["routing"]["scored_candidates"]) >= 1
