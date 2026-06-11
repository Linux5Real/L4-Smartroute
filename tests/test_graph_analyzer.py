import json
from pathlib import Path

import pytest

from l4_smartroute.graph_analyzer import GraphAnalyzer

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestGraphLoading:
    def test_loads_nodes(self, analyzer):
        assert analyzer.node_count() > 0

    def test_loads_edges(self, analyzer):
        assert analyzer.edge_count() > 0

    def test_node_has_attributes(self, analyzer):
        node = analyzer.get_node("auth_middleware_py")
        assert node["label"] == "auth_middleware.py"
        assert node["community"] == 0
        assert node["source_file"] == "src/auth/middleware.py"

    def test_nonexistent_node_returns_none(self, analyzer):
        assert analyzer.get_node("nonexistent") is None


class TestCommunityLookup:
    def test_get_community_labels(self, analyzer):
        labels = analyzer.community_labels()
        assert isinstance(labels, dict)
        assert 0 in labels
        assert 1 in labels

    def test_nodes_in_community(self, analyzer):
        nodes = analyzer.nodes_in_community(0)
        assert len(nodes) == 5
        ids = {n["id"] for n in nodes}
        assert "auth_middleware_py" in ids
        assert "jwt_handler" in ids


class TestNodeSearch:
    def test_find_nodes_by_source_file(self, analyzer):
        nodes = analyzer.find_by_source_file("src/auth/middleware.py")
        assert len(nodes) >= 1
        assert nodes[0]["id"] == "auth_middleware_py"

    def test_find_nodes_by_label_substring(self, analyzer):
        nodes = analyzer.find_by_label("jwt")
        assert any(n["id"] == "jwt_handler" for n in nodes)

    def test_find_returns_empty_for_no_match(self, analyzer):
        assert analyzer.find_by_label("zzz_nonexistent_zzz") == []


class TestCentrality:
    def test_betweenness_centrality_returns_dict(self, analyzer):
        bc = analyzer.betweenness_centrality()
        assert isinstance(bc, dict)
        assert "auth_middleware_py" in bc

    def test_centrality_values_between_0_and_1(self, analyzer):
        bc = analyzer.betweenness_centrality()
        for v in bc.values():
            assert 0.0 <= v <= 1.0
