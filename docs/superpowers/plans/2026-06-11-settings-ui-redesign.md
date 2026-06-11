# Settings UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely redesign the Model Selector Settings web UI for a modern, clean, premium developer-tool aesthetic — no generic AI look, no emojis, with live-save, better model browsing, and separated pricing/context display.

**Architecture:** Single-file rewrite of the `HTML_PAGE` constant in `web_ui.py`. The Python HTTP server code stays identical — only the embedded HTML/CSS/JS changes. External resources: Google Fonts CDN (Outfit) and Simple Icons CDN (brand logos). All behavior changes (live-save, search, sort, router mode section) are pure frontend.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, animations), vanilla JavaScript, Google Fonts CDN, Simple Icons CDN

**Security note:** All innerHTML usage in this codebase is with trusted, developer-controlled template strings — model data is from a local JSON file served by our own backend, not user input. No sanitization library is needed.

---

## Design Direction

**Aesthetic:** Industrial-refined dark — inspired by Linear, Raycast, Arc. Premium developer tooling, not generic AI product.

**Typography:** Outfit (geometric, modern, distinctive) via Google Fonts

**Color Palette (warm dark + teal accent):**
- `--bg: #0c0c0f` — deep dark background
- `--surface: #151519` — card/section backgrounds
- `--accent: #2dd4bf` — teal (fresh, modern, not the typical blue/purple)
- `--green: #34d399` — success/input pricing
- `--amber: #fbbf24` — warning/output pricing

**Key Changes from Current:**
1. Custom inline SVG icons replace emojis on optimization modes
2. Router Mode becomes its own section (radio buttons with descriptions) instead of a dropdown
3. Model cards: compact with provider brand icon, separated In/Out pricing, human-readable context (128k, 1M)
4. Search + Sort controls for model list
5. Live-save (debounced 600ms) — no manual save button
6. Footer with credits and GitHub link
7. Staggered fade-in animations on sections

---

## File Structure

- **Modify:** `src/model_selector/web_ui.py` — replace `HTML_PAGE` constant (lines 49-461)
- No new files created
- No Python server code changes needed

---

### Task 1: Write the complete redesigned web_ui.py

**Files:**
- Modify: `src/model_selector/web_ui.py:49-461` (replace HTML_PAGE constant)

This is the core task. The entire frontend is a single HTML string constant embedded in Python. We replace it wholesale with the new design.

- [ ] **Step 1: Read the current file to confirm structure**

Run: `head -50 src/model_selector/web_ui.py && echo "---" && tail -80 src/model_selector/web_ui.py`

Verify: Python imports and server code at top/bottom, `HTML_PAGE = r"""..."""` in the middle.

- [ ] **Step 2: Write the complete new web_ui.py**

Use the Write tool to write the entire file to `src/model_selector/web_ui.py`. The Python server code (imports, helpers, SetupHandler class, run_setup function) stays identical. Only `HTML_PAGE` changes.

The complete file content is provided in the companion code file: `docs/superpowers/plans/2026-06-11-settings-ui-redesign-code.py`

Key sections of the new HTML_PAGE:

**CSS Design System (~120 lines):**
- Google Fonts import (Outfit)
- CSS variables: warm dark palette with teal accent, 4 tier colors
- Component styles: mode cards, router options, model cards, filter chips, settings form
- Animations: fadeUp for sections, syncPulse for save indicator
- Responsive: 2-column mode grid on mobile, single-column settings

**HTML Structure (~70 lines):**
- Header: title + sync indicator dot + subtitle
- Warning banner: shows when model list changes (SVG warning icon, not emoji)
- Section 1: Optimization Mode (4-card grid, rendered by JS)
- Section 2: Router Mode (radio buttons with descriptions, rendered by JS)
- Section 3: Models (search + sort controls, filter chips, scrollable card grid)
- Section 4: Advanced Settings (graphify path, BFS depth, max budget)
- Footer: credits line + Reset to Defaults button
- Toast notification element

**JavaScript (~200 lines):**
- State: allModels, config, selectedModels, savedModels, activeFilter, searchQuery, currentSort, currentRouterMode
- Constants: MODES (with inline SVG icons), ROUTER_MODES, PROVIDER_ICONS mapping, PROVIDER_NAMES display names
- Utilities: debounce(), formatCtx() (context window formatting), providerIconHtml() (brand icon with letter fallback)
- autoSave: debounced 600ms, POSTs config, updates sync dot state, shows toast
- Rendering: renderModes(), renderRouterModes(), renderFilters(), renderModels() with search/sort/filter
- bindInputs(): wires all form inputs to autoSave, search to debounced filter, sort to re-render
- Polling: 5-second interval to detect external config.yaml changes

