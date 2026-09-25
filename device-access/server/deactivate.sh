#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
rm -f "$RUNTIME_DIR/mtls.caddy"
reload_caddy
echo "Trusted-device enforcement is inactive."
