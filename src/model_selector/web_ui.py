import json
import webbrowser
import threading
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from model_selector.config import load_config, load_model_library

SERVER_DIR = Path(__file__).parent.parent.parent
DEFAULT_CONFIG = SERVER_DIR / "config.yaml"
DEFAULT_MODELS = SERVER_DIR / "models.json"


def _load_state():
    models = load_model_library(DEFAULT_MODELS)
    try:
        cfg = load_config(DEFAULT_CONFIG)
    except FileNotFoundError:
        cfg = {
            "available_models": [],
            "graphify_path": "./graphify-out/graph.json",
            "preferences": {
                "optimize_for": "balanced",
                "max_budget_per_task": None,
                "bfs_max_depth": 3,
            },
        }
    return models, cfg


def _save_config(cfg: dict):
    import yaml
    with open(DEFAULT_CONFIG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Model Selector MCP — Setup</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;--accent2:#3fb950;--red:#f85149;--orange:#d29922;--purple:#bc8cff}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
.container{max-width:960px;margin:0 auto;padding:24px}
h1{font-size:24px;font-weight:600;margin-bottom:4px}
.subtitle{color:var(--muted);font-size:14px;margin-bottom:32px}
.section{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:20px}
.section h2{font-size:16px;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.badge{font-size:11px;padding:2px 8px;border-radius:12px;font-weight:500}
.badge-ultra{background:#7c3aed33;color:var(--purple)}
.badge-high{background:#f8514933;color:var(--red)}
.badge-medium{background:#d2992233;color:var(--orange)}
.badge-low{background:#3fb95033;color:var(--accent2)}

.mode-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.mode-card{border:2px solid var(--border);border-radius:8px;padding:16px;cursor:pointer;transition:all .15s;text-align:center}
.mode-card:hover{border-color:var(--accent);background:#58a6ff0a}
.mode-card.active{border-color:var(--accent);background:#58a6ff15}
.mode-card h3{font-size:14px;margin-bottom:4px}
.mode-card p{font-size:12px;color:var(--muted)}
.mode-card .icon{font-size:28px;margin-bottom:8px}

.model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;max-height:520px;overflow-y:auto;padding-right:4px}
.model-card{border:1px solid var(--border);border-radius:6px;padding:12px;cursor:pointer;transition:all .15s;display:flex;gap:10px;align-items:flex-start}
.model-card:hover{border-color:var(--muted)}
.model-card.selected{border-color:var(--accent);background:#58a6ff0a}
.model-card input[type=checkbox]{margin-top:3px;accent-color:var(--accent)}
.model-info{flex:1;min-width:0}
.model-name{font-size:13px;font-weight:600}
.model-provider{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.model-meta{display:flex;gap:8px;margin-top:4px;flex-wrap:wrap}
.model-meta span{font-size:11px;color:var(--muted)}
.model-cost{font-weight:600;color:var(--accent2)}

.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-group label{display:block;font-size:13px;font-weight:500;margin-bottom:6px}
.form-group input,.form-group select{width:100%;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px}
.form-group input:focus,.form-group select:focus{outline:none;border-color:var(--accent)}

.actions{display:flex;gap:12px;justify-content:flex-end;margin-top:24px}
.btn{padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:1px solid var(--border);transition:all .15s}
.btn-primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn-primary:hover{opacity:.9}
.btn-secondary{background:transparent;color:var(--text)}
.btn-secondary:hover{background:var(--surface)}

.toast{position:fixed;bottom:24px;right:24px;background:var(--accent2);color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;transform:translateY(80px);opacity:0;transition:all .3s}
.toast.show{transform:translateY(0);opacity:1}

.filter-bar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filter-chip{padding:4px 12px;border:1px solid var(--border);border-radius:16px;font-size:12px;cursor:pointer;background:transparent;color:var(--muted);transition:all .15s}
.filter-chip:hover{border-color:var(--muted)}
.filter-chip.active{border-color:var(--accent);color:var(--accent);background:#58a6ff0a}

.count{font-size:12px;color:var(--muted);font-weight:400;margin-left:auto}
</style>
</head>
<body>
<div class="container">
  <h1>Model Selector MCP</h1>
  <p class="subtitle">Configure your AI model preferences. Changes are saved to config.yaml.</p>

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
        <label for="maxBudget">Max Budget per Task ($)</label>
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
const ESC = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
function esc(s){return String(s).replace(/[&<>"']/g,c=>ESC[c])}

let allModels = [];
let config = {};
let selectedModels = new Set();
let activeFilter = 'all';

const MODES = [
  {id:'quality',  icon:'★', title:'Quality',     desc:'Best model for every task. No compromises.'},
  {id:'balanced', icon:'⚖', title:'Balanced',     desc:'Smart trade-off between cost and quality.'},
  {id:'performance', icon:'⚡', title:'Performance', desc:'DLSS-style: cheaper model, boosted effort.'},
  {id:'token-saver', icon:'💰', title:'Token Saver', desc:'Maximum savings, minimum viable quality.'},
];

async function init() {
  const resp = await fetch('/api/state');
  const data = await resp.json();
  allModels = data.models;
  config = data.config;
  selectedModels = new Set(config.available_models || []);
  renderModes();
  setMode(config.preferences?.optimize_for || 'balanced');
  document.getElementById('graphifyPath').value = config.graphify_path || './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = config.preferences?.bfs_max_depth || 3;
  if (config.preferences?.max_budget_per_task) {
    document.getElementById('maxBudget').value = config.preferences.max_budget_per_task;
  }
  renderFilters();
  renderModels();
}

function renderModes() {
  const grid = document.getElementById('modeGrid');
  grid.textContent = '';
  MODES.forEach(m => {
    const card = document.createElement('div');
    card.className = 'mode-card';
    card.dataset.mode = m.id;
    card.onclick = () => setMode(m.id);
    const iconEl = document.createElement('div');
    iconEl.className = 'icon';
    iconEl.textContent = m.icon;
    const h3 = document.createElement('h3');
    h3.textContent = m.title;
    const p = document.createElement('p');
    p.textContent = m.desc;
    card.appendChild(iconEl);
    card.appendChild(h3);
    card.appendChild(p);
    grid.appendChild(card);
  });
}

function setMode(mode) {
  document.querySelectorAll('.mode-card').forEach(c => {
    c.classList.toggle('active', c.dataset.mode === mode);
  });
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
  document.querySelectorAll('.filter-chip').forEach(c => {
    c.classList.toggle('active', c.dataset.filter === f);
  });
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
  const filtered = activeFilter === 'all' ? allModels : allModels.filter(m => m.provider === activeFilter);

  filtered.forEach(m => {
    const card = document.createElement('div');
    card.className = 'model-card' + (selectedModels.has(m.id) ? ' selected' : '');
    card.onclick = () => { toggleModel(m.id); };

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = selectedModels.has(m.id);
    cb.onclick = (e) => { e.stopPropagation(); toggleModel(m.id); };

    const info = document.createElement('div');
    info.className = 'model-info';

    const nameRow = document.createElement('div');
    nameRow.className = 'model-name';
    nameRow.appendChild(document.createTextNode(m.name + ' '));
    nameRow.appendChild(createBadge(m.tier));

    const provRow = document.createElement('div');
    provRow.className = 'model-provider';
    provRow.textContent = m.provider;

    const metaRow = document.createElement('div');
    metaRow.className = 'model-meta';
    const totalCost = (m.cost.input_per_1m + m.cost.output_per_1m).toFixed(2);
    const ctxLabel = m.context_window >= 1048576 ? '1M ctx' : Math.round(m.context_window/1000)+'K ctx';
    const efforts = m.effort_levels ? m.effort_levels.join(', ') : 'none';
    [
      {cls: 'model-cost', text: '$'+totalCost+'/1M'},
      {cls: '', text: ctxLabel},
      {cls: '', text: 'Q:'+m.quality_score},
      {cls: '', text: m.speed},
    ].forEach(item => {
      const s = document.createElement('span');
      s.textContent = item.text;
      if(item.cls) s.className = item.cls;
      metaRow.appendChild(s);
    });

    const effortRow = document.createElement('div');
    effortRow.className = 'model-meta';
    const effortSpan = document.createElement('span');
    effortSpan.textContent = 'Effort: ' + efforts;
    effortRow.appendChild(effortSpan);

    info.appendChild(nameRow);
    info.appendChild(provRow);
    info.appendChild(metaRow);
    info.appendChild(effortRow);

    card.appendChild(cb);
    card.appendChild(info);
    grid.appendChild(card);
  });

  document.getElementById('modelCount').textContent =
    selectedModels.size + ' of ' + allModels.length + ' selected';
}

function toggleModel(id) {
  if (selectedModels.has(id)) {
    selectedModels.delete(id);
  } else {
    selectedModels.add(id);
  }
  renderModels();
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
    showToast('Configuration saved!');
    config = cfg;
  } else {
    showToast('Error saving configuration');
  }
}

function resetDefaults() {
  selectedModels = new Set(['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5']);
  setMode('balanced');
  document.getElementById('graphifyPath').value = './graphify-out/graph.json';
  document.getElementById('bfsDepth').value = 3;
  document.getElementById('maxBudget').value = '';
  renderModels();
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

init();
</script>
</body>
</html>"""


class SetupHandler(BaseHTTPRequestHandler):
    def __init__(self, models, cfg, *args, **kwargs):
        self.all_models = models
        self.current_config = cfg
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/state":
            state = {"models": self.all_models, "config": self.current_config}
            self._json_response(200, state)
        elif self.path == "/" or self.path == "/index.html":
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
                self.current_config.update(cfg)
                self._json_response(200, {"status": "ok"})
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            self.send_error(404)

    def _json_response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def run_setup(port: int = 6639):
    models, cfg = _load_state()
    handler = partial(SetupHandler, models, cfg)
    server = HTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}"
    print(f"Model Selector Setup running at {url}")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSetup server stopped.")
    finally:
        server.server_close()


def main():
    run_setup()


if __name__ == "__main__":
    main()
