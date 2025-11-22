<#
Stops any running `app.py` Python processes and launches `ui.py` using `py -3`.
Run this from the repository root in PowerShell:
    .\run_ui.ps1

This is a convenience helper to ensure the CLI `app.py` isn't still running.
#>

Write-Host "Looking for running 'app.py' Python processes..."
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*app.py*' }
if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Stopping PID $($p.ProcessId): $($p.CommandLine)"
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Warning "Failed to stop PID $($p.ProcessId): $_"
        }
    }
} else {
    Write-Host "No running 'app.py' processes found."
}

Write-Host "Starting UI..."
py -3 .\ui.py
