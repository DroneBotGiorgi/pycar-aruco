import argparse
import math
import socket
import time

import cv2
import cv2.aruco as aruco
import numpy as np

from settings import (
    DEFAULT_ALLOW_REVERSE,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_COMMAND_HEARTBEAT_SEC,
    DEFAULT_DEADZONE_X,
    DEFAULT_HOST,
    DEFAULT_LOST_STOP_FRAMES,
    DEFAULT_MARKER_ID,
    DEFAULT_MODE,
    DEFAULT_PORT,
    DEFAULT_SIZE_TOLERANCE,
    DEFAULT_TARGET_SIZE,
    DEFAULT_WINDOW_TITLE,
)


def compute_dpad_command(
    marker_corners: np.ndarray,
) -> tuple[str, str, tuple[int, int, int], tuple[int, int], tuple[int, int]]:
    top_x = (marker_corners[0][0] + marker_corners[1][0]) / 2
    top_y = (marker_corners[0][1] + marker_corners[1][1]) / 2
    bottom_x = (marker_corners[2][0] + marker_corners[3][0]) / 2
    bottom_y = (marker_corners[2][1] + marker_corners[3][1]) / 2

    delta_x = top_x - bottom_x
    delta_y = top_y - bottom_y
    angle = math.degrees(math.atan2(delta_y, delta_x))

    if -135 <= angle < -45:
        return "W", "AVANTI (Su)", (0, 255, 0), (int(bottom_x), int(bottom_y)), (int(top_x), int(top_y))
    if -45 <= angle < 45:
        return "D", "DESTRA", (255, 255, 0), (int(bottom_x), int(bottom_y)), (int(top_x), int(top_y))
    if 45 <= angle < 135:
        return "S", "INDIETRO (Giu)", (0, 165, 255), (int(bottom_x), int(bottom_y)), (int(top_x), int(top_y))
    return "A", "SINISTRA", (255, 0, 255), (int(bottom_x), int(bottom_y)), (int(top_x), int(top_y))


