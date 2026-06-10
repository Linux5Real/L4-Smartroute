# Model Selector MCP

**Stop overpaying for AI.** This MCP server analyzes your task and recommends the right model at the right price — automatically.

A typo fix doesn't need GPT-5.5. A cross-cutting refactor shouldn't run on Haiku. Model Selector uses your project's [Graphify](https://github.com/graphify) knowledge graph to measure the **blast radius** of each task and picks the optimal model + effort level.

## Install

```bash
pip install -e .
```

Then add to your MCP config (`.mcp.json`, Claude Desktop, etc.):

```json
{
  "mcpServers": {
    "model-selector": {
      "command": "model-selector-mcp"
    }
  }
}
```

## Setup

Run the setup wizard to configure models and preferences via a local web UI:

```bash
model-selector-setup
```

This opens a browser at `http://localhost:6639` where you can:
- **Pick your models** — 32+ models from 12 providers (Anthropic, OpenAI, Google, DeepSeek, Meta, Mistral, xAI, and more)
- **Choose your mode** — Quality, Balanced, Performance, or Token Saver
- **Set your budget** — optional per-task spending limit
- **Configure Graphify** — point to your project's knowledge graph

Settings are saved to `config.yaml`.

## How It Works

```
Task / Diff → Graph Analysis → Blast Radius Score → Model Recommendation
```

1. You send a task prompt or git diff
2. The server maps affected code to your Graphify knowledge graph
3. BFS traversal calculates blast radius (files, communities, centrality, depth)
4. A complexity score determines the right model tier and effort level

## Optimization Modes

| Mode | Strategy | Best For |
|------|----------|----------|
| **Quality** | Best model, highest effort | Critical features, architecture decisions |
| **Balanced** | Smart cost/quality trade-off | Daily development (default) |
| **Performance** | Cheaper model + boosted effort (DLSS-style) | Fast iteration, prototyping |
| **Token Saver** | Cheapest viable model, minimum effort | Bulk tasks, simple fixes, documentation |

**Performance mode** works like NVIDIA DLSS: it drops one model tier but compensates with higher effort levels — giving you near-quality results at a fraction of the cost and latency.

## Supported Models

| Provider | Models | Price Range (per 1M tokens) |
|----------|--------|-----------------------------|
| Anthropic | Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5 | $1.50 - $120.00 |
| OpenAI | GPT-5.5, GPT-5.4, GPT-4.1, 4.1-mini, 4.1-nano, o3, o4-mini | $0.50 - $90.00 |
| Google | Gemini 2.5 Pro, Flash, Flash Lite | $0.38 - $11.25 |
| DeepSeek | V4 Pro, V4 Flash, V3 | $1.37 - $10.00 |
| Moonshot | Kimi K2.6 | $12.50 |
| xAI | Grok 3, Grok 3 Mini | $0.80 - $18.00 |
| Meta | Llama 4 Maverick, Scout | $0.75 - $2.50 |
| Mistral | Large, Small, Codestral | $0.40 - $8.00 |
| Alibaba | Qwen 3, Qwen 3 Coder | $4.00 |
| Zhipu | GLM 5.1 | $5.00 |
| MiniMax | M3 | $7.50 |
| Xiaomi | Mimo 2.5 Pro, Mimo 2.5 | $1.50 - $6.00 |
| Cohere | Command A | $12.50 |

## MCP Tools

### `analyze_task`
Send a task description, get a model recommendation:
```json
{"prompt": "refactor the auth module to support OAuth2"}
```

### `analyze_diff`
Analyze a git diff for code review:
```json
{"diff_target": "main"}
```

### `list_models`
List all configured models with metadata and pricing.

## Requirements

- Python 3.11+
- A Graphify knowledge graph for your project (`graphify ./your-project`)

## License

MIT
