import argparse
from pathlib import Path

import cv2
import cv2.aruco as aruco


def generate_single_marker(output_dir: Path, marker_id: int, size_px: int) -> Path:
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
    marker = aruco.generateImageMarker(dictionary, marker_id, size_px)
    out_path = output_dir / f"aruco_id{marker_id}_{size_px}px.png"
    cv2.imwrite(str(out_path), marker)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a single printable ArUco marker")
    default_out = Path(__file__).resolve().parent / "printables"
    parser.add_argument("--id", type=int, default=0, help="ArUco marker id")
    parser.add_argument("--size", type=int, default=900, help="Marker side in pixels")
    parser.add_argument("--out", default=str(default_out), help="Output folder")
    args = parser.parse_args()

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    single = generate_single_marker(output_dir, args.id, args.size)

    print(f"Generated: {single}")


if __name__ == "__main__":
    main()
