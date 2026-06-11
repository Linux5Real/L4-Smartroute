import json
import os
import webbrowser
import threading
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from model_selector.config import load_config, load_model_library

SERVER_DIR = Path(__file__).parent.parent.parent
DEFAULT_CONFIG = SERVER_DIR / "config.yaml"
DEFAULT_MODELS = SERVER_DIR / "models.json"


def _load_models():
    return load_model_library(DEFAULT_MODELS)


def _load_cfg():
    try:
        return load_config(DEFAULT_CONFIG)
    except FileNotFoundError:
        return {
            "available_models": [],
            "graphify_path": "./graphify-out/graph.json",
            "preferences": {
                "optimize_for": "balanced",
                "router_mode": "hybrid",
                "max_budget_per_task": None,
                "bfs_max_depth": 3,
            },
        }


def _save_config(cfg: dict):
    import yaml
    with open(DEFAULT_CONFIG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


def _config_mtime() -> float:
    try:
        return os.path.getmtime(DEFAULT_CONFIG)
    except OSError:
        return 0.0


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Model Selector &#8212; Settings</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#e5e5e5;--surface:#efefef;--surface-raised:#f5f5f5;--surface-hover:#f9f9f9;
  --border:#d1d1d6;--border-hover:#c4c4ca;
  --text:#18181b;--text-secondary:#71717a;--text-tertiary:#a1a1aa;
  --accent:#ffffff;--accent-dim:#ffffff;--accent-medium:rgba(255,255,255,0.9);
  --accent-border:#ffffff;
  --green:#059669;--amber:#d97706;--red:#dc2626;
  --tier-ultra:#7c3aed;--tier-high:#ea580c;--tier-medium:#2563eb;--tier-low:#059669;
  --radius:12px;--radius-sm:8px;--radius-xs:6px;
  --font:'Outfit',system-ui,-apple-system,sans-serif;
  --shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04)
}
body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh;-webkit-font-smoothing:antialiased}
.app{max-width:880px;margin:0 auto;padding:40px 24px 24px}

header{margin-bottom:32px}
.header-row{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.header-row h1{font-size:22px;font-weight:600;letter-spacing:-0.3px}
.sync-indicator{width:8px;height:8px;border-radius:50%;background:var(--green);position:relative;flex-shrink:0}
.sync-indicator::after{content:'';position:absolute;inset:-3px;border-radius:50%;border:1.5px solid var(--green);opacity:0}
.sync-indicator.saving{background:var(--amber)}
.sync-indicator.saving::after{border-color:var(--amber);animation:syncPulse 1s ease infinite}
.sync-indicator.error{background:var(--red)}
@keyframes syncPulse{0%{opacity:.5;transform:scale(1)}100%{opacity:0;transform:scale(2)}}
.subtitle{font-size:13px;color:var(--text-secondary)}

.banner{border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:20px;display:none;align-items:center;gap:10px;font-size:13px;line-height:1.5}
.banner.show{display:flex}
.banner--warning{background:rgba(217,119,6,0.06);border:1px solid rgba(217,119,6,0.2)}
.banner--warning svg{color:var(--amber);flex-shrink:0}
.banner strong{color:var(--amber)}

.section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:16px;box-shadow:var(--shadow);animation:fadeUp 400ms ease both}
.section:nth-child(3){animation-delay:50ms}
.section:nth-child(4){animation-delay:100ms}
.section:nth-child(5){animation-delay:150ms}
.section:nth-child(6){animation-delay:200ms}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.section-title{font-size:14px;font-weight:600;margin-bottom:16px;letter-spacing:-0.2px;color:var(--text)}

