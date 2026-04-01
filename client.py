import argparse
import importlib
import socket
import time

from config import DEFAULT_PORT, DEFAULT_SPEED, DEFAULT_STEERING_ANGLE, DEFAULT_STEERING_INVERSION


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
        default=2.0,
        help="Secondi di attesa tra i tentativi di connessione.",
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


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    Picarx = importlib.import_module("picarx").Picarx

    px = Picarx()
    px.set_dir_servo_angle(0)
    px.forward(0)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Cerco il server all'indirizzo {args.host}:{args.port}...")
    while True:
        try:
            client_socket.connect((args.host, args.port))
            print("Connesso. Modalita arcade a 4 direzioni attiva.")
            break
        except OSError:
            time.sleep(args.retry_delay)

    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            command = extract_latest_command(data)
            if command is None:
                continue

            apply_command(
                px,
                command,
                args.speed,
                args.steering_angle,
                args.steering_inversion,
            )
    except KeyboardInterrupt:
        print("\nSpegnimento...")
    finally:
        px.forward(0)
        px.set_dir_servo_angle(0)
        client_socket.close()


if __name__ == "__main__":
    main()