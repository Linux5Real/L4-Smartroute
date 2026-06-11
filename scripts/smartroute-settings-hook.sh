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
