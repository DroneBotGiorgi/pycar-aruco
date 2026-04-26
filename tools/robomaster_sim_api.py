from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimRoboMasterCommandApi:
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
            f"[RoboMaster-SIM] connected ip={self.robot_ip} conn_type={self.conn_type} speed={self.speed:.3f}"
        )

    def send(self, command: str, speed_multiplier: float = 1.0) -> None:
        if not self._connected:
            raise RuntimeError("Sim RoboMaster API non connessa. Chiama connect() prima di send().")

        vx, vy, vz = self._command_to_velocity(command, speed_multiplier)
        self._send_count += 1
        self._last_command = command
        print(f"[RoboMaster-SIM] send#{self._send_count}: cmd={command} x={vx:.3f} y={vy:.3f} z={vz:.3f}")

    def close(self) -> None:
        if self._connected:
            print(f"[RoboMaster-SIM] close last_cmd={self._last_command} total_sends={self._send_count}")
        self._connected = False

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
