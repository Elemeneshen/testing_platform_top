#!/usr/bin/env sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this command as root." >&2
  exit 1
fi
if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
  echo "Usage: $0 ENROLLMENT_PUBLIC_KEY.pub" >&2
  exit 1
fi

public_key=$(cat "$1")
case "$public_key" in
  ssh-ed25519\ *|ssh-rsa\ *) ;;
  *) echo "Unsupported SSH public key." >&2; exit 1 ;;
esac

if ! id device-enroll >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin device-enroll
fi

install -o root -g root -m 0755 \
  /opt/testing-platform/device-access/server/device-enroll-command \
  /usr/local/sbin/device-enroll-command
printf '%s\n' \
  'device-enroll ALL=(root) NOPASSWD: /usr/local/sbin/device-enroll-command *' \
  > /etc/sudoers.d/device-enroll
chmod 0440 /etc/sudoers.d/device-enroll
visudo -cf /etc/sudoers.d/device-enroll >/dev/null

home=$(getent passwd device-enroll | cut -d: -f6)
install -d -o device-enroll -g device-enroll -m 0700 "$home/.ssh"
forced='command="/usr/bin/sudo -n /usr/local/sbin/device-enroll-command \"$SSH_ORIGINAL_COMMAND\"",restrict'
printf '%s %s\n' "$forced" "$public_key" > "$home/.ssh/authorized_keys"
chown device-enroll:device-enroll "$home/.ssh/authorized_keys"
chmod 0600 "$home/.ssh/authorized_keys"

echo "Restricted enrollment key installed."
