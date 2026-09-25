#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
ensure_directories
[ -s "$RUNTIME_DIR/trusted-clients.pem" ] || {
  echo "Enroll and install at least one device before activation." >&2
  exit 1
}

cat > "$RUNTIME_DIR/mtls.caddy" <<'EOF'
tls {
    client_auth {
        mode require_and_verify
        trust_pool file /etc/caddy/device-access/trusted-clients.pem
    }
}
EOF
chmod 644 "$RUNTIME_DIR/mtls.caddy"
reload_caddy
echo "Trusted-device enforcement is active."
