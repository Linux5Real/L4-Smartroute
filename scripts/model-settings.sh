#!/usr/bin/env bash
set -euo pipefail

HOST="127.0.0.1"
PORT="6639"
LOG_FILE="${TMPDIR:-/tmp}/model-selector-setup.log"

port_open() {
  (exec 3<>"/dev/tcp/${HOST}/${PORT}") >/dev/null 2>&1
}

print_ready_message() {
  cat <<'EOF'

Model Selector Settings is running at:

http://localhost:6639

Open that link in your browser to configure:
- Which models are available
- Optimization mode (Quality / Balanced / Performance / Token Saver)
- Graphify path and budget settings

After saving, changes to the optimization mode take effect immediately.
Changes to the model list require a Claude Code restart to apply.

To stop the settings server, run: `pkill -f model-selector-setup`
EOF
}

if port_open; then
  print_ready_message
  exit 0
fi

if ! command -v model-selector-setup >/dev/null 2>&1; then
  echo "model-selector-setup is not available on PATH." >&2
  exit 1
fi

MODEL_SELECTOR_OPEN_BROWSER=0 nohup model-selector-setup >"${LOG_FILE}" 2>&1 &

for _ in {1..20}; do
  if port_open; then
    print_ready_message
    exit 0
  fi
  sleep 0.25
done

echo "Model Selector Settings did not start on http://localhost:${PORT}." >&2
echo "Check ${LOG_FILE} for details." >&2
exit 1
