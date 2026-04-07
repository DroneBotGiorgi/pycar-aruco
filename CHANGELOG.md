# Changelog

All notable changes to pycar-aruco are documented here.

## [0.4.0] - 2026-04-07

### Added
- **Chase mode**: Target-based approach control—marker centering + distance estimation for autonomous pursuit.
- **Watchdog safety**: Client-side command timeout with automatic STOP to prevent runaway behavior on network silence.
- **Command heartbeat**: Server resends current command periodically to fix dpad freeze issue.
- **Visual rover simulator**: Test without hardware using `tools/simulator_client.py` with 2D animation.
- **Printable marker generator**: Create ArUco markers on demand with `tools/generate_markers.py`.
- **Centralized settings**: All parameters and tuning now in `settings.py` with full documentation.
- **Vscode launch profiles**: For different scenario, either real HW or simulation

## [0.1.0] - Initial commit

### Initial features
- Basic ArUco marker detection via OpenCV.
- D-pad orientation-based 4-way control (W/A/S/D/STOP).
- Chase mode with target centering and approach behavior.
- TCP server/client with simple command protocol.
- Picar-X hardware integration layer.
