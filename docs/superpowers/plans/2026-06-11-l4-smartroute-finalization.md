# L4-Smartroute Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename "Model Selector" to "L4-Smartroute", create a one-command installer, write an English README, clean up dead code, add comprehensive real tests across all router modes × optimization levels, and review performance.

**Architecture:** The Python module directory moves from `src/model_selector/` to `src/l4_smartroute/`. All entry points, configs, slash commands, and scripts are renamed to match. A new `install.sh` at the repo root auto-detects `uv`/`pipx`/`pip` and registers the MCP server with Claude Code. Existing tests are updated to use the new import paths, then 30 new real tests cover every combination.

**Tech Stack:** Python 3.11+, pytest, FastMCP, NetworkX, PyYAML, bash (install script)

---

## File Map

### Created
- `install.sh` — one-command installer (curl|bash)
- `src/l4_smartroute/` — renamed module directory (all 8 Python files)
- `.claude/commands/smartroute-settings.md` — renamed slash command
- `.claude/commands/smartroute.md` — renamed slash command
- `tests/test_full_matrix.py` — 30+ real tests across all combinations

### Modified
- `pyproject.toml` — package name, entry points, module find
- `.claude/settings.json` — MCP server name, hook matcher/script references
- `.claude/settings.local.json` — MCP server name
- `.mcp.json` — server name and module path
- `scripts/model-settings.sh` → `scripts/smartroute-settings.sh` — renamed, updated references
- `scripts/model-settings-hook.sh` → `scripts/smartroute-settings-hook.sh` — renamed
- `README.md` — complete rewrite in English
- `src/l4_smartroute/web_ui.py` — title rename + "made by linux5real" footer
- `src/l4_smartroute/server.py` — FastMCP name string
- All test files — updated import paths

### Deleted
- `src/model_selector/` — old module directory
- `src/model_selector_mcp.egg-info/` — stale egg-info
- `.claude/commands/model-settings.md` — old slash command
- `.claude/commands/whichmodel.md` — old slash command
- `scripts/model-settings.sh` — old script
- `scripts/model-settings-hook.sh` — old script
- `.pytest_cache/` — stale cache

---

### Task 1: Rename Python Module Directory

**Files:**
- Move: `src/model_selector/` → `src/l4_smartroute/`
- Modify: every `.py` file in the new directory (update internal imports)
- Delete: `src/model_selector_mcp.egg-info/`

- [ ] **Step 1: Move the module directory**

```bash
mv src/model_selector src/l4_smartroute
rm -rf src/model_selector_mcp.egg-info
```

- [ ] **Step 2: Update all internal imports in the new module**

In every `.py` file under `src/l4_smartroute/`, replace `model_selector` with `l4_smartroute`. The files that contain these imports are:

`src/l4_smartroute/server.py` — lines 7-12:
```python
from l4_smartroute.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from l4_smartroute.config import get_available_models, load_config, load_model_library
from l4_smartroute.git_diff_analyzer import get_changed_files, match_diff
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.prompt_matcher import extract_keywords, match_prompt
from l4_smartroute.recommender import recommend
```

`src/l4_smartroute/config.py` — line 6:
```python
from l4_smartroute.recommender import _infer_capabilities
```

`src/l4_smartroute/web_ui.py` — line 9:
```python
from l4_smartroute.config import load_config, load_model_library
```

`src/l4_smartroute/blast_radius.py` — line 1:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
```

`src/l4_smartroute/prompt_matcher.py` — line 3:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
```

`src/l4_smartroute/git_diff_analyzer.py` — line 3:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
```

`src/l4_smartroute/recommender.py` — line 3:
```python
from l4_smartroute.task_classifier import classify_task
```

- [ ] **Step 3: Update the FastMCP server name string**

In `src/l4_smartroute/server.py` line 94, change:
```python
mcp = FastMCP("l4-smartroute")
```

- [ ] **Step 4: Commit**

```bash
git add -A src/l4_smartroute src/model_selector
git commit -m "refactor: rename module model_selector → l4_smartroute"
```

---

### Task 2: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update package name, entry points, and module find**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "l4-smartroute"
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
l4-smartroute = "l4_smartroute.server:main"
l4-smartroute-setup = "l4_smartroute.web_ui:main"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Reinstall the package**

```bash
pip install -e .
```

Expected: commands `l4-smartroute` and `l4-smartroute-setup` are now available.

- [ ] **Step 3: Verify the new commands exist**

```bash
which l4-smartroute
which l4-smartroute-setup
```

Expected: both return paths.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: rename package to l4-smartroute with new entry points"
```

