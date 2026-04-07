from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RoboMasterCommandApi:
    robot_ip: str
    speed: float = 0.5
    conn_type: str = "network"

    def __post_init__(self) -> None:
        self._robot = None
        self._chassis = None

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
        self._chassis = self._robot.chassis

    def send(self, command: str) -> None:
        if self._chassis is None:
            raise RuntimeError("RoboMaster API non connessa. Chiama connect() prima di send().")

        vx, vy = self._command_to_velocity(command)
        self._chassis.drive_speed(x=vx, y=vy, z=0)

    def close(self) -> None:
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

    def _command_to_velocity(self, command: str) -> tuple[float, float]:
        if command == "W":
            return (self.speed, 0.0)
        if command == "S":
            return (-self.speed, 0.0)
        if command == "A":
            return (0.0, -self.speed)
        if command == "D":
            return (0.0, self.speed)
        return (0.0, 0.0)
