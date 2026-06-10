# Model Selector MCP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that recommends AI models + effort levels by analyzing a Graphify knowledge graph's blast radius, community structure, and node centrality.

**Architecture:** Six components layered bottom-up: config loader → graph analyzer → prompt matcher / git diff analyzer → blast radius calculator → recommender → MCP server. Each component is a single focused module with a clean interface. Tests use a small synthetic graph fixture.

**Tech Stack:** Python 3.11+, networkx, mcp SDK (FastMCP), PyYAML, pytest

**Spec:** `docs/superpowers/specs/2026-06-10-model-selector-mcp-design.md`

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package config, dependencies, entry point |
| `models.json` | Pre-built model library (Opus 4.8, Sonnet 4.6, Haiku 4.5) |
| `config.yaml` | User config (available models, preferences) |
| `src/model_selector/__init__.py` | Package marker |
| `src/model_selector/config.py` | Load user config + model library, merge defaults |
| `src/model_selector/graph_analyzer.py` | Load graph.json into networkx, cache, provide query methods |
| `src/model_selector/prompt_matcher.py` | Extract keywords from prompt, match against graph nodes |
| `src/model_selector/git_diff_analyzer.py` | Parse git diff output, map files to graph nodes |
| `src/model_selector/blast_radius.py` | BFS traversal, centrality, community crossing, scoring |
| `src/model_selector/recommender.py` | Map complexity score → model + effort level recommendation |
| `src/model_selector/server.py` | FastMCP server exposing analyze_task, analyze_diff, list_models |
| `tests/fixtures/sample_graph.json` | Small synthetic graph for all tests (3 communities, ~20 nodes, ~25 edges) |
| `tests/test_config.py` | Config loading tests |
| `tests/test_graph_analyzer.py` | Graph loading + query tests |
| `tests/test_prompt_matcher.py` | Keyword extraction + node matching tests |
| `tests/test_git_diff_analyzer.py` | Git diff parsing + node mapping tests |
| `tests/test_blast_radius.py` | BFS, centrality, scoring formula tests |
| `tests/test_recommender.py` | Complexity → recommendation mapping tests |
| `tests/test_server.py` | MCP tool integration tests |

---

### Task 1: Project Scaffolding + Test Fixture

**Files:**
- Create: `pyproject.toml`
- Create: `src/model_selector/__init__.py`
- Create: `models.json`
- Create: `config.yaml`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/sample_graph.json`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "model-selector-mcp"
version = "0.1.0"
description = "MCP server that recommends AI models based on Graphify knowledge graph analysis"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "networkx>=3.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[project.scripts]
model-selector-mcp = "model_selector.server:main"
```

- [ ] **Step 2: Create package init**

```python
# src/model_selector/__init__.py
```

Empty file — package marker only.

- [ ] **Step 3: Create models.json**

```json
{
  "models": [
    {
      "id": "claude-opus-4-8",
      "provider": "anthropic",
      "tier": "high",
      "cost": {
        "input_per_1m": 15.0,
        "output_per_1m": 75.0
      },
      "context_window": 200000,
      "strengths": [
        "complex-reasoning",
        "multi-file-refactoring",
        "architecture-decisions",
        "cross-cutting-changes"
      ],
      "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"]
    },
    {
      "id": "claude-sonnet-4-6",
      "provider": "anthropic",
      "tier": "medium",
      "cost": {
        "input_per_1m": 3.0,
        "output_per_1m": 15.0
      },
      "context_window": 200000,
      "strengths": [
        "code-generation",
        "moderate-refactoring",
        "bug-fixes",
        "single-module-changes"
      ],
      "effort_levels": ["low", "medium", "high"]
    },
    {
      "id": "claude-haiku-4-5",
      "provider": "anthropic",
      "tier": "low",
      "cost": {
        "input_per_1m": 0.25,
        "output_per_1m": 1.25
      },
      "context_window": 200000,
      "strengths": [
        "simple-fixes",
        "typo-corrections",
        "single-file-edits",
        "boilerplate",
        "documentation"
      ],
      "effort_levels": null
    }
  ]
}
```

- [ ] **Step 4: Create config.yaml**

```yaml
available_models:
  - claude-opus-4-8
  - claude-sonnet-4-6
  - claude-haiku-4-5

graphify_path: ./graphify-out/graph.json

preferences:
  optimize_for: balanced
  max_budget_per_task: null
  bfs_max_depth: 3
```

- [ ] **Step 5: Create test fixture — sample_graph.json**

A small synthetic graph with 3 communities (auth=0, api=1, db=2), ~20 nodes, ~25 edges. Mirrors real Graphify output structure exactly (keys: `directed`, `multigraph`, `graph`, `nodes`, `links`, `hyperedges`, `built_at_commit`). Node keys: `label`, `file_type`, `source_file`, `source_location`, `id`, `community`, `norm_label`. Link keys: `relation`, `confidence`, `source_file`, `source_location`, `weight`, `confidence_score`, `source`, `target`.

