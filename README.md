# TORCS AI Racing Submission

Clean TORCS driver submission for the IBM AI Racing / TORCS challenge.

This repository contains a ready-to-run Python driver and the saved best tuning profile used for our final run. It does not require Ollama, Granite, or any online AI service at runtime.

## Project Contents

- `driver.py` - main entry point for running the driver.
- `racing_controller.py` - driving logic: steering, throttle, braking, recovery, and speed control.
- `race_config.py` - controller presets and tunable configuration values.
- `tuning_profiles/best_profile.json` - saved best profile used by `run_best`.
- `run_best.bat` - easiest Windows launcher.
- `run_best.ps1` - PowerShell launcher for the best profile.
- `run_driver.ps1` - configurable launcher for presets and profile files.
- `telemetry.py` - optional telemetry logging.
- `livery/car1-ow1.rgb` - our custom car livery.

## Requirements

- Windows 10 or Windows 11.
- TORCS competition build installed and working.
- Python virtual environment at:

```powershell
C:\torcs-env\Scripts\python.exe
```

The runtime driver uses only standard Python libraries and the included TORCS socket client files. The older Gym-TORCS example files may require extra packages such as `numpy` or `gym`, but they are not needed to run the final driver.

## Setup

Clone the repository:

```powershell
cd C:\RaceYourCode
git clone https://github.com/Cezary124/TORCS-SUBMIT.git TORCS-clean-solution
cd C:\RaceYourCode\TORCS-clean-solution
```

If you already downloaded the ZIP, extract it to:

```text
C:\RaceYourCode\TORCS-clean-solution
```

Make sure the best profile exists:

```text
C:\RaceYourCode\TORCS-clean-solution\tuning_profiles\best_profile.json
```

## TORCS Race Setup

Start TORCS, then configure the race:

1. Open TORCS.
2. Go to `Race -> Practice -> Configure Race`.
3. Select the Corkscrew track.
4. Set the race to one lap.
5. Select `scr_server` as the driver.
6. Accept the configuration.
7. Go to `Race -> Practice -> New Race`.

TORCS should now show the blue SCR waiting screen. Keep TORCS open on that screen before starting the Python driver.

## Run the Best Driver

From `C:\RaceYourCode\TORCS-clean-solution`, run:

```powershell
.\run_best.bat
```

Or run the PowerShell launcher directly:

```powershell
.\run_best.ps1
```

Equivalent direct Python command:

```powershell
C:\torcs-env\Scripts\python.exe .\driver.py --preset balanced --profile-file .\tuning_profiles\best_profile.json
```

When the driver connects, the car should start moving in TORCS.

## Optional Driver Modes

Run without the saved profile:

```powershell
.\run_driver.ps1 -Preset balanced
```

Run with another preset:

```powershell
.\run_driver.ps1 -Preset conservative
.\run_driver.ps1 -Preset aggressive
.\run_driver.ps1 -Preset profiled
```

Run continuously instead of stopping after the first completed standing-start lap:

```powershell
.\run_driver.ps1 -Preset balanced -ProfileFile .\tuning_profiles\best_profile.json -KeepRunning
```

## Troubleshooting

If the script waits or the car does not move:

- Check that TORCS is already on the blue SCR waiting screen.
- Check that `scr_server` is selected as the driver.
- Check that TORCS and the Python driver are using port `3001`.
- Close TORCS completely, open it again, start `Practice -> New Race`, and rerun `run_best.bat`.

If PowerShell blocks the script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_best.ps1
```

If `C:\torcs-env\Scripts\python.exe` does not exist, create or restore the TORCS Python environment from the Windows setup guide before running the driver.

## Notes

This repository is a clean submission package. Training/tuning artifacts, telemetry runs, caches, and local IDE files are intentionally excluded from Git.
