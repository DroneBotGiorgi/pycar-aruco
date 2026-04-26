"""
Camera calibration utility for rover-aruco.

Acquires frames of a chessboard pattern from the drone virtual camera (or any
webcam), computes the camera intrinsics via cv2.calibrateCamera, prints the
results ready to paste into server/settings.py, and saves them to a YAML file
readable by cv2.FileStorage.

Usage:
    python tools/calibration.py [--webcam-index 0] [--rows 6] [--cols 9]
                                 [--square-size 2.5] [--output tools/calibration_output.yaml]

Controls during capture:
    SPACE  — save current frame (capture at least 15 frames in different positions/angles)
    ENTER  — compute calibration with saved frames
    q      — quit without computing

Setup:
    1. Print a standard OpenCV chessboard (9×6 inner corners) at 100% scale on A4.
    2. Glue it to a rigid, flat surface so it does not bend.
    3. Measure the side of a single square in cm; pass it as --square-size.
    4. Point the drone camera (via ADB/scrcpy virtual camera) at the board and
       move it to 10-15 different positions/angles while pressing SPACE.
    5. Press ENTER to compute; copy the printed values into server/settings.py.
"""

import argparse
import sys

import cv2
import numpy as np

MIN_FRAMES = 5  # absolute minimum; 15+ recommended


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chessboard camera calibration for rover-aruco.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--webcam-index", type=int, default=0, metavar="N",
                        help="OpenCV VideoCapture device index")
    parser.add_argument("--rows", type=int, default=6, metavar="N",
                        help="Inner corners along the short side of the board")
    parser.add_argument("--cols", type=int, default=9, metavar="N",
                        help="Inner corners along the long side of the board")
    parser.add_argument("--square-size", type=float, default=2.5, metavar="CM",
                        help="Physical side length of one square in centimetres")
    parser.add_argument("--output", default="tools/calibration_output.yaml",
                        metavar="PATH",
                        help="File path to save the calibration YAML")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _object_points(rows: int, cols: int, square_size: float) -> np.ndarray:
    """3-D coordinates of the chessboard corners in the board reference frame."""
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    return objp * square_size


def _save_yaml(path: str, mtx: np.ndarray, dist: np.ndarray, rms: float) -> None:
    fs = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    fs.write("rms_error", float(rms))
    fs.write("camera_matrix", mtx)
    fs.write("dist_coeffs", dist)
    fs.release()


def _print_results(mtx: np.ndarray, dist: np.ndarray, rms: float) -> None:
    print("\n=== CALIBRAZIONE COMPLETATA ===")
    print(f"Errore RMS: {rms:.4f}  (< 1.0 è ottimo, < 0.5 è eccellente)")
    print("\nCopia questi valori in server/settings.py:\n")
    print("camera_matrix = np.array(")
    print(repr(mtx))
    print(", dtype=np.float32)\n")
    print("dist_coeffs = np.array(")
    print(repr(dist))
    print(", dtype=np.float32)")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    rows, cols = args.rows, args.cols
    objp_template = _object_points(rows, cols, args.square_size)

    objpoints: list[np.ndarray] = []
    imgpoints: list[np.ndarray] = []
    frame_size: tuple[int, int] | None = None

    cap = cv2.VideoCapture(args.webcam_index)
    if not cap.isOpened():
        print(
            f"Errore: impossibile aprire la telecamera (index {args.webcam_index}).",
            file=sys.stderr,
        )
        return 1

    print("Premi SPAZIO per salvare un frame (ne servono almeno 15 in posizioni diverse).")
    print("Premi INVIO per calcolare la calibrazione.")
    print("Premi 'q' per uscire senza salvare.\n")

    subpix_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Errore: impossibile leggere dalla telecamera.", file=sys.stderr)
            break

        if frame_size is None:
            h, w = frame.shape[:2]
            frame_size = (w, h)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, (cols, rows), None)

        display = frame.copy()
        if found:
            corners_sub = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), subpix_criteria)
            cv2.drawChessboardCorners(display, (cols, rows), corners_sub, found)
            cv2.putText(
                display, "SCACCHIERA TROVATA — Premi SPAZIO per salvare",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
            )
        else:
            cv2.putText(
                display, "Cercando scacchiera...",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
            )

        cv2.putText(
            display, f"Frame salvati: {len(objpoints)}",
            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2,
        )
        cv2.imshow("Calibrazione — rover-aruco", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(" "):  # SPACE — capture
            if found:
                objpoints.append(objp_template)
                imgpoints.append(corners_sub)
                print(f"  Frame salvato! Totale: {len(objpoints)}")
            else:
                print("  Nessuna scacchiera visibile in questo frame.")

        elif key in (13, 10):  # ENTER — compute
            if len(objpoints) < MIN_FRAMES:
                print(f"  Servono almeno {MIN_FRAMES} frame. Catturane altri.")
            else:
                print("\nCalcolo calibrazione in corso — attendere...")
                cap.release()
                cv2.destroyAllWindows()
                rms, mtx, dist, _, _ = cv2.calibrateCamera(  # type: ignore[call-overload]
                    objpoints, imgpoints, frame_size,
                    None,  # type: ignore[arg-type]
                    None,  # type: ignore[arg-type]
                )
                _print_results(mtx, dist, rms)
                _save_yaml(args.output, mtx, dist, rms)
                print(f"\nRisultati salvati in: {args.output}")
                return 0

        elif key == ord("q"):
            print("Uscita senza salvare.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    return run(_parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
