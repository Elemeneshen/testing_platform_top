param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$CertificateFile
)

$ErrorActionPreference = 'Stop'
& certreq.exe -accept (Resolve-Path -LiteralPath $CertificateFile).Path
if ($LASTEXITCODE -ne 0) {
    throw "Certificate installation failed with exit code $LASTEXITCODE"
}
Write-Host 'Trusted-device certificate installed for the current Windows user.'
Write-Host 'Restart the browser before opening the site.'
