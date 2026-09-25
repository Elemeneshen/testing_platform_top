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
  rm -f "$temporary" "$RUNTIME_DIR/trusted-clients.pem"
  echo "No active device certificates remain. Deactivate mTLS before reloading Caddy." >&2
  exit 2
fi

mv "$temporary" "$RUNTIME_DIR/trusted-clients.pem"
chmod 644 "$RUNTIME_DIR/trusted-clients.pem"
echo "Rebuilt trusted device bundle."
