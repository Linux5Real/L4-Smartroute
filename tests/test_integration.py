import json
from pathlib import Path

import pytest

from model_selector.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from model_selector.config import get_available_models, load_config, load_model_library
from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.prompt_matcher import match_prompt, extract_keywords
from model_selector.recommender import recommend

ROOT = Path(__file__).parent.parent
REAL_GRAPH = ROOT / "graphify-out" / "graph.json"


@pytest.fixture
def real_analyzer():
    if not REAL_GRAPH.exists():
        pytest.skip("No real graphify-out/graph.json available")
    return GraphAnalyzer(REAL_GRAPH)


@pytest.fixture
def available_models():
    return load_model_library(ROOT / "models.json")


class TestEndToEndPrompt:
    def test_full_pipeline(self, real_analyzer, available_models):
        prompt = "Refactor the database models"
        keywords = extract_keywords(prompt)
        matched = match_prompt(real_analyzer, prompt)

        br = calculate_blast_radius(real_analyzer, matched, max_depth=3)
        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)

        rec = recommend(complexity, available_models, "balanced")

        all_model_ids = {m["id"] for m in available_models}
        assert rec["primary"]["model"] in all_model_ids
        assert complexity in {"low", "medium", "high", "critical"}
        assert br["files_affected"] >= 0
        assert br["communities_crossed"] >= 0

    def test_different_prompts_produce_different_scores(self, real_analyzer, available_models):
        matched_a = match_prompt(real_analyzer, "fix typo in readme")
        matched_b = match_prompt(real_analyzer, "refactor database models and authentication")

        br_a = calculate_blast_radius(real_analyzer, matched_a, max_depth=3)
        br_b = calculate_blast_radius(real_analyzer, matched_b, max_depth=3)

        score_a = compute_blast_score(
            br_a["files_affected"], br_a["communities_crossed"],
            br_a["avg_centrality"], br_a["max_edge_depth"],
        )
        score_b = compute_blast_score(
            br_b["files_affected"], br_b["communities_crossed"],
            br_b["avg_centrality"], br_b["max_edge_depth"],
        )

        assert score_a >= 0
        assert score_b >= 0
        assert score_a != score_b
