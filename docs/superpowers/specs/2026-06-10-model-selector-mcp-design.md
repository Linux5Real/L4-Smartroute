# Model Selector MCP — Design Spec

**Date:** 2026-06-10
**Status:** Approved
**Approach:** B — Smart Graph Analyzer

## Overview

An MCP server that recommends which AI model and effort level to use for a given task. It reads Graphify's knowledge graph locally, calculates a blast radius / complexity score, and returns structured analysis data so the AI agent can make an informed model recommendation.

The server supports two analysis modes:
1. **Prompt-based** (planning phase) — user describes a task, MCP matches it against the graph
2. **Git-diff-based** (implementation/review phase) — MCP maps changed files to the graph and calculates ripple effect

## Target Platform

- **V1:** Claude Code (MCP support is first-class)
- **Later:** Codex, OpenCode, Hermes, and other MCP-compatible tools

## Tech Stack

- **Language:** Python
- **Graph analysis:** networkx (already a Graphify dependency)
- **MCP SDK:** `mcp` (official Anthropic Python SDK)
- **Config format:** YAML for user config, JSON for model library
- **Graphify integration:** Reads `graphify-out/graph.json` directly (no CLI dependency at runtime)

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 MCP Server (FastMCP)             │
│  Tools: analyze_task · analyze_diff · list_models│
├──────────┬──────────┬───────────┬───────────────┤
│  Prompt  │ Git Diff │  Blast    │    Model      │
│  Matcher │ Analyzer │  Radius   │   Library     │
│          │          │  Calc     │               │
├──────────┴──────────┴───────────┴───────────────┤
│           Graph Analyzer (networkx)              │
│         Reads graphify-out/graph.json            │
├─────────────────────────────────────────────────┤
│            User Config (YAML)                    │
│      Which models are available?                 │
└─────────────────────────────────────────────────┘
```

### Components

| Component | Responsibility |
|---|---|
| **Graph Analyzer** | Loads `graph.json` into a networkx graph, caches in memory, provides analysis methods (BFS, centrality, community lookup) |
| **Prompt Matcher** | Tokenizes user prompt, extracts keywords, matches against node labels + file paths + community labels |
| **Git Diff Analyzer** | Runs `git diff --name-only`, maps changed file paths to graph nodes via the `source_file` field |
| **Blast Radius Calculator** | BFS traversal from matched nodes, computes centrality scores, detects community boundary crossings, measures edge depth |
| **Model Library** | Pre-built JSON database of all common AI models with costs, context windows, strengths, and effort levels |
| **User Config** | YAML file where the user selects available models and sets preferences |

## MCP Tools

### 1. `analyze_task` — Prompt-based analysis

**Purpose:** Planning phase — "which model do I need for this idea?"

**Input:**
```json
{
  "prompt": "Refactor the auth middleware to use JWT",
  "graphify_path": "./graphify-out/graph.json"  // optional override
}
```

**Internal flow:**
1. Tokenize prompt, extract keywords
2. Match keywords against node labels (fuzzy), file paths (substring), and community labels
3. Expand matches by including all nodes in matched communities
4. Run Blast Radius Calculator from matched nodes
5. Load user config, fetch available models
6. Compute recommendation based on complexity + user preferences
7. Return structured response

### 2. `analyze_diff` — Git-diff-based analysis

**Purpose:** Implementation/review phase — "now that I've made changes, what model for review?"

**Input:**
```json
{
  "diff_target": "HEAD",        // optional, default: unstaged changes
  "graphify_path": null          // optional override
}
```

**Internal flow:**
1. Run `git diff --name-only` (or against specified target)
2. Map changed file paths to graph nodes via `source_file` field
3. Run Blast Radius Calculator from those nodes
4. Same recommendation flow as `analyze_task`

### 3. `list_models` — Show configured models

**Purpose:** Let the user/AI see what's available.

**Input:** none

**Output:** Full list of available models with all metadata.

## Data Flow

### Prompt-based (`analyze_task`)

```
User prompt
  → Prompt Matcher
    → extract keywords: ["auth", "middleware", "jwt", "refactor"]
    → fuzzy match against node labels
    → substring match against source_file paths
    → find communities containing matched nodes
    → expand: include neighboring nodes in those communities
  → Blast Radius Calculator
    → BFS from matched nodes (max depth configurable, default: 3)
    → compute betweenness centrality of start nodes
    → count distinct communities touched
    → measure max edge depth reached
  → Scoring Formula
    → weighted combination → blast_score
    → map to complexity level
  → Recommendation Engine
    → complexity + user preference → model + effort level
  → Structured JSON response
```

### Git-diff-based (`analyze_diff`)

```
git diff --name-only
  → Git Diff Analyzer
    → list changed files
    → match each file against node source_file field
  → Blast Radius Calculator (same as above)
  → Scoring Formula (same as above)
  → Recommendation Engine (same as above)
  → Structured JSON response
