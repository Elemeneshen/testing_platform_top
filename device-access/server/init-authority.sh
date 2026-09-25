#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
ensure_directories

if [ -f "$AUTHORITY_DIR/ca.key" ] || [ -f "$AUTHORITY_DIR/ca.crt" ]; then
  echo "Device authority already exists at $AUTHORITY_DIR"
  exit 0
fi

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$AUTHORITY_DIR/ca.key"
openssl req -x509 -new -sha256 -days 3650 \
  -key "$AUTHORITY_DIR/ca.key" \
  -subj "/CN=Siberian Livecoding Device Authority" \
  -out "$AUTHORITY_DIR/ca.crt"
chmod 600 "$AUTHORITY_DIR/ca.key"
chmod 644 "$AUTHORITY_DIR/ca.crt"
echo "Created device authority at $AUTHORITY_DIR"
