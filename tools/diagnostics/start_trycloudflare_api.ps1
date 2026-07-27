param(
    [string]$PythonPath = "C:\python\python.exe",
    [string]$CloudflaredPath = "",
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [switch]$SkipApiStart
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalUrl = "http://${ApiHost}:${ApiPort}"
$OutputDir = Join-Path $ProjectRoot "data\api"
$UrlFile = Join-Path $OutputDir "trycloudflare_url.txt"
$ApiStdoutLog = Join-Path $OutputDir "api_server_stdout.log"
$ApiStderrLog = Join-Path $OutputDir "api_server_stderr.log"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

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

function Test-ApiHealth {
    try {
        $Client = New-Object System.Net.WebClient
        $Client.DownloadString("$LocalUrl/health") | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-ApiHealth {
    param([int]$TimeoutSeconds = 20)

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (Test-ApiHealth) {
            Write-Host "Local Medicus API health check OK: $LocalUrl/health"
            return
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "Local Medicus API did not become healthy within $TimeoutSeconds seconds."
    Write-Host "API stdout log: $ApiStdoutLog"
    Write-Host "API stderr log: $ApiStderrLog"
    if (Test-Path $ApiStderrLog) {
        Write-Host ""
        Write-Host "Last API stderr lines:"
        Get-Content $ApiStderrLog -Tail 30 | ForEach-Object { Write-Host $_ }
    }
    throw "Local Medicus API health check failed."
}

if (-not $SkipApiStart) {
    Write-Host "Starting local Medicus API on $LocalUrl ..."

    if (Test-ApiHealth) {
        Write-Host "Local Medicus API is already running."
    } else {
        if (Test-Path $ApiStdoutLog) { Clear-Content $ApiStdoutLog }
        if (Test-Path $ApiStderrLog) { Clear-Content $ApiStderrLog }

        $ApiProcess = Start-Process `
        -FilePath $PythonPath `
        -ArgumentList @("scripts\api_server.py") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $ApiStdoutLog `
        -RedirectStandardError $ApiStderrLog `
        -PassThru

        Write-Host "Started API process PID: $($ApiProcess.Id)"
        Wait-ApiHealth -TimeoutSeconds 20
    }
} else {
    Wait-ApiHealth -TimeoutSeconds 5
}

Write-Host "Starting trycloudflare tunnel to $LocalUrl ..."
Write-Host "Waiting for public URL..."

$CloudflaredCommand = "`"$ResolvedCloudflaredPath`" tunnel --url `"$LocalUrl`" 2>&1"
& cmd.exe /c $CloudflaredCommand | ForEach-Object {
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
