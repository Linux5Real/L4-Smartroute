# L4-Smartroute

Intelligent AI model routing for coding agents. Picks the right model for the right task - so you stop overpaying for simple fixes and underpowering complex refactors.

*made by [linux5real](https://github.com/Linux5real)*

## What is L4-Smartroute?

L4-Smartroute is an MCP server that analyzes your task (prompt or git diff), calculates code complexity using knowledge graph analysis, and recommends the best AI model + effort level. Instead of always using the most expensive model, it routes each task to the most appropriate one from 80+ AI-models (Coding-Models) across 15 providers.

## Built on Graphify

L4-Smartroute uses [Graphify](https://github.com/safishamsi/graphify) knowledge graphs to calculate blast radius - how many files, communities, and code paths a change affects. This drives complexity scoring and ensures high-risk cross-module work gets a capable model while simple edits stay cheap.

## Features

- **54+ models** across 14 providers (Anthropic, OpenAI, Google, xAI, Meta, and more)
- **3 router modes**: deterministic, hybrid, ai-review
- **4 optimization levels**: quality, balanced, performance, token-saver
- **Graphify-powered** blast radius analysis for accurate complexity scoring
- **Web UI** for configuration on `http://localhost:6639`
- **One-command install** with auto Claude Code integration

## Prerequisites

- **Python 3.11+**
- **One of:** `uv`, `pipx`, or `pip`
- **Claude Code CLI** (optional — for automatic MCP server registration)
- **Graphify** (optional — for full blast radius analysis, run `graphify ./your-project`)

## Installation

### One Command

```bash
curl -fsSL https://raw.githubusercontent.com/Linux5Real/L4-Smartroute/main/install.sh | bash
```

This auto-detects your package manager (`uv` > `pipx` > `pip`), clones the repo locally, installs it editable, and registers it with Claude Code.

### Manual

```bash
git clone https://github.com/Linux5Real/L4-Smartroute.git
cd L4-Smartroute
pip install -e .
claude mcp add l4-smartroute -- l4-smartroute
```

### From Source

```bash
git clone https://github.com/Linux5Real/L4-Smartroute.git
cd L4-Smartroute
pip install -e .
```

## Setup

Start the configuration UI:

```bash
l4-smartroute-setup
```

This opens `http://localhost:6639` where you can:

- Select which models are available
- Choose optimization mode (Quality / Balanced / Performance / Token Saver)
- Set router mode (Deterministic / Hybrid / AI Review)
- Configure Graphify path and budget settings

### Claude Code Commands

- **`/smartroute`** — Get a model recommendation for your current task
- **`/smartroute-settings`** — Open the configuration UI

## How It Works

```
Prompt / Git Diff
  -> Graphify blast radius (files, communities, centrality)
  -> Task classification (13 task types)
  -> Candidate scoring (fit, tier, cost, speed)
  -> Optional AI review (hybrid/ai-review mode)
  -> Final model + effort level + budget alternative
```

## Supported Models

| Provider | Models |
|----------|--------|
| Anthropic | Claude Fable 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6 / 4.5, Haiku 4.5 |
| OpenAI | GPT-5.5, GPT-5.5 Pro, GPT-5.4, GPT-5.4 mini/nano, GPT-5.3 Codex, GPT-5.2 |
| Google | Gemini 3.1 Pro, 3.5 Flash, 3.1 Flash-Lite, 3 Deep Think, 2.5 Pro / flash |
| xAI | Grok 4.3, Grok 4.20, Grok 4.1, Grok-build-0.1 |
| Meta | Llama 4 Maverick, Llama 4 Scout |
| Alibaba | Qwen3.7 Max/Plus, Qwen3.6 Plus, Qwen3.5, Qwen3 Coder Next, and more |
| Mistral | Mistral Large 3, Medium 3.5, Small 4 |
| DeepSeek | DeepSeek V4 Pro, V4 Flash and more |
| NVIDIA | Nemotron 3 Ultra, Super, Nano Omni |
| Moonshot | Kimi K2.6, Kimi K2.5|
| MiniMax | MiniMax-M3, M2.7, M2.5, M2.1, M2 |
| Xiaomi | MiMo-V2.5-Pro, V2.5, V2-Omni, V2-Flash |
| Zhipu AI | GLM-5.1, GLM-5-Turbo and more |
| Others | Command A/A+, Step 3.7 Flash, KAT-Coder-Pro V2, Hy3 |

**Missing a model?** [Open an issue](https://github.com/Linux5Real/L4-Smartroute/issues) and we'll add it.

## License

MIT