def compute_chase_command(
    marker_corners: np.ndarray,
    frame_shape: tuple[int, int, int],
    deadzone_x: float,
    target_size: float,
    size_tolerance: float,
    allow_reverse: bool,
) -> tuple[str, str, tuple[int, int, int], tuple[int, int], tuple[int, int], float, float]:
    frame_h, frame_w = frame_shape[:2]

    center = marker_corners.mean(axis=0)
    center_x, center_y = float(center[0]), float(center[1])
    x = marker_corners[:, 0]
    y = marker_corners[:, 1]
    area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
    size_ratio = area / float(frame_w * frame_h)

    x_error = (center_x - frame_w / 2.0) / (frame_w / 2.0)

    if x_error < -deadzone_x:
        command, text, color = "A", "ALLINEA SX", (255, 0, 255)
    elif x_error > deadzone_x:
        command, text, color = "D", "ALLINEA DX", (255, 255, 0)
    else:
        if size_ratio < target_size - size_tolerance:
            command, text, color = "W", "AVANZA", (0, 255, 0)
        elif size_ratio > target_size + size_tolerance and allow_reverse:
            command, text, color = "S", "ARRETRA", (0, 165, 255)
        else:
            command, text, color = "STOP", "BLOCCATO SU TARGET", (0, 255, 255)

    start_point = (int(frame_w / 2), int(center_y))
    end_point = (int(center_x), int(center_y))
    return command, text, color, start_point, end_point, x_error, size_ratio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Server di visione: legge ArUco e invia comandi al rover via TCP.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host su cui mettersi in ascolto.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP del server.")
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX, help="Indice della webcam da usare.")
    parser.add_argument("--marker-id", type=int, default=DEFAULT_MARKER_ID, help="ID del marker ArUco da seguire.")
    parser.add_argument(
        "--mode",
        choices=["dpad", "chase"],
        default=DEFAULT_MODE,
        help="dpad: 4 direzioni orientamento marker, chase: inseguimento target piu rapido.",
    )
    parser.add_argument(
        "--deadzone-x",
        type=float,
        default=DEFAULT_DEADZONE_X,
        help="Errore orizzontale normalizzato entro cui il rover considera il target centrato.",
    )
    parser.add_argument(
        "--target-size",
        type=float,
        default=DEFAULT_TARGET_SIZE,
        help="Area marker / area frame desiderata per considerare la distanza corretta.",
    )
    parser.add_argument(
        "--size-tolerance",
        type=float,
        default=DEFAULT_SIZE_TOLERANCE,
        help="Tolleranza su target-size per decidere se avanzare/arretrare.",
    )
    parser.add_argument(
        "--allow-reverse",
        action="store_true",
        default=DEFAULT_ALLOW_REVERSE,
        help="Permette il comando S in modalita chase quando il target e troppo vicino.",
    )
    parser.add_argument(
        "--lost-stop-frames",
        type=int,
        default=DEFAULT_LOST_STOP_FRAMES,
        help="Numero frame senza marker prima di forzare STOP.",
    )
    parser.add_argument(
        "--command-heartbeat-sec",
        type=float,
        default=DEFAULT_COMMAND_HEARTBEAT_SEC,
        help="Invia periodicamente il comando corrente anche se invariato.",
    )
    parser.add_argument("--window-title", default=DEFAULT_WINDOW_TITLE, help="Titolo della finestra OpenCV.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((args.host, args.port))
    server_socket.listen(1)

    print(f"In attesa di connessione dal rover su {args.host}:{args.port}...")
    client_socket, address = server_socket.accept()
    print(f"Rover connesso da {address}.")

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        client_socket.close()
        server_socket.close()
        raise RuntimeError(f"Impossibile aprire la webcam con indice {args.camera}.")

    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    detector = aruco.ArucoDetector(aruco_dict, aruco.DetectorParameters())

    print(f"Modalita {args.mode} attiva. Premi Q per uscire.")

    lost_frames = 0
    last_command = "STOP"
    last_send_ts = time.monotonic()
    last_fps_ts = time.perf_counter()
    fps = 0.0

    try:
        while True:
            ret, frame = capture.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = detector.detectMarkers(gray)

            command = "STOP"
            status_text = "NESSUN MARKER"
            color = (0, 0, 255)
            x_error = 0.0
            size_ratio = 0.0

            if ids is not None:
                matches = np.where(ids.flatten() == args.marker_id)[0]
                if matches.size > 0:
                    marker_corners = corners[matches[0]][0]
                    if args.mode == "dpad":
                        command, status_text, color, start_point, end_point = compute_dpad_command(marker_corners)
                    else:
                        (
                            command,
                            status_text,
                            color,
                            start_point,
                            end_point,
                            x_error,
                            size_ratio,
                        ) = compute_chase_command(
                            marker_corners,
                            frame.shape,
                            args.deadzone_x,
                            args.target_size,
                            args.size_tolerance,
                            args.allow_reverse,
                        )
                    lost_frames = 0
                    marker_poly = marker_corners.astype(np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [marker_poly], True, (255, 255, 255), 2)
                    cv2.arrowedLine(frame, start_point, end_point, color, 4)
                else:
                    lost_frames += 1
            else:
                lost_frames += 1

            if lost_frames >= args.lost_stop_frames:
                command = "STOP"
                status_text = "MARKER PERSO -> STOP"
                color = (0, 0, 255)

            cv2.putText(frame, f"AZIONE: {status_text}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
            cv2.putText(frame, f"CMD: {command}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            if args.mode == "chase":
                cv2.putText(
                    frame,
                    f"x_err={x_error:+.2f} size={size_ratio:.3f}",
                    (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            now = time.perf_counter()
            dt = now - last_fps_ts
            if dt > 0:
                fps = 1.0 / dt
            last_fps_ts = now
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            try:
                now_send = time.monotonic()
                should_send = (
                    command != last_command
                    or command == "STOP"
                    or (now_send - last_send_ts) >= args.command_heartbeat_sec
                )
                if should_send:
                    client_socket.sendall(f"{command}\n".encode("utf-8"))
                    last_command = command
                    last_send_ts = now_send
            except OSError:
                break

            cv2.imshow(args.window_title, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            client_socket.sendall("STOP\n".encode("utf-8"))
        except OSError:
            pass
        capture.release()
        cv2.destroyAllWindows()
        client_socket.close()
        server_socket.close()


if __name__ == "__main__":
    main()