```json
{
  "directed": false,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {"label": "auth_middleware.py", "file_type": "code", "source_file": "src/auth/middleware.py", "source_location": "L1", "id": "auth_middleware_py", "community": 0, "norm_label": "auth_middleware.py"},
    {"label": "JWTHandler", "file_type": "code", "source_file": "src/auth/jwt.py", "source_location": "L5", "id": "jwt_handler", "community": 0, "norm_label": "jwthandler"},
    {"label": "validate_token()", "file_type": "code", "source_file": "src/auth/jwt.py", "source_location": "L20", "id": "validate_token", "community": 0, "norm_label": "validate_token()"},
    {"label": "UserSession", "file_type": "code", "source_file": "src/auth/session.py", "source_location": "L1", "id": "user_session", "community": 0, "norm_label": "usersession"},
    {"label": "hash_password()", "file_type": "code", "source_file": "src/auth/utils.py", "source_location": "L10", "id": "hash_password", "community": 0, "norm_label": "hash_password()"},

    {"label": "routes.py", "file_type": "code", "source_file": "src/api/routes.py", "source_location": "L1", "id": "routes_py", "community": 1, "norm_label": "routes.py"},
    {"label": "UserController", "file_type": "code", "source_file": "src/api/controllers/user.py", "source_location": "L1", "id": "user_controller", "community": 1, "norm_label": "usercontroller"},
    {"label": "handle_request()", "file_type": "code", "source_file": "src/api/handlers.py", "source_location": "L15", "id": "handle_request", "community": 1, "norm_label": "handle_request()"},
    {"label": "RateLimiter", "file_type": "code", "source_file": "src/api/rate_limiter.py", "source_location": "L1", "id": "rate_limiter", "community": 1, "norm_label": "ratelimiter"},
    {"label": "serialize_response()", "file_type": "code", "source_file": "src/api/serializers.py", "source_location": "L8", "id": "serialize_response", "community": 1, "norm_label": "serialize_response()"},

    {"label": "DatabasePool", "file_type": "code", "source_file": "src/db/pool.py", "source_location": "L1", "id": "db_pool", "community": 2, "norm_label": "databasepool"},
    {"label": "UserModel", "file_type": "code", "source_file": "src/db/models/user.py", "source_location": "L1", "id": "user_model", "community": 2, "norm_label": "usermodel"},
    {"label": "migrate()", "file_type": "code", "source_file": "src/db/migrations.py", "source_location": "L30", "id": "migrate", "community": 2, "norm_label": "migrate()"},
    {"label": "QueryBuilder", "file_type": "code", "source_file": "src/db/query.py", "source_location": "L1", "id": "query_builder", "community": 2, "norm_label": "querybuilder"},
    {"label": "ConnectionConfig", "file_type": "code", "source_file": "src/db/config.py", "source_location": "L1", "id": "conn_config", "community": 2, "norm_label": "connectionconfig"},

    {"label": "README.md", "file_type": "document", "source_file": "README.md", "source_location": "L1", "id": "readme_md", "community": 3, "norm_label": "readme.md"},
    {"label": "Architecture Decision", "file_type": "rationale", "source_file": "docs/adr-001.md", "source_location": "L1", "id": "adr_001", "community": 3, "norm_label": "architecture decision"},

    {"label": "config.py", "file_type": "code", "source_file": "src/config.py", "source_location": "L1", "id": "app_config", "community": 1, "norm_label": "config.py"},
    {"label": "logger.py", "file_type": "code", "source_file": "src/utils/logger.py", "source_location": "L1", "id": "logger", "community": 1, "norm_label": "logger.py"}
  ],
  "links": [
    {"relation": "contains", "confidence": "EXTRACTED", "source_file": "src/auth/jwt.py", "source_location": "L5", "weight": 1.0, "confidence_score": 1.0, "source": "auth_middleware_py", "target": "jwt_handler"},
    {"relation": "calls", "confidence": "EXTRACTED", "source_file": "src/auth/middleware.py", "source_location": "L25", "weight": 1.0, "confidence_score": 1.0, "source": "auth_middleware_py", "target": "validate_token"},
    {"relation": "uses", "confidence": "EXTRACTED", "source_file": "src/auth/middleware.py", "source_location": "L30", "weight": 1.0, "confidence_score": 1.0, "source": "auth_middleware_py", "target": "user_session"},
    {"relation": "calls", "confidence": "EXTRACTED", "source_file": "src/auth/session.py", "source_location": "L15", "weight": 1.0, "confidence_score": 0.9, "source": "user_session", "target": "hash_password"},

    {"relation": "imports", "confidence": "EXTRACTED", "source_file": "src/api/routes.py", "source_location": "L3", "weight": 1.0, "confidence_score": 1.0, "source": "routes_py", "target": "auth_middleware_py"},
    {"relation": "calls", "confidence": "EXTRACTED", "source_file": "src/api/routes.py", "source_location": "L20", "weight": 1.0, "confidence_score": 1.0, "source": "routes_py", "target": "handle_request"},
    {"relation": "uses", "confidence": "EXTRACTED", "source_file": "src/api/routes.py", "source_location": "L8", "weight": 1.0, "confidence_score": 0.9, "source": "routes_py", "target": "rate_limiter"},
    {"relation": "calls", "confidence": "EXTRACTED", "source_file": "src/api/handlers.py", "source_location": "L30", "weight": 1.0, "confidence_score": 1.0, "source": "handle_request", "target": "serialize_response"},
    {"relation": "uses", "confidence": "INFERRED", "source_file": "src/api/controllers/user.py", "source_location": "L10", "weight": 0.8, "confidence_score": 0.7, "source": "user_controller", "target": "user_model"},
    {"relation": "imports", "confidence": "EXTRACTED", "source_file": "src/api/controllers/user.py", "source_location": "L2", "weight": 1.0, "confidence_score": 1.0, "source": "user_controller", "target": "user_session"},

    {"relation": "uses", "confidence": "EXTRACTED", "source_file": "src/db/models/user.py", "source_location": "L5", "weight": 1.0, "confidence_score": 1.0, "source": "user_model", "target": "db_pool"},
    {"relation": "uses", "confidence": "EXTRACTED", "source_file": "src/db/models/user.py", "source_location": "L8", "weight": 1.0, "confidence_score": 1.0, "source": "user_model", "target": "query_builder"},
    {"relation": "calls", "confidence": "EXTRACTED", "source_file": "src/db/migrations.py", "source_location": "L35", "weight": 1.0, "confidence_score": 0.9, "source": "migrate", "target": "db_pool"},
    {"relation": "uses", "confidence": "EXTRACTED", "source_file": "src/db/pool.py", "source_location": "L10", "weight": 1.0, "confidence_score": 1.0, "source": "db_pool", "target": "conn_config"},

    {"relation": "imports", "confidence": "EXTRACTED", "source_file": "src/api/handlers.py", "source_location": "L2", "weight": 1.0, "confidence_score": 1.0, "source": "handle_request", "target": "user_model"},
    {"relation": "uses", "confidence": "INFERRED", "source_file": "src/api/routes.py", "source_location": "L5", "weight": 0.8, "confidence_score": 0.7, "source": "routes_py", "target": "app_config"},
    {"relation": "uses", "confidence": "INFERRED", "source_file": "src/auth/middleware.py", "source_location": "L8", "weight": 0.8, "confidence_score": 0.7, "source": "auth_middleware_py", "target": "logger"},

    {"relation": "describes", "confidence": "EXTRACTED", "source_file": "README.md", "source_location": "L1", "weight": 1.0, "confidence_score": 1.0, "source": "readme_md", "target": "routes_py"},
    {"relation": "rationale_for", "confidence": "EXTRACTED", "source_file": "docs/adr-001.md", "source_location": "L1", "weight": 1.0, "confidence_score": 1.0, "source": "adr_001", "target": "auth_middleware_py"}
  ],
  "hyperedges": [],
  "built_at_commit": "abc1234"
}
```

