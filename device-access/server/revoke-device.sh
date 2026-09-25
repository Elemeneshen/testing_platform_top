#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 DEVICE_NAME" >&2
  exit 1
fi

device_name=$(safe_name "$1")
certificate="$ISSUED_DIR/$device_name.crt"
[ -f "$certificate" ] || { echo "Unknown device: $device_name" >&2; exit 1; }
ensure_directories
mv "$certificate" "$REVOKED_DIR/$device_name.crt"
rm -f "$ISSUED_DIR/$device_name.cer"

"$(dirname "$0")/rebuild-trust.sh"
reload_caddy
echo "Revoked: $device_name"
