from __future__ import annotations

from dataclasses import dataclass

from server.settings import (
    DEFAULT_RM_OBSTACLE_THRESHOLD_MM,
    DEFAULT_RM_USE_TOF,
)


@dataclass
class RoboMasterCommandApi:
    robot_ip: str
    speed: float = 0.5
    conn_type: str = "network"
    use_tof: bool = DEFAULT_RM_USE_TOF
    obstacle_threshold_mm: int = DEFAULT_RM_OBSTACLE_THRESHOLD_MM

    def __post_init__(self) -> None:
        self._robot = None
        self._chassis = None
        self._sensor = None
        self._latest_distance_mm = 9999

    def connect(self) -> None:
        try:
            import robomaster
            from robomaster import robot
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Dipendenze RoboMaster incomplete. Verifica installazione SDK e moduli nativi richiesti."
            ) from exc

        sdk_config = getattr(robomaster, "config", None)
        if sdk_config is not None:
            sdk_config.ROBOT_IP_STR = self.robot_ip
        self._robot = robot.Robot()
        self._robot.initialize(conn_type=self.conn_type)
        if hasattr(robot, "FREE"):
            self._robot.set_robot_mode(mode=robot.FREE)
        self._chassis = self._robot.chassis

        if self.use_tof:
            self._sensor = self._robot.sensor
            self._sensor.sub_distance(freq=10, callback=self._on_detect_distance)

    def send(self, command: str, speed_multiplier: float = 1.0) -> None:
        if self._chassis is None:
            raise RuntimeError("RoboMaster API non connessa. Chiama connect() prima di send().")

        cmd = command
        if self._should_block_forward(cmd):
            cmd = "STOP"
            speed_multiplier = 0.0

        vx, vy, vz = self._command_to_velocity(cmd, speed_multiplier)
        self._chassis.drive_speed(x=vx, y=vy, z=vz)

    def close(self) -> None:
        if self._sensor is not None:
            try:
                self._sensor.unsub_distance()
            except Exception:
                pass
        if self._chassis is not None:
            try:
                self._chassis.drive_speed(x=0, y=0, z=0)
            except Exception:
                pass
        if self._robot is not None:
            try:
                self._robot.close()
            except Exception:
                pass

    def _on_detect_distance(self, dist_info) -> None:
        valid = [d for d in dist_info if d > 0]
        if valid:
            self._latest_distance_mm = min(valid)

    def _should_block_forward(self, command: str) -> bool:
        if not self.use_tof:
            return False
        if command in ("W", "W_MAX", "WA", "WD"):
            return self._latest_distance_mm < self.obstacle_threshold_mm
        return False

    def _command_to_velocity(self, command: str, speed_multiplier: float) -> tuple[float, float, float]:
        speed_multiplier = max(0.0, min(1.0, float(speed_multiplier)))
        speed = self.speed * speed_multiplier

        if command == "W":
            return (speed, 0.0, 0.0)
        if command == "W_MAX":
            return (0.8, 0.0, 0.0)
        if command == "S":
            return (-speed, 0.0, 0.0)
        if command == "A":
            return (0.0, 0.0, -speed * 40.0)
        if command == "D":
            return (0.0, 0.0, speed * 40.0)
        if command == "WA":
            return (speed, 0.0, -speed * 30.0)
        if command == "WD":
            return (speed, 0.0, speed * 30.0)
        return (0.0, 0.0, 0.0)
