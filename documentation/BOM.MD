# DroneBotGiorgi - BOM (Bill of Materials)

## Scope

Questo documento unifica la BOM hardware delle tre varianti rover (Team 1 RoboMaster, Team 2 PiCar-X, Team 3 Arduino 4WD).

## Componenti hardware comuni

| # | Componente | Qt\u00e0 | Ruolo |
|---|---|---|---|
| 1 | DJI Neo 1 | 1 | Drone per acquisizione video e osservazione scena |
| 2 | Smartphone con DJI Fly | 1 | Ricezione feed O4 e bridge verso PC |
| 3 | PC/Laptop Windows | 1 | Esecuzione detector + server visione/guida |
| 4 | Cavo USB smartphone-PC | 1 | Collegamento ADB/scrcpy |
| 5 | ArUco marker (DICT_6X6_250, ID 0) | 1 | Target visivo per tracking rover |
| 6 | Router/AP Wi-Fi locale | 1 | Rete rover/PC (e RoboMaster quando usato) |

## Team 1 - RoboMaster EP Core

| # | Componente | Qt\u00e0 | Ruolo |
|---|---|---|---|
| 1 | DJI RoboMaster EP Core | 1 | Rover con controllo via SDK |

Note:
- Nessun SBC o MCU aggiuntivo richiesto sul rover.
- Ruote Mecanum e sensori ToF integrati nella piattaforma.

## Team 2 - PiCar-X

| # | Componente | Qt\u00e0 | Ruolo |
|---|---|---|---|
| 1 | SunFounder PiCar-X kit | 1 | Piattaforma rover |
| 2 | Raspberry Pi (4B/3B+/Zero 2W) | 1 | Esecuzione client Python rover |
| 3 | Robot HAT | 1 | Driver HW per motori/servo |
| 4 | Motori TT DC | 2 | Trazione |
| 5 | Servo sterzo | 1 | Sterzo asse anteriore |
| 6 | Ultrasuoni HC-SR04 | 1 | Anti-collisione locale |
| 7 | Batteria LiPo | 1 | Alimentazione rover |

## Team 3 - Arduino 4WD

| # | Componente | Qt\u00e0 | Ruolo |
|---|---|---|---|
| 1 | Keyestudio 4WD Smart Car V2.0 | 1 | Piattaforma rover |
| 2 | Arduino Uno R4 WiFi | 1 | Esecuzione firmware rover |
| 3 | Driver board DRV8833 (expansion) | 1 | Pilotaggio motori |
| 4 | Motori DC gear | 4 | Trazione differenziale |
| 5 | Ultrasuoni HC-SR04 | 1 | Anti-collisione locale |
| 6 | Chassis/ruote/cablaggio kit | 1 | Struttura meccanica |

## Materiali di supporto

- Marker ArUco stampabili: `tools/generate_markers.py` e output in `tools/printables/`.
- Parametri camera da calibrazione: generati programmaticamente da `tools/calibration.py` -> `tools/calibration_output.yaml`.