- [ ] **Step 6: Create tests/__init__.py**

Empty file.

- [ ] **Step 7: Install dependencies and verify**

Run: `cd /home/mcp-project && pip install -e ".[dev]"`
Expected: Successfully installed model-selector-mcp with networkx, mcp, pyyaml, pytest

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml models.json config.yaml src/ tests/
git commit -m "feat: project scaffolding with test fixture, model library, and config"
```

---

### Task 2: Config Loader

**Files:**
- Create: `src/model_selector/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config loading**

```python
# tests/test_config.py
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
        assert len(models) == 3

    def test_model_has_required_fields(self):
        models = load_model_library(ROOT / "models.json")
        for m in models:
            assert "id" in m
            assert "provider" in m
            assert "tier" in m
            assert "cost" in m
            assert "context_window" in m
            assert "strengths" in m
            assert "effort_levels" in m

    def test_opus_has_six_effort_levels(self):
        models = load_model_library(ROOT / "models.json")
        opus = next(m for m in models if m["id"] == "claude-opus-4-8")
        assert opus["effort_levels"] == ["low", "medium", "high", "xhigh", "max", "ultra"]

    def test_haiku_has_no_effort_levels(self):
        models = load_model_library(ROOT / "models.json")
        haiku = next(m for m in models if m["id"] == "claude-haiku-4-5")
        assert haiku["effort_levels"] is None


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
        assert cfg["preferences"]["optimize_for"] == "cost"

    def test_applies_defaults_for_missing_preferences(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({
            "available_models": ["claude-haiku-4-5"],
        }))
        cfg = load_config(cfg_file)
        assert cfg["preferences"]["optimize_for"] == "balanced"
        assert cfg["preferences"]["bfs_max_depth"] == 3
        assert cfg["graphify_path"] == "./graphify-out/graph.json"


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.config'`

