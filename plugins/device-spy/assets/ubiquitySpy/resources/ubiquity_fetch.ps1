# ubiquity_fetch.ps1 — env-driven, READ-ONLY inspector for Ubiquiti "System Manager" routers.
#
# Reads (environment only):
#   UBQ_IP    target router IP (e.g. 192.168.10.6)
#   UBQ_USER  admin username
#   UBQ_PW    admin password — SECRET. Used only as the JSON login body; never an argument, never disk.
#   UBQ_OUT   path to write the authenticated dashboard HTML (the captured config).
#
# Behavior: identify the device (landing-page <title>), log in (POST /login JSON), and save the
# AUTHENTICATED dashboard HTML (server-rendered — all interface/networking/VPN config is inline).
# It performs LOGIN + GET only; it never POSTs a configuration change.
#
# PowerShell-native (Invoke-RestMethod / Invoke-WebRequest -UseBasicParsing) with a TLS cert bypass,
# so a self-signed device cert + the JSON body + the cookie session are all handled cleanly.
#
# Output lines (for the caller to parse):
#   DEVICE_TITLE: …   LOGIN_OK | LOGIN_FAILED   AUTHENTICATED: True|False   SAVED_BYTES: …
$ErrorActionPreference = 'Stop'
$ip = $env:UBQ_IP; $user = $env:UBQ_USER; $out = $env:UBQ_OUT
if (-not $ip -or -not $user -or -not $env:UBQ_PW -or -not $out) {
    Write-Output 'ERROR: missing one of UBQ_IP / UBQ_USER / UBQ_PW / UBQ_OUT'; exit 1
}
$base = "https://$ip"

# Trust the device's self-signed cert (PS 5.1) + force TLS 1.2.
try {
    Add-Type -ErrorAction SilentlyContinue @"
using System.Net; using System.Security.Cryptography.X509Certificates;
public class UbqTrustAll : ICertificatePolicy { public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p){ return true; } }
"@
} catch {}
[System.Net.ServicePointManager]::CertificatePolicy = New-Object UbqTrustAll
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

# 1) Identify the device from the unauthenticated landing page.
try {
    $land = Invoke-WebRequest -Uri "$base/" -UseBasicParsing -TimeoutSec 10
    if ($land.Content -match '<title>([^<]*)</title>') { Write-Output ("DEVICE_TITLE: " + $Matches[1]) }
    else { Write-Output 'DEVICE_TITLE: (unknown)' }
} catch { Write-Output 'DEVICE_TITLE: (unreachable)' }

# 2) Log in. Body via ConvertTo-Json (escapes any special chars in the password). The password is
#    only ever the request body of this single call — never a command-line argument, never on disk.
$body = @{ username = $user; password = $env:UBQ_PW } | ConvertTo-Json -Compress
try {
    Invoke-RestMethod -Uri "$base/login" -Method Post -Body $body -ContentType 'application/json' `
        -SessionVariable sess -TimeoutSec 20 | Out-Null
} catch {
    Write-Output 'LOGIN_FAILED'; exit 2
}
Write-Output 'LOGIN_OK'

# 3) Fetch the authenticated dashboard (READ ONLY) and save it.
try {
    $dash = Invoke-WebRequest -Uri "$base/" -WebSession $sess -UseBasicParsing -TimeoutSec 30
    [System.IO.File]::WriteAllText($out, $dash.Content, (New-Object System.Text.UTF8Encoding($false)))
    $authed = $dash.Content -match 'pills-networking'
    Write-Output ("AUTHENTICATED: " + $authed)
    Write-Output ("SAVED_BYTES: " + (Get-Item $out).Length)
} catch {
    Write-Output ('SAVE_FAILED: ' + $_.Exception.Message); exit 3
}
