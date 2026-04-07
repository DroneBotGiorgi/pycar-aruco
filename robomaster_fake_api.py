from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FakeRoboMasterCommandApi:
    robot_ip: str
    speed: float = 0.5
    conn_type: str = "network"

    def __post_init__(self) -> None:
        self._connected = False
        self._last_command = "STOP"
        self._send_count = 0

    def connect(self) -> None:
        self._connected = True
        print(
            f"[RoboMaster-FAKE] connected ip={self.robot_ip} conn_type={self.conn_type} speed={self.speed:.3f}"
        )

    def send(self, command: str) -> None:
        if not self._connected:
            raise RuntimeError("Fake RoboMaster API non connessa. Chiama connect() prima di send().")

        vx, vy = self._command_to_velocity(command)
        self._send_count += 1
        self._last_command = command
        print(f"[RoboMaster-FAKE] send#{self._send_count}: cmd={command} x={vx:.3f} y={vy:.3f} z=0.000")

    def close(self) -> None:
        if self._connected:
            print(f"[RoboMaster-FAKE] close last_cmd={self._last_command} total_sends={self._send_count}")
        self._connected = False

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
