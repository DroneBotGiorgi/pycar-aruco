# BOM e SBOM — Soluzione DJI RoboMaster EP Core

---

## BOM — Bill of Materials (Hardware)

| # | Componente | Descrizione | Qtà | Note |
|---|---|---|---|---|
| 1 | DJI Neo 1 | Drone; camera 1/2″ CMOS 12 MP; trasmissione video O4; peso ~135 g | 1 | Unico drone ammesso dalla gara |
| 2 | Smartphone | Esegue DJI Fly; riceve feed O4 dal drone; connesso al PC via USB | 1 | Qualsiasi Android/iOS compatibile con DJI Fly |
| 3 | PC / Laptop | Server Python; elaborazione video + ArUco + YOLO; chiama SDK RoboMaster direttamente | 1 | GPU NVIDIA CUDA consigliata; **Python 3.8 obbligatorio** per SDK RoboMaster |
| 4 | Cavo USB | Connessione smartphone → PC per ADB | 1 | Tipo adeguato al modello smartphone |
| 5 | DJI RoboMaster EP Core | Rover terrestre; 4 motori indipendenti su ruote Mecanum omnidirezionali; Wi-Fi integrato | 1 | Controllato direttamente via SDK dal PC; nessun client separato |
| 6 | ArUco Marker | Stampa min 25×25 cm; dizionario DICT_6X6_250 ID 0 | 1 | Stampabile da `tools/generate_markers.py` |
| 7 | Router Wi-Fi | Rete locale 2.4/5 GHz condivisa tra PC e RoboMaster EP | 1 | IP RoboMaster default: `192.168.1.101` (configurabile in `settings.py`) |

**Nota**: non è necessario alcun hardware di controllo aggiuntivo sul rover (niente Raspberry Pi, niente Arduino); il RoboMaster EP Core ha tutta l'elettronica integrata e il PC lo comanda direttamente via SDK.

---

## SBOM — Software Bill of Materials

### Codice sorgente del repository

| File | Ruolo |
|---|---|
| `server/server.py` | Server principale: acquisizione video, rilevamento ArUco, calcolo distanza via solvePnP, HUD 8 zone, chiamata diretta SDK |
| `server/settings.py` | Unica fonte di verità per tutti i parametri runtime (rete, HUD, distanze, bridge mode, velocità RoboMaster) |
| `detector/main.py` | Entry point CLI del modulo fire detection |
| `detector/pipeline.py` | Loop di rilevamento frame-per-frame |
| `detector/detector.py` | Wrapper `YoloDetector`: carica il modello `.pt`, esegue inferenza |
| `detector/capture.py` | Sorgenti video: ADB/scrcpy, webcam, RTMP |
| `detector/config.py` | Caricamento configurazione da `settings.yaml` |
| `detector/gui.py` | Pannello Tkinter opzionale |
| `detector/settings.yaml` | Configurazione default fire detection |
| `detector/models/best_test.pt` | Pesi YOLOv8 addestrati per rilevamento fuoco |
| `team1/robomaster_api.py` | Adapter SDK: converte comandi simbolici (W/A/D/…) in `chassis.drive_speed(x,y,z)`; gestisce ToF asincrono opzionale |
| `team1/simulator_api.py` | Adapter simulato RoboMaster: valida la logica senza hardware fisico |
| `team1/simulator_client.py` | Client TCP simulato per test pipeline visione |
| `tools/generate_markers.py` | Generatore marker ArUco stampabili |

### Dipendenze Python — lato PC (venv `.venv-robomaster38`, Python 3.8 obbligatorio)

| # | Pacchetto | Versione consigliata | Licenza | Ruolo |
|---|---|---|---|---|
| 1 | Python | **3.8** | PSF | Unica versione compatibile con la wheel RoboMaster SDK |
| 2 | robomaster | SDK DJI ufficiale | Proprietaria DJI | Controllo chassis EP Core: `robot.initialize`, `chassis.drive_speed`, `sensor.sub_distance` |
| 3 | opencv-contrib-python | ≥ 4.8 | Apache 2.0 | Visione artificiale: cattura frame, rilevamento ArUco, solvePnP, HUD |
| 4 | numpy | ≥ 1.24 | BSD 3-Clause | Calcolo numerico; matrici camera; maschere HUD |
| 5 | ultralytics | ≥ 8.0 | AGPL-3.0 | Framework YOLOv8 per fire detection |
| 6 | torch (PyTorch) | ≥ 2.0 | BSD | Backend inferenza YOLO; opzionale GPU CUDA |
| 7 | PyYAML | ≥ 6.0 | MIT | Parsing `detector/settings.yaml` |
| 8 | scrcpy | ≥ 2.0 | Apache 2.0 | Mirror video smartphone → virtual camera sul PC |
| 9 | ADB (Android Debug Bridge) | — | Apache 2.0 | Bridge USB smartphone-PC; richiesto da scrcpy |
| 10 | socket (stdlib) | — | PSF | Non usato per la guida RoboMaster (nessun TCP verso rover), presente solo nel server base |
| 11 | argparse (stdlib) | — | PSF | CLI server e detector |
| 12 | time, math (stdlib) | — | PSF | Timing bridge mode, calcoli geometrici HUD |