---

### Task 3: Update All Test Files

**Files:**
- Modify: all 8 files in `tests/`

- [ ] **Step 1: Replace all imports across test files**

In every test file, replace `from model_selector.` with `from l4_smartroute.`:

`tests/test_recommender.py`:
```python
from l4_smartroute.recommender import recommend
from l4_smartroute.task_classifier import classify_task
```

`tests/test_config.py`:
```python
from l4_smartroute.config import load_config, load_model_library, get_available_models
```

`tests/test_blast_radius.py`:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
```

`tests/test_graph_analyzer.py`:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
```

`tests/test_prompt_matcher.py`:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.prompt_matcher import extract_keywords, match_prompt
```

`tests/test_git_diff_analyzer.py`:
```python
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.git_diff_analyzer import parse_diff_output, match_diff
```

`tests/test_server.py`:
```python
from l4_smartroute.server import build_analyze_result, create_server
```

`tests/test_integration.py`:
```python
from l4_smartroute.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from l4_smartroute.config import get_available_models, load_config, load_model_library
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.prompt_matcher import match_prompt, extract_keywords
from l4_smartroute.recommender import recommend
```

- [ ] **Step 2: Run all existing tests**

```bash
pytest tests/ -v
```

Expected: all tests pass with the new import paths.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "refactor: update test imports to l4_smartroute"
```

---

### Task 4: Update Config Files and Slash Commands

**Files:**
- Modify: `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json`
- Create: `.claude/commands/smartroute-settings.md`, `.claude/commands/smartroute.md`
- Delete: `.claude/commands/model-settings.md`, `.claude/commands/whichmodel.md`
- Create: `scripts/smartroute-settings.sh`, `scripts/smartroute-settings-hook.sh`
- Delete: `scripts/model-settings.sh`, `scripts/model-settings-hook.sh`

- [ ] **Step 1: Update `.claude/settings.json`**

```json
{
  "hooks": {
    "UserPromptExpansion": [
      {
        "matcher": "smartroute-settings",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/scripts/smartroute-settings-hook.sh"
          }
        ]
      }
    ]
  },
  "mcpServers": {
    "l4-smartroute": {
      "command": "python",
      "args": ["-m", "l4_smartroute.server"],
      "cwd": "/home/mcp-project"
    }
  }
}
```

- [ ] **Step 2: Update `.claude/settings.local.json`**

```json
{
  "enabledMcpjsonServers": [
    "l4-smartroute"
  ],
  "enableAllProjectMcpServers": true
}
```

- [ ] **Step 3: Update `.mcp.json`**

```json
{
  "mcpServers": {
    "l4-smartroute": {
      "command": "python3",
      "args": ["-m", "l4_smartroute.server"],
      "cwd": "/home/mcp-project"
    }
  }
}
```

- [ ] **Step 4: Create new slash command files**

`.claude/commands/smartroute-settings.md`:
```markdown
Start the local L4-Smartroute settings server.
```

