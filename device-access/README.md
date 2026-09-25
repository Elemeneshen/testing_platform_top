# Trusted device access

The production edge can require a client certificate whose private key is
created inside a Windows TPM and marked non-exportable.

## Enrollment

1. On the trusted Windows PC, run `windows/New-TrustedDeviceRequest.ps1`.
2. Copy the generated `.csr` file to the server.
3. On the server run `server/enroll-csr.sh DEVICE_NAME CSR_FILE`.
4. Copy the resulting `.cer` file back to that same PC.
5. On the PC run `windows/Install-TrustedDeviceCertificate.ps1 CERT_FILE`.
6. Run `server/rebuild-trust.sh` to publish the CA and active-device list.
7. Run `server/probe.sh`. Confirm the trusted browser offers its certificate and
   the site still opens. Untrusted devices remain allowed in this mode.
8. Only after the probe succeeds, run `server/activate.sh` to require a trusted
   certificate for every connection.

The server stores its private device CA outside the repository in
`/opt/testing-platform-device-ca`. Never copy or commit that directory.

## Revocation

Run `server/revoke-device.sh DEVICE_NAME`. The exact leaf certificate is
removed from Caddy's trust bundle and Caddy is reloaded. Other devices stay
authorized.