.mode-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:700px){.mode-grid{grid-template-columns:repeat(2,1fr)}}
.mode-card{border:1.5px solid var(--border);border-radius:var(--radius-sm);padding:16px 14px;cursor:pointer;transition:border-color 220ms ease,background 220ms ease,box-shadow 220ms ease,transform 180ms ease;text-align:center;background:#f9f9f9}
.mode-card:hover{border-color:var(--border-hover);background:#fff;transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,0.08)}
.mode-card.active{border-color:#999;background:#fff;box-shadow:0 0 0 2px #d1d1d6}
.mode-card .mode-icon{width:32px;height:32px;margin:0 auto 10px;color:var(--text-secondary);transition:color 220ms ease}
.mode-card.active .mode-icon{color:var(--accent)}
.mode-card h3{font-size:13px;font-weight:600;margin-bottom:3px}
.mode-card p{font-size:11px;color:var(--text-secondary);line-height:1.4}

.router-options{display:flex;flex-direction:column;gap:8px}
.router-option{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;border:1.5px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;transition:border-color 220ms ease,background 220ms ease,box-shadow 220ms ease;background:#f9f9f9}
.router-option:hover{border-color:var(--border-hover);background:#fff}
.router-option.active{border-color:#999;background:#fff;box-shadow:0 0 0 2px #d1d1d6}
.router-option input[type=radio]{margin-top:2px;accent-color:var(--accent);flex-shrink:0}
.router-option-content{display:flex;flex-direction:column;gap:2px}
.router-option-title{font-size:13px;font-weight:600}
.router-option-desc{font-size:12px;color:var(--text-secondary);line-height:1.4}
.tag{display:inline-block;font-size:10px;font-weight:500;padding:1px 6px;border-radius:4px;background:#fff;color:#666;vertical-align:middle;margin-left:4px;border:1px solid #d1d1d6}

.models-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:10px}
.models-header .section-title{margin-bottom:0}
.models-controls{display:flex;gap:8px;align-items:center}
.search-input{padding:6px 12px;background:#f9f9f9;border:1px solid var(--border);border-radius:var(--radius-xs);color:var(--text);font-family:var(--font);font-size:12px;width:180px;transition:border-color 200ms}
.search-input:focus{outline:none;border-color:#999;box-shadow:0 0 0 2px rgba(0,0,0,0.05)}
.search-input::placeholder{color:var(--text-tertiary)}
.sort-select{padding:6px 10px;background:#f9f9f9;border:1px solid var(--border);border-radius:var(--radius-xs);color:var(--text);font-family:var(--font);font-size:12px;cursor:pointer;appearance:none;-webkit-appearance:none;padding-right:24px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23a1a1aa' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 8px center}
.sort-select:focus{outline:none;border-color:var(--accent)}

.filter-bar{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.filter-chip{padding:4px 12px;border:1px solid var(--border);border-radius:20px;font-size:11px;font-weight:500;cursor:pointer;background:transparent;color:var(--text-secondary);transition:border-color 200ms ease,color 200ms ease,background 200ms ease;font-family:var(--font)}
.filter-chip:hover{border-color:var(--border-hover);color:var(--text)}
.filter-chip.active{border-color:#999;color:var(--text);background:#fff}

.model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:8px;max-height:560px;overflow-y:auto;padding-right:4px}
.model-grid::-webkit-scrollbar{width:4px}
.model-grid::-webkit-scrollbar-track{background:transparent}
.model-grid::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.model-card{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-xs);cursor:pointer;transition:border-color 220ms ease,background 220ms ease,box-shadow 220ms ease,transform 180ms ease;background:#f9f9f9}
.model-card:hover{border-color:var(--border-hover);background:#fff;transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.model-card.selected{border-color:#999;background:#fff;box-shadow:0 0 0 2px #d1d1d6}
.model-info{flex:1;min-width:0}
.model-name-row{display:flex;align-items:center;gap:6px;margin-bottom:2px}
.provider-icon{width:16px;height:16px;border-radius:3px;flex-shrink:0;object-fit:contain}
.provider-avatar{width:16px;height:16px;border-radius:3px;background:var(--surface-raised);border:1px solid var(--border);display:inline-flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:var(--text-secondary);flex-shrink:0}
.model-name{font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0}
.badge{font-size:10px;padding:1px 7px;border-radius:4px;font-weight:500;flex-shrink:0;letter-spacing:0.3px}
.badge-ultra{background:rgba(124,58,237,0.1);color:var(--tier-ultra)}
.badge-high{background:rgba(234,88,12,0.1);color:var(--tier-high)}
.badge-medium{background:rgba(37,99,235,0.1);color:var(--tier-medium)}
.badge-low{background:rgba(5,150,105,0.1);color:var(--tier-low)}
.model-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:3px}
.model-meta span{font-size:11px;color:var(--text-secondary)}
.model-meta .price-in{color:var(--green)}
.model-meta .price-out{color:var(--amber)}
.model-meta .meta-sep{color:var(--text-tertiary)}
.model-effort{font-size:11px;color:var(--text-tertiary);margin-top:2px}
.count{font-size:12px;color:var(--text-secondary);font-weight:400;margin-left:6px}

.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:500px){.settings-grid{grid-template-columns:1fr}}
.form-group label{display:block;font-size:12px;font-weight:500;margin-bottom:5px;color:var(--text-secondary)}
.form-group input,.form-group select{width:100%;padding:8px 12px;background:#f9f9f9;border:1px solid var(--border);border-radius:var(--radius-xs);color:var(--text);font-family:var(--font);font-size:13px;transition:border-color 200ms,box-shadow 200ms}
.form-group input:focus,.form-group select:focus{outline:none;border-color:#999;box-shadow:0 0 0 2px rgba(0,0,0,0.05)}
.form-group input::placeholder{color:var(--text-tertiary)}

.footer{display:flex;align-items:center;justify-content:space-between;padding:20px 0 0;margin-top:8px;border-top:1px solid var(--border)}
.footer-left{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-tertiary)}
.footer-left a{color:var(--text-secondary);text-decoration:none;transition:color 150ms}
.footer-left a:hover{color:var(--accent)}
.btn{padding:7px 16px;border-radius:var(--radius-xs);font-size:12px;font-weight:500;cursor:pointer;border:1px solid var(--border);background:#f9f9f9;color:var(--text-secondary);font-family:var(--font);transition:all 180ms ease}
.btn:hover{border-color:var(--border-hover);color:var(--text);background:var(--surface-raised)}

.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(30px);padding:8px 18px;border-radius:var(--radius-xs);font-size:13px;font-weight:500;opacity:0;transition:all 250ms ease;pointer-events:none;z-index:100;font-family:var(--font)}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
.toast--ok{background:rgba(5,150,105,0.08);border:1px solid rgba(5,150,105,0.2);color:var(--green)}
.toast--err{background:rgba(220,38,38,0.08);border:1px solid rgba(220,38,38,0.2);color:var(--red)}
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="header-row">
      <h1>Model Selector</h1>
      <div class="sync-indicator" id="syncDot" title="Live sync active"></div>
    </div>
    <p class="subtitle">Configure model routing and preferences &#183; auto-saved to config.yaml</p>
  </header>

  <div class="banner banner--warning" id="restartBanner">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    <div><strong>Model list changed.</strong> Restart Claude Code to make added or removed models available to the MCP server.</div>
  </div>

  <section class="section">
    <h2 class="section-title">Optimization Mode</h2>
    <div class="mode-grid" id="modeGrid"></div>
  </section>

  <section class="section">
    <h2 class="section-title">Router Mode</h2>
    <div class="router-options" id="routerOptions"></div>
  </section>

  <section class="section">
    <div class="models-header">
      <h2 class="section-title">Models <span class="count" id="modelCount"></span></h2>
      <div class="models-controls">
        <input type="text" id="modelSearch" class="search-input" placeholder="Search models...">
        <select id="modelSort" class="sort-select">
          <option value="name">Name</option>
          <option value="quality">Quality</option>
          <option value="cost">Cost</option>
          <option value="context">Context</option>
        </select>
      </div>
    </div>
    <div class="filter-bar" id="filterBar"></div>
    <div class="model-grid" id="modelGrid"></div>
  </section>

  <section class="section">
    <h2 class="section-title">Advanced Settings</h2>
    <div class="settings-grid">
      <div class="form-group">
        <label for="graphifyPath">Graphify Path</label>
        <input type="text" id="graphifyPath" placeholder="./graphify-out/graph.json">
      </div>
      <div class="form-group">
        <label for="bfsDepth">BFS Max Depth</label>
        <input type="number" id="bfsDepth" min="1" max="10" value="3">
      </div>
      <div class="form-group">
        <label for="maxBudget">Max Budget per Task ($)</label>
        <input type="number" id="maxBudget" step="0.01" min="0" placeholder="No limit">
      </div>
    </div>
  </section>

  <footer class="footer">
    <div class="footer-left">
      <span>Model Selector MCP</span>
      <span>&#183;</span>
      <span>Built by <a href="https://github.com/Linux5real" target="_blank" rel="noopener">Linux5real</a></span>
    </div>
    <button class="btn" onclick="resetDefaults()">Reset to Defaults</button>
  </footer>
</div>

<div class="toast" id="toast"></div>

<script>
// All data in this page comes from a trusted local models.json file
// served by our own Python backend. No user-supplied content is rendered.
var allModels = [];
var config = {};
var selectedModels = new Set();
var savedModels = new Set();
var activeFilter = 'all';
var searchQuery = '';
var currentSort = 'name';
var currentRouterMode = 'hybrid';
var lastMtime = 0;

var MODE_ICONS = {
  quality: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M2 9h20"/><path d="M12 22l3-13"/><path d="M12 22l-3-13"/></svg>',
  balanced: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="4" y1="8" x2="20" y2="8"/><line x1="4" y1="16" x2="20" y2="16"/><circle cx="9" cy="8" r="2.5"/><circle cx="15" cy="16" r="2.5"/></svg>',
  performance: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10"/></svg>',
  'token-saver': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5a2.5 2.5 0 00-5 0c0 2.5 5 3 5 5.5a2.5 2.5 0 01-5 0"/><line x1="12" y1="6.5" x2="12" y2="17.5"/></svg>'
};

var MODES = [
  {id:'quality', title:'Quality', desc:'Best model for every task. No compromises.'},
  {id:'balanced', title:'Balanced', desc:'Smart trade-off between cost and quality.'},
  {id:'performance', title:'Performance', desc:'Faster models with boosted effort levels.'},
  {id:'token-saver', title:'Token Saver', desc:'Maximum savings, minimum viable quality.'},
];

var ROUTER_MODES = [
  {id:'deterministic', title:'Deterministic', desc:'Pure local scoring. Fast, cheap, and consistent — no AI calls during routing.'},
  {id:'hybrid', title:'Hybrid', recommended:true, desc:'Local scoring first, AI review only for complex tasks or close-call decisions.'},
  {id:'ai-review', title:'AI Review', desc:'Always consult AI to rank model candidates. Best for calibration and evaluation.'},
];

var PROVIDER_ICONS = {
  anthropic:'anthropic', openai:null, google:'google', xai:'x',
  meta:'meta', alibaba:'alibabacloud', mistral:'mistralai', nvidia:'nvidia',
  cohere:null, deepseek:'deepseek', minimax:null, moonshot:null,
  xiaomi:'xiaomi', zai:null
};

var PROVIDER_NAMES = {
  anthropic:'Anthropic', openai:'OpenAI', google:'Google', xai:'xAI',
  meta:'Meta', alibaba:'Alibaba', mistral:'Mistral', nvidia:'NVIDIA',
  cohere:'Cohere', deepseek:'DeepSeek', minimax:'MiniMax', moonshot:'Moonshot',
  xiaomi:'Xiaomi', zai:'Zhipu AI'
};

function debounce(fn, ms) {
  var t;
  return function() {
    var a = arguments, s = this;
    clearTimeout(t);
    t = setTimeout(function() { fn.apply(s, a); }, ms);
  };
}

function formatCtx(n) {
  return n >= 1000000 ? (n / 1000000) + 'M' : Math.round(n / 1000) + 'k';
}

function createProviderIcon(provider) {
  var slug = PROVIDER_ICONS[provider];
  var initial = (provider || '?')[0].toUpperCase();
  var frag = document.createDocumentFragment();
  if (!slug) {
    var av = document.createElement('span');
    av.className = 'provider-avatar';
    av.textContent = initial;
    frag.appendChild(av);
    return frag;
  }
  var img = document.createElement('img');
  img.className = 'provider-icon';
  img.src = 'https://cdn.simpleicons.org/' + slug + '/52525b';
  img.width = 16;
  img.height = 16;
  img.alt = '';
  var fallback = document.createElement('span');
  fallback.className = 'provider-avatar';
  fallback.textContent = initial;
  fallback.style.display = 'none';
  img.onerror = function() {
    img.style.display = 'none';
    fallback.style.display = 'inline-flex';
  };
  frag.appendChild(img);
  frag.appendChild(fallback);
  return frag;
}

var autoSave = debounce(function() {
  var dot = document.getElementById('syncDot');
  dot.className = 'sync-indicator saving';
  var cfg = {
    available_models: Array.from(selectedModels),
    graphify_path: document.getElementById('graphifyPath').value || './graphify-out/graph.json',
    preferences: {
      optimize_for: (config.preferences && config.preferences.optimize_for) || 'balanced',
      router_mode: currentRouterMode,
      max_budget_per_task: parseFloat(document.getElementById('maxBudget').value) || null,
      bfs_max_depth: parseInt(document.getElementById('bfsDepth').value) || 3,
    }
  };
  fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(cfg),
  }).then(function(resp) {
    if (resp.ok) {
      config = cfg;
      savedModels = new Set(selectedModels);
      return fetch('/api/state').then(function(r) { return r.json(); }).then(function(st) {
        lastMtime = st.mtime || lastMtime;
        dot.className = 'sync-indicator';
        showToast('Saved', 'ok');
        checkRestartNeeded();
      });
    } else {
      dot.className = 'sync-indicator error';
      showToast('Save failed', 'err');
    }
  }).catch(function() {
    dot.className = 'sync-indicator error';
    showToast('Connection error', 'err');
  });
}, 600);

function init() {
  fetchState().then(function(data) {
    if (!data) return;
    allModels = data.models;
    config = data.config;
    lastMtime = data.mtime || 0;
    selectedModels = new Set(config.available_models || []);
    savedModels = new Set(selectedModels);
    currentRouterMode = (config.preferences && config.preferences.router_mode) || 'hybrid';
    populateForm();
    renderModes();
    setMode((config.preferences && config.preferences.optimize_for) || 'balanced', true);
    renderRouterModes();
    renderFilters();
    renderModels();
    bindInputs();
    startPolling();
  });
}

function fetchState() {
  return fetch('/api/state').then(function(r) { return r.ok ? r.json() : null; }).catch(function() { return null; });
}

function populateForm() {
  document.getElementById('graphifyPath').value = config.graphify_path || './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = (config.preferences && config.preferences.bfs_max_depth) || 3;
  if (config.preferences && config.preferences.max_budget_per_task) {
    document.getElementById('maxBudget').value = config.preferences.max_budget_per_task;
  }
}

function bindInputs() {
  ['graphifyPath', 'bfsDepth', 'maxBudget'].forEach(function(id) {
    document.getElementById(id).addEventListener('input', autoSave);
  });
  document.getElementById('modelSearch').addEventListener('input', debounce(function() {
    searchQuery = document.getElementById('modelSearch').value;
    renderModels();
  }, 200));
  document.getElementById('modelSort').addEventListener('change', function(e) {
    currentSort = e.target.value;
    renderModels();
  });
}

function startPolling() {
  setInterval(function() {
    fetchState().then(function(data) {
      if (!data) { document.getElementById('syncDot').className = 'sync-indicator error'; return; }
      if (data.mtime && data.mtime !== lastMtime) {
        lastMtime = data.mtime;
        config = data.config;
        savedModels = new Set(config.available_models || []);
        selectedModels = new Set(savedModels);
        currentRouterMode = (config.preferences && config.preferences.router_mode) || 'hybrid';
        setMode((config.preferences && config.preferences.optimize_for) || 'balanced', true);
        renderRouterModes();
        populateForm();
        renderModels();
        showToast('Reloaded from disk', 'ok');
      }
    });
  }, 5000);
}

function renderModes() {
  var grid = document.getElementById('modeGrid');
  grid.textContent = '';
  MODES.forEach(function(m) {
    var card = document.createElement('div');
    card.className = 'mode-card';
    card.dataset.mode = m.id;
    card.onclick = function() { setMode(m.id); };
    var iconDiv = document.createElement('div');
    iconDiv.className = 'mode-icon';
    // Trusted static SVG string from MODE_ICONS constant
    iconDiv.innerHTML = MODE_ICONS[m.id];
    var h3 = document.createElement('h3');
    h3.textContent = m.title;
    var p = document.createElement('p');
    p.textContent = m.desc;
    card.appendChild(iconDiv);
    card.appendChild(h3);
    card.appendChild(p);
    grid.appendChild(card);
  });
}

function setMode(mode, silent) {
  document.querySelectorAll('.mode-card').forEach(function(c) {
    c.classList.toggle('active', c.dataset.mode === mode);
  });
  config.preferences = config.preferences || {};
  config.preferences.optimize_for = mode;
  if (!silent) autoSave();
}

function renderRouterModes() {
  var container = document.getElementById('routerOptions');
  container.textContent = '';
  ROUTER_MODES.forEach(function(rm) {
    var opt = document.createElement('label');
    opt.className = 'router-option' + (currentRouterMode === rm.id ? ' active' : '');
    var radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'routerMode';
    radio.value = rm.id;
    radio.checked = currentRouterMode === rm.id;
    radio.addEventListener('change', function() {
      currentRouterMode = rm.id;
      document.querySelectorAll('.router-option').forEach(function(o) { o.classList.remove('active'); });
      opt.classList.add('active');
      autoSave();
    });
    var content = document.createElement('div');
    content.className = 'router-option-content';
    var titleSpan = document.createElement('span');
    titleSpan.className = 'router-option-title';
    titleSpan.textContent = rm.title;
    if (rm.recommended) {
      var tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = 'Recommended';
      titleSpan.appendChild(document.createTextNode(' '));
      titleSpan.appendChild(tag);
    }
    var descSpan = document.createElement('span');
    descSpan.className = 'router-option-desc';
    descSpan.textContent = rm.desc;
    content.appendChild(titleSpan);
    content.appendChild(descSpan);
    opt.appendChild(radio);
    opt.appendChild(content);
    container.appendChild(opt);
  });
}

function renderFilters() {
  var seen = {};
  var providers = [];
  allModels.forEach(function(m) {
    if (!seen[m.provider]) { seen[m.provider] = true; providers.push(m.provider); }
  });
  providers.sort();
  var bar = document.getElementById('filterBar');
  bar.textContent = '';
  var allBtn = document.createElement('button');
  allBtn.className = 'filter-chip active';
  allBtn.dataset.filter = 'all';
  allBtn.textContent = 'All';
  allBtn.onclick = function() { setFilter('all'); };
  bar.appendChild(allBtn);
  providers.forEach(function(p) {
    var chip = document.createElement('button');
    chip.className = 'filter-chip';
    chip.dataset.filter = p;
    chip.textContent = PROVIDER_NAMES[p] || p;
    chip.onclick = function() { setFilter(p); };
    bar.appendChild(chip);
  });
}

function setFilter(f) {
  activeFilter = f;
  document.querySelectorAll('.filter-chip').forEach(function(c) {
    c.classList.toggle('active', c.dataset.filter === f);
  });
  renderModels();
}

function sortModels(models) {
  return models.slice().sort(function(a, b) {
    switch (currentSort) {
      case 'quality': return b.quality_score - a.quality_score;
      case 'cost': return a.cost.input_per_1m - b.cost.input_per_1m;
      case 'context': return b.context_window - a.context_window;
      default: return a.name.localeCompare(b.name);
    }
  });
}

function renderModels() {
  var grid = document.getElementById('modelGrid');
  grid.textContent = '';
  var filtered = allModels;
  if (activeFilter !== 'all') {
    filtered = filtered.filter(function(m) { return m.provider === activeFilter; });
  }
  if (searchQuery) {
    var q = searchQuery.toLowerCase();
    filtered = filtered.filter(function(m) {
      return m.name.toLowerCase().indexOf(q) !== -1
        || m.provider.toLowerCase().indexOf(q) !== -1
        || m.id.toLowerCase().indexOf(q) !== -1;
    });
  }
  filtered = sortModels(filtered);

  filtered.forEach(function(m) {
    var card = document.createElement('div');
    card.className = 'model-card' + (selectedModels.has(m.id) ? ' selected' : '');
    card.onclick = function() { toggleModel(m.id); };

    var info = document.createElement('div');
    info.className = 'model-info';

    var nameRow = document.createElement('div');
    nameRow.className = 'model-name-row';
    nameRow.appendChild(createProviderIcon(m.provider));
    var nameSpan = document.createElement('span');
    nameSpan.className = 'model-name';
    nameSpan.textContent = m.name;
    nameRow.appendChild(nameSpan);
    var badge = document.createElement('span');
    badge.className = 'badge badge-' + m.tier;
    badge.textContent = m.tier;
    nameRow.appendChild(badge);

    var meta = document.createElement('div');
    meta.className = 'model-meta';
    var inPrice = m.cost.input_per_1m;
    var outPrice = m.cost.output_per_1m;
    if (inPrice === 0 && outPrice === 0) {
      var freeSpan = document.createElement('span');
      freeSpan.className = 'price-in';
      freeSpan.textContent = 'Free';
      meta.appendChild(freeSpan);
    } else {
      var inSpan = document.createElement('span');
      inSpan.className = 'price-in';
      inSpan.textContent = 'In $' + inPrice;
      meta.appendChild(inSpan);
      var sep1 = document.createElement('span');
      sep1.className = 'meta-sep';
      sep1.textContent = '·';
      meta.appendChild(sep1);
      var outSpan = document.createElement('span');
      outSpan.className = 'price-out';
      outSpan.textContent = 'Out $' + outPrice;
      meta.appendChild(outSpan);
    }
    var sep2 = document.createElement('span');
    sep2.className = 'meta-sep';
    sep2.textContent = '·';
    meta.appendChild(sep2);
    var ctxSpan = document.createElement('span');
    ctxSpan.textContent = formatCtx(m.context_window);
    meta.appendChild(ctxSpan);
    var sep3 = document.createElement('span');
    sep3.className = 'meta-sep';
    sep3.textContent = '·';
    meta.appendChild(sep3);
    var speedSpan = document.createElement('span');
    speedSpan.textContent = m.speed;
    meta.appendChild(speedSpan);

    info.appendChild(nameRow);
    info.appendChild(meta);

    if (m.effort_levels && m.effort_levels.length) {
      var effort = document.createElement('div');
      effort.className = 'model-effort';
      effort.textContent = 'Effort: ' + m.effort_levels.join(', ');
      info.appendChild(effort);
    }

    card.appendChild(info);
    grid.appendChild(card);
  });

  document.getElementById('modelCount').textContent = selectedModels.size + ' / ' + allModels.length;
}

function toggleModel(id) {
  if (selectedModels.has(id)) selectedModels.delete(id);
  else selectedModels.add(id);
  checkRestartNeeded();
  renderModels();
  autoSave();
}

function checkRestartNeeded() {
  var changed = false;
  selectedModels.forEach(function(id) { if (!savedModels.has(id)) changed = true; });
  if (!changed) savedModels.forEach(function(id) { if (!selectedModels.has(id)) changed = true; });
  document.getElementById('restartBanner').className = 'banner banner--warning' + (changed ? ' show' : '');
}

function resetDefaults() {
  selectedModels = new Set(['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5']);
  setMode('balanced');
  currentRouterMode = 'hybrid';
  renderRouterModes();
  document.getElementById('graphifyPath').value = './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = 3;
  document.getElementById('maxBudget').value = '';
  checkRestartNeeded();
  renderModels();
  autoSave();
}

function showToast(msg, type) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast toast--' + type + ' show';
  setTimeout(function() { t.className = 'toast'; }, 2000);
}

init();
</script>
</body>
</html>"""


class SetupHandler(BaseHTTPRequestHandler):
    def __init__(self, models, *args, **kwargs):
        self.all_models = models
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/state":
            cfg = _load_cfg()
            state = {
                "models": self.all_models,
                "config": cfg,
                "mtime": _config_mtime(),
            }
            self._json(200, state)
        elif self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                cfg = json.loads(body)
                _save_config(cfg)
                self._json(200, {"status": "ok"})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self.send_error(404)

    def _json(self, code, data):
        payload = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_setup(port: int = 6639):
    models = _load_models()
    handler = partial(SetupHandler, models)
    server = HTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}"
    open_browser = os.environ.get("MODEL_SELECTOR_OPEN_BROWSER", "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    print(f"Model Selector Settings: {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSettings server stopped.")
    finally:
        server.server_close()


def main():
    run_setup()


if __name__ == "__main__":
    main()
