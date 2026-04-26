import argparse
import importlib
import socket
import time

from server.settings import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_PYCAR_BASE_SPEED,
    DEFAULT_PYCAR_EVASION_SPEED,
    DEFAULT_PYCAR_OBSTACLE_THRESHOLD_CM,
    DEFAULT_PYCAR_SERVER_IP,
    DEFAULT_PYCAR_STEERING_COEFF,
    DEFAULT_PYCAR_STEERING_TRIM,
    DEFAULT_PYCAR_TURN_PULSE_SEC,
    DEFAULT_PYCAR_WD_WA_SPEED_SCALE,
    DEFAULT_RETRY_DELAY,
    DEFAULT_SOCKET_TIMEOUT,
)


VALID_COMMANDS = {"W", "W_MAX", "S", "A", "D", "WA", "WD", "STOP"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client Picar-X: riceve cmd,v_mult,distanza e pilota il rover.")
    parser.add_argument("--host", default=DEFAULT_PYCAR_SERVER_IP, help="IP del server visione.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP del server.")
    parser.add_argument("--base-speed", type=int, default=DEFAULT_PYCAR_BASE_SPEED, help="Velocita base avanti/indietro.")
    parser.add_argument("--evasion-speed", type=int, default=DEFAULT_PYCAR_EVASION_SPEED, help="Velocita usata nelle manovre evasive.")
    parser.add_argument(
        "--obstacle-threshold-cm",
        type=float,
        default=DEFAULT_PYCAR_OBSTACLE_THRESHOLD_CM,
        help="Soglia distanza ostacolo per attivare la manovra evasiva.",
    )
    parser.add_argument("--steering-trim", type=int, default=DEFAULT_PYCAR_STEERING_TRIM)
    parser.add_argument("--steering-coeff", type=float, default=DEFAULT_PYCAR_STEERING_COEFF)
    parser.add_argument("--turn-pulse-sec", type=float, default=DEFAULT_PYCAR_TURN_PULSE_SEC)
    parser.add_argument("--wdwa-speed-scale", type=float, default=DEFAULT_PYCAR_WD_WA_SPEED_SCALE)
    parser.add_argument("--retry-delay", type=float, default=DEFAULT_RETRY_DELAY)
    parser.add_argument("--socket-timeout", type=float, default=DEFAULT_SOCKET_TIMEOUT)
    parser.add_argument("--command-timeout", type=float, default=DEFAULT_COMMAND_TIMEOUT)
    parser.add_argument("--dry-run", action="store_true", help="Simula senza hardware.")
    return parser


def build_rover(dry_run: bool):
    if dry_run:
        return DryRunPicarx()
    Picarx = importlib.import_module("picarx").Picarx
    return Picarx()


class DryRunUltrasonic:
    def read(self):
        return 999.0


class DryRunPicarx:
    def __init__(self):
        self.ultrasonic = DryRunUltrasonic()

    def set_dir_servo_angle(self, angle: int) -> None:
        print(f"[DRY-RUN] steering={angle}")

    def forward(self, speed: int) -> None:
        print(f"[DRY-RUN] forward={speed}")

    def backward(self, speed: int) -> None:
        print(f"[DRY-RUN] backward={speed}")


def safe_stop(px, steering_trim: int) -> None:
    px.forward(0)
    px.set_dir_servo_angle(steering_trim)


def parse_latest_command(buffer: str):
    lines = buffer.split("\n")
    if len(lines) < 2:
        return None, lines[-1]

    latest = lines[-2].strip()
    rest = lines[-1]
    if not latest:
        return None, rest

    parts = latest.split(",")
    if len(parts) < 2:
        return None, rest

    cmd = parts[0].strip()
    if cmd not in VALID_COMMANDS:
        return None, rest

    try:
        v_mult = float(parts[1])
    except ValueError:
        return None, rest

    try:
        distanza = float(parts[2]) if len(parts) >= 3 else 0.0
    except ValueError:
        distanza = 0.0

    return (cmd, v_mult, distanza), rest


def esegui_evasione(px, cmd: str, steering_trim: int, evasion_speed: int) -> None:
    print(f"OSTACOLO RILEVATO durante {cmd}")
    px.forward(0)
    time.sleep(0.1)

    if cmd in ["W", "W_MAX", "WD", "WA"]:
        px.set_dir_servo_angle(steering_trim)
        px.backward(evasion_speed)
        time.sleep(1.2)
    elif cmd == "A":
        px.set_dir_servo_angle(-35)
        px.backward(evasion_speed)
        time.sleep(0.9)
    elif cmd == "D":
        px.set_dir_servo_angle(35)
        px.backward(evasion_speed)
        time.sleep(0.9)

    px.forward(0)
    px.set_dir_servo_angle(steering_trim)


def gestisci_motori(px, cmd: str, v_mult: float, base_speed: int, steering_trim: int, steering_coeff: float, turn_pulse_sec: float, wdwa_speed_scale: float) -> None:
    speed = int(base_speed * max(0.0, min(1.0, v_mult)))

    if cmd == "STOP":
        px.forward(0)
        px.set_dir_servo_angle(steering_trim)
    elif cmd in ["W", "W_MAX"]:
        px.set_dir_servo_angle(steering_trim)
        px.forward(speed)
    elif cmd == "S":
        px.set_dir_servo_angle(steering_trim)
        px.backward(speed)
    elif cmd == "D":
        px.set_dir_servo_angle(-35)
        px.forward(int(speed * steering_coeff))
        time.sleep(turn_pulse_sec)
        px.set_dir_servo_angle(steering_trim)
        px.forward(0)
    elif cmd == "A":
        px.set_dir_servo_angle(35)
        px.forward(int(speed * steering_coeff))
        time.sleep(turn_pulse_sec)
        px.set_dir_servo_angle(steering_trim)
        px.forward(0)
    elif cmd == "WD":
        px.set_dir_servo_angle(-20)
        px.forward(int(speed * wdwa_speed_scale))
    elif cmd == "WA":
        px.set_dir_servo_angle(20)
        px.forward(int(speed * wdwa_speed_scale))


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    px = build_rover(args.dry_run)

    safe_stop(px, args.steering_trim)
    last_command_time = time.monotonic()
    current_cmd = "STOP"

    try:
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(args.socket_timeout)
            try:
                print(f"Tentativo connessione a {args.host}:{args.port}...")
                sock.connect((args.host, args.port))
                print("Connesso. Client Picar-X attivo.")
            except OSError:
                sock.close()
                time.sleep(args.retry_delay)
                continue

            buffer = ""
            try:
                while True:
                    try:
                        raw = sock.recv(1024)
                    except socket.timeout:
                        if time.monotonic() - last_command_time > args.command_timeout and current_cmd != "STOP":
                            safe_stop(px, args.steering_trim)
                            current_cmd = "STOP"
                        continue

                    if not raw:
                        raise ConnectionError("Connessione chiusa dal server")

                    buffer += raw.decode("utf-8", errors="ignore")
                    parsed, buffer = parse_latest_command(buffer)
                    if parsed is None:
                        continue

                    cmd, v_mult, _ = parsed
                    last_command_time = time.monotonic()

                    distanza = px.ultrasonic.read()
                    if distanza > 0 and distanza < args.obstacle_threshold_cm and cmd not in ["S", "STOP"]:
                        esegui_evasione(px, cmd, args.steering_trim, args.evasion_speed)
                        buffer = ""
                        current_cmd = "STOP"
                        continue

                    gestisci_motori(
                        px,
                        cmd,
                        v_mult,
                        args.base_speed,
                        args.steering_trim,
                        args.steering_coeff,
                        args.turn_pulse_sec,
                        args.wdwa_speed_scale,
                    )
                    current_cmd = cmd
            except (OSError, ConnectionError) as exc:
                print(f"Connessione persa: {exc}")
                safe_stop(px, args.steering_trim)
                current_cmd = "STOP"
                sock.close()
                time.sleep(args.retry_delay)
    except KeyboardInterrupt:
        print("Arresto manuale")
    finally:
        safe_stop(px, args.steering_trim)


if __name__ == "__main__":
    main()
