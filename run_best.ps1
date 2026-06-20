param(
    [string]$BestProfile = "tuning_profiles\best_profile.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path $BestProfile)) {
    throw "Best profile not found: $BestProfile"
}

& "$Root\run_driver.ps1" -Preset balanced -ProfileFile $BestProfile
