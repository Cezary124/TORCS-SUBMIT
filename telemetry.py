import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class TelemetryLogger:
    def __init__(
        self,
        enabled: bool = True,
        sample_every: int = 5,
        directory: str = "telemetry_runs",
        label: str = "run",
    ):
        self.enabled = enabled
        self.sample_every = max(1, int(sample_every))
        self.path: Optional[Path] = None
        self.file = None
        self.writer = None

        if enabled:
            out_dir = Path(directory)
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_label = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in label)
            self.path = out_dir / f"run_{stamp}_{safe_label}.csv"
            self.file = self.path.open("w", newline="", encoding="utf-8")
            self.writer = csv.DictWriter(self.file, fieldnames=self._fieldnames())
            self.writer.writeheader()

    def record(self, step: int, sensors: Dict[str, object], action: Dict[str, object], force: bool = False) -> None:
        if not self.enabled or (not force and step % self.sample_every != 0):
            return

        track = sensors.get("track", [])
        if not isinstance(track, list):
            track = []

        row = {
            "step": step,
            "curLapTime": sensors.get("curLapTime", 0.0),
            "lastLapTime": sensors.get("lastLapTime", 0.0),
            "distFromStart": sensors.get("distFromStart", 0.0),
            "distRaced": sensors.get("distRaced", 0.0),
            "speedX": sensors.get("speedX", 0.0),
            "speedY": sensors.get("speedY", 0.0),
            "trackPos": sensors.get("trackPos", 0.0),
            "angle": sensors.get("angle", 0.0),
            "rpm": sensors.get("rpm", 0.0),
            "gear": sensors.get("gear", 0),
            "damage": sensors.get("damage", 0.0),
            "front": track[9] if len(track) > 9 else 0.0,
            "left": max(track[:9]) if len(track) >= 9 else 0.0,
            "right": max(track[10:]) if len(track) > 10 else 0.0,
            "steer": action.get("steer", 0.0),
            "accel": action.get("accel", 0.0),
            "brake": action.get("brake", 0.0),
            "targetSpeed": action.get("targetSpeed", 0.0),
            "targetTrackPos": action.get("targetTrackPos", 0.0),
        }
        self.writer.writerow(row)

    def close(self) -> None:
        if self.file:
            self.file.flush()
            self.file.close()

    @staticmethod
    def _fieldnames():
        return [
            "step",
            "curLapTime",
            "lastLapTime",
            "distFromStart",
            "distRaced",
            "speedX",
            "speedY",
            "trackPos",
            "angle",
            "rpm",
            "gear",
            "damage",
            "front",
            "left",
            "right",
            "steer",
            "accel",
            "brake",
            "targetSpeed",
            "targetTrackPos",
        ]
