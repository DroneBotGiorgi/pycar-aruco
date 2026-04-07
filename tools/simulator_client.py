import argparse
import math
import socket
import sys
import time
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import DEFAULT_COMMAND_TIMEOUT, DEFAULT_PORT, DEFAULT_RETRY_DELAY, DEFAULT_SOCKET_TIMEOUT


VALID_COMMANDS = {"W", "S", "A", "D", "STOP"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulatore visivo rover: riceve comandi TCP e anima un rover 2D senza hardware."
    )
    parser.add_argument("--host", required=True, help="IP del computer che esegue il server.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP del server.")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY,
        help="Secondi tra tentativi di connessione.",
    )
    parser.add_argument(
        "--command-timeout",
        type=float,
        default=DEFAULT_COMMAND_TIMEOUT,
        help="Se non arrivano comandi entro questo tempo, il simulatore forza STOP.",
    )
    parser.add_argument(
        "--socket-timeout",
        type=float,
        default=DEFAULT_SOCKET_TIMEOUT,
        help="Timeout lettura socket in secondi.",
    )
    parser.add_argument("--tick-rate", type=float, default=30.0, help="Aggiornamenti al secondo del simulatore.")
    parser.add_argument("--max-speed", type=float, default=220.0, help="Velocita lineare simulata (px/s).")
    parser.add_argument("--turn-rate", type=float, default=140.0, help="Velocita angolare simulata (gradi/s).")
    parser.add_argument("--width", type=int, default=960, help="Larghezza finestra simulatore.")
    parser.add_argument("--height", type=int, default=640, help="Altezza finestra simulatore.")
    return parser


def extract_latest_command(data: str) -> str | None:
    for command in reversed(data.splitlines()):
        if command in VALID_COMMANDS:
            return command
    return None


class RoverSimulator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.sock: socket.socket | None = None
        self.next_connect_time = 0.0

        self.current_command = "STOP"
        self.last_command_time = time.monotonic()

        self.x = args.width / 2
        self.y = args.height / 2
        self.heading_deg = -90.0

        self.root = tk.Tk()
        self.root.title("Rover Visual Simulator")
        self.canvas = tk.Canvas(self.root, width=args.width, height=args.height, bg="#10131a", highlightthickness=0)
        self.canvas.pack()

        self.status_var = tk.StringVar(value="DISCONNECTED")
        self.command_var = tk.StringVar(value="CMD: STOP")

        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(status_frame, textvariable=self.status_var, fg="#d9e2ff", bg="#1b2130", padx=8, pady=4).pack(
            side=tk.LEFT
        )
        tk.Label(status_frame, textvariable=self.command_var, fg="#10131a", bg="#8cf2a4", padx=8, pady=4).pack(
            side=tk.LEFT, padx=8
        )

        self.last_tick = time.perf_counter()
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def connect_if_needed(self) -> None:
        if self.sock is not None:
            return

        now = time.monotonic()
        if now < self.next_connect_time:
            return

        self.status_var.set("CONNECTING")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.args.socket_timeout)

        try:
            sock.connect((self.args.host, self.args.port))
        except OSError:
            sock.close()
            self.next_connect_time = now + self.args.retry_delay
            self.status_var.set("DISCONNECTED")
            return

        self.sock = sock
        self.last_command_time = now
        self.status_var.set(f"CONNECTED {self.args.host}:{self.args.port}")

    def disconnect(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.status_var.set("DISCONNECTED")
        self.next_connect_time = time.monotonic() + self.args.retry_delay

    def poll_network(self) -> None:
        if self.sock is None:
            return

        try:
            data = self.sock.recv(1024).decode("utf-8")
        except socket.timeout:
            data = ""
        except OSError:
            self.disconnect()
            self.current_command = "STOP"
            return

        if data == "":
            if time.monotonic() - self.last_command_time > self.args.command_timeout:
                self.current_command = "STOP"
            return

        command = extract_latest_command(data)
        if command is None:
            return

        self.current_command = command
        self.last_command_time = time.monotonic()

    def integrate_motion(self, dt: float) -> None:
        move_speed = 0.0
        turn_speed = 0.0

        if self.current_command == "W":
            move_speed = self.args.max_speed
        elif self.current_command == "S":
            move_speed = -self.args.max_speed * 0.85
        elif self.current_command == "A":
            move_speed = self.args.max_speed * 0.75
            turn_speed = -self.args.turn_rate
        elif self.current_command == "D":
            move_speed = self.args.max_speed * 0.75
            turn_speed = self.args.turn_rate

        self.heading_deg += turn_speed * dt
        theta = math.radians(self.heading_deg)

        self.x += math.cos(theta) * move_speed * dt
        self.y += math.sin(theta) * move_speed * dt

        margin = 24
        self.x = max(margin, min(self.args.width - margin, self.x))
        self.y = max(margin, min(self.args.height - margin, self.y))

    def draw_scene(self) -> None:
        self.canvas.delete("all")

        w = self.args.width
        h = self.args.height

        self.canvas.create_rectangle(0, 0, w, h, fill="#10131a", outline="")
        self.canvas.create_line(w / 2, 0, w / 2, h, fill="#2a3248", dash=(4, 6))
        self.canvas.create_line(0, h / 2, w, h / 2, fill="#2a3248", dash=(4, 6))

        theta = math.radians(self.heading_deg)
        nose_x = self.x + math.cos(theta) * 22
        nose_y = self.y + math.sin(theta) * 22
        left_x = self.x + math.cos(theta + 2.45) * 16
        left_y = self.y + math.sin(theta + 2.45) * 16
        right_x = self.x + math.cos(theta - 2.45) * 16
        right_y = self.y + math.sin(theta - 2.45) * 16

        self.canvas.create_polygon(
            nose_x,
            nose_y,
            left_x,
            left_y,
            right_x,
            right_y,
            fill="#5fd4ff",
            outline="#dff7ff",
            width=2,
        )

        self.canvas.create_text(
            12,
            12,
            anchor="nw",
            fill="#c8d4f0",
            font=("Consolas", 12),
            text=f"x={self.x:6.1f}  y={self.y:6.1f}  heading={self.heading_deg:7.1f}",
        )

        self.command_var.set(f"CMD: {self.current_command}")

    def tick(self) -> None:
        self.connect_if_needed()
        self.poll_network()

        now = time.perf_counter()
        dt = max(0.0, min(0.1, now - self.last_tick))
        self.last_tick = now

        self.integrate_motion(dt)
        self.draw_scene()

        interval_ms = int(1000 / max(1.0, self.args.tick_rate))
        self.root.after(interval_ms, self.tick)

    def shutdown(self) -> None:
        self.disconnect()
        self.root.destroy()

    def run(self) -> None:
        self.tick()
        self.root.mainloop()


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    RoverSimulator(args).run()


if __name__ == "__main__":
    main()
