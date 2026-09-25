param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$DeviceName,

    [string]$OutputDirectory = (Join-Path $env:USERPROFILE 'Desktop')
)

$ErrorActionPreference = 'Stop'
$provider = 'Microsoft Platform Crypto Provider'
if (-not (Get-Tpm).TpmPresent) {
    throw 'TPM is not available on this computer.'
}
if (-not (Get-Tpm).TpmReady) {
    throw 'TPM is present but not ready. Initialize it in Windows Security first.'
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$infPath = Join-Path $env:TEMP ("trusted-device-{0}.inf" -f [guid]::NewGuid().ToString('N'))
$csrPath = Join-Path $OutputDirectory ("{0}.csr" -f $DeviceName.ToLowerInvariant())

$inf = @"
[Version]
Signature=`"`$Windows NT`$`"

[NewRequest]
Subject = `"CN=$DeviceName`"
KeyAlgorithm = RSA
KeyLength = 2048
HashAlgorithm = SHA256
KeySpec = 1
KeyUsage = 0xA0
MachineKeySet = FALSE
Exportable = FALSE
ProviderName = `"$provider`"
RequestType = PKCS10
SMIME = FALSE

[Extensions]
2.5.29.37 = `"{text}`"
_continue_ = `"1.3.6.1.5.5.7.3.2`"
"@

try {
    Set-Content -LiteralPath $infPath -Value $inf -Encoding ascii
    & certreq.exe -new $infPath $csrPath
    if ($LASTEXITCODE -ne 0) { throw "certreq failed with exit code $LASTEXITCODE" }
    Write-Host "TPM-backed request created: $csrPath"
    Write-Host 'Send only the .csr file to the server administrator.'
} finally {
    Remove-Item -LiteralPath $infPath -Force -ErrorAction SilentlyContinue
}