```

## Scoring Formula

```python
# BFS max depth: 3 (configurable via config.yaml)
blast_score = (
    files_affected      * 1.0    # base weight
  + communities_crossed * 3.0    # cross-cutting changes weigh heavily
  + avg_centrality      * 20.0   # central nodes = high risk (centrality is 0-1)
  + max_edge_depth      * 1.5    # deep dependency chains = complexity
)
```

### Complexity Mapping

| blast_score | complexity | meaning |
|---|---|---|
| < 15 | `low` | isolated change, small scope |
| 15 - 39 | `medium` | moderate scope, few communities |
| 40 - 79 | `high` | broad impact, multiple communities |
| >= 80 | `critical` | architectural change, deep cross-cutting |

### Weight Rationale

- **`communities_crossed × 3.0`** — Strongest indicator. A change staying within one community is isolated. Crossing 5 communities is architecturally complex.
- **`avg_centrality × 20.0`** — High multiplier because centrality ranges 0-1. A node with high betweenness centrality is a bottleneck — changes there have disproportionate impact.
- **`max_edge_depth × 1.5`** — Long dependency chains mean more context the model needs to understand.

## Model Library

Pre-installed JSON database. Users don't edit this — they only select which models they have access to.

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

Additional models (Codex, DeepSeek, Gemini, GPT-4.1, etc.) follow the same schema and are added over time.

## Recommendation Mapping

Based on complexity level and user's `optimize_for` preference:

| complexity | cost | quality | balanced |
|---|---|---|---|
| low | Haiku | Sonnet @ Low | Haiku |
| medium | Sonnet @ Medium | Opus @ Low | Sonnet @ High |
| high | Sonnet @ High | Opus @ High | Opus @ Medium |
| critical | Opus @ Medium | Opus @ Ultra | Opus @ Max |

Every recommendation includes a primary pick and a budget alternative.

## User Config

File: `config.yaml` in the MCP server directory (or user-specified path).

```yaml
available_models:
  - claude-opus-4-8
  - claude-sonnet-4-6
  - claude-haiku-4-5

graphify_path: ./graphify-out/graph.json

preferences:
  optimize_for: balanced    # "cost" | "quality" | "balanced"
  max_budget_per_task: null  # optional dollar cap per task
  bfs_max_depth: 3           # how far to traverse from matched nodes
```

Minimal required config: just the `available_models` list. Everything else has sensible defaults.

## Response Format

Both `analyze_task` and `analyze_diff` return:

```json
{
  "analysis": {
    "mode": "prompt",
    "matched_keywords": ["auth", "middleware", "jwt"],
    "blast_radius": {
      "files_affected": 23,
      "communities_crossed": 5,
      "avg_centrality": 0.34,
      "max_edge_depth": 4,
      "total_score": 47.2
    },
    "complexity": "high",
    "affected_files": [
      "src/auth/middleware.py",
      "src/auth/jwt_handler.py",
      "src/api/routes.py"
    ],
    "affected_communities": [
      { "id": 3, "label": "Authentication", "nodes_affected": 12 },
      { "id": 7, "label": "API Routes", "nodes_affected": 6 },
      { "id": 12, "label": "Database Models", "nodes_affected": 5 }
    ]
  },
  "recommendation": {
    "optimize_for": "balanced",
    "primary": {
      "model": "claude-opus-4-8",
      "effort_level": "medium",
      "reason": "Cross-cutting change across 5 communities with high centrality nodes"
    },
    "budget_alternative": {
      "model": "claude-sonnet-4-6",
      "effort_level": "high",
      "reason": "Cheaper option, may need more iterations"
    },
    "estimated_cost": {
      "primary": "$0.85 - $1.50",
      "alternative": "$0.18 - $0.35"
    }
  },
  "available_models": [
    { "id": "claude-opus-4-8", "tier": "high", "effort_levels": ["low","medium","high","xhigh","max","ultra"] },
    { "id": "claude-sonnet-4-6", "tier": "medium", "effort_levels": ["low","medium","high"] },
    { "id": "claude-haiku-4-5", "tier": "low", "effort_levels": null }
  ]
}
```

## Cost per Analysis Call

The MCP server does all heavy computation locally (graph traversal, networkx analysis). The only AI token cost is the tool call itself:

| Current model | Estimated cost per call |
|---|---|
| Opus 4.8 | ~$0.04 |
| Sonnet 4.6 | ~$0.008 |
| Haiku 4.5 | ~$0.001 |

A single correct "use Haiku instead of Opus" recommendation saves 50-100x the analysis cost.

## License Compatibility

Graphify is MIT-licensed (Copyright Safi Shamsi). The MCP server reads Graphify's output files locally — no license issues. The MCP server itself can use any license.

## File Structure (estimated)

```
model-selector-mcp/
├── pyproject.toml
├── config.yaml                  # user config
├── models.json                  # pre-built model library
├── src/
│   └── model_selector/
│       ├── __init__.py
│       ├── server.py            # MCP server entry point (FastMCP)
│       ├── graph_analyzer.py    # load graph.json, networkx operations
│       ├── prompt_matcher.py    # keyword extraction + node matching
│       ├── git_diff_analyzer.py # git diff parsing + node mapping
│       ├── blast_radius.py      # BFS, centrality, scoring formula
│       ├── recommender.py       # complexity → model+effort mapping
│       └── config.py            # load user config + model library
└── tests/
    ├── test_graph_analyzer.py
    ├── test_prompt_matcher.py
    ├── test_blast_radius.py
    ├── test_recommender.py
    └── fixtures/
        └── sample_graph.json    # small test graph
```

Estimated size: ~1200-1500 lines of Python.
