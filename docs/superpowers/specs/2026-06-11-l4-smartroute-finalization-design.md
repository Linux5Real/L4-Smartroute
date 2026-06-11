# L4-Smartroute Finalization Design

**Date:** 2026-06-11
**Author:** linux5real + Claude
**Repo:** https://github.com/Linux5Real/L4-Smartroute

---

## Overview

Finalize the L4-Smartroute MCP project: rename from "Model Selector", create a one-command installer, write an English README, clean up the codebase, review performance, and add comprehensive real tests.

---

## 1. Rename: "Model Selector" → "L4-Smartroute"

### Scope

| Location | Old | New |
|---|---|---|
| Python package (`pyproject.toml`) | `model-selector` | `l4-smartroute` |
| CLI entry points | `model-selector-mcp`, `model-selector-setup` | `l4-smartroute`, `l4-smartroute-setup` |
| MCP server name (`.claude/settings.json`) | `model-selector` | `l4-smartroute` |
| Web UI title & text | "Model Selector" | "L4-Smartroute" |
| `.mcp.json` | `model-selector` | `l4-smartroute` |
| Slash command: settings | `/model-settings` | `/smartroute-settings` |
| Slash command: recommend | `/whichmodel` | `/smartroute` |
| Python module directory | `src/model_selector/` | `src/l4_smartroute/` |
| All internal references | `model_selector` | `l4_smartroute` |

### Branding

- README header: "made by linux5real"
- Web UI footer: "made by linux5real"

---

## 2. One-Command Installer

### User-facing command

```bash
curl -fsSL https://raw.githubusercontent.com/Linux5Real/L4-Smartroute/main/install.sh | bash
```

### Install script logic

1. **Check prerequisites:** Verify `python3` is available, error if not.
2. **Detect package manager:** `uv` > `pipx` > `pip` (use the best available).
3. **Install package:**
   - `uv tool install l4-smartroute`, OR
   - `pipx install l4-smartroute`, OR
   - `pip install l4-smartroute`
4. **Claude Code integration:** Run `claude mcp add l4-smartroute -- l4-smartroute` to auto-register the MCP server.
   - If `claude` CLI not found: print warning with manual instructions, don't abort.
5. **Success message:** Confirm installation, point to `l4-smartroute-setup` for configuration.

### Future extensibility

The script uses `claude` for registration. When other CLIs are supported (Cursor, Copilot), add their registration commands to the same script.

---

## 3. README (English)

### Structure (kept concise — installation near the top)

1. **Header** — "L4-Smartroute" + one-line description + "made by linux5real"
2. **What is L4-Smartroute?** — 2-3 sentences: intelligent model routing based on task analysis and code complexity.
3. **Built on Graphify** — Credit + link to Graphify repo. One paragraph explaining the knowledge graph integration.
4. **Features** — Bullet list: 3 router modes, 4 optimization levels, 54+ models, 14 providers, web UI.
5. **Prerequisites** — Python 3.10+, one of: `uv`/`pipx`/`pip`, Claude Code CLI (for auto-integration), Graphify (optional, for full blast radius analysis).
6. **Installation** — One-command (`curl | bash`) + manual alternative step-by-step.
7. **Setup** — Start web UI (`l4-smartroute-setup`), describe configuration options, slash commands (`/smartroute`, `/smartroute-settings`).
8. **How it works** — Brief: Task Classification → Blast Radius → Model Scoring → Recommendation.
9. **Supported Models** — Table or list of all 54+ models by provider. Note: "Missing a model? Open an issue and we'll add it."
10. **License**

---

## 4. Code Cleanup

### Actions

- Remove any files not needed for the MCP server.
- Check every file in project root for relevance.
- Check `scripts/` — update for new names, remove obsolete scripts.
- Check `src/` for dead imports or unused modules.
- Keep `tests/` — needed for real tests (but clean up obsolete test files if any).
- Update `.mcp.json` and `.claude/` configs to new names.
- Remove old German README content (replaced by English README).

---

## 5. Performance & Real Tests

### Test matrix

Every combination of router mode × optimization level:

| Router Mode | Optimization Levels |
|---|---|
| `deterministic` | `quality`, `balanced`, `performance`, `token-saver` |
| `hybrid` | `quality`, `balanced`, `performance`, `token-saver` |
| `ai-review` | `quality`, `balanced`, `performance`, `token-saver` |

= 12 combinations × 2-3 test cases each = ~30 tests

### Test cases per combination

1. **Simple task** (e.g., "fix a typo in the readme") → should recommend a budget model.
2. **Complex task** (e.g., "refactor the authentication system across multiple modules") → should recommend a powerful model.
3. **Edge case** — no Graphify graph available, missing config, empty prompt.

### Performance review

- Measure MCP server response times.
- Profile the scoring algorithm in `recommender.py`.
- Optimize if any operation takes >500ms.

---

## Execution Order

1. Rename (Model Selector → L4-Smartroute) — must happen first, everything else builds on it.
2. Code cleanup — remove dead weight before writing tests.
3. Install script (`install.sh`) — create the one-command installer.
4. README — write English documentation.
5. Tests — comprehensive real tests across all combinations.
6. Performance — review and optimize based on test results.
