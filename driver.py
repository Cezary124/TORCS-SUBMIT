import argparse
import json
import sys
from dataclasses import fields, replace
from pathlib import Path
from typing import Dict

from race_config import PRESETS
from racing_controller import RacingController
from snakeoil3_gym import Client
from telemetry import TelemetryLogger


def parse_args():
    parser = argparse.ArgumentParser(description="IBM AI Racing TORCS driver")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--steps", type=int, default=100000)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="balanced")
    parser.add_argument("--profile-file", help="JSON tuning profile created by tune_next.py")
    parser.add_argument("--log-every", type=int, default=5)
    parser.add_argument("--no-telemetry", action="store_true")
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Do not stop after the first completed standing-start lap.",
    )
    return parser.parse_args()


def load_profile_file(config, profile_file: str):
    path = Path(profile_file)
    data = json.loads(path.read_text(encoding="utf-8"))
    allowed = {field.name for field in fields(config)}
    overrides = {key: value for key, value in data.items() if key in allowed}
    if "speed_profile" in overrides:
        overrides["speed_profile"] = tuple(tuple(float(v) for v in item) for item in overrides["speed_profile"])
    if "line_profile" in overrides:
        overrides["line_profile"] = tuple(tuple(float(v) for v in item) for item in overrides["line_profile"])
    if "brake_profile" in overrides:
        overrides["brake_profile"] = tuple(tuple(float(v) for v in item) for item in overrides["brake_profile"])
    if "control_profile" in overrides:
        overrides["control_profile"] = tuple(tuple(float(v) for v in item) for item in overrides["control_profile"])
    if "name" not in overrides:
        overrides["name"] = path.stem
    return replace(config, **overrides)


def create_client(host: str, port: int, steps: int) -> Client:
    original_argv = sys.argv[:]
    sys.argv = [original_argv[0], "--host", host, "--port", str(port), "--steps", str(steps)]
    try:
        return Client()
    finally:
        sys.argv = original_argv


def apply_action(response: Dict[str, object], action: Dict[str, object]) -> None:
    for key in ("steer", "accel", "brake", "gear", "clutch", "meta"):
        if key in action:
            response[key] = action[key]


def main() -> int:
    args = parse_args()
    config = PRESETS[args.preset]
    if args.profile_file:
        config = load_profile_file(config, args.profile_file)
    controller = RacingController(config)
    telemetry = TelemetryLogger(enabled=not args.no_telemetry, sample_every=args.log_every, label=config.name)

    print(f"Preset: {config.name}")
    if telemetry.path:
        print(f"Telemetry: {telemetry.path}")

    client = create_client(args.host, args.port, args.steps)
    best_last_lap = None
    previous_dist_from_start = None

    try:
        for step in range(client.maxSteps):
            client.get_servers_input()
            sensors = client.S.d
            action = controller.drive(sensors, client.R.d)
            apply_action(client.R.d, action)
            telemetry.record(step, sensors, action)

            last_lap = float(sensors.get("lastLapTime", 0.0))
            if last_lap > 0.0 and (best_last_lap is None or last_lap < best_last_lap):
                telemetry.record(step, sensors, action, force=True)
                best_last_lap = last_lap
                print(f"New best completed lap: {best_last_lap:.3f}s at step {step}")

            if last_lap > 0.0 and not args.keep_running:
                print(f"Standing-start lap completed: {last_lap:.3f}s")
                break

            dist_from_start = float(sensors.get("distFromStart", 0.0))
            cur_lap_time = float(sensors.get("curLapTime", 0.0))
            if (
                previous_dist_from_start is not None
                and previous_dist_from_start > 3000.0
                and dist_from_start < 120.0
                and cur_lap_time > 20.0
                and not args.keep_running
            ):
                telemetry.record(step, sensors, action, force=True)
                print(f"Standing-start lap wrap detected near start/finish at step {step}.")
                break
            previous_dist_from_start = dist_from_start

            if step % config.sample_print_steps == 0:
                print(
                    "step={step} speed={speed:.1f} target={target:.1f} "
                    "steer={steer:.2f} pos={pos:.2f} lap={lap:.2f}".format(
                        step=step,
                        speed=float(sensors.get("speedX", 0.0)),
                        target=float(action.get("targetSpeed", 0.0)),
                        steer=float(action.get("steer", 0.0)),
                        pos=float(sensors.get("trackPos", 0.0)),
                        lap=float(sensors.get("curLapTime", 0.0)),
                    )
                )

            client.respond_to_server()
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        telemetry.close()
        client.shutdown()
        if best_last_lap is not None:
            print(f"Best completed lap in this run: {best_last_lap:.3f}s")
        if telemetry.path:
            print(f"Telemetry saved to: {telemetry.path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
