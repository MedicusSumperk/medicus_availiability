param(
    [string]$PythonPath = "C:\python\python.exe",
    [string]$CloudflaredPath = "cloudflared",
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [switch]$SkipApiStart
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalUrl = "http://${ApiHost}:${ApiPort}"
$OutputDir = Join-Path $ProjectRoot "data\api"
$UrlFile = Join-Path $OutputDir "trycloudflare_url.txt"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if (-not $SkipApiStart) {
    Write-Host "Starting local Medicus API on $LocalUrl ..."
    Start-Process `
        -FilePath $PythonPath `
        -ArgumentList @("scripts\api_server.py") `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -PassThru | Out-Null
    Start-Sleep -Seconds 3
}

Write-Host "Starting trycloudflare tunnel to $LocalUrl ..."
Write-Host "Waiting for public URL..."

& $CloudflaredPath tunnel --url $LocalUrl 2>&1 | ForEach-Object {
    $Line = $_.ToString()
    Write-Host $Line

    if ($Line -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
        $BaseUrl = $Matches[0]
        Set-Content -Path $UrlFile -Value $BaseUrl -Encoding UTF8

        Write-Host ""
        Write-Host "trycloudflare base URL:"
        Write-Host $BaseUrl
        Write-Host ""
        Write-Host "Webhook endpoints:"
        Write-Host "$BaseUrl/doctor-availability"
        Write-Host "$BaseUrl/patient-lookup"
        Write-Host "$BaseUrl/book-appointment"
        Write-Host ""
        Write-Host "Saved base URL to: $UrlFile"
    }
}
