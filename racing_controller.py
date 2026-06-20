import math
from typing import Dict, List, Tuple

from race_config import ControllerConfig


TRACK_SENSOR_ANGLES_DEG = [
    -45.0,
    -19.0,
    -12.0,
    -7.0,
    -4.0,
    -2.5,
    -1.7,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    1.7,
    2.5,
    4.0,
    7.0,
    12.0,
    19.0,
    45.0,
]


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_list(values, expected: int, fill: float) -> List[float]:
    if not isinstance(values, list):
        return [fill] * expected
    cleaned = [float(v) for v in values[:expected]]
    if len(cleaned) < expected:
        cleaned.extend([fill] * (expected - len(cleaned)))
    return cleaned


class RacingController:
    def __init__(self, config: ControllerConfig):
        self.config = config
        self.previous_steer = 0.0
        self.slow_steps = 0
        self.reverse_remaining = 0

    def drive(self, sensors: Dict[str, object], previous_action: Dict[str, object]) -> Dict[str, float]:
        speed = float(sensors.get("speedX", 0.0))
        track_pos = float(sensors.get("trackPos", 0.0))
        angle = float(sensors.get("angle", 0.0))
        dist_from_start = float(sensors.get("distFromStart", 0.0))
        track = safe_list(sensors.get("track"), 19, 200.0)

        if self._should_recover(speed, track_pos):
            return self._recovery_action(speed, track_pos, angle)

        target_track_pos = self._profile_line_target(dist_from_start)
        raw_steer, target_angle = self._steer(track, track_pos, angle, target_track_pos, dist_from_start)
        steer = self._smooth_steer(raw_steer)
        target_speed = self._target_speed(speed, track, track_pos, angle, steer, target_angle, dist_from_start)
        accel, brake = self._speed_control(speed, target_speed, steer, dist_from_start)
        accel = self._traction_control(sensors, accel)

        return {
            "steer": steer,
            "accel": accel,
            "brake": brake,
            "gear": self._gear(sensors),
            "clutch": 0.0,
            "meta": 0,
            "targetSpeed": target_speed,
            "targetTrackPos": target_track_pos,
        }

    def _should_recover(self, speed: float, track_pos: float) -> bool:
        if abs(track_pos) > 1.15:
            return True
        if abs(speed) < self.config.stuck_speed:
            self.slow_steps += 1
        else:
            self.slow_steps = 0
        if self.slow_steps > self.config.stuck_after_steps:
            self.reverse_remaining = self.config.reverse_steps
            self.slow_steps = 0
        return self.reverse_remaining > 0

    def _recovery_action(self, speed: float, track_pos: float, angle: float) -> Dict[str, float]:
        steer_back_to_track = -math.copysign(1.0, track_pos if track_pos else angle)
        if self.reverse_remaining > 0:
            self.reverse_remaining -= 1
            return {
                "steer": steer_back_to_track,
                "accel": 0.45,
                "brake": 0.0,
                "gear": -1,
                "clutch": 0.0,
                "meta": 0,
                "targetSpeed": -12.0,
            }
        return {
            "steer": steer_back_to_track,
            "accel": 0.35 if speed < 35.0 else 0.0,
            "brake": 0.1 if speed > 45.0 else 0.0,
            "gear": 1,
            "clutch": 0.0,
            "meta": 0,
            "targetSpeed": 30.0,
        }

    def _steer(
        self,
        track: List[float],
        track_pos: float,
        angle: float,
        target_track_pos: float,
        dist_from_start: float,
    ) -> Tuple[float, float]:
        best_index = self._best_track_sensor(track)
        target_angle = math.radians(TRACK_SENSOR_ANGLES_DEG[best_index])
        position_error = track_pos - target_track_pos
        _curve_penalty, _accel_limit, _brake_gain, center_gain = self._control_values(dist_from_start)

        steer = angle * self.config.steer_angle_gain / math.pi
        steer -= position_error * center_gain
        steer += target_angle * self.config.lookahead_gain
        return clip(steer, -1.0, 1.0), target_angle

    def _best_track_sensor(self, track: List[float]) -> int:
        best_index = 9
        best_score = -1.0
        for idx, distance in enumerate(track):
            forward_bias = 1.0 - min(abs(idx - 9) / 11.0, 0.85)
            score = distance * (0.35 + forward_bias)
            if score > best_score:
                best_score = score
                best_index = idx
        return best_index

    def _smooth_steer(self, steer: float) -> float:
        alpha = self.config.steer_smoothing
        smoothed = (alpha * self.previous_steer) + ((1.0 - alpha) * steer)
        self.previous_steer = clip(smoothed, -1.0, 1.0)
        return self.previous_steer

    def _target_speed(
        self,
        speed: float,
        track: List[float],
        track_pos: float,
        angle: float,
        steer: float,
        target_angle: float,
        dist_from_start: float,
    ) -> float:
        front = track[9]
        near_front = min(track[7:12])
        corner_load = abs(steer) + 0.65 * abs(angle) + 0.35 * abs(target_angle)
        curve_speed_penalty, _accel_limit, _brake_gain, _center_gain = self._control_values(dist_from_start)

        target = self.config.max_speed
        target -= corner_load * curve_speed_penalty
        target -= abs(track_pos) * self.config.lateral_speed_penalty

        if near_front < self.config.near_wall_distance:
            target = min(target, 72.0)
        if front < self.config.emergency_wall_distance:
            target = min(target, 46.0)
        if speed < self.config.launch_speed:
            target = max(target, self.config.launch_speed)

        profile_cap = self._profile_speed_cap(dist_from_start)
        if profile_cap is not None:
            target = min(target, profile_cap)

        return clip(target, self.config.min_speed, self.config.max_speed)

    def _profile_speed_cap(self, dist_from_start: float):
        for start, end, cap in self.config.speed_profile:
            if start <= dist_from_start <= end:
                return cap
            brake_lead = self._brake_lead_for_segment(start, end)
            if brake_lead > 0.0 and start > brake_lead and start - brake_lead <= dist_from_start < start:
                distance_to_entry = start - dist_from_start
                buffer = self.config.approach_speed_buffer * (distance_to_entry / brake_lead)
                return cap + buffer
        return None

    def _brake_lead_for_segment(self, segment_start: float, segment_end: float) -> float:
        for start, end, lead in self.config.brake_profile:
            if abs(float(start) - float(segment_start)) < 0.01 and abs(float(end) - float(segment_end)) < 0.01:
                return max(0.0, float(lead))
        return 0.0

    def _profile_line_target(self, dist_from_start: float) -> float:
        for start, end, target in self.config.line_profile:
            if start <= dist_from_start <= end:
                return clip(float(target), -0.65, 0.65)
        return 0.0

    def _control_values(self, dist_from_start: float) -> Tuple[float, float, float, float]:
        values = (
            self.config.curve_speed_penalty,
            self.config.corner_accel_limit,
            self.config.brake_gain,
            self.config.center_gain,
        )
        for start, end, curve_penalty, accel_limit, brake_gain, center_gain in self.config.control_profile:
            if start <= dist_from_start <= end:
                return (
                    clip(float(curve_penalty), 82.0, 112.0),
                    clip(float(accel_limit), 0.24, 0.56),
                    clip(float(brake_gain), 0.010, 0.032),
                    clip(float(center_gain), 0.28, 0.58),
                )
        return values

    def _speed_control(self, speed: float, target_speed: float, steer: float, dist_from_start: float) -> Tuple[float, float]:
        _curve_penalty, corner_accel_limit, brake_gain, _center_gain = self._control_values(dist_from_start)
        error = target_speed - speed
        if error >= 0:
            accel = clip(0.35 + error * self.config.accel_gain, 0.0, 1.0)
            brake = 0.0
        else:
            accel = 0.0
            brake = clip((-error) * brake_gain, 0.0, 0.9)

        if abs(steer) > self.config.brake_steer_threshold:
            accel = min(accel, corner_accel_limit)
            if speed > target_speed + 8.0:
                brake = max(brake, min(0.55, (abs(steer) - self.config.brake_steer_threshold) * 1.1))

        return accel, brake

    def _traction_control(self, sensors: Dict[str, object], accel: float) -> float:
        wheels = safe_list(sensors.get("wheelSpinVel"), 4, 0.0)
        rear_slip = (wheels[2] + wheels[3]) - (wheels[0] + wheels[1])
        if rear_slip > self.config.traction_slip_threshold:
            accel -= self.config.traction_cut
        return clip(accel, 0.0, 1.0)

    def _gear(self, sensors: Dict[str, object]) -> int:
        gear = int(float(sensors.get("gear", 1)))
        rpm = float(sensors.get("rpm", 0.0))
        speed = float(sensors.get("speedX", 0.0))

        if speed < -1.0:
            return -1
        if gear < 1:
            return 1
        if rpm > 8200.0 and gear < 6:
            return gear + 1
        if rpm < 3200.0 and gear > 1:
            return gear - 1

        speed_fallback = 1
        for idx, threshold in enumerate([0, 55, 88, 126, 166, 205], start=1):
            if speed > threshold:
                speed_fallback = idx
        if rpm <= 0.0:
            return min(speed_fallback, 6)
        return int(clip(gear, 1, 6))
