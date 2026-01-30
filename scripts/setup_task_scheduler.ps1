# InstaGenerate - Register Windows Task Scheduler task for fully automatic daily run
# Run once (e.g. right-click -> Run with PowerShell) to register the task.
# After this, the user never opens terminal or runs scripts manually.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BatPath = Join-Path $ProjectRoot "run_daily.bat"

if (-not (Test-Path $BatPath)) {
    Write-Host "ERROR: run_daily.bat not found at $BatPath"
    exit 1
}

# Action: run run_daily.bat (no python/terminal visible to user)
$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ProjectRoot
# Trigger: Daily at 22:00 (Turkey time - set Windows timezone to Turkey or set 22:00 local)
$Trigger = New-ScheduledTaskTrigger -Daily -At "10:00PM"
# If laptop was OFF at 22:00, run as soon as possible after next boot
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

try {
    Register-ScheduledTask -TaskName "InstaGenerate" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily Reel content generation. Runs at 22:00; if PC was off, runs when you turn it on."
    Write-Host "Task 'InstaGenerate' registered. It runs daily at 22:00. If the PC was off, it runs when you next turn it on."
} catch {
    Write-Host "ERROR: Could not register task. Try running PowerShell as Administrator: $($_.Exception.Message)"
    exit 1
}
