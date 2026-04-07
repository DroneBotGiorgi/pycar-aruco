"""Centralized runtime settings for pycar-aruco.

Edit this file to tune behavior for both simulation and real hardware runs.
CLI flags still exist, but launch profiles now intentionally pass only a small subset
of arguments and rely on these defaults for day-to-day work.
"""

# Network settings
# Host used by server bind. Use 0.0.0.0 to accept connections from LAN clients.
DEFAULT_HOST = "0.0.0.0"
# TCP port used by server/client communication.
DEFAULT_PORT = 9999

# Vision input and target settings
# Camera index used by OpenCV VideoCapture.
DEFAULT_CAMERA_INDEX = 0
# ArUco ID to track.
DEFAULT_MARKER_ID = 0

# Control mode
# dpad: marker orientation drives W/A/S/D
# chase: target centering + size drives approach behavior
DEFAULT_MODE = "dpad"

# Chase tuning
# Normalized horizontal deadzone in range [0, 1].
# Larger values reduce steering oscillation but react slower to offset.
DEFAULT_DEADZONE_X = 0.12
# Desired marker area ratio (marker_area / frame_area).
# Smaller value keeps rover farther from target, larger value approaches more.
DEFAULT_TARGET_SIZE = 0.08
# Hysteresis around target size to avoid jittering between move/stop states.
DEFAULT_SIZE_TOLERANCE = 0.02
# Number of consecutive frames without marker before forcing STOP.
DEFAULT_LOST_STOP_FRAMES = 3
# Whether chase mode can emit reverse command when target is too close.
DEFAULT_ALLOW_REVERSE = False

# Command stream reliability
# Heartbeat interval: server resends current command at this period even if unchanged.
# This keeps clients alive under watchdog logic and fixes dpad hold behavior.
DEFAULT_COMMAND_HEARTBEAT_SEC = 0.20

# Rover actuation defaults (client)
# Base speed for movement commands.
DEFAULT_SPEED = 50
# Steering magnitude for A/D commands.
DEFAULT_STEERING_ANGLE = 30
# Use -1 or 1 based on hardware steering polarity.
DEFAULT_STEERING_INVERSION = -1

# Client safety watchdog
# If no valid command is received within this interval, client forces STOP.
DEFAULT_COMMAND_TIMEOUT = 0.8
# Socket read timeout used to periodically evaluate watchdog conditions.
DEFAULT_SOCKET_TIMEOUT = 0.2
# Delay before reconnect attempts after disconnect.
DEFAULT_RETRY_DELAY = 2.0

# Visualization
DEFAULT_WINDOW_TITLE = "Vision Server"
