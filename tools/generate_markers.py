import argparse
from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np


def generate_single_marker(output_dir: Path, marker_id: int, size_px: int) -> Path:
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    marker = aruco.generateImageMarker(dictionary, marker_id, size_px)
    out_path = output_dir / f"aruco_id{marker_id}_{size_px}px.png"
    cv2.imwrite(str(out_path), marker)
    return out_path


def generate_a4_sheet(output_dir: Path, marker_id: int, marker_px: int) -> Path:
    # A4 at 300 DPI: 2480 x 3508 px
    width, height = 2480, 3508
    sheet = np.full((height, width), 255, dtype=np.uint8)

    dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    marker = aruco.generateImageMarker(dictionary, marker_id, marker_px)

    positions = [
        (220, 220),
        (width - 220 - marker_px, 220),
        (220, height - 220 - marker_px),
        (width - 220 - marker_px, height - 220 - marker_px),
        ((width - marker_px) // 2, (height - marker_px) // 2),
    ]

    for x, y in positions:
        sheet[y : y + marker_px, x : x + marker_px] = marker

    out_path = output_dir / f"aruco_id{marker_id}_A4_300dpi.png"
    cv2.imwrite(str(out_path), sheet)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate printable ArUco markers")
    default_out = Path(__file__).resolve().parent / "printables"
    parser.add_argument("--id", type=int, default=0, help="ArUco marker id")
    parser.add_argument("--size", type=int, default=900, help="Marker side in pixels")
    parser.add_argument("--out", default=str(default_out), help="Output folder")
    args = parser.parse_args()

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    single = generate_single_marker(output_dir, args.id, args.size)
    sheet = generate_a4_sheet(output_dir, args.id, min(args.size, 900))

    print(f"Generated: {single}")
    print(f"Generated: {sheet}")


if __name__ == "__main__":
    main()
