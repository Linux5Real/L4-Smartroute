# Model Selector MCP

Model Selector MCP waehlt fuer eine Aufgabe das passende Modell aus, statt pauschal das teuerste zu nehmen.
Es kombiniert Graphify-Blast-Radius, Task-Typ, Router-Modus, Modellkosten, Context Window und Modellfaehigkeiten zu einer Empfehlung, die fuer Coding-Agents praktisch nutzbar ist.

## What It Does

- Analysiert Prompts und Git-Diffs
- Nutzt Graphify, um Risiko und betroffene Bereiche im Projekt zu erkennen
- Bewertet aktive Modelle aus vielen Providern gegeneinander
- Unterstuetzt `deterministic`, `hybrid` und `ai-review` Routing
- Liefert Modell + Effort-Level + Budget-Alternative

Aktuell sind `54` aktive Modelle aus `14` Providern im Katalog, dazu weitere als `deprecated` markierte Vergleichsmodelle.

## Supported Platforms

Model Selector MCP ist ein Python-Projekt und laeuft dort, wo Python 3.11+ verfuegbar ist:

- Linux: empfohlen
- macOS: unterstuetzt
- Windows: unterstuetzt
- WSL2: sehr gute Wahl fuer Windows-Nutzer

Die Setup-UI laeuft lokal auf `http://localhost:6639`.

## Claude Code Shortcut

Wenn du Claude Code im Repository nutzt, starte die UI mit `/model-settings`.
Der Slash-Command wird per Hook abgefangen, startet `./scripts/model-settings.sh` direkt und kostet keinen extra Claude-Turn.

## Requirements

- Python `3.11` oder neuer
- `pip`
- Ein Graphify-Graph fuer dein Projekt, z. B. `graphify ./your-project`

Optional, aber praktisch:

- `git`
- Ein MCP-Client wie Claude Code oder Claude Desktop

## Quick Start

### Linux / macOS

```bash
git clone <YOUR-REPO-URL>
cd model-selector-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
model-selector-setup
```

### Windows PowerShell

```powershell
git clone <YOUR-REPO-URL>
cd model-selector-mcp
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
model-selector-setup
```

### Windows CMD

```cmd
git clone <YOUR-REPO-URL>
cd model-selector-mcp
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -U pip
pip install -e .
model-selector-setup
```

Danach oeffnet sich die lokale Setup-Oberflaeche auf:

```text
http://localhost:6639
```

## Installation Details

### 1. Install package

```bash
pip install -e .
```

Das installiert diese Commands:

- `model-selector-mcp`
- `model-selector-setup`

### 2. Configure your models

Starte die lokale UI:

```bash
model-selector-setup
```

Dort kannst du:

- aktive Modelle auswaehlen
- `quality`, `balanced`, `performance` oder `token-saver` setzen
- `deterministic`, `hybrid` oder `ai-review` als Router-Modus waehlen
- `graphify_path` setzen
- `bfs_max_depth` und optionales Budget konfigurieren

Die Einstellungen werden in [config.yaml](/home/mcp-project/config.yaml) gespeichert.

### 3. Add the MCP server to your client

Beispiel fuer `.mcp.json`:

```json
{
  "mcpServers": {
    "model-selector": {
      "command": "python3",
      "args": ["-m", "model_selector.server"],
      "cwd": "/absolute/path/to/model-selector-mcp"
    }
  }
}
```

Wenn `model-selector-mcp` auf deinem `PATH` liegt, geht auch:

```json
{
  "mcpServers": {
    "model-selector": {
      "command": "model-selector-mcp"
    }
  }
}
```

## Router Modes

### `deterministic`

Nur lokales Routing.
Schnell, billig, stabil.
Gut fuer einfache oder hochvolumige Tasks.

### `hybrid`

Empfohlener Standard.
Der Router sortiert lokal Top-Kandidaten vor und fordert nur bei schwierigen, knappen oder risikoreichen Aufgaben ein kompaktes AI-Review an.

### `ai-review`

Erzwingt immer einen AI-Rerank ueber die Top-Kandidaten.
Gut fuer Kalibrierung, Evaluation und kritische Entscheidungen.

## Optimization Modes

| Mode | Meaning | Good For |
|------|---------|----------|
| `quality` | bestes Modell fuer die Aufgabe | Architektur, High-Risk-Refactors |
| `balanced` | Fit pro Kosten | Standard fuer Alltag |
| `performance` | schnellere Modelle mit guter Task-Fit-Balance | Iteration, Tempo |
| `token-saver` | billigstes noch sinnvolles Modell | Docs, kleine Fixes, hohe Menge |

