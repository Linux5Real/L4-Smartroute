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
<title>Model Selector MCP — Settings</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#e6edf3;
  --muted:#8b949e;--accent:#58a6ff;--accent2:#3fb950;
  --red:#f85149;--orange:#d29922;--purple:#bc8cff;--yellow:#e3b341
}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
.container{max-width:960px;margin:0 auto;padding:24px}
.header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:32px}
.header-left h1{font-size:24px;font-weight:600;margin-bottom:2px}
.header-left p{color:var(--muted);font-size:13px}
.sync-dot{width:8px;height:8px;border-radius:50%;background:var(--accent2);margin-top:8px;flex-shrink:0;transition:background .3s}
.sync-dot.syncing{background:var(--orange);animation:pulse .8s infinite}
.sync-dot.error{background:var(--red)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.restart-banner{background:#e3b34118;border:1px solid var(--yellow);border-radius:8px;padding:14px 18px;margin-bottom:20px;display:none;align-items:flex-start;gap:12px}
.restart-banner.show{display:flex}
.restart-banner-icon{font-size:18px;flex-shrink:0;margin-top:1px}
.restart-banner-text{font-size:13px;line-height:1.6}
.restart-banner-text strong{color:var(--yellow)}

.section{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:20px}
.section h2{font-size:15px;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.badge{font-size:11px;padding:2px 8px;border-radius:12px;font-weight:500}
.badge-ultra{background:#7c3aed33;color:var(--purple)}
.badge-high{background:#f8514933;color:var(--red)}
.badge-medium{background:#d2992233;color:var(--orange)}
.badge-low{background:#3fb95033;color:var(--accent2)}

.mode-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.mode-card{border:2px solid var(--border);border-radius:8px;padding:16px;cursor:pointer;transition:all .15s;text-align:center}
.mode-card:hover{border-color:var(--accent);background:#58a6ff08}
.mode-card.active{border-color:var(--accent);background:#58a6ff15}
.mode-card h3{font-size:14px;margin-bottom:4px}
.mode-card p{font-size:12px;color:var(--muted)}
.mode-icon{font-size:26px;margin-bottom:8px}

.model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;max-height:520px;overflow-y:auto;padding-right:4px}
.model-card{border:1px solid var(--border);border-radius:6px;padding:12px;cursor:pointer;transition:all .15s;display:flex;gap:10px;align-items:flex-start}
.model-card:hover{border-color:var(--muted)}
.model-card.selected{border-color:var(--accent);background:#58a6ff0a}
.model-card input[type=checkbox]{margin-top:3px;accent-color:var(--accent);flex-shrink:0}
.model-info{flex:1;min-width:0}
.model-name{font-size:13px;font-weight:600}
.model-provider{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.model-meta{display:flex;gap:8px;margin-top:4px;flex-wrap:wrap}
.model-meta span{font-size:11px;color:var(--muted)}
.model-cost{font-weight:600;color:var(--accent2) !important}

.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-group label{display:block;font-size:13px;font-weight:500;margin-bottom:6px;color:var(--muted)}
.form-group input{width:100%;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px}
.form-group input:focus{outline:none;border-color:var(--accent)}

.filter-bar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filter-chip{padding:4px 12px;border:1px solid var(--border);border-radius:16px;font-size:12px;cursor:pointer;background:transparent;color:var(--muted);transition:all .15s}
.filter-chip:hover{border-color:var(--muted);color:var(--text)}
.filter-chip.active{border-color:var(--accent);color:var(--accent);background:#58a6ff0a}

.count{font-size:12px;color:var(--muted);font-weight:400;margin-left:auto}
.actions{display:flex;gap:12px;justify-content:flex-end;margin-top:24px}
.btn{padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:1px solid var(--border);transition:all .15s}
.btn-primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn-primary:hover{opacity:.88}
.btn-secondary{background:transparent;color:var(--text)}
.btn-secondary:hover{background:#ffffff0a}

.toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-size:14px;font-weight:500;transform:translateY(80px);opacity:0;transition:all .3s;z-index:100}
.toast.show{transform:translateY(0);opacity:1}
.toast-ok{background:var(--accent2);color:#fff}
.toast-err{background:var(--red);color:#fff}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <h1>Model Selector MCP</h1>
      <p>Settings are saved to <code>config.yaml</code> and sync live to the MCP server.</p>
    </div>
    <div class="sync-dot" id="syncDot" title="Live sync active"></div>
  </div>

  <div class="restart-banner" id="restartBanner">
    <div class="restart-banner-icon">⚠</div>
    <div class="restart-banner-text">
      <strong>Model list changed.</strong> The optimization mode and settings apply immediately.
      To make added or removed models available to the MCP server,
      <strong>restart Claude Code</strong> once after saving.
    </div>
  </div>

  <div class="section">
    <h2>Optimization Mode</h2>
    <div class="mode-grid" id="modeGrid"></div>
  </div>

  <div class="section">
    <h2>Available Models <span class="count" id="modelCount"></span></h2>
    <div class="filter-bar" id="filterBar"></div>
    <div class="model-grid" id="modelGrid"></div>
  </div>

  <div class="section">
    <h2>Settings</h2>
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
        <label for="maxBudget">Max Budget per Task ($, optional)</label>
        <input type="number" id="maxBudget" step="0.01" min="0" placeholder="No limit">
      </div>
    </div>
  </div>

  <div class="actions">
    <button class="btn btn-secondary" onclick="resetDefaults()">Reset Defaults</button>
    <button class="btn btn-primary" onclick="saveConfig()">Save Configuration</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let allModels = [];
let config = {};
let selectedModels = new Set();
let savedModels = new Set();
let activeFilter = 'all';
let lastMtime = 0;
let pollingId = null;

const MODES = [
  {id:'quality',      icon:'★', title:'Quality',      desc:'Best model for every task. No compromises.'},
  {id:'balanced',     icon:'⚖', title:'Balanced',      desc:'Smart trade-off between cost and quality.'},
  {id:'performance',  icon:'⚡', title:'Performance',   desc:'DLSS-style: cheaper model, boosted effort level.'},
  {id:'token-saver',  icon:'💰', title:'Token Saver',   desc:'Maximum savings, minimum viable quality.'},
];

async function init() {
  const data = await fetchState();
  if (!data) return;
  allModels = data.models;
  config = data.config;
  lastMtime = data.mtime || 0;
  selectedModels = new Set(config.available_models || []);
  savedModels = new Set(selectedModels);
  populateForm();
  renderModes();
  setMode(config.preferences?.optimize_for || 'balanced');
  renderFilters();
  renderModels();
  startPolling();
}

async function fetchState() {
  try {
    const resp = await fetch('/api/state');
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

function populateForm() {
  document.getElementById('graphifyPath').value = config.graphify_path || './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = config.preferences?.bfs_max_depth || 3;
  if (config.preferences?.max_budget_per_task) {
    document.getElementById('maxBudget').value = config.preferences.max_budget_per_task;
  }
}

function startPolling() {
  pollingId = setInterval(async () => {
    const dot = document.getElementById('syncDot');
    dot.className = 'sync-dot syncing';
    const data = await fetchState();
    if (!data) { dot.className = 'sync-dot error'; return; }
    dot.className = 'sync-dot';
    if (data.mtime && data.mtime !== lastMtime) {
      lastMtime = data.mtime;
      config = data.config;
      savedModels = new Set(config.available_models || []);
      selectedModels = new Set(savedModels);
      setMode(config.preferences?.optimize_for || 'balanced');
      populateForm();
      renderModels();
      showToast('Settings reloaded from disk', 'ok');
    }
  }, 3000);
}

function renderModes() {
  const grid = document.getElementById('modeGrid');
  grid.textContent = '';
  MODES.forEach(m => {
    const card = document.createElement('div');
    card.className = 'mode-card';
    card.dataset.mode = m.id;
    card.onclick = () => setMode(m.id);
    const icon = document.createElement('div');
    icon.className = 'mode-icon';
    icon.textContent = m.icon;
    const h3 = document.createElement('h3');
    h3.textContent = m.title;
    const p = document.createElement('p');
    p.textContent = m.desc;
    card.append(icon, h3, p);
    grid.appendChild(card);
  });
}

function setMode(mode) {
  document.querySelectorAll('.mode-card').forEach(c =>
    c.classList.toggle('active', c.dataset.mode === mode)
  );
  config.preferences = config.preferences || {};
  config.preferences.optimize_for = mode;
}

function renderFilters() {
  const providers = [...new Set(allModels.map(m => m.provider))].sort();
  const bar = document.getElementById('filterBar');
  bar.textContent = '';
  const allChip = document.createElement('div');
  allChip.className = 'filter-chip active';
  allChip.dataset.filter = 'all';
  allChip.textContent = 'All';
  allChip.onclick = () => setFilter('all');
  bar.appendChild(allChip);
  providers.forEach(p => {
    const chip = document.createElement('div');
    chip.className = 'filter-chip';
    chip.dataset.filter = p;
    chip.textContent = p;
    chip.onclick = () => setFilter(p);
    bar.appendChild(chip);
  });
}

function setFilter(f) {
  activeFilter = f;
  document.querySelectorAll('.filter-chip').forEach(c =>
    c.classList.toggle('active', c.dataset.filter === f)
  );
  renderModels();
}

function createBadge(tier) {
  const span = document.createElement('span');
  span.className = 'badge badge-' + tier;
  span.textContent = tier;
  return span;
}

function renderModels() {
  const grid = document.getElementById('modelGrid');
  grid.textContent = '';
  const filtered = activeFilter === 'all'
    ? allModels
    : allModels.filter(m => m.provider === activeFilter);

  filtered.forEach(m => {
    const card = document.createElement('div');
    card.className = 'model-card' + (selectedModels.has(m.id) ? ' selected' : '');
    card.onclick = () => toggleModel(m.id);

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = selectedModels.has(m.id);
    cb.onclick = e => { e.stopPropagation(); toggleModel(m.id); };

    const info = document.createElement('div');
    info.className = 'model-info';

    const nameRow = document.createElement('div');
    nameRow.className = 'model-name';
    nameRow.appendChild(document.createTextNode(m.name + ' '));
    nameRow.appendChild(createBadge(m.tier));

    const prov = document.createElement('div');
    prov.className = 'model-provider';
    prov.textContent = m.provider;

    const meta = document.createElement('div');
    meta.className = 'model-meta';
    const totalCost = (m.cost.input_per_1m + m.cost.output_per_1m).toFixed(2);
    const ctxLabel = m.context_window >= 1048576 ? '1M ctx' : Math.round(m.context_window/1000)+'K ctx';
    [
      {text: '$'+totalCost+'/1M', extra: 'model-cost'},
      {text: ctxLabel},
      {text: 'Q:'+m.quality_score},
      {text: m.speed},
    ].forEach(({text, extra}) => {
      const s = document.createElement('span');
      s.textContent = text;
      if (extra) s.classList.add(extra);
      meta.appendChild(s);
    });

    const efforts = document.createElement('div');
    efforts.className = 'model-meta';
    const es = document.createElement('span');
    es.textContent = 'Effort: ' + (m.effort_levels ? m.effort_levels.join(', ') : 'none');
    efforts.appendChild(es);

    info.append(nameRow, prov, meta, efforts);
    card.append(cb, info);
    grid.appendChild(card);
  });

  document.getElementById('modelCount').textContent =
    selectedModels.size + ' of ' + allModels.length + ' selected';
}

function toggleModel(id) {
  if (selectedModels.has(id)) selectedModels.delete(id);
  else selectedModels.add(id);
  checkRestartNeeded();
  renderModels();
}

function checkRestartNeeded() {
  const changed = [...selectedModels].some(id => !savedModels.has(id))
    || [...savedModels].some(id => !selectedModels.has(id));
  document.getElementById('restartBanner').className =
    'restart-banner' + (changed ? ' show' : '');
}

async function saveConfig() {
  const cfg = {
    available_models: [...selectedModels],
    graphify_path: document.getElementById('graphifyPath').value,
    preferences: {
      optimize_for: config.preferences?.optimize_for || 'balanced',
      max_budget_per_task: parseFloat(document.getElementById('maxBudget').value) || null,
      bfs_max_depth: parseInt(document.getElementById('bfsDepth').value) || 3,
    }
  };
  const resp = await fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(cfg),
  });
  if (resp.ok) {
    config = cfg;
    savedModels = new Set(selectedModels);
    lastMtime = (await (await fetch('/api/state')).json()).mtime || lastMtime;
    showToast('Configuration saved!', 'ok');
    checkRestartNeeded();
  } else {
    showToast('Error saving — check config.yaml permissions', 'err');
  }
}

function resetDefaults() {
  selectedModels = new Set(['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5']);
  setMode('balanced');
  document.getElementById('graphifyPath').value = './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = 3;
  document.getElementById('maxBudget').value = '';
  checkRestartNeeded();
  renderModels();
}

function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast toast-' + type + ' show';
  setTimeout(() => t.className = 'toast toast-' + type, 2500);
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
