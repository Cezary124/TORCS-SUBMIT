param(
    [ValidateSet("conservative", "balanced", "aggressive", "profiled")]
    [string]$Preset = "balanced",

    [int]$Steps = 100000,
    [int]$LogEvery = 5,

    [string]$ProfileFile = "",

    [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"
$Python = "C:\torcs-env\Scripts\python.exe"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $Root
$Args = @("$Root\driver.py", "--preset", $Preset, "--steps", $Steps, "--log-every", $LogEvery)
if ($ProfileFile -ne "") {
    $Args += @("--profile-file", $ProfileFile)
}
if ($KeepRunning) {
    $Args += "--keep-running"
}
& $Python @Args
