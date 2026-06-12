#!/usr/bin/env bash
set -euo pipefail

PACKAGE="l4-smartroute"
REPO="https://github.com/Linux5Real/L4-Smartroute"
REPO_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/l4-smartroute"

info()  { printf '\033[1;34m[info]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[ok]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[warn]\033[0m  %s\n' "$1"; }
fail()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

info "Installing $PACKAGE..."

# --- check python3 ---
command -v python3 >/dev/null 2>&1 || fail "python3 is required but not found. Install Python 3.11+ first."

# --- fetch source checkout ---
if command -v git >/dev/null 2>&1; then
  if [ -d "$REPO_DIR/.git" ]; then
    info "Updating source checkout at $REPO_DIR"
    git -C "$REPO_DIR" pull --ff-only
  else
    info "Cloning source checkout to $REPO_DIR"
    mkdir -p "$(dirname "$REPO_DIR")"
    git clone --depth 1 "$REPO.git" "$REPO_DIR"
  fi
else
  fail "git is required but not found. Install Git first."
fi

# --- detect package manager ---
if command -v uv >/dev/null 2>&1; then
  PM="uv"
  info "Using uv"
  uv tool install --force --editable "$REPO_DIR"
elif command -v pipx >/dev/null 2>&1; then
  PM="pipx"
  info "Using pipx"
  pipx install --force --editable "$REPO_DIR"
else
  PM="pip"
  info "Using pip"
  pip install -e "$REPO_DIR"
fi

ok "$PACKAGE installed via $PM"

# --- register with Claude Code ---
if command -v claude >/dev/null 2>&1; then
  info "Registering MCP server with Claude Code..."
  claude mcp add l4-smartroute -- l4-smartroute
  ok "MCP server registered. Restart Claude Code to activate."
else
  warn "Claude Code CLI not found. To register manually, run:"
  echo "  claude mcp add l4-smartroute -- l4-smartroute"
fi

echo ""
ok "Installation complete!"
info "Run 'l4-smartroute-setup' to open the configuration UI."
info "Docs: $REPO"