- [ ] **Step 3: Implement config.py**

```python
# src/model_selector/config.py
import json
from pathlib import Path

import yaml

DEFAULTS = {
    "graphify_path": "./graphify-out/graph.json",
    "preferences": {
        "optimize_for": "balanced",
        "max_budget_per_task": None,
        "bfs_max_depth": 3,
    },
}


def load_model_library(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["models"]


def load_config(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    if "graphify_path" not in cfg:
        cfg["graphify_path"] = DEFAULTS["graphify_path"]

    defaults_prefs = DEFAULTS["preferences"].copy()
    user_prefs = cfg.get("preferences") or {}
    defaults_prefs.update({k: v for k, v in user_prefs.items() if v is not None})
    cfg["preferences"] = defaults_prefs

    return cfg


def get_available_models(all_models: list[dict], model_ids: list[str]) -> list[dict]:
    id_set = set(model_ids)
    return [m for m in all_models if m["id"] in id_set]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_config.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/config.py tests/test_config.py
git commit -m "feat: config loader with model library and user preferences"
```

---

### Task 3: Graph Analyzer

**Files:**
- Create: `src/model_selector/graph_analyzer.py`
- Create: `tests/test_graph_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_graph_analyzer.py
import json
from pathlib import Path

import pytest

from model_selector.graph_analyzer import GraphAnalyzer

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_graph_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.graph_analyzer'`

- [ ] **Step 3: Implement graph_analyzer.py**

```python
# src/model_selector/graph_analyzer.py
import json
from pathlib import Path

import networkx as nx


class GraphAnalyzer:
    def __init__(self, graph_path: Path):
        self._path = Path(graph_path)
        self._graph = nx.Graph()
        self._node_data = {}
        self._communities = {}
        self._centrality_cache = None
        self._labels_cache = None
        self._load()

    def _load(self):
        with open(self._path) as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            nid = node["id"]
            self._graph.add_node(nid)
            self._node_data[nid] = node
            community = node.get("community")
            if community is not None:
                self._communities.setdefault(community, []).append(node)

        for link in data.get("links", []):
            self._graph.add_edge(
                link["source"],
                link["target"],
                relation=link.get("relation"),
                weight=link.get("weight", 1.0),
                confidence_score=link.get("confidence_score", 1.0),
            )

        labels_path = self._path.parent / ".graphify_labels.json"
        if labels_path.exists():
            with open(labels_path) as f:
                self._labels_cache = {int(k): v for k, v in json.load(f).items()}

    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def get_node(self, node_id: str) -> dict | None:
        return self._node_data.get(node_id)

    def community_labels(self) -> dict[int, str]:
        if self._labels_cache:
            return self._labels_cache
        return {cid: f"Community {cid}" for cid in self._communities}

    def nodes_in_community(self, community_id: int) -> list[dict]:
        return self._communities.get(community_id, [])

    def find_by_source_file(self, path: str) -> list[dict]:
        return [n for n in self._node_data.values() if n.get("source_file") == path]

    def find_by_label(self, substring: str) -> list[dict]:
        sub_lower = substring.lower()
        return [
            n for n in self._node_data.values()
            if sub_lower in n.get("norm_label", "").lower()
            or sub_lower in n.get("label", "").lower()
        ]

    def betweenness_centrality(self) -> dict[str, float]:
        if self._centrality_cache is None:
            self._centrality_cache = nx.betweenness_centrality(self._graph)
        return self._centrality_cache

    def neighbors(self, node_id: str) -> list[str]:
        if node_id not in self._graph:
            return []
        return list(self._graph.neighbors(node_id))

    def bfs_reachable(self, start_ids: list[str], max_depth: int) -> dict[str, int]:
        visited = {}
        queue = [(nid, 0) for nid in start_ids if nid in self._graph]
        for nid, depth in queue:
            if nid in visited:
                continue
            visited[nid] = depth
            if depth < max_depth:
                for neighbor in self._graph.neighbors(nid):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
        return visited
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_graph_analyzer.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/graph_analyzer.py tests/test_graph_analyzer.py
git commit -m "feat: graph analyzer with networkx loading, community lookup, BFS traversal"
```

---

### Task 4: Prompt Matcher

