import json
from pathlib import Path

import pytest
import yaml

from model_selector.config import load_config, load_model_library, get_available_models

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).parent.parent


class TestLoadModelLibrary:
    def test_loads_all_models(self):
        models = load_model_library(ROOT / "models.json")
        assert len(models) >= 30

    def test_model_has_required_fields(self):
        models = load_model_library(ROOT / "models.json")
        for m in models:
            assert "id" in m
            assert "name" in m
            assert "provider" in m
            assert "tier" in m
            assert "cost" in m
            assert "context_window" in m
            assert "quality_score" in m
            assert "speed" in m
            assert "strengths" in m
            assert "effort_levels" in m

    def test_opus_48_has_xhigh_effort_level(self):
        models = load_model_library(ROOT / "models.json")
        opus = next(m for m in models if m["id"] == "claude-opus-4-8")
        assert opus["effort_levels"] == ["high", "xhigh", "max"]

    def test_opus_46_does_not_have_xhigh_effort_level(self):
        models = load_model_library(ROOT / "models.json")
        opus = next(m for m in models if m["id"] == "claude-opus-4-6")
        assert opus["effort_levels"] == ["high", "max"]

    def test_o_series_models_are_removed(self):
        models = load_model_library(ROOT / "models.json")
        ids = {m["id"] for m in models}
        assert {"o3", "o4", "o4-mini"}.isdisjoint(ids)


class TestLoadConfig:
    def test_loads_yaml_config(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({
            "available_models": ["claude-opus-4-8"],
            "graphify_path": "./graphify-out/graph.json",
            "preferences": {"optimize_for": "cost"},
        }))
        cfg = load_config(cfg_file)
        assert cfg["available_models"] == ["claude-opus-4-8"]
        assert cfg["preferences"]["optimize_for"] == "token-saver"

    def test_applies_defaults_for_missing_preferences(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({
            "available_models": ["claude-haiku-4-5"],
        }))
        cfg = load_config(cfg_file)
        assert cfg["preferences"]["optimize_for"] == "balanced"
        assert cfg["preferences"]["router_mode"] == "hybrid"
        assert cfg["preferences"]["bfs_max_depth"] == 3
        assert cfg["graphify_path"] == "./graphify-out/graph.json"

    def test_invalid_router_mode_falls_back_to_hybrid(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({
            "available_models": ["claude-haiku-4-5"],
            "preferences": {"router_mode": "magic"},
        }))
        cfg = load_config(cfg_file)
        assert cfg["preferences"]["router_mode"] == "hybrid"


class TestGetAvailableModels:
    def test_filters_to_configured_models(self):
        all_models = [
            {"id": "claude-opus-4-8", "tier": "high"},
            {"id": "claude-sonnet-4-6", "tier": "medium"},
            {"id": "claude-haiku-4-5", "tier": "low"},
        ]
        available = get_available_models(all_models, ["claude-opus-4-8", "claude-haiku-4-5"])
        assert len(available) == 2
        assert available[0]["id"] == "claude-opus-4-8"
        assert available[1]["id"] == "claude-haiku-4-5"

    def test_ignores_unknown_model_ids(self):
        all_models = [{"id": "claude-opus-4-8", "tier": "high"}]
        available = get_available_models(all_models, ["claude-opus-4-8", "nonexistent-model"])
        assert len(available) == 1
