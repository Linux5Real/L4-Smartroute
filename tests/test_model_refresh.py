import json
import os
from pathlib import Path

from l4_smartroute.config import load_latest_model_library


def test_load_latest_model_library_refreshes_repo_checkout(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    models_path = repo / "models.json"
    models_path.write_text(json.dumps({"models": [{"id": "old-model", "cost": "$0.01"}]}))

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_path = bin_dir / "git"
    git_path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

if [ "$1" = "-C" ] && [ "$3" = "pull" ]; then
  cat > "$2/models.json" <<'JSON'
{"models":[{"id":"new-model","cost":"$0.02"}]}
JSON
fi
"""
    )
    git_path.chmod(0o755)

    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

    models = load_latest_model_library(models_path)

    assert [m["id"] for m in models] == ["new-model"]