## Supported Model Families

Der Katalog enthaelt aktuell unter anderem:

- Anthropic: Claude Fable 5, Opus 4.8, 4.7, 4.6, 4.5, Sonnet 4.6, Haiku 4.5
- OpenAI: GPT-5.5, GPT-5.4 mini/nano, GPT-5.3 Codex, GPT-5.2 Varianten
- Google: Gemini 3.1 Pro Preview, 3.5 Flash, 3.1 Flash-Lite, 3 Flash, 2.5 Flash, 2.5 Pro
- xAI: Grok 4.3 low/medium/high/non-reasoning, Grok 4.1 Fast, Grok Build 0.1
- Alibaba: Qwen3.7 Max/Plus, Qwen3.6, Qwen3 Next, Qwen3 Coder, relevante Qwen Open-Weight-Modelle
- Z AI: GLM-5.1, GLM-5 Turbo, GLM-5, GLM-4.7 Varianten
- Moonshot: Kimi K2.6, K2.5, K2 Thinking
- MiniMax: M3, M2.7, M2.5, M2.1, M2
- Xiaomi: MiMo V2.5 Pro, V2.5, V2 Omni, V2 Flash, V2 Pro
- DeepSeek, Mistral, Meta, NVIDIA, Others (StepFun, KAT Coder, Hy3, Cohere)

Veraltete Modelle koennen weiter im Katalog stehen, werden aber mit `status: deprecated` markiert und im Router abgewertet.

## How Recommendation Works

```text
Prompt / Diff
-> Graphify blast radius
-> Task classification
-> Candidate scoring
-> Optional AI review
-> Final model + effort level
```

Der Router beruecksichtigt unter anderem:

- Task-Typen wie `backend_systems`, `frontend_ui`, `math_science`, `docs`, `debugging`, `multi_file_refactor`
- Blast Radius ueber Dateien, Communities, Tiefe und Zentralitaet
- Modellkosten
- Context Window
- Speed
- Capability-Scores
- Modellstatus wie `active`, `deprecated`, `preview`

## MCP Tools

### `analyze_task`

Analysiert einen Prompt und empfiehlt ein Modell:

```json
{
  "prompt": "refactor auth middleware and update tests"
}
```

### `analyze_diff`

Analysiert einen Git-Diff fuer Review oder Modellwahl:

```json
{
  "diff_target": "main"
}
```

### `list_models`

Listet die aktuell aktivierbaren Modelle mit Metadaten.

## Project Files

- [models.json](/home/mcp-project/models.json): Modellkatalog
- [config.yaml](/home/mcp-project/config.yaml): lokale Auswahl und Routing-Praeferenzen
- [.mcp.json](/home/mcp-project/.mcp.json): Beispiel fuer lokale MCP-Konfiguration
- [src/model_selector/server.py](/home/mcp-project/src/model_selector/server.py): MCP-Server
- [src/model_selector/recommender.py](/home/mcp-project/src/model_selector/recommender.py): Modell-Routing
- [src/model_selector/web_ui.py](/home/mcp-project/src/model_selector/web_ui.py): lokale Setup-UI

## Development

Tests ausfuehren:

```bash
pytest -q
```

Editable Install fuer lokale Entwicklung:

```bash
pip install -e .[dev]
```

## Troubleshooting

### `model-selector-setup` wird nicht gefunden

Stelle sicher, dass deine virtuelle Umgebung aktiv ist:

```bash
source .venv/bin/activate
```

Oder auf Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Graphify-Datei fehlt

Lege einen Graphify-Graph an und setze den Pfad in der UI oder in [config.yaml](/home/mcp-project/config.yaml):

```bash
graphify ./your-project
```

### Port `6639` ist schon belegt

Beende die lokale Setup-UI:

```bash
pkill -f model-selector-setup
```

Unter Windows den Prozess im Task Manager beenden oder die Shell neu starten.

### MCP client finds the server but gets no useful recommendations

Pruefe:

- ob Modelle in der UI ausgewaehlt sind
- ob `graphify_path` stimmt
- ob dein MCP-Client das richtige Arbeitsverzeichnis nutzt
- ob `router_mode` zu deinem Use-Case passt

## Data Sources

Die Modellmetadaten stammen primaer aus:

- Artificial Analysis: Preis, Speed, Context Window, Intelligence, Modellstatus
- offizielle Anbieter-Dokumentation, wenn noetig fuer einzelne Modelle oder Sonderfaelle

## License

MIT
