from pathlib import Path

import pytest

from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestCalculateBlastRadius:
    def test_returns_required_fields(self, analyzer):
        start_nodes = [analyzer.get_node("auth_middleware_py")]
        result = calculate_blast_radius(analyzer, start_nodes, max_depth=3)
        assert "files_affected" in result
        assert "communities_crossed" in result
        assert "avg_centrality" in result
        assert "max_edge_depth" in result
        assert "affected_files" in result
        assert "affected_communities" in result

    def test_single_isolated_node_low_radius(self, analyzer):
        start_nodes = [analyzer.get_node("hash_password")]
        result = calculate_blast_radius(analyzer, start_nodes, max_depth=1)
        assert result["communities_crossed"] <= 1

    def test_cross_community_node_high_radius(self, analyzer):
        start_nodes = [analyzer.get_node("auth_middleware_py")]
        result = calculate_blast_radius(analyzer, start_nodes, max_depth=3)
        assert result["communities_crossed"] >= 2

    def test_affected_files_are_source_files(self, analyzer):
        start_nodes = [analyzer.get_node("routes_py")]
        result = calculate_blast_radius(analyzer, start_nodes, max_depth=2)
        for f in result["affected_files"]:
            assert "/" in f or "." in f

    def test_empty_start_nodes(self, analyzer):
        result = calculate_blast_radius(analyzer, [], max_depth=3)
        assert result["files_affected"] == 0
        assert result["communities_crossed"] == 0


class TestComputeBlastScore:
    def test_formula(self):
        score = compute_blast_score(
            files_affected=10,
            communities_crossed=3,
            avg_centrality=0.5,
            max_edge_depth=2,
        )
        expected = 10 * 1.0 + 3 * 3.0 + 0.5 * 20.0 + 2 * 1.5
        assert score == pytest.approx(expected)

    def test_zero_inputs(self):
        assert compute_blast_score(0, 0, 0.0, 0) == 0.0


class TestScoreToComplexity:
    def test_low(self):
        assert score_to_complexity(5.0) == "low"
        assert score_to_complexity(14.9) == "low"

    def test_medium(self):
        assert score_to_complexity(15.0) == "medium"
        assert score_to_complexity(39.9) == "medium"

    def test_high(self):
        assert score_to_complexity(40.0) == "high"
        assert score_to_complexity(79.9) == "high"

    def test_critical(self):
        assert score_to_complexity(80.0) == "critical"
        assert score_to_complexity(200.0) == "critical"
