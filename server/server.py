import argparse
import math
import socket
import time

import cv2
import cv2.aruco as aruco
import numpy as np

from robomaster.robomaster_api import RoboMasterCommandApi
from server.settings import (
    DEFAULT_BRIDGE_FAKE_DISTANCE_CM,
    DEFAULT_BRIDGE_JUMP_DURATION_SEC,
    DEFAULT_BRIDGE_JUMP_SPEED,
    DEFAULT_BRIDGE_TRIGGER_MAX_CM,
    DEFAULT_BRIDGE_TRIGGER_MIN_CM,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_CAMERA_MATRIX,
    DEFAULT_DIST_COEFFS,
    DEFAULT_DIST_MAX_GUIDE_CM,
    DEFAULT_DIST_MEDIUM_CM,
    DEFAULT_DIST_MIN_GUIDE_CM,
    DEFAULT_DIST_SLOW_CM,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_HOST,
    DEFAULT_HUD_CENTER_ANGLE,
    DEFAULT_HUD_INTERSECTION_THRESHOLD,
    DEFAULT_HUD_R1,
    DEFAULT_HUD_R2,
    DEFAULT_HUD_R3,
    DEFAULT_HUD_RMAX,
    DEFAULT_MARKER_ID,
    DEFAULT_MARKER_SIZE_CM,
    DEFAULT_PORT,
    DEFAULT_ROBOMASTER_CONN_TYPE,
    DEFAULT_ROBOMASTER_IP,
    DEFAULT_ROBOMASTER_SPEED,
    DEFAULT_TRANSPORT,
    DEFAULT_VEL_MAX,
    DEFAULT_VEL_MEDIUM,
    DEFAULT_VEL_REVERSE,
    DEFAULT_VEL_SLOW,
    DEFAULT_WINDOW_TITLE,
)
from tools.robomaster_sim_api import SimRoboMasterCommandApi


ZONE_NAMES = ["DRITTO", "V 100", "STOP", "INDIETRO", "AV-SX", "SX", "AV-DX", "DX"]
ZONE_CMDS = ["W", "W_MAX", "STOP", "S", "WA", "A", "WD", "D"]
ZONE_COLORS = [
    (0, 255, 0),
    (255, 255, 255),
    (0, 0, 255),
    (0, 165, 255),
    (0, 255, 150),
    (255, 0, 255),
    (150, 255, 0),
    (255, 255, 0),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Radar server: ArUco -> comandi rover (TCP o RoboMaster API).")
    parser.add_argument("--transport", choices=["tcp", "robomaster", "robomaster-sim"], default=DEFAULT_TRANSPORT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX)
    parser.add_argument("--marker-id", type=int, default=DEFAULT_MARKER_ID)
    parser.add_argument("--marker-size-cm", type=float, default=DEFAULT_MARKER_SIZE_CM)
    parser.add_argument("--window-title", default=DEFAULT_WINDOW_TITLE)
    parser.add_argument("--robomaster-ip", default=DEFAULT_ROBOMASTER_IP)
    parser.add_argument("--robomaster-speed", type=float, default=DEFAULT_ROBOMASTER_SPEED)
    parser.add_argument("--robomaster-conn-type", default=DEFAULT_ROBOMASTER_CONN_TYPE)
    return parser


def create_wedge(h, w, cx, cy, start_ang, end_ang, r_min, r_max):
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (cx, cy), (r_max, r_max), 0, start_ang, end_ang, 255, -1)
    if r_min > 0:
        cv2.circle(mask, (cx, cy), r_min, 0, -1)
    return mask


