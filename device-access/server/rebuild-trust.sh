#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
ensure_directories

temporary="$RUNTIME_DIR/trusted-clients.pem.tmp"
: > "$temporary"
found=0
for certificate in "$ISSUED_DIR"/*.crt; do
  [ -f "$certificate" ] || continue
  cat "$certificate" >> "$temporary"
  found=1
done

if [ "$found" -eq 0 ]; then
  if [ ! -f "$RUNTIME_DIR/mtls.caddy" ]; then
    rm -f "$temporary" "$RUNTIME_DIR/trusted-clients.pem"
    echo "No active device certificates remain." >&2
    exit 2
  fi
  # Keep mTLS closed after the last device is revoked. This certificate's
  # private key is immediately destroyed, so nobody can authenticate with it.
  if [ ! -f "$AUTHORITY_DIR/deny-all.crt" ]; then
    deny_key=$(mktemp)
    openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 3650 \
      -subj '/CN=Revoked device sentinel' \
      -keyout "$deny_key" -out "$AUTHORITY_DIR/deny-all.crt" >/dev/null 2>&1
    rm -f "$deny_key"
    chmod 644 "$AUTHORITY_DIR/deny-all.crt"
  fi
  cat "$AUTHORITY_DIR/deny-all.crt" > "$temporary"
fi

mv "$temporary" "$RUNTIME_DIR/trusted-clients.pem"
chmod 644 "$RUNTIME_DIR/trusted-clients.pem"
echo "Rebuilt trusted device bundle."
