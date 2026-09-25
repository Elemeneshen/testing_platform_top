#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/common.sh"

require_root
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 DEVICE_NAME CSR_FILE" >&2
  exit 1
fi

device_name=$(safe_name "$1")
csr_file=$2
[ -n "$device_name" ] || { echo "Invalid device name." >&2; exit 1; }
[ -f "$csr_file" ] || { echo "CSR file not found: $csr_file" >&2; exit 1; }

ensure_directories
if [ ! -f "$AUTHORITY_DIR/ca.key" ]; then
  "$(dirname "$0")/init-authority.sh"
fi
if [ -e "$ISSUED_DIR/$device_name.crt" ]; then
  echo "Device already exists: $device_name" >&2
  exit 1
fi

openssl req -in "$csr_file" -noout -verify
extensions=$(mktemp)
trap 'rm -f "$extensions"' EXIT
printf '%s\n' \
  'basicConstraints=critical,CA:FALSE' \
  'keyUsage=critical,digitalSignature,keyEncipherment' \
  'extendedKeyUsage=critical,clientAuth' \
  "subjectAltName=DNS:$device_name" > "$extensions"

openssl x509 -req -sha256 -days 825 \
  -in "$csr_file" \
  -CA "$AUTHORITY_DIR/ca.crt" \
  -CAkey "$AUTHORITY_DIR/ca.key" \
  -CAcreateserial \
  -extfile "$extensions" \
  -out "$ISSUED_DIR/$device_name.crt"
chmod 644 "$ISSUED_DIR/$device_name.crt"
"$(dirname "$0")/rebuild-trust.sh"
openssl x509 -in "$ISSUED_DIR/$device_name.crt" -outform DER -out "$ISSUED_DIR/$device_name.cer"
chmod 644 "$ISSUED_DIR/$device_name.cer"

echo "Enrolled: $device_name"
echo "Return this file to the same PC: $ISSUED_DIR/$device_name.cer"