def get_hud_masks(h, w, cx, cy, r1, r2, r3, rmax, ang_center):
    a_t_left, a_t_right = 270 - ang_center, 270 + ang_center
    a_b_left, a_b_right = 90 + ang_center, 90 - ang_center

    z_dritto = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(z_dritto, (cx, cy), r1, 255, -1)
    z_v100 = create_wedge(h, w, cx, cy, a_t_left, a_t_right, r1, rmax)

    z_stop_bottom = create_wedge(h, w, cx, cy, a_b_right, a_b_left, r1, rmax)
    z_stop_mid_sx = create_wedge(h, w, cx, cy, 180, a_t_left, r2, r3)
    z_stop_mid_dx = create_wedge(h, w, cx, cy, a_t_right, 360, r2, r3)
    z_stop_inf_sx = create_wedge(h, w, cx, cy, a_b_left, 180, r1, r3)
    z_stop_inf_dx = create_wedge(h, w, cx, cy, 0, a_b_right, r1, r3)
    z_stop = cv2.bitwise_or(
        z_stop_bottom,
        cv2.bitwise_or(
            z_stop_mid_sx,
            cv2.bitwise_or(z_stop_mid_dx, cv2.bitwise_or(z_stop_inf_sx, z_stop_inf_dx)),
        ),
    )

    z_indietro = cv2.bitwise_or(
        create_wedge(h, w, cx, cy, a_b_left, 180, r3, rmax),
        create_wedge(h, w, cx, cy, 0, a_b_right, r3, rmax),
    )
    z_av_sx = create_wedge(h, w, cx, cy, 180, a_t_left, r1, r2)
    z_sx = create_wedge(h, w, cx, cy, 180, a_t_left, r3, rmax)
    z_av_dx = create_wedge(h, w, cx, cy, a_t_right, 360, r1, r2)
    z_dx = create_wedge(h, w, cx, cy, a_t_right, 360, r3, rmax)

    return [z_dritto, z_v100, z_stop, z_indietro, z_av_sx, z_sx, z_av_dx, z_dx]


def draw_hud_lines(frame, cx, cy, w, r1, r2, r3, ang_center):
    a_t_left, a_t_right = 270 - ang_center, 270 + ang_center
    a_b_left, a_b_right = 90 + ang_center, 90 - ang_center

    c_blue = (255, 200, 0)
    c_red = (0, 0, 255)
    c_orange = (0, 165, 255)
    c_white = (255, 255, 255)
    f = cv2.FONT_HERSHEY_SIMPLEX

    cv2.circle(frame, (cx, cy), r1, c_blue, 2)
    for ang in [a_t_left, a_t_right, a_b_left, a_b_right]:
        rad = math.radians(ang)
        x2 = int(cx + 1000 * math.cos(rad))
        y2 = int(cy + 1000 * math.sin(rad))
        cv2.line(frame, (cx, cy), (x2, y2), c_blue, 2)
    cv2.line(frame, (0, cy), (w, cy), c_blue, 2)

    for r in [r2, r3]:
        cv2.ellipse(frame, (cx, cy), (r, r), 0, 180, a_t_left, c_red, 2)
        cv2.ellipse(frame, (cx, cy), (r, r), 0, a_t_right, 360, c_red, 2)
        cv2.ellipse(frame, (cx, cy), (r, r), 0, a_b_left, 180, c_red, 2)
        cv2.ellipse(frame, (cx, cy), (r, r), 0, 0, a_b_right, c_red, 2)

    cv2.putText(frame, "DRITTO", (cx - 35, cy + 5), f, 0.6, c_white, 2)
    cv2.putText(frame, "V 100", (cx - 30, cy - r1 - 40), f, 0.6, c_white, 2)
    cv2.putText(frame, "AV-SX", (cx - 110, cy - 20), f, 0.5, c_white, 2)
    cv2.putText(frame, "AV-DX", (cx + 50, cy - 20), f, 0.5, c_white, 2)
    cv2.putText(frame, "SX", (cx - 220, cy - 20), f, 0.7, c_white, 2)
    cv2.putText(frame, "DX", (cx + 180, cy - 20), f, 0.7, c_white, 2)
    cv2.putText(frame, "STOP", (cx - 10, cy + r1 + 100), f, 0.6, c_red, 2)
    cv2.putText(frame, "INDIETRO", (cx - 240, cy + 140), f, 0.6, c_orange, 2)
    cv2.putText(frame, "INDIETRO", (cx + 140, cy + 140), f, 0.6, c_orange, 2)