`.claude/commands/smartroute.md`:
```markdown
Analyze what model to use for: "$ARGUMENTS"

IMPORTANT: You MUST call MCP tools using the tool-call interface, NOT via Bash. MCP tools are NOT shell commands.

## Instructions

1. If $ARGUMENTS is empty, ask the user what task they want analyzed.

2. Call the MCP tool `mcp__l4-smartroute__analyze_task` (this is a tool call, NOT a bash command) with these parameters:
   - `prompt`: "$ARGUMENTS"
   - `graphify_path`: "./graphify-out/graph.json" (if graphify-out/ exists in the working directory, otherwise omit)

3. If `recommendation.routing.ai_review.required` is true:
   - Internally rerank only `recommendation.routing.ai_review.candidates`.
   - Follow `recommendation.routing.ai_review.policy`.
   - Pick exactly one candidate model id and effort level.
   - Do not pick a model outside the candidate list.
   - Treat this as the final recommendation.

4. If `recommendation.routing.ai_review.required` is false, use `recommendation.primary`.

5. Present the result as follows:

---

### Model Recommendation

**Complexity**: {complexity} (score: {total_score})
**Task type**: `{routing.task_type}`
**Router**: `{routing.router_mode}`{if ai_review.required: " + AI review"}
**Model**: `{final_model}` | **Effort**: {final_effort}
**Budget alt**: `{budget_alternative.model}` | {budget_alternative.effort_level} effort

**Blast radius**: {files_affected} files across {communities_crossed} communities
Top areas:
- {community_label} ({nodes_affected} nodes)
- ...

**Cost**: {primary cost} | Alt: {alternative cost}
Top model fits:
- `{routing.scored_candidates[0].model}` score {score}, fit {fit}, ${cost_per_1m}/1M
- `{routing.scored_candidates[1].model}` score {score}, fit {fit}, ${cost_per_1m}/1M
- `{routing.scored_candidates[2].model}` score {score}, fit {fit}, ${cost_per_1m}/1M

Reason:
{one short reason from deterministic or AI review}

➜ `/model {recommended_model_id}`

---

## Rules
- NEVER run MCP tools as bash commands
- Do NOT dump raw JSON
- If AI review is required, mention it in one short phrase only
- If blast radius is 0: note recommendation is keyword-only
- If complexity is "critical": warn this is a high-risk cross-system change
```

- [ ] **Step 5: Delete old slash command files**

```bash
rm .claude/commands/model-settings.md
rm .claude/commands/whichmodel.md
```

- [ ] **Step 6: Create renamed scripts**

`scripts/smartroute-settings.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

PORT="6639"
LOG_FILE="${TMPDIR:-/tmp}/l4-smartroute-setup.log"

print_ready_message() {
  cat <<'EOF'

L4-Smartroute Settings is running at:

http://localhost:6639

Open that link in your browser to configure:
- Which models are available
- Optimization mode (Quality / Balanced / Performance / Token Saver)
- Graphify path and budget settings

After saving, changes to the optimization mode take effect immediately.
Changes to the model list require a Claude Code restart to apply.

To stop the settings server, run: `pkill -f l4-smartroute-setup`
EOF
}

stop_existing_server() {
  python3 - <<'PY'
import os
import signal

patterns = ("l4-smartroute-setup", "l4_smartroute.web_ui")

if not os.path.isdir("/proc"):
    raise SystemExit(0)

for pid_str in os.listdir("/proc"):
    if not pid_str.isdigit():
        continue
    cmdline_path = f"/proc/{pid_str}/cmdline"
    try:
        with open(cmdline_path, "rb") as f:
            cmdline = f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        continue
    if any(pattern in cmdline for pattern in patterns):
        try:
            os.kill(int(pid_str), signal.SIGTERM)
        except ProcessLookupError:
            pass
PY
}

if ! command -v l4-smartroute-setup >/dev/null 2>&1; then
  echo "l4-smartroute-setup is not available on PATH." >&2
  exit 1
fi

stop_existing_server
sleep 0.2

setsid -f sh -c 'L4_SMARTROUTE_OPEN_BROWSER=0 exec l4-smartroute-setup' >"${LOG_FILE}" 2>&1 </dev/null
print_ready_message
```

`scripts/smartroute-settings-hook.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="${SCRIPT_DIR}/smartroute-settings.sh"

reason="$("${SETUP_SCRIPT}")"

REASON="$reason" python3 - <<'PY'
import json
import os

print(json.dumps({
    "decision": "block",
    "reason": os.environ["REASON"],
}))
PY
```

- [ ] **Step 7: Delete old scripts**

```bash
rm scripts/model-settings.sh
rm scripts/model-settings-hook.sh
chmod +x scripts/smartroute-settings.sh scripts/smartroute-settings-hook.sh
```

- [ ] **Step 8: Commit**

```bash
git add .claude/ .mcp.json scripts/
git commit -m "refactor: rename configs and slash commands to L4-Smartroute"
```

