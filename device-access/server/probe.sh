#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
ensure_directories
[ -s "$RUNTIME_DIR/trusted-clients.pem" ] || {
  echo "Enroll at least one device and run rebuild-trust.sh first." >&2
  exit 1
}
[ -s "$RUNTIME_DIR/device-ca.crt" ] || {
  echo "Device CA is missing from the runtime trust directory. Run rebuild-trust.sh first." >&2
  exit 1
}

cat > "$RUNTIME_DIR/mtls.caddy" <<'EOF'
tls {
    client_auth {
        mode verify_if_given
        trust_pool file /etc/caddy/device-access/device-ca.crt
        verifier leaf {
            file /etc/caddy/device-access/trusted-clients.pem
        }
    }
}
EOF
chmod 644 "$RUNTIME_DIR/mtls.caddy"
reload_caddy
echo "Trusted-device probe mode is active; clients without certificates remain allowed."
