[CmdletBinding()]
param([string]$PythonPath = 'C:\python\python.exe')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $root 'config\api.local.json') -Raw | ConvertFrom-Json
if (!$config.approval_store_path -or ![IO.Path]::IsPathRooted($config.approval_store_path)) {
    throw 'Absolute handoff store path is required'
}
$directory = Join-Path (Split-Path -Parent $config.approval_store_path) 'backups'
if (!(Test-Path -LiteralPath $directory -PathType Container)) {
    throw 'Prepare a protected backup directory first'
}
$name = 'handoff-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N') + '.sqlite'
$destination = Join-Path $directory $name
& $PythonPath (Join-Path $PSScriptRoot 'approval_backup.py') --destination $destination
if ($LASTEXITCODE -ne 0) { throw 'Handoff backup failed' }
@{completed_at_utc=[DateTime]::UtcNow.ToString('o');file=$name;integrity_check='ok'} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $directory 'last-success.json') -Encoding UTF8
# Preserve pilot backups; retention/off-host storage requires its own rollout.
