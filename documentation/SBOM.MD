# DroneBotGiorgi - SBOM (Software Bill of Materials)

## Scope

Questo documento unifica la Software BOM (SBOM) delle tre varianti rover.

## Codice sorgente principale (repository)

| Percorso | Ruolo |
|---|---|
| `detector/main.py` | Entry point detection target |
| `detector/pipeline.py` | Loop inferenza frame-by-frame |
| `detector/detector.py` | Wrapper YOLO |
| `detector/capture.py` | Input video ADB/webcam/RTMP |
| `detector/config.py` | Config runtime da YAML |
| `detector/gui.py` | Pannello controllo opzionale |
| `detector/settings.yaml` | Parametri detector |
| `server/server.py` | Tracking ArUco, solvePnP, logica HUD, dispatch comandi |
| `server/settings.py` | Parametri centralizzati di guida/rete/visione |
| `team1/robomaster_api.py` | Adapter SDK RoboMaster |
| `team1/simulator_api.py` | Adapter RoboMaster simulato |
| `team1/simulator_client.py` | Client rover simulato TCP |
| `team2/client_picar.py` | Client rover PiCar-X |
| `team3/client_arduino.c` | Firmware rover Arduino |
| `team3/settings.h` | Config firmware Arduino |
| `team3/arduino_c_compat.h` | Utility parsing firmware |
| `tools/calibration.py` | Calibrazione camera |
| `tools/generate_markers.py` | Generazione marker ArUco |

## Stack software lato PC (comune)

| Componente | Versione indicativa | Licenza | Ruolo |
|---|---|---|---|
| Python | 3.10+ | PSF | Runtime principale |
| opencv-contrib-python | >= 4.8 | Apache-2.0 | ArUco, solvePnP, rendering HUD |
| numpy | >= 1.24 | BSD-3-Clause | Calcolo numerico/matrici |
| ultralytics | >= 8.0 | AGPL-3.0 | Framework YOLOv8 |
| torch | >= 2.0 | BSD-style | Backend inferenza |
| PyYAML | >= 6.0 | MIT | Parsing config YAML |
| scrcpy | >= 2.0 | Apache-2.0 | Mirror smartphone |
| ADB | platform-tools | Apache-2.0 | Bridge smartphone-PC |
| socket / argparse / time / math | stdlib | PSF | Networking, CLI, temporizzazione |

## Software specifico Team 1 (RoboMaster)

| Componente | Versione indicativa | Licenza | Ruolo |
|---|---|---|---|
| Python | 3.8 | PSF | Runtime richiesto da SDK RoboMaster |
| robomaster SDK | vendor | Proprietaria DJI | Controllo chassis/sensori |

## Software specifico Team 2 (PiCar-X)

| Componente | Versione indicativa | Licenza | Ruolo |
|---|---|---|---|
| Python | 3.x | PSF | Runtime rover |
| picarx | corrente | MIT | API controllo PiCar-X |
| robot_hat | corrente | MIT | HAL GPIO/PWM per PiCar-X |
| socket/importlib | stdlib | PSF | TCP e import dinamico |

## Software specifico Team 3 (Arduino 4WD)

| Componente | Versione indicativa | Licenza | Ruolo |
|---|---|---|---|
| Arduino IDE | >= 2.0 | LGPL/Apache | Build e upload firmware |
| WiFiS3 | bundled R4 | LGPL | Wi-Fi e TCP su Uno R4 WiFi |
| Firmware custom (`team3/client_arduino.c`) | progetto | interna | Controllo rover e sicurezza locale |

## Artefatti modello

- Checkpoint runtime nel repository: `detector/models/*.pt`.
- Pipeline di training separata: https://github.com/DroneBotGiorgi/yolo-fire-detector.
