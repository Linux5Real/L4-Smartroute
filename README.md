# Model Selector MCP

> **v1.0-beta** — Intelligent AI model selection powered by knowledge graph analysis

An MCP server that recommends the optimal AI model and effort level for your tasks by analyzing your project's [Graphify](https://github.com/graphify) knowledge graph. Instead of guessing which model to use, let the blast radius of your changes guide the decision.

## Why?

Not every task needs the most expensive model. A typo fix doesn't require the same firepower as a cross-cutting architectural refactor. Model Selector MCP analyzes the **structural impact** of your task — affected files, community boundaries, node centrality — and maps it to the right model at the right cost.

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Task Prompt /   │────▶│  Graph Analysis   │────▶│  Recommendation │
│  Git Diff        │     │  (Blast Radius)   │     │  (Model+Effort) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

1. **Input**: Either a natural language task prompt or a git diff
2. **Graph Lookup**: Matches affected nodes in your Graphify knowledge graph
3. **Blast Radius**: BFS traversal calculates affected files, crossed communities, centrality scores, and depth
4. **Scoring**: Weighted formula produces a complexity score (`low` → `critical`)
5. **Recommendation**: Maps complexity + your optimization preference to a model tier and effort level

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Generate a Graphify knowledge graph

```bash
graphify ./your-project
# Produces: ./graphify-out/graph.json
```

### 2. Configure available models

Edit `config.yaml`:

```yaml
available_models:
  - claude-opus-4-8
  - claude-sonnet-4-6
  - claude-haiku-4-5

graphify_path: ./graphify-out/graph.json

preferences:
  optimize_for: balanced  # cost | quality | balanced
  bfs_max_depth: 3
```

### 3. Run the MCP server

```bash
model-selector-mcp
```

## MCP Tools

### `analyze_task`

Analyzes a natural language prompt and recommends a model.

```json
{
  "prompt": "refactor the authentication module to support OAuth2"
}
```

**Response:**
```json
{
  "analysis": {
    "mode": "prompt",
    "matched_keywords": ["refactor", "authentication", "module", "oauth2"],
    "blast_radius": {
      "files_affected": 8,
      "communities_crossed": 2,
      "avg_centrality": 0.1542,
      "max_edge_depth": 3,
      "total_score": 34.71
    },
    "complexity": "medium",
    "affected_files": ["src/auth/login.py", "src/auth/oauth.py", ...],
    "affected_communities": [...]
  },
  "recommendation": {
    "optimize_for": "balanced",
    "primary": {
      "model": "claude-sonnet-4-6",
      "effort_level": "high",
      "reason": "Complexity: medium"
    },
    "budget_alternative": {
      "model": "claude-haiku-4-5",
      "effort_level": null,
      "reason": "Cheaper option, may need more iterations"
    },
    "estimated_cost": {
      "primary": "$0.09 - $0.36",
      "alternative": "$0.00 - $0.01"
    }
  }
}
```

### `analyze_diff`

Analyzes a git diff and recommends a model for review or implementation.

```json
{
  "diff_target": "main"
}
```

### `list_models`

Lists all available models with metadata, costs, and supported effort levels.

## Model Tiers

| Tier | Model | Input $/1M | Output $/1M | Best For |
|------|-------|------------|-------------|----------|
| **high** | claude-opus-4-8 | $15.00 | $75.00 | Complex reasoning, architecture, cross-cutting changes |
| **medium** | claude-sonnet-4-6 | $3.00 | $15.00 | Code generation, moderate refactoring, bug fixes |
| **low** | claude-haiku-4-5 | $0.25 | $1.25 | Simple fixes, typos, boilerplate, documentation |

## Cost per `analyze_task` Call

Token usage per call: ~3,150 input tokens, ~250 output tokens.

| Model | First Call | With Cache |
|-------|------------|------------|
| Haiku | $0.0012 | $0.0007 |
| Sonnet | $0.015 | $0.008 |
| Opus | $0.074 | $0.039 |

Even with Opus, a single recommendation costs less than 8 cents. Most calls will hit cache and cost half that.

## Complexity Scoring

The blast radius score is computed as:

```
score = (files × 1.0) + (communities × 3.0) + (centrality × 20.0) + (depth × 1.5)
```

| Score | Complexity | Typical Scenario |
|-------|------------|------------------|
| < 15 | `low` | Single file, no community boundaries |
| 15–40 | `medium` | Multiple files, 1–2 communities |
| 40–80 | `high` | Many files, high centrality, deep reach |
| 80+ | `critical` | Cross-cutting, high-centrality nodes |

## Optimization Modes

- **`cost`** — Prioritize cheaper models, accept more iterations
- **`quality`** — Prioritize the best model for the task
- **`balanced`** — Default trade-off between cost and quality

## Configuration

### `config.yaml`

```yaml
available_models:
  - claude-opus-4-8
  - claude-sonnet-4-6

graphify_path: ./graphify-out/graph.json

preferences:
  optimize_for: balanced
  max_budget_per_task: null
  bfs_max_depth: 3
```

### `models.json`

Defines model metadata, pricing, and capabilities. Ships with sensible defaults for Anthropic models. Extend by adding entries to the `models` array.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with live reload
python -m model_selector.server
```

## Architecture

```
src/model_selector/
├── server.py           # MCP server + tool definitions
├── graph_analyzer.py   # NetworkX-based graph loading & queries
├── blast_radius.py     # BFS traversal + complexity scoring
├── prompt_matcher.py   # Keyword extraction + node matching
├── git_diff_analyzer.py# Git diff parsing + file-to-node mapping
├── recommender.py      # Tier/effort mapping logic
└── config.py           # YAML/JSON config loading
```

## License

MIT
