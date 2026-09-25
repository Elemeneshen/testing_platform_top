#!/usr/bin/env sh
set -eu

PROJECT_DIR="${PROJECT_DIR:-/opt/testing-platform}"
AUTHORITY_DIR="${AUTHORITY_DIR:-/opt/testing-platform-device-ca}"
ISSUED_DIR="$AUTHORITY_DIR/issued"
REVOKED_DIR="$AUTHORITY_DIR/revoked"
RUNTIME_DIR="$PROJECT_DIR/runtime/device-access"

safe_name() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g'
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this command as root." >&2
    exit 1
  fi
}

ensure_directories() {
  umask 077
  mkdir -p "$AUTHORITY_DIR" "$ISSUED_DIR" "$REVOKED_DIR" "$RUNTIME_DIR"
}

reload_caddy() {
  cd "$PROJECT_DIR"
  docker compose -f docker-compose.prod.yml exec -T caddy caddy reload --config /etc/caddy/Caddyfile
}
