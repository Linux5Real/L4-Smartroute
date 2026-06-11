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
