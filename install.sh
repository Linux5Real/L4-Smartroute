#!/usr/bin/env bash
set -euo pipefail

PACKAGE="l4-smartroute"
REPO="https://github.com/Linux5Real/L4-Smartroute"
REPO_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/l4-smartroute"
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"

info() { printf '\033[1;34m[info]\033[0m  %s\n' "$1"; }
ok() { printf '\033[1;32m[ok]\033[0m    %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m  %s\n' "$1"; }
fail() { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

is_windows_shell() {
  case "$(uname -s 2>/dev/null || true)" in
    MINGW*|MSYS*|CYGWIN*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

to_native_path() {
  local path="$1"
  if is_windows_shell && command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$path"
  else
    printf '%s\n' "$path"
  fi
}

resolve_executable() {
  local name="$1"
  local path

  path="$(command -v "$name" 2>/dev/null || true)"
  [ -n "$path" ] || fail "Could not find '$name' after installation."
  to_native_path "$path"
}

ensure_repo_checkout() {
  if ! command -v git >/dev/null 2>&1; then
    fail "git is required but not found. Install Git first."
  fi

  if [ -d "$REPO_DIR/.git" ]; then
    info "Updating source checkout at $REPO_DIR"
    local config_backup=""
    if [ -f "$REPO_DIR/config.yaml" ]; then
      config_backup="$(mktemp)"
      cp "$REPO_DIR/config.yaml" "$config_backup"
    fi

    git -C "$REPO_DIR" fetch --depth 1 origin main
    git -C "$REPO_DIR" reset --hard FETCH_HEAD

    if [ -n "$config_backup" ]; then
      mv "$config_backup" "$REPO_DIR/config.yaml"
    fi
  else
    info "Cloning source checkout to $REPO_DIR"
    mkdir -p "$(dirname "$REPO_DIR")"
    git clone --depth 1 "${REPO}.git" "$REPO_DIR"
  fi
}

install_package() {
  if command -v uv >/dev/null 2>&1; then
    info "Using uv"
    uv tool install --force --editable "$REPO_DIR"
    PM="uv"
  elif command -v pipx >/dev/null 2>&1; then
    info "Using pipx"
    pipx install --force --editable "$REPO_DIR"
    PM="pipx"
  else
    info "Using pip"
    pip install -e "$REPO_DIR"
    PM="pip"
  fi
}

install_claude_commands() {
  mkdir -p "$COMMANDS_DIR"
  cat > "$COMMANDS_DIR/smartroute.md" <<'EOF'
# Smartroute

Use the `l4-smartroute` MCP server to recommend the best model for the user's current task.

Rules:
- If the user is asking about the current task or general code changes, call `analyze_task`.
- If the task is already classified, prefer the recommended model and effort level.
- If the user asks for budget or speed tradeoffs, include the cheaper fallback.

EOF
}

register_with_claude() {
  local server_cmd
  server_cmd="$(resolve_executable l4-smartroute)"

  if command -v claude >/dev/null 2>&1; then
    info "Registering MCP server with Claude Code..."
    claude mcp add l4-smartroute -- "$server_cmd"
    ok "MCP server registered. Restart Claude Code to activate."
  else
    warn "Claude Code CLI not found. To register manually, run:"
    echo "  claude mcp add l4-smartroute -- \"$server_cmd\""
  fi
}

main() {
  info "Installing $PACKAGE..."

  command -v python3 >/dev/null 2>&1 || fail "python3 is required but not found. Install Python 3.11+ first."

  ensure_repo_checkout
  install_package
  ok "$PACKAGE installed via $PM"

  install_claude_commands
  register_with_claude

  echo ""
  ok "Installation complete!"
  info "Run 'l4-smartroute-setup' to open the configuration UI."
  info "Docs: $REPO"
}

main "$@"
