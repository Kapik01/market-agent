$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = "$scriptDir\scheduler.bat"

# Task 1: Alerts — every 5 minutes, 24/7
$alertAction = New-ScheduledTaskAction -Execute $bat -Argument "alerts" -WorkingDirectory $scriptDir
$alertTrigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Register-ScheduledTask -TaskName "MarketAgentAlerts" -Action $alertAction -Trigger $alertTrigger -RunLevel Highest -Force

# Task 2: Hourly updates — every hour, 24/7
$hourlyAction = New-ScheduledTaskAction -Execute $bat -Argument "hourly" -WorkingDirectory $scriptDir
$hourlyTrigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -Once -At (Get-Date)
Register-ScheduledTask -TaskName "MarketAgentHourly" -Action $hourlyAction -Trigger $hourlyTrigger -RunLevel Highest -Force

# Task 3: EOD summary — Mon-Fri at 4:30 PM ET
$eodAction = New-ScheduledTaskAction -Execute $bat -Argument "eod" -WorkingDirectory $scriptDir
$eodTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "4:30PM"
Register-ScheduledTask -TaskName "MarketAgentEOD" -Action $eodAction -Trigger $eodTrigger -RunLevel Highest -Force

Write-Host "All three Market Agent tasks registered successfully."
Write-Host "Check Task Scheduler to verify: MarketAgentAlerts, MarketAgentHourly, MarketAgentEOD"