- [ ] **Step 3: Verify Python syntax**

Run: `python3 -c "import py_compile; py_compile.compile('src/model_selector/web_ui.py', doraise=True)" && echo "OK"`

Expected: `OK` — no syntax errors.

- [ ] **Step 4: Commit the redesign**

```bash
git add src/model_selector/web_ui.py
git commit -m "feat: redesign settings UI with modern dark theme, live-save, and improved model browsing"
```

---

### Task 2: Start the server and verify in browser

**Files:** None (testing only)

- [ ] **Step 1: Kill any existing server on port 6639**

Run: `lsof -ti:6639 | xargs -r kill 2>/dev/null; echo "Port cleared"`

- [ ] **Step 2: Start the settings server**

Run: `cd /home/mcp-project && MODEL_SELECTOR_OPEN_BROWSER=0 python3 -m model_selector.web_ui &`

Expected: `Model Selector Settings: http://127.0.0.1:6639`

- [ ] **Step 3: Verify the page loads**

Run: `curl -s http://127.0.0.1:6639/ | head -5`

Expected: HTML starting with `<!DOCTYPE html>` and containing `<title>Model Selector — Settings</title>`

- [ ] **Step 4: Verify the API endpoint works**

Run: `curl -s http://127.0.0.1:6639/api/state | python3 -c "import json,sys; d=json.load(sys.stdin); print('Models:', len(d['models'])); print('Config:', d['config']['preferences']['optimize_for'])"`

Expected:
```
Models: 113
Config: quality
```

- [ ] **Step 5: Open in browser and verify visually**

Open `http://127.0.0.1:6639` in a browser. Verify:

1. **Header:** "Model Selector" title with green sync dot, subtitle mentioning auto-save
2. **Optimization Mode:** 4 cards with SVG icons (diamond, sliders, lightning, coin) — NO emojis. Active mode highlighted in teal.
3. **Router Mode:** 3 radio-button options with descriptions. "Hybrid" has a "Recommended" tag. Selecting a mode auto-saves.
4. **Models:** Search input + sort dropdown. Provider filter chips. Compact model cards with:
   - Provider brand icon (from Simple Icons CDN) or letter fallback
   - Model name + tier badge (ultra/high/medium/low with distinct colors)
   - Separated pricing: "In $5 · Out $25" (green/amber)
   - Context window: "1M", "200k", "128k" (not "1000K ctx")
   - Speed + effort levels
5. **Settings:** Graphify Path, BFS Depth, Max Budget — 2-column grid
6. **Footer:** "Model Selector MCP · Built by Linux5real" with GitHub link + "Reset to Defaults" button
7. **Live-save:** Change any setting -> sync dot pulses amber -> "Saved" toast appears -> no manual save button
8. **Search:** Type in the search box -> models filter by name/provider/id in real-time
9. **Sort:** Change sort dropdown -> models reorder by name/quality/cost/context

- [ ] **Step 6: Test reset to defaults**

Click "Reset to Defaults". Verify:
- Models reset to claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5
- Optimization mode resets to Balanced
- Router mode resets to Hybrid
- Settings fields reset to defaults
- Auto-save triggers

- [ ] **Step 7: Stop the test server**

Run: `lsof -ti:6639 | xargs -r kill 2>/dev/null; echo "Server stopped"`

---

## Design Decisions Reference

| Aspect | Old | New |
|--------|-----|-----|
| Font | System fonts | Outfit (Google Fonts CDN) |
| Icons (modes) | Emoji (star, balance, lightning, money) | Custom inline SVGs |
| Icons (providers) | Text "ANTHROPIC" | Brand logos via Simple Icons CDN |
| Context window | "1000K ctx" | "1M", "200k", "128k" |
| Pricing | Combined "$30.00/1M" | Separated "In $5 / Out $25" |
| Router Mode | Dropdown in Settings | Own section with radio buttons + descriptions |
| Save | Manual "Save Configuration" button | Live-save (debounced 600ms) |
| Color accent | Blue (#58a6ff) | Teal (#2dd4bf) |
| Search | None | Text search filtering models |
| Sort | None | Sort by name/quality/cost/context |
| Footer | None | Credits + GitHub link |
| Animation | None | Staggered fade-up + sync pulse |
