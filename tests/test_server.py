import json
from pathlib import Path

import pytest

from model_selector.server import build_analyze_result, create_server

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"
ROOT = Path(__file__).parent.parent


class TestBuildAnalyzeResult:
    def test_returns_complete_response(self):
        result = build_analyze_result(
            mode="prompt",
            matched_keywords=["auth", "jwt"],
            blast_radius={
                "files_affected": 5,
                "communities_crossed": 2,
                "avg_centrality": 0.15,
                "max_edge_depth": 2,
                "affected_files": ["src/auth/middleware.py"],
                "affected_communities": [{"id": 0, "label": "Auth", "nodes_affected": 3}],
            },
            complexity="medium",
            total_score=25.0,
            recommendation={
                "optimize_for": "balanced",
                "primary": {"model": "claude-sonnet-4-6", "effort_level": "high", "reason": "test"},
                "budget_alternative": None,
                "estimated_cost": {"primary": "$0.10", "alternative": "$0.10"},
            },
            available_models=[{"id": "claude-sonnet-4-6", "tier": "medium", "effort_levels": ["low", "medium", "high"]}],
        )
        assert result["analysis"]["mode"] == "prompt"
        assert result["analysis"]["complexity"] == "medium"
        assert result["analysis"]["blast_radius"]["total_score"] == 25.0
        assert result["recommendation"]["primary"]["model"] == "claude-sonnet-4-6"
        assert len(result["available_models"]) == 1


class TestCreateServer:
    def test_server_has_tools(self):
        server = create_server(
            config_path=ROOT / "config.yaml",
            models_path=ROOT / "models.json",
        )
        assert server is not None
