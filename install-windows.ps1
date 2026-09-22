param(
    [string]$Destination,
    [string]$Python
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Use install-macos.sh on macOS.' }
$pythonArgs = @()
if (-not $Python) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $Python = 'py'
        $pythonArgs = @('-3')
    } else { $Python = 'python' }
}
$installerArgs = @((Join-Path $PSScriptRoot 'scripts/install.py'))
if ($Destination) { $installerArgs += @('--destination', $Destination) }
& $Python @pythonArgs @installerArgs
if ($LASTEXITCODE -ne 0) { throw "Installer failed with exit code $LASTEXITCODE" }
