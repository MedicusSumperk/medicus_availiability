param(
    [string]$PythonPath = "C:\python\python.exe",
    [string]$CloudflaredPath = "",
    [string]$TunnelName = "",
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [switch]$SkipApiStart
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalUrl = "http://${ApiHost}:${ApiPort}"

function Resolve-CloudflaredPath {
    param([string]$RequestedPath)

    if ($RequestedPath -and (Test-Path $RequestedPath)) {
        return (Resolve-Path $RequestedPath).Path
    }

    $Candidates = @(
        (Join-Path $ProjectRoot "cloudflared.exe"),
        (Join-Path $ProjectRoot "tools\cloudflared.exe"),
        "C:\tools\cloudflared\cloudflared.exe",
        "C:\cloudflared\cloudflared.exe"
    )

    foreach ($Candidate in $Candidates) {
        if (Test-Path $Candidate) {
            return (Resolve-Path $Candidate).Path
        }
    }

    $Command = Get-Command "cloudflared" -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    throw "cloudflared.exe was not found. Pass -CloudflaredPath `"C:\path\to\cloudflared.exe`" or place it in C:\tools\cloudflared\cloudflared.exe."
}

$ResolvedCloudflaredPath = Resolve-CloudflaredPath -RequestedPath $CloudflaredPath
Write-Host "Using cloudflared: $ResolvedCloudflaredPath"

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

if ($TunnelName) {
    Write-Host "Starting named Cloudflare tunnel: $TunnelName"
    & $ResolvedCloudflaredPath tunnel run $TunnelName
} else {
    Write-Host "Starting default named Cloudflare tunnel from cloudflared config."
    Write-Host "If multiple tunnels are configured, pass -TunnelName <name>."
    & $ResolvedCloudflaredPath tunnel run
}