---

### Task 5: Update Web UI Branding

**Files:**
- Modify: `src/l4_smartroute/web_ui.py`

- [ ] **Step 1: Update the HTML title**

Line 54, change:
```html
<title>L4-Smartroute &#8212; Settings</title>
```

- [ ] **Step 2: Update the header h1**

Line 181, change:
```html
<h1>L4-Smartroute</h1>
```

- [ ] **Step 3: Update the footer branding**

Lines 238-242, change the footer to:
```html
  <footer class="footer">
    <div class="footer-left">
      <span>L4-Smartroute</span>
      <span>&#183;</span>
      <span>made by <a href="https://github.com/Linux5real" target="_blank" rel="noopener">linux5real</a></span>
    </div>
    <button class="btn" onclick="resetDefaults()">Reset to Defaults</button>
  </footer>
```

- [ ] **Step 4: Update the env var name for browser opening**

Line 755, change:
```python
open_browser = os.environ.get("L4_SMARTROUTE_OPEN_BROWSER", "1").lower() not in {
```

- [ ] **Step 5: Update the print line**

Line 761, change:
```python
print(f"L4-Smartroute Settings: {url}")
```

- [ ] **Step 6: Update the shutdown message**

Line 766, change:
```python
print("\nSettings server stopped.")
```

(This line is already correct — no change needed.)

- [ ] **Step 7: Commit**

```bash
git add src/l4_smartroute/web_ui.py
git commit -m "feat: rebrand web UI to L4-Smartroute with linux5real footer"
```

---

### Task 6: Code Cleanup

**Files:**
- Delete: `.pytest_cache/`, `src/model_selector_mcp.egg-info/` (if not already deleted)
- Modify: `.gitignore`

- [ ] **Step 1: Delete stale cache and build artifacts**

```bash
rm -rf .pytest_cache
rm -rf src/model_selector_mcp.egg-info
```

- [ ] **Step 2: Add `.pytest_cache` and `.venv` to `.gitignore`**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.eggs/
.pytest_cache/
.venv/
```

- [ ] **Step 3: Verify no stale references remain**

```bash
grep -rn "model.selector\|model_selector\|Model.Selector" --include='*.py' --include='*.json' --include='*.yaml' --include='*.md' --include='*.sh' --include='*.toml' | grep -v '.git/' | grep -v 'docs/superpowers/' | grep -v '__pycache__'
```

Expected: zero matches outside docs/superpowers/.

- [ ] **Step 4: Run all tests to verify nothing is broken**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: clean up stale artifacts and update gitignore"
```

---

### Task 7: Create Install Script

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Write the installer**

```bash
#!/usr/bin/env bash
set -euo pipefail

PACKAGE="l4-smartroute"
REPO="https://github.com/Linux5Real/L4-Smartroute"

info()  { printf '\033[1;34m[info]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[ok]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[warn]\033[0m  %s\n' "$1"; }
fail()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

info "Installing $PACKAGE..."

# --- check python3 ---
command -v python3 >/dev/null 2>&1 || fail "python3 is required but not found. Install Python 3.11+ first."

# --- detect package manager ---
if command -v uv >/dev/null 2>&1; then
  PM="uv"
  info "Using uv"
  uv tool install "$PACKAGE"
elif command -v pipx >/dev/null 2>&1; then
  PM="pipx"
  info "Using pipx"
  pipx install "$PACKAGE"
else
  PM="pip"
  info "Using pip"
  pip install "$PACKAGE"
fi

ok "$PACKAGE installed via $PM"

# --- register with Claude Code ---
if command -v claude >/dev/null 2>&1; then
  info "Registering MCP server with Claude Code..."
  claude mcp add l4-smartroute -- l4-smartroute
  ok "MCP server registered. Restart Claude Code to activate."
else
  warn "Claude Code CLI not found. To register manually, run:"
  echo "  claude mcp add l4-smartroute -- l4-smartroute"
fi

echo ""
ok "Installation complete!"
info "Run 'l4-smartroute-setup' to open the configuration UI."
info "Docs: $REPO"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x install.sh
```

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: add one-command installer (curl|bash)"
```

---

### Task 8: Write English README

**Files:**
- Modify: `README.md` (complete rewrite)

- [ ] **Step 1: Write the new README**

The README should contain these sections in order:
1. Header with "L4-Smartroute" + one-line description + "made by linux5real"
2. What is L4-Smartroute? (2-3 sentences)
3. Built on Graphify (credit + link)
4. Features (bullet list)
5. Prerequisites
6. Installation (one-command + manual)
7. Setup (web UI, slash commands)
8. How It Works (brief pipeline)
9. Supported Models (table by provider with note about requesting new ones)
10. License

Key content for each section:

**Header:**
```markdown
# L4-Smartroute

