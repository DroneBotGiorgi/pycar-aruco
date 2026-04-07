import argparse
import importlib
import socket
import time

from settings import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_SPEED,
    DEFAULT_STEERING_ANGLE,
    DEFAULT_STEERING_INVERSION,
)


VALID_COMMANDS = {"W", "S", "A", "D", "STOP"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client rover: riceve comandi TCP e pilota Picar-X.")
    parser.add_argument("--host", required=True, help="IP del computer che esegue il server.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP del server.")
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED, help="Velocita del rover.")
    parser.add_argument("--steering-angle", type=int, default=DEFAULT_STEERING_ANGLE, help="Angolo massimo di sterzata.")
    parser.add_argument(
        "--steering-inversion",
        type=int,
        choices=[-1, 1],
        default=DEFAULT_STEERING_INVERSION,
        help="Usa -1 o 1 per invertire la direzione dello sterzo.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY,
        help="Secondi di attesa tra i tentativi di connessione.",
    )
    parser.add_argument(
        "--command-timeout",
        type=float,
        default=DEFAULT_COMMAND_TIMEOUT,
        help="Se non arrivano comandi entro questo tempo, invia STOP di sicurezza.",
    )
    parser.add_argument(
        "--socket-timeout",
        type=float,
        default=DEFAULT_SOCKET_TIMEOUT,
        help="Timeout lettura socket per attivare il watchdog senza blocchi lunghi.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula il rover senza toccare l'hardware Picar-X.",
    )
    return parser


def extract_latest_command(data: str) -> str | None:
    for command in reversed(data.splitlines()):
        if command in VALID_COMMANDS:
            return command
    return None


def apply_command(px, command: str, speed: int, steering_angle: int, steering_inversion: int) -> None:
    if command == "W":
        px.set_dir_servo_angle(0)
        px.forward(speed)
        return

    if command == "S":
        px.set_dir_servo_angle(0)
        px.backward(speed)
        return

    if command == "A":
        px.set_dir_servo_angle(-steering_angle * steering_inversion)
        px.forward(speed)
        return

    if command == "D":
        px.set_dir_servo_angle(steering_angle * steering_inversion)
        px.forward(speed)
        return

    px.forward(0)
    px.set_dir_servo_angle(0)


def safe_stop(px) -> None:
    try:
        px.forward(0)
    finally:
        px.set_dir_servo_angle(0)


class DryRunPicarx:
    def set_dir_servo_angle(self, angle: int) -> None:
        print(f"[DRY-RUN] steering={angle}")

    def forward(self, speed: int) -> None:
        print(f"[DRY-RUN] forward={speed}")

    def backward(self, speed: int) -> None:
        print(f"[DRY-RUN] backward={speed}")


def build_rover(dry_run: bool):
    if dry_run:
        return DryRunPicarx()

    Picarx = importlib.import_module("picarx").Picarx
    return Picarx()


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    px = build_rover(args.dry_run)
    safe_stop(px)

    print(f"Cerco il server all'indirizzo {args.host}:{args.port}...")

    current_command = "STOP"
    last_command_time = time.monotonic()

    try:
        while True:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(args.socket_timeout)

            try:
                client_socket.connect((args.host, args.port))
                print("Connesso. Modalita comandi rover attiva.")
            except OSError:
                client_socket.close()
                time.sleep(args.retry_delay)
                continue

            try:
                while True:
                    try:
                        data = client_socket.recv(1024).decode("utf-8")
                    except socket.timeout:
                        if time.monotonic() - last_command_time > args.command_timeout and current_command != "STOP":
                            apply_command(px, "STOP", args.speed, args.steering_angle, args.steering_inversion)
                            current_command = "STOP"
                        continue

                    if not data:
                        raise ConnectionError("Connessione chiusa dal server.")

                    command = extract_latest_command(data)
                    if command is None:
                        continue

                    last_command_time = time.monotonic()
                    if command != current_command:
                        apply_command(
                            px,
                            command,
                            args.speed,
                            args.steering_angle,
                            args.steering_inversion,
                        )
                        current_command = command
            except (OSError, ConnectionError):
                if current_command != "STOP":
                    apply_command(px, "STOP", args.speed, args.steering_angle, args.steering_inversion)
                    current_command = "STOP"
                client_socket.close()
                time.sleep(args.retry_delay)
    except KeyboardInterrupt:
        print("\nSpegnimento...")
    finally:
        safe_stop(px)


if __name__ == "__main__":
    main()