def bridge_triggered(distance_cm: float) -> bool:
    if DEFAULT_BRIDGE_TRIGGER_MAX_CM > DEFAULT_BRIDGE_TRIGGER_MIN_CM:
        return DEFAULT_BRIDGE_TRIGGER_MIN_CM <= distance_cm <= DEFAULT_BRIDGE_TRIGGER_MAX_CM
    return distance_cm >= DEFAULT_BRIDGE_TRIGGER_MIN_CM


def connect_transport(args):
    server_socket = None
    client_socket = None
    robomaster_api = None

    if args.transport == "tcp":
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen(1)
        server_socket.settimeout(0.05)
        print(f"SERVER AVVIATO su {args.host}:{args.port}. In attesa del rover...")
    elif args.transport == "robomaster":
        robomaster_api = RoboMasterCommandApi(
            robot_ip=args.robomaster_ip,
            speed=args.robomaster_speed,
            conn_type=args.robomaster_conn_type,
        )
        robomaster_api.connect()
        print("RoboMaster API connessa.")
    else:
        robomaster_api = SimRoboMasterCommandApi(
            robot_ip=args.robomaster_ip,
            speed=args.robomaster_speed,
            conn_type=args.robomaster_conn_type,
        )
        robomaster_api.connect()
        print("RoboMaster simulato connesso.")

    return server_socket, client_socket, robomaster_api


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    server_socket, client_socket, robomaster_api = connect_transport(args)

    capture = cv2.VideoCapture(args.camera)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, DEFAULT_FRAME_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, DEFAULT_FRAME_HEIGHT)
    if not capture.isOpened():
        raise RuntimeError(f"Impossibile aprire la webcam {args.camera}.")

    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    detector = aruco.ArucoDetector(aruco_dict, aruco.DetectorParameters())

    camera_matrix = np.array(DEFAULT_CAMERA_MATRIX, dtype=np.float32)
    dist_coeffs = np.array([DEFAULT_DIST_COEFFS], dtype=np.float32)
    obj_points = np.array(
        [
            [-args.marker_size_cm / 2, args.marker_size_cm / 2, 0],
            [args.marker_size_cm / 2, args.marker_size_cm / 2, 0],
            [args.marker_size_cm / 2, -args.marker_size_cm / 2, 0],
            [-args.marker_size_cm / 2, -args.marker_size_cm / 2, 0],
        ],
        dtype=np.float32,
    )

    hud_masks = None
    in_bridge_mode = False
    bridge_start_time = 0.0

    try:
        while True:
            ret, frame = capture.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2
            display_frame = frame.copy()

            if hud_masks is None or hud_masks[0].shape != (h, w):
                hud_masks = get_hud_masks(
                    h,
                    w,
                    cx,
                    cy,
                    DEFAULT_HUD_R1,
                    DEFAULT_HUD_R2,
                    DEFAULT_HUD_R3,
                    DEFAULT_HUD_RMAX,
                    DEFAULT_HUD_CENTER_ANGLE,
                )

            if args.transport == "tcp" and client_socket is None and server_socket is not None:
                try:
                    client_socket, addr = server_socket.accept()
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    print(f"Client connesso: {addr}")
                except Exception:
                    pass

            cmd = "STOP"
            v_mult = 0.0
            distanza_cm = 0.0
            stato_testo = "RICERCA MARKER..."
            colore_marker = (0, 0, 255)

            now = time.time()
            if in_bridge_mode:
                if now - bridge_start_time < DEFAULT_BRIDGE_JUMP_DURATION_SEC:
                    cmd = "W"
                    v_mult = DEFAULT_BRIDGE_JUMP_SPEED
                    stato_testo = "SALTO PONTE ATTIVO"
                    colore_marker = (0, 255, 255)
                else:
                    in_bridge_mode = False
                    print("Salto ponte completato.")

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = detector.detectMarkers(gray)

            if ids is not None and args.marker_id in ids:
                idx = np.where(ids == args.marker_id)[0][0]
                m_corners = corners[idx]

                success, _, tvec = cv2.solvePnP(obj_points, m_corners[0], camera_matrix, dist_coeffs)
                if success:
                    distanza_cm = float(tvec[2][0])

                    cv2.polylines(
                        display_frame,
                        [m_corners.astype(np.int32)],
                        True,
                        (255, 0, 0) if in_bridge_mode else colore_marker,
                        3,
                    )
                    cv2.putText(
                        display_frame,
                        f"DISTANZA: {int(distanza_cm)}cm",
                        (w - 230, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )

                    if not in_bridge_mode:
                        if bridge_triggered(distanza_cm):
                            in_bridge_mode = True
                            bridge_start_time = now
                            cmd = "W"
                            v_mult = DEFAULT_BRIDGE_JUMP_SPEED
                            stato_testo = "AVVIO SALTO PONTE"
                            colore_marker = (255, 255, 255)
                            print("INIZIO SALTO PONTE")
                        elif DEFAULT_DIST_MIN_GUIDE_CM <= distanza_cm <= DEFAULT_DIST_MAX_GUIDE_CM:
                            mask_aruco = np.zeros((h, w), dtype=np.uint8)
                            cv2.fillPoly(mask_aruco, [m_corners.astype(np.int32)], 255)
                            intersezioni = [cv2.countNonZero(cv2.bitwise_and(mask_aruco, m)) for m in hud_masks]

                            if sum(intersezioni) > DEFAULT_HUD_INTERSECTION_THRESHOLD:
                                z_idx = int(np.argmax(intersezioni))
                                zone_cmd = ZONE_CMDS[z_idx]
                                stato_testo = ZONE_NAMES[z_idx]
                                colore_marker = ZONE_COLORS[z_idx]

                                if zone_cmd == "W_MAX":
                                    cmd = "W"
                                    v_mult = DEFAULT_VEL_MAX
                                elif zone_cmd == "S":
                                    cmd = "S"
                                    v_mult = DEFAULT_VEL_REVERSE
                                elif zone_cmd == "STOP":
                                    cmd = "STOP"
                                    v_mult = 0.0
                                else:
                                    cmd = zone_cmd
                                    if distanza_cm < DEFAULT_DIST_SLOW_CM:
                                        v_mult = DEFAULT_VEL_SLOW
                                    elif distanza_cm <= DEFAULT_DIST_MEDIUM_CM:
                                        v_mult = DEFAULT_VEL_MEDIUM
                                    else:
                                        v_mult = DEFAULT_VEL_MAX
                        else:
                            stato_testo = "FUORI RANGE"

            draw_hud_lines(
                display_frame,
                cx,
                cy,
                w,
                DEFAULT_HUD_R1,
                DEFAULT_HUD_R2,
                DEFAULT_HUD_R3,
                DEFAULT_HUD_CENTER_ANGLE,
            )
            cv2.putText(display_frame, f"AZIONE: {stato_testo}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colore_marker, 2)

            try:
                if args.transport == "tcp":
                    if client_socket is not None:
                        dist_out = DEFAULT_BRIDGE_FAKE_DISTANCE_CM if in_bridge_mode else int(distanza_cm)
                        msg = f"{cmd},{v_mult},{dist_out}\n"
                        client_socket.sendall(msg.encode("utf-8"))
                elif robomaster_api is not None:
                    robomaster_api.send(cmd, speed_multiplier=v_mult)
            except Exception:
                if args.transport == "tcp":
                    client_socket = None

            cv2.imshow(args.window_title, display_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        try:
            if args.transport == "tcp" and client_socket is not None:
                client_socket.sendall("STOP,0.0,0\n".encode("utf-8"))
            if args.transport in ("robomaster", "robomaster-sim") and robomaster_api is not None:
                robomaster_api.send("STOP", speed_multiplier=0.0)
        except Exception:
            pass

        capture.release()
        cv2.destroyAllWindows()
        if client_socket is not None:
            client_socket.close()
        if server_socket is not None:
            server_socket.close()
        if robomaster_api is not None:
            robomaster_api.close()


if __name__ == "__main__":
    main()