**Files:**
- Create: `src/model_selector/prompt_matcher.py`
- Create: `tests/test_prompt_matcher.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_prompt_matcher.py
from pathlib import Path

import pytest

from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.prompt_matcher import extract_keywords, match_prompt

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestExtractKeywords:
    def test_basic_extraction(self):
        keywords = extract_keywords("Refactor the auth middleware to use JWT")
        assert "auth" in keywords
        assert "middleware" in keywords
        assert "jwt" in keywords
        assert "refactor" in keywords

    def test_strips_stopwords(self):
        keywords = extract_keywords("Fix the bug in the database pool")
        assert "the" not in keywords
        assert "in" not in keywords
        assert "database" in keywords
        assert "pool" in keywords

    def test_lowercases(self):
        keywords = extract_keywords("Update JWTHandler")
        assert "jwthandler" in keywords

    def test_empty_prompt(self):
        assert extract_keywords("") == []

    def test_splits_compound_words(self):
        keywords = extract_keywords("auth_middleware jwt_handler")
        assert "auth" in keywords
        assert "middleware" in keywords


class TestMatchPrompt:
    def test_matches_by_label(self, analyzer):
        result = match_prompt(analyzer, "jwt handler")
        ids = {n["id"] for n in result}
        assert "jwt_handler" in ids

    def test_matches_by_source_file_path(self, analyzer):
        result = match_prompt(analyzer, "middleware")
        ids = {n["id"] for n in result}
        assert "auth_middleware_py" in ids

    def test_no_matches_returns_empty(self, analyzer):
        result = match_prompt(analyzer, "zzz_nonexistent_zzz")
        assert result == []

    def test_deduplicates_matches(self, analyzer):
        result = match_prompt(analyzer, "auth middleware")
        ids = [n["id"] for n in result]
        assert len(ids) == len(set(ids))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_prompt_matcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.prompt_matcher'`

- [ ] **Step 3: Implement prompt_matcher.py**

```python
# src/model_selector/prompt_matcher.py
import re

from model_selector.graph_analyzer import GraphAnalyzer

STOPWORDS = frozenset({
    "a", "an", "the", "to", "in", "on", "at", "of", "for", "is", "it",
    "and", "or", "but", "with", "from", "by", "as", "be", "was", "were",
    "this", "that", "these", "those", "i", "we", "you", "they", "my",
    "do", "does", "did", "will", "would", "should", "could", "can",
    "not", "no", "so", "if", "then", "than", "also", "just", "about",
})


def extract_keywords(prompt: str) -> list[str]:
    if not prompt.strip():
        return []
    tokens = re.split(r'[\s,.:;!?()"\'/]+', prompt.lower())
    expanded = []
    for token in tokens:
        parts = re.split(r'[_\-]', token)
        if len(parts) > 1:
            expanded.extend(parts)
        expanded.append(token)
    keywords = [t for t in expanded if t and t not in STOPWORDS and len(t) > 1]
    return list(dict.fromkeys(keywords))


def match_prompt(analyzer: GraphAnalyzer, prompt: str) -> list[dict]:
    keywords = extract_keywords(prompt)
    if not keywords:
        return []

    matched = {}
    for kw in keywords:
        for node in analyzer.find_by_label(kw):
            matched[node["id"]] = node
        for node in analyzer._node_data.values():
            sf = node.get("source_file", "")
            if kw in sf.lower():
                matched[node["id"]] = node

    return list(matched.values())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_prompt_matcher.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/prompt_matcher.py tests/test_prompt_matcher.py
git commit -m "feat: prompt matcher with keyword extraction and node matching"
```

---

### Task 5: Git Diff Analyzer

**Files:**
- Create: `src/model_selector/git_diff_analyzer.py`
- Create: `tests/test_git_diff_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_git_diff_analyzer.py
from pathlib import Path
from unittest.mock import patch

import pytest

from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.git_diff_analyzer import parse_diff_output, match_diff

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestParseDiffOutput:
    def test_parses_file_list(self):
        output = "src/auth/middleware.py\nsrc/api/routes.py\n"
        files = parse_diff_output(output)
        assert files == ["src/auth/middleware.py", "src/api/routes.py"]

    def test_strips_whitespace(self):
        output = "  src/auth/jwt.py  \n"
        files = parse_diff_output(output)
        assert files == ["src/auth/jwt.py"]

    def test_empty_output(self):
        assert parse_diff_output("") == []
        assert parse_diff_output("\n") == []


class TestMatchDiff:
    def test_matches_changed_files_to_nodes(self, analyzer):
        changed_files = ["src/auth/middleware.py", "src/auth/jwt.py"]
        nodes = match_diff(analyzer, changed_files)
        ids = {n["id"] for n in nodes}
        assert "auth_middleware_py" in ids
        assert "jwt_handler" in ids
        assert "validate_token" in ids

    def test_unknown_files_are_skipped(self, analyzer):
        changed_files = ["nonexistent/file.py"]
        nodes = match_diff(analyzer, changed_files)
        assert nodes == []

    def test_deduplicates(self, analyzer):
        changed_files = ["src/auth/jwt.py", "src/auth/jwt.py"]
        nodes = match_diff(analyzer, changed_files)
        ids = [n["id"] for n in nodes]
        assert len(ids) == len(set(ids))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_git_diff_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.git_diff_analyzer'`

