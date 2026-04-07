# Changelog

All notable changes to pycar-aruco are documented here.

## [0.4.0] - 2026-04-07

### Added
- **Command heartbeat**: Server now resends current command periodically (default 200ms) to keep client watchdog alive, fixing dpad freeze behavior when marker orientation remains static.
- **Settings-based configuration**: New `settings.py` as single source of truth for all runtime parameters with detailed docstrings for each setting.
- **Visual simulator client**: `tools/simulator_client.py` provides 2D rover animation for testing without hardware (includes TCP connectivity testing).
- **Marker generator utility**: `tools/generate_markers.py` generates printable ArUco markers (single marker or A4 sheet at 300 DPI).
- **Simplified launch profiles**: Reduced VS Code debug inputs to essentials (host/port/camera/marker-id/mode); tuning now via `settings.py`.
- **Project organization**: Moved simulator and marker tools into `tools/` folder for cleaner structure.
- **`.gitignore`**: Proper Python/venv/cache exclusions; shared only `launch.json` from `.vscode/`.

### Changed
- **Default mode**: Switched from `chase` to `dpad` as default for initial testing.
- **README**: Consolidated parameter documentation; now points to `settings.py` for detailed tuning reference.
- **Config layer**: `config.py` removed entirely; all imports now directly use `settings.py`.
- **Version badge**: Updated README to 0.4.0 for visibility.

### Fixed
- **dpad stalling bug**: With command heartbeat, rover no longer stops when marker stays in same orientation.
- **OpenCV typing**: Fixed `contourArea` and `polylines` type issues in chase mode.

### Technical Details
- Server imports centralized on `settings` module.
- Client includes watchdog timeout with STOP auto-trigger on network silence.
- Simulator integrates proper import paths and heartbeat-aware client logic.

## [0.1.0] - Initial commit

### Initial features
- Basic ArUco marker detection via OpenCV.
- D-pad orientation-based 4-way control (W/A/S/D/STOP).
- Chase mode with target centering and approach behavior.
- TCP server/client with simple command protocol.
- Picar-X hardware integration layer.
