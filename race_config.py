from dataclasses import dataclass, replace
from typing import Tuple


SpeedProfile = Tuple[Tuple[float, float, float], ...]
LineProfile = Tuple[Tuple[float, float, float], ...]
BrakeProfile = Tuple[Tuple[float, float, float], ...]
ControlProfile = Tuple[Tuple[float, float, float, float, float, float], ...]


@dataclass(frozen=True)
class ControllerConfig:
    """Single place for values worth tuning between test runs."""

    name: str = "balanced"
    max_speed: float = 190.0
    min_speed: float = 42.0
    launch_speed: float = 35.0

    steer_angle_gain: float = 14.0
    center_gain: float = 0.42
    lookahead_gain: float = 0.55
    steer_smoothing: float = 0.28

    curve_speed_penalty: float = 118.0
    lateral_speed_penalty: float = 34.0
    near_wall_distance: float = 42.0
    emergency_wall_distance: float = 24.0

    accel_gain: float = 0.018
    brake_gain: float = 0.018
    corner_accel_limit: float = 0.34
    brake_steer_threshold: float = 0.52
    approach_speed_buffer: float = 34.0

    traction_slip_threshold: float = 5.5
    traction_cut: float = 0.22

    stuck_speed: float = 4.0
    stuck_after_steps: int = 95
    reverse_steps: int = 45

    sample_print_steps: int = 250
    speed_profile: SpeedProfile = ()
    line_profile: LineProfile = ()
    brake_profile: BrakeProfile = ()
    control_profile: ControlProfile = ()


BALANCED = ControllerConfig()

CONSERVATIVE = replace(
    BALANCED,
    name="conservative",
    max_speed=155.0,
    steer_angle_gain=12.0,
    lookahead_gain=0.45,
    curve_speed_penalty=135.0,
    corner_accel_limit=0.24,
)

AGGRESSIVE = replace(
    BALANCED,
    name="aggressive",
    max_speed=220.0,
    min_speed=48.0,
    steer_angle_gain=16.0,
    center_gain=0.36,
    lookahead_gain=0.68,
    curve_speed_penalty=104.0,
    lateral_speed_penalty=24.0,
    corner_accel_limit=0.44,
)

PROFILED_CORKSCREW = replace(
    BALANCED,
    name="profiled",
    max_speed=205.0,
    min_speed=42.0,
    steer_angle_gain=14.5,
    center_gain=0.41,
    lookahead_gain=0.58,
    curve_speed_penalty=112.0,
    lateral_speed_penalty=32.0,
    near_wall_distance=42.0,
    emergency_wall_distance=24.0,
    brake_gain=0.020,
    approach_speed_buffer=34.0,
    corner_accel_limit=0.36,
    speed_profile=(
        (0.0, 95.0, 150.0),
        (150.0, 235.0, 106.0),
        (365.0, 570.0, 70.0),
        (685.0, 805.0, 70.0),
        (955.0, 1090.0, 76.0),
        (1370.0, 1450.0, 112.0),
        (1450.0, 1595.0, 66.0),
        (1875.0, 2010.0, 86.0),
        (2265.0, 2385.0, 96.0),
        (2385.0, 2515.0, 64.0),
        (2570.0, 2760.0, 76.0),
        (2875.0, 3035.0, 78.0),
        (3165.0, 3315.0, 66.0),
        (3500.0, 3565.0, 96.0),
        (3565.0, 3665.0, 78.0),
    ),
    line_profile=(),
    brake_profile=(),
    control_profile=(),
)

PRESETS = {
    "balanced": BALANCED,
    "conservative": CONSERVATIVE,
    "aggressive": AGGRESSIVE,
    "profiled": PROFILED_CORKSCREW,
}