- [ ] **Step 3: Implement git_diff_analyzer.py**

```python
# src/model_selector/git_diff_analyzer.py
import subprocess

from model_selector.graph_analyzer import GraphAnalyzer


def parse_diff_output(output: str) -> list[str]:
    return [line.strip() for line in output.strip().splitlines() if line.strip()]


def get_changed_files(diff_target: str | None = None) -> list[str]:
    if diff_target:
        cmd = ["git", "diff", "--name-only", diff_target]
    else:
        cmd = ["git", "diff", "--name-only"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return parse_diff_output(result.stdout)


def match_diff(analyzer: GraphAnalyzer, changed_files: list[str]) -> list[dict]:
    matched = {}
    for filepath in changed_files:
        for node in analyzer.find_by_source_file(filepath):
            matched[node["id"]] = node
    return list(matched.values())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_git_diff_analyzer.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/git_diff_analyzer.py tests/test_git_diff_analyzer.py
git commit -m "feat: git diff analyzer with file parsing and node mapping"
```

---

### Task 6: Blast Radius Calculator

**Files:**
- Create: `src/model_selector/blast_radius.py`
- Create: `tests/test_blast_radius.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_blast_radius.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_blast_radius.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.blast_radius'`

- [ ] **Step 3: Implement blast_radius.py**

```python
# src/model_selector/blast_radius.py
from model_selector.graph_analyzer import GraphAnalyzer

WEIGHT_FILES = 1.0
WEIGHT_COMMUNITIES = 3.0
WEIGHT_CENTRALITY = 20.0
WEIGHT_DEPTH = 1.5


def calculate_blast_radius(
    analyzer: GraphAnalyzer,
    start_nodes: list[dict],
    max_depth: int,
) -> dict:
    if not start_nodes:
        return {
            "files_affected": 0,
            "communities_crossed": 0,
            "avg_centrality": 0.0,
            "max_edge_depth": 0,
            "affected_files": [],
            "affected_communities": [],
        }

    start_ids = [n["id"] for n in start_nodes if n]
    reachable = analyzer.bfs_reachable(start_ids, max_depth)

    centrality = analyzer.betweenness_centrality()
    start_centralities = [centrality.get(nid, 0.0) for nid in start_ids]
    avg_centrality = sum(start_centralities) / len(start_centralities) if start_centralities else 0.0

    max_edge_depth = max(reachable.values()) if reachable else 0

    source_files = set()
    communities = {}
    for nid, depth in reachable.items():
        node = analyzer.get_node(nid)
        if not node:
            continue
        sf = node.get("source_file")
        if sf:
            source_files.add(sf)
        cid = node.get("community")
        if cid is not None:
            if cid not in communities:
                community_labels = analyzer.community_labels()
                communities[cid] = {
                    "id": cid,
                    "label": community_labels.get(cid, f"Community {cid}"),
                    "nodes_affected": 0,
                }
            communities[cid]["nodes_affected"] += 1

    return {
        "files_affected": len(source_files),
        "communities_crossed": len(communities),
        "avg_centrality": round(avg_centrality, 4),
        "max_edge_depth": max_edge_depth,
        "affected_files": sorted(source_files),
        "affected_communities": sorted(communities.values(), key=lambda c: -c["nodes_affected"]),
    }


def compute_blast_score(
    files_affected: int,
    communities_crossed: int,
    avg_centrality: float,
    max_edge_depth: int,
) -> float:
    return (
        files_affected * WEIGHT_FILES
        + communities_crossed * WEIGHT_COMMUNITIES
        + avg_centrality * WEIGHT_CENTRALITY
        + max_edge_depth * WEIGHT_DEPTH
    )


def score_to_complexity(score: float) -> str:
    if score < 15:
        return "low"
    elif score < 40:
        return "medium"
    elif score < 80:
        return "high"
    else:
        return "critical"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_blast_radius.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/blast_radius.py tests/test_blast_radius.py
git commit -m "feat: blast radius calculator with BFS, centrality scoring, complexity mapping"
```

---

### Task 7: Recommender

**Files:**
- Create: `src/model_selector/recommender.py`
- Create: `tests/test_recommender.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_recommender.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_recommender.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.recommender'`

- [ ] **Step 3: Implement recommender.py**

