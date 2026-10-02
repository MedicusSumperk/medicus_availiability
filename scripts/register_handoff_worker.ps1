[CmdletBinding()]
param(
    [string]$PythonPath = 'C:\python\python.exe'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$worker = Join-Path $PSScriptRoot 'handoff_delivery.py'
$configPath = Join-Path $root 'config\api.local.json'
if (!(Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python is missing' }
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
if ($config.enable_durable_handoff -ne $true) { throw 'Enable durable handoff after preparing its configuration' }
if (!$config.approval_store_path -or ![IO.Path]::IsPathRooted($config.approval_store_path) -or
    !(Test-Path -LiteralPath $config.approval_store_path -PathType Leaf)) {
    throw 'Initialize the protected handoff store before registering the worker'
}
$name = 'Medicus Handoff Delivery'
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    throw 'Worker task already exists; inspect it before updating'
}
# Only this worker task is created. Existing API/Medicus tasks are untouched.
$action = New-ScheduledTaskAction -Execute $PythonPath -Argument ('"' + $worker + '"') -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 20 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Deliver durable staff requests to Operator; no Medicus database writes.' | Out-Null
Start-ScheduledTask -TaskName $name
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State
