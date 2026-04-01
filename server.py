import argparse
import math
import socket

import cv2
import cv2.aruco as aruco
import numpy as np

from config import DEFAULT_CAMERA_INDEX, DEFAULT_HOST, DEFAULT_MARKER_ID, DEFAULT_PORT


def compute_command(marker_corners: np.ndarray) -> tuple[str, str, tuple[int, int, int], tuple[int, int], tuple[int, int]]:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Server di visione: legge ArUco e invia comandi al rover via TCP.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host su cui mettersi in ascolto.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP del server.")
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX, help="Indice della webcam da usare.")
    parser.add_argument("--marker-id", type=int, default=DEFAULT_MARKER_ID, help="ID del marker ArUco da seguire.")
    parser.add_argument("--window-title", default="Drone D-Pad", help="Titolo della finestra OpenCV.")
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

    print("Modalita D-Pad a 4 direzioni attiva. Premi Q per uscire.")

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

            if ids is not None:
                matches = np.where(ids.flatten() == args.marker_id)[0]
                if matches.size > 0:
                    marker_corners = corners[matches[0]][0]
                    command, status_text, color, start_point, end_point = compute_command(marker_corners)
                    cv2.polylines(frame, [np.int32(marker_corners)], True, (255, 255, 255), 2)
                    cv2.arrowedLine(frame, start_point, end_point, color, 4)

            cv2.putText(frame, f"AZIONE: {status_text}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

            try:
                client_socket.sendall(f"{command}\n".encode("utf-8"))
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