```python
# src/model_selector/recommender.py

MAPPING = {
    ("low", "cost"):        ("low", None),
    ("low", "quality"):     ("medium", "low"),
    ("low", "balanced"):    ("low", None),
    ("medium", "cost"):     ("medium", "medium"),
    ("medium", "quality"):  ("high", "low"),
    ("medium", "balanced"): ("medium", "high"),
    ("high", "cost"):       ("medium", "high"),
    ("high", "quality"):    ("high", "high"),
    ("high", "balanced"):   ("high", "medium"),
    ("critical", "cost"):       ("high", "medium"),
    ("critical", "quality"):    ("high", "ultra"),
    ("critical", "balanced"):   ("high", "max"),
}

BUDGET_ALT_MAPPING = {
    ("low", "cost"):        None,
    ("low", "quality"):     ("low", None),
    ("low", "balanced"):    None,
    ("medium", "cost"):     ("low", None),
    ("medium", "quality"):  ("medium", "medium"),
    ("medium", "balanced"): ("low", None),
    ("high", "cost"):       ("low", None),
    ("high", "quality"):    ("medium", "high"),
    ("high", "balanced"):   ("medium", "high"),
    ("critical", "cost"):       ("medium", "high"),
    ("critical", "quality"):    ("high", "high"),
    ("critical", "balanced"):   ("medium", "high"),
}


def _find_model_by_tier(models: list[dict], tier: str) -> dict | None:
    for m in models:
        if m["tier"] == tier:
            return m
    return None


def _best_available(models: list[dict], tier: str) -> dict:
    model = _find_model_by_tier(models, tier)
    if model:
        return model
    tier_order = ["high", "medium", "low"]
    for t in tier_order:
        model = _find_model_by_tier(models, t)
        if model:
            return model
    return models[0]


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


def recommend(complexity: str, available_models: list[dict], optimize_for: str) -> dict:
    tier, effort = MAPPING.get((complexity, optimize_for), ("high", "medium"))
    primary_model = _best_available(available_models, tier)
    primary_effort = _resolve_effort(primary_model, effort)

    budget_alt = None
    budget_entry = BUDGET_ALT_MAPPING.get((complexity, optimize_for))
    if budget_entry:
        alt_tier, alt_effort = budget_entry
        alt_model = _best_available(available_models, alt_tier)
        alt_effort_resolved = _resolve_effort(alt_model, alt_effort)
        if alt_model["id"] != primary_model["id"] or alt_effort_resolved != primary_effort:
            budget_alt = {
                "model": alt_model["id"],
                "effort_level": alt_effort_resolved,
                "reason": "Cheaper option, may need more iterations",
            }

    return {
        "optimize_for": optimize_for,
        "primary": {
            "model": primary_model["id"],
            "effort_level": primary_effort,
            "reason": f"Complexity: {complexity}",
        },
        "budget_alternative": budget_alt,
        "estimated_cost": {
            "primary": _estimate_cost(primary_model),
            "alternative": _estimate_cost(
                _best_available(available_models, budget_entry[0]) if budget_entry else primary_model
            ),
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_recommender.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/model_selector/recommender.py tests/test_recommender.py
git commit -m "feat: recommender with complexity-to-model mapping and budget alternatives"
```

---

### Task 8: MCP Server

**Files:**
- Create: `src/model_selector/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_server.py
import json
from pathlib import Path
from unittest.mock import patch

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/mcp-project && python -m pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'model_selector.server'`

- [ ] **Step 3: Implement server.py**

