# Changelog

All notable changes to rover-aruco are documented here.

## [0.5.1] - 2026-04-07

### Added
- **RoboMaster sim adapter**: Added `tools/robomaster_sim_api.py` to simulate RoboMaster command dispatch without hardware.
- **Sim launch profile**: Added `Sim | Vision Server (RoboMaster Sim API)` for no-device validation of RoboMaster mapping logic.

### Changed
- **RoboMaster resilience**: `server.py` now degrades to vision-only mode if RoboMaster connect/send fails, instead of aborting the session.
- **Heartbeat control**: Heartbeat resend is now explicitly disable-able with `--command-heartbeat-sec <= 0`.
- **Launch consistency**: Reordered launch profiles (all Sim first, then HW) and aligned naming for clarity.

## [0.5.0] - 2026-04-07

### Added
- **Arduino TCP client integration**: Added dedicated firmware client `client_arduino.c` with centralized configuration in `settings.h`.
- **RoboMaster API integration**: Added `robomaster_api.py` and `server.py --transport robomaster` backend for direct SDK command dispatch.
- **RoboMaster dedicated runtime profile**: Added Python 3.8 isolated environment flow and launch profile for RoboMaster API execution.

### Changed
- **Documentation split**: Installation/deployment moved to `install.md`, while `README.md` now focuses on product features and usage behavior.

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