Intelligent AI model routing for coding agents. Picks the right model for the right task — so you stop overpaying for simple fixes and underpowering complex refactors.

*made by [linux5real](https://github.com/Linux5real)*
```

**What is L4-Smartroute:**
L4-Smartroute is an MCP server that analyzes your task (prompt or git diff), calculates code complexity using Graphify knowledge graphs, and recommends the best AI model + effort level from 54+ models across 14 providers. It supports three router modes (deterministic, hybrid, ai-review) and four optimization levels (quality, balanced, performance, token-saver).

**Built on Graphify:**
Credit [Graphify](https://github.com/Linux5real/graphify) for the knowledge graph analysis that powers blast radius calculation. Explain in 2-3 sentences.

**Features:**
- 54+ models across 14 providers
- 3 router modes, 4 optimization levels
- Graphify-powered blast radius analysis
- Web UI for configuration (port 6639)
- One-command install with auto Claude Code integration

**Prerequisites:**
- Python 3.11+
- One of: `uv`, `pipx`, or `pip`
- Claude Code CLI (for auto-integration, optional)
- Graphify (for blast radius analysis, optional)

**Installation:**
```bash
curl -fsSL https://raw.githubusercontent.com/Linux5Real/L4-Smartroute/main/install.sh | bash
```
Then manual alternative with step-by-step.

**Setup:**
- Run `l4-smartroute-setup` to open configuration UI
- In Claude Code: `/smartroute` for model recommendation, `/smartroute-settings` for configuration

**How It Works:**
```
Prompt / Diff → Graphify blast radius → Task classification → Candidate scoring → Optional AI review → Model + effort level
```

**Supported Models:**
Table grouped by provider. Bottom note: "Missing a model? [Open an issue](https://github.com/Linux5Real/L4-Smartroute/issues) and we'll add it."

**License:** MIT

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README in English with install instructions"
```

---

### Task 9: Comprehensive Real Tests

**Files:**
- Create: `tests/test_full_matrix.py`

- [ ] **Step 1: Write the full matrix test file**

This file tests every router_mode × optimize_for combination (12 total) with 2-3 test cases each. Each test calls `recommend()` with realistic parameters and verifies the output structure and behavior.

```python
import pytest

from l4_smartroute.recommender import recommend

MODELS = [
    {
        "id": "claude-fable-5",
        "provider": "anthropic",
        "tier": "ultra",
        "cost": {"input_per_1m": 20.0, "output_per_1m": 100.0},
        "context_window": 200000,
        "quality_score": 98,
        "speed": "medium",
        "strengths": ["ultra-coding", "complex-reasoning", "architecture-decisions"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    {
        "id": "claude-opus-4-8",
        "provider": "anthropic",
        "tier": "high",
        "cost": {"input_per_1m": 15.0, "output_per_1m": 75.0},
        "context_window": 200000,
        "quality_score": 94,
        "speed": "slow",
        "strengths": ["complex-reasoning", "multi-file-refactoring", "architecture-decisions", "debugging"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "tier": "medium",
        "cost": {"input_per_1m": 3.0, "output_per_1m": 15.0},
        "context_window": 200000,
        "quality_score": 85,
        "speed": "fast",
        "strengths": ["code-generation", "moderate-refactoring", "bug-fixes"],
        "effort_levels": ["low", "medium", "high"],
    },
    {
        "id": "claude-haiku-4-5",
        "provider": "anthropic",
        "tier": "low",
        "cost": {"input_per_1m": 0.25, "output_per_1m": 1.25},
        "context_window": 200000,
        "quality_score": 72,
        "speed": "fast",
        "strengths": ["simple-fixes", "typo-corrections", "documentation", "boilerplate"],
        "effort_levels": None,
    },
    {
        "id": "gemini-2.5-flash",
        "provider": "google",
        "tier": "medium",
        "cost": {"input_per_1m": 0.15, "output_per_1m": 0.60},
        "context_window": 1048576,
        "quality_score": 80,
        "speed": "fast",
        "strengths": ["code-generation", "long-context"],
        "effort_levels": ["low", "medium", "high"],
    },
]

ROUTER_MODES = ["deterministic", "hybrid", "ai-review"]
OPTIMIZE_MODES = ["quality", "balanced", "performance", "token-saver"]

SIMPLE_PROMPT = "fix a typo in the readme"
COMPLEX_PROMPT = "refactor the authentication system across multiple modules and update all tests"
SIMPLE_BLAST = {"files_affected": 1, "communities_crossed": 0, "avg_centrality": 0.01, "max_edge_depth": 0}
COMPLEX_BLAST = {"files_affected": 15, "communities_crossed": 4, "avg_centrality": 0.25, "max_edge_depth": 3}


def _rec(router_mode, optimize_for, prompt, blast_radius=None):
    return recommend(
        "medium" if "typo" in prompt else "high",
        MODELS,
        optimize_for,
        prompt=prompt,
        blast_radius=blast_radius,
        router_mode=router_mode,
    )


def _validate_structure(rec):
    assert "primary" in rec
    assert "model" in rec["primary"]
    assert "effort_level" in rec["primary"]
    assert "reason" in rec["primary"]
    assert "budget_alternative" in rec
    assert "estimated_cost" in rec
    assert "routing" in rec
    assert "task_type" in rec["routing"]
    assert "router_mode" in rec["routing"]
    assert "scored_candidates" in rec["routing"]
    assert "ai_review" in rec["routing"]
    model_ids = {m["id"] for m in MODELS}
    assert rec["primary"]["model"] in model_ids


class TestDeterministicQuality:
    def test_simple_task(self):
        rec = _rec("deterministic", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_task(self):
        rec = _rec("deterministic", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_recommends_strong_model(self):
        rec = _rec("deterministic", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert rec["primary"]["model"] in ("claude-fable-5", "claude-opus-4-8")


class TestDeterministicBalanced:
    def test_simple_task(self):
        rec = _rec("deterministic", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is False

    def test_complex_task(self):
        rec = _rec("deterministic", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_complex_has_budget_alternative(self):
        rec = _rec("deterministic", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert rec["budget_alternative"] is not None


class TestDeterministicPerformance:
    def test_simple_task(self):
        rec = _rec("deterministic", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("deterministic", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_prefers_fast_models(self):
        rec = _rec("deterministic", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        assert model["speed"] in ("fast", "medium")


class TestDeterministicTokenSaver:
    def test_simple_task(self):
        rec = _rec("deterministic", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("deterministic", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_prefers_cheap_models(self):
        rec = _rec("deterministic", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        cost = model["cost"]["input_per_1m"] + model["cost"]["output_per_1m"]
        assert cost <= 20.0


class TestHybridQuality:
    def test_simple_task_no_ai_review(self):
        rec = _rec("hybrid", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task_triggers_ai_review(self):
        rec = _rec("hybrid", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True
        assert len(rec["routing"]["ai_review"]["candidates"]) >= 1

    def test_ai_review_candidates_have_capabilities(self):
        rec = _rec("hybrid", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        if rec["routing"]["ai_review"]["required"]:
            for c in rec["routing"]["ai_review"]["candidates"]:
                assert "capabilities" in c
                assert "model" in c


class TestHybridBalanced:
    def test_simple_task(self):
        rec = _rec("hybrid", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestHybridPerformance:
    def test_simple_task(self):
        rec = _rec("hybrid", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)


class TestHybridTokenSaver:
    def test_simple_task(self):
        rec = _rec("hybrid", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)

    def test_complex_task(self):
        rec = _rec("hybrid", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)

    def test_complex_prefers_budget(self):
        rec = _rec("hybrid", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        primary = rec["primary"]["model"]
        model = next(m for m in MODELS if m["id"] == primary)
        assert model["tier"] in ("low", "medium")


class TestAiReviewQuality:
    def test_simple_task_always_reviews(self):
        rec = _rec("ai-review", "quality", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task_always_reviews(self):
        rec = _rec("ai-review", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_candidates_include_policy(self):
        rec = _rec("ai-review", "quality", COMPLEX_PROMPT, COMPLEX_BLAST)
        assert len(rec["routing"]["ai_review"]["policy"]) >= 1


class TestAiReviewBalanced:
    def test_simple_task(self):
        rec = _rec("ai-review", "balanced", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "balanced", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestAiReviewPerformance:
    def test_simple_task(self):
        rec = _rec("ai-review", "performance", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "performance", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestAiReviewTokenSaver:
    def test_simple_task(self):
        rec = _rec("ai-review", "token-saver", SIMPLE_PROMPT, SIMPLE_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True

    def test_complex_task(self):
        rec = _rec("ai-review", "token-saver", COMPLEX_PROMPT, COMPLEX_BLAST)
        _validate_structure(rec)
        assert rec["routing"]["ai_review"]["required"] is True


class TestEdgeCases:
    def test_no_graphify_graph_still_works(self):
        rec = recommend(
            "medium", MODELS, "balanced",
            prompt="fix a bug",
            blast_radius=None,
            router_mode="hybrid",
        )
        _validate_structure(rec)

    def test_empty_prompt_with_blast_radius(self):
        rec = recommend(
            "high", MODELS, "balanced",
            prompt="",
            blast_radius=COMPLEX_BLAST,
            router_mode="deterministic",
        )
        _validate_structure(rec)
        assert rec["routing"]["task_type"] == "review"

    def test_single_model_available(self):
        rec = recommend(
            "critical", [MODELS[0]], "quality",
            prompt="refactor everything",
            router_mode="hybrid",
        )
        _validate_structure(rec)
        assert rec["primary"]["model"] == "claude-fable-5"

    def test_all_modes_return_scored_candidates(self):
        for router in ROUTER_MODES:
            for opt in OPTIMIZE_MODES:
                rec = _rec(router, opt, COMPLEX_PROMPT, COMPLEX_BLAST)
                assert len(rec["routing"]["scored_candidates"]) >= 1
```

- [ ] **Step 2: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all existing tests + all new matrix tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_full_matrix.py
git commit -m "test: add full router×optimization matrix tests (30+ cases)"
```

---

### Task 10: Performance Review

**Files:**
- No files modified (analysis only, optimize if needed)

- [ ] **Step 1: Profile the recommendation engine**

```bash
python3 -c "
import time
from l4_smartroute.recommender import recommend
from l4_smartroute.config import load_model_library

models = load_model_library('models.json')
active = models[:15]

start = time.perf_counter()
for _ in range(100):
    recommend('high', active, 'balanced', prompt='refactor auth across modules', blast_radius={'files_affected': 12, 'communities_crossed': 3, 'avg_centrality': 0.2, 'max_edge_depth': 3}, router_mode='hybrid')
elapsed = time.perf_counter() - start
print(f'100 recommendations: {elapsed:.3f}s ({elapsed/100*1000:.1f}ms each)')
"
```

Expected: under 5ms per recommendation call (pure Python scoring, no I/O).

- [ ] **Step 2: Profile graph loading if graph exists**

```bash
python3 -c "
import time
from pathlib import Path

graph = Path('graphify-out/graph.json')
if not graph.exists():
    print('No graph file — skipping graph load benchmark')
else:
    from l4_smartroute.graph_analyzer import GraphAnalyzer
    start = time.perf_counter()
    analyzer = GraphAnalyzer(graph)
    elapsed = time.perf_counter() - start
    print(f'Graph load: {elapsed:.3f}s ({analyzer.node_count()} nodes, {analyzer.edge_count()} edges)')
"
```

Expected: under 500ms for typical project graphs. If over, flag for optimization.

- [ ] **Step 3: Document findings**

If any operation exceeds thresholds, optimize. Otherwise note that performance is acceptable and move on.