```python
# src/model_selector/server.py
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from model_selector.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from model_selector.config import get_available_models, load_config, load_model_library
from model_selector.git_diff_analyzer import get_changed_files, match_diff
from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.prompt_matcher import match_prompt
from model_selector.recommender import recommend

SERVER_DIR = Path(__file__).parent.parent.parent


def build_analyze_result(
    mode: str,
    matched_keywords: list[str],
    blast_radius: dict,
    complexity: str,
    total_score: float,
    recommendation: dict,
    available_models: list[dict],
) -> dict:
    br = blast_radius.copy()
    br["total_score"] = total_score
    return {
        "analysis": {
            "mode": mode,
            "matched_keywords": matched_keywords,
            "blast_radius": br,
            "complexity": complexity,
            "affected_files": blast_radius["affected_files"],
            "affected_communities": blast_radius["affected_communities"],
        },
        "recommendation": recommendation,
        "available_models": [
            {"id": m["id"], "tier": m["tier"], "effort_levels": m.get("effort_levels")}
            for m in available_models
        ],
    }


def create_server(
    config_path: Path | None = None,
    models_path: Path | None = None,
) -> FastMCP:
    if config_path is None:
        config_path = SERVER_DIR / "config.yaml"
    if models_path is None:
        models_path = SERVER_DIR / "models.json"

    cfg = load_config(config_path)
    all_models = load_model_library(models_path)
    available = get_available_models(all_models, cfg["available_models"])

    mcp = FastMCP("model-selector")

    @mcp.tool()
    def analyze_task(prompt: str, graphify_path: str | None = None) -> str:
        """Analyze a task prompt and recommend the best AI model + effort level.

        Uses the project's Graphify knowledge graph to calculate blast radius,
        affected files/communities, and complexity score.
        """
        gpath = Path(graphify_path) if graphify_path else Path(cfg["graphify_path"])
        analyzer = GraphAnalyzer(gpath)

        matched = match_prompt(analyzer, prompt)
        from model_selector.prompt_matcher import extract_keywords
        keywords = extract_keywords(prompt)

        max_depth = cfg["preferences"]["bfs_max_depth"]
        br = calculate_blast_radius(analyzer, matched, max_depth)

        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)

        rec = recommend(complexity, available, cfg["preferences"]["optimize_for"])

        result = build_analyze_result(
            mode="prompt",
            matched_keywords=keywords,
            blast_radius=br,
            complexity=complexity,
            total_score=round(score, 2),
            recommendation=rec,
            available_models=available,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    def analyze_diff(diff_target: str | None = None, graphify_path: str | None = None) -> str:
        """Analyze git diff and recommend the best AI model + effort level for review.

        Maps changed files to the Graphify knowledge graph to calculate blast radius.
        """
        gpath = Path(graphify_path) if graphify_path else Path(cfg["graphify_path"])
        analyzer = GraphAnalyzer(gpath)

        changed_files = get_changed_files(diff_target)
        matched = match_diff(analyzer, changed_files)

        max_depth = cfg["preferences"]["bfs_max_depth"]
        br = calculate_blast_radius(analyzer, matched, max_depth)

        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)

        rec = recommend(complexity, available, cfg["preferences"]["optimize_for"])

        result = build_analyze_result(
            mode="diff",
            matched_keywords=changed_files,
            blast_radius=br,
            complexity=complexity,
            total_score=round(score, 2),
            recommendation=rec,
            available_models=available,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    def list_models() -> str:
        """List all available AI models with their metadata, costs, and effort levels."""
        return json.dumps(available, indent=2)

    return mcp


def main():
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/mcp-project && python -m pytest tests/test_server.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /home/mcp-project && python -m pytest tests/ -v`
Expected: All tests across all modules PASS (59 total)

- [ ] **Step 6: Commit**

```bash
git add src/model_selector/server.py tests/test_server.py
git commit -m "feat: MCP server with analyze_task, analyze_diff, and list_models tools"
```

---

### Task 9: Integration Test with Real Graphify Data

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test using the real graph.json**

```python
# tests/test_integration.py
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

        assert rec["primary"]["model"] in {"claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"}
        assert complexity in {"low", "medium", "high", "critical"}
        assert br["files_affected"] >= 0
        assert br["communities_crossed"] >= 0

    def test_simple_prompt_gets_lower_complexity(self, real_analyzer, available_models):
        simple = match_prompt(real_analyzer, "fix typo in readme")
        complex_ = match_prompt(real_analyzer, "refactor database models and authentication")

        br_simple = calculate_blast_radius(real_analyzer, simple, max_depth=3)
        br_complex = calculate_blast_radius(real_analyzer, complex_, max_depth=3)

        score_simple = compute_blast_score(
            br_simple["files_affected"], br_simple["communities_crossed"],
            br_simple["avg_centrality"], br_simple["max_edge_depth"],
        )
        score_complex = compute_blast_score(
            br_complex["files_affected"], br_complex["communities_crossed"],
            br_complex["avg_centrality"], br_complex["max_edge_depth"],
        )

        assert score_simple <= score_complex
```

- [ ] **Step 2: Run integration tests**

Run: `cd /home/mcp-project && python -m pytest tests/test_integration.py -v`
Expected: PASS (or skip if no real graph.json)

- [ ] **Step 3: Run full suite one final time**

Run: `cd /home/mcp-project && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration tests with real graphify data"
```

---

### Task 10: Manual Smoke Test

- [ ] **Step 1: Start the MCP server**

Run: `cd /home/mcp-project && python -m model_selector.server`
Expected: Server starts and listens on stdio

- [ ] **Step 2: Test with Claude Code MCP config**

Add to `~/.claude/claude_desktop_config.json` or project `.claude/settings.json`:
```json
{
  "mcpServers": {
    "model-selector": {
      "command": "python",
      "args": ["-m", "model_selector.server"],
      "cwd": "/home/mcp-project"
    }
  }
}
```

- [ ] **Step 3: Verify tools are visible in Claude Code**

Start a new Claude Code session and verify the three tools appear:
- `model-selector:analyze_task`
- `model-selector:analyze_diff`
- `model-selector:list_models`

- [ ] **Step 4: Test analyze_task with a real prompt**

In Claude Code, trigger the tool with a prompt and verify the JSON response includes analysis, recommendation, and available_models.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: finalize model-selector-mcp v0.1.0"
```
