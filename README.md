# DroneBotGiorgi

![version](https://img.shields.io/badge/version-1.0-blue)

Questo repository gestisce un flusso operativo in due fasi con lo stesso drone dotato di camera: prima rileva il fuoco, poi usa l'inquadratura del marker ArUco per guidare uno dei tre rover verso il punto rilevato. Il server supporta due backend: TCP per client esterni e API RoboMaster via SDK.

Per installazione, requisiti runtime, caveat RoboMaster e note di deployment, vedi [INSTALL.md](INSTALL.md).

## Componenti

- `server/server.py`: acquisisce il video, rileva il marker ArUco e invia comandi radar con protocollo `cmd,v_mult,distanza`.
- `server/settings.py`: file principale con i parametri runtime (rete, calibrazione camera, HUD, ponte, velocita, client).
- `team1/robomaster_api.py`: adapter API per RoboMaster con supporto comandi estesi e sicurezza ToF opzionale.
- `team2/client_picar.py`: client TCP Picar-X con parsing `cmd,v_mult,distanza`, anti ostacolo e riconnessione automatica.
- `team3/client_arduino.c`: firmware client TCP per rover Arduino con anti-lag, anti ostacolo e comandi estesi.
- `team3/settings.h`: configurazione centralizzata del client Arduino (Wi-Fi, server, pin, sensore, timing evasione).
- `team3/arduino_c_compat.h`: utility C minimale per confronto stringhe lato firmware Arduino.

- `fire_detect/`: modulo nativo del repository per rilevamento fuoco via pipeline YOLO su stream ADB, webcam o RTMP.

- `tools/simulator_client.py`: client TCP con simulazione visiva 2D per test senza rover reale.
- `tools/robomaster_sim_api.py`: adapter simulato per validare la logica RoboMaster senza hardware.
- `tools/generate_markers.py`: genera marker ArUco stampabili in `tools/printables`.

- `install.md`: guida completa a installazione, caveat runtime e deployment per i vari target.

## Come funziona

Fase 1: il drone esegue il modulo `fire_detect` per individuare il fuoco nel flusso video.

Fase 2: lo stesso drone, usando la camera che inquadra il marker ArUco, esegue `server/server.py` e guida il rover scelto verso il fuoco tramite backend PiCar, Arduino o RoboMaster.

Il server usa una logica radar a zone con HUD, stima distanza reale via `solvePnP` e calibrazione camera reale. La guida decide il comando in base alla zona ArUco e alla distanza, con velocita dinamica e modalita "salto ponte" temporizzata per ostacoli sospesi.

Protocollo TCP inviato ai client:

- `cmd,v_mult,distanza`
- comandi possibili: `W`, `W_MAX`, `S`, `A`, `D`, `WA`, `WD`, `STOP`
- `v_mult` e un moltiplicatore tra 0.0 e 1.0
- `distanza` e la distanza stimata in cm

## Profili Launch VS Code

Nel file `.vscode/launch.json` sono disponibili profili unificati per rilevamento, guida e simulazione.

### Rilevamento fuoco

- `Drone | Fire Detect`: avvia `fire_detect.main` con webcam e pannello GUI.

### Simulazione

- `Simulation | TCP Rover`: avvio combinato server TCP + rover simulato (`tools/simulator_client.py`).
- `Simulation | RoboMaster`: avvio server con backend RoboMaster simulato (senza hardware).

### Hardware reale

- `Drone | Guide PiCar`: avvia `server/server.py` per guidare il rover PiCar via TCP.
- `Drone | Guide Arduino`: avvia `server/server.py` per guidare il rover Arduino via TCP.
- `Drone | Guide RoboMaster`: avvia `server/server.py` con backend RoboMaster SDK.

Ogni profilo usa input runtime modificabili al momento del lancio:

- rete: host/port, camera, marker-id, mode

Per tutti i parametri di tuning e sicurezza (server/client/simulatore), fai riferimento a [server/settings.py](server/settings.py).

## Uso pratico

- avvia prima `Drone | Fire Detect` per trovare il fuoco
- poi avvia il profilo `Drone | Guide ...` del rover che vuoi mandare sul target
- se usi PiCar o Arduino, avvia poi il client sul rover; se sei in test usa uno dei profili `Simulation | ...`
- usa i parametri in `server/settings.py` per tuning rapido di calibrazione, ponte, velocita e sicurezza
- scegli il backend con `--transport tcp|robomaster|robomaster-sim`
- premi `Q` sulla finestra del server per fermare il sistema

Quando il server termina, prova a inviare `STOP` al rover prima di chiudere la connessione.

## Struttura del repository

```
DroneBotGiorgi/
├── server/
│   ├── server.py          # Server principale: visione, ArUco, HUD, comandi
│   └── settings.py        # Tutti i parametri runtime
├── fire_detect/
│   ├── main.py            # Entry point CLI (--source, --conf, --gui)
│   ├── pipeline.py        # Loop rilevamento frame → YOLOv8 → output
│   ├── detector.py        # Wrapper YoloDetector
│   ├── capture.py         # Sorgenti video: ADB, webcam, RTMP
│   ├── gui.py             # Pannello Tkinter opzionale
│   ├── settings.yaml      # Configurazione default
│   └── models/best_test.pt  # Pesi YOLOv8
├── team1/
│   └── robomaster_api.py  # Adapter SDK DJI (chassis.drive_speed)
├── team2/
│   └── client_picar.py    # Client TCP rover PiCar-X
├── team3/
│   ├── client_arduino.c   # Firmware Arduino (TCP, motori, ultrasuoni)
│   ├── settings.h         # Costanti compilate (Wi-Fi, pin, soglie)
│   └── arduino_c_compat.h # Utility C per parsing comandi
├── tools/
│   ├── calibration.py         # Calibrazione telecamera drone (chessboard → camera_matrix)
│   ├── calibration_output.yaml  # Output calibrazione (generato da calibration.py)
│   ├── simulator_client.py    # Client simulato 2D
│   ├── robomaster_sim_api.py  # RoboMaster simulato
│   └── generate_markers.py   # Generatore marker ArUco
├── documentation/
│   ├── team1/
│   │   ├── team1_flusso.md
│   │   ├── team1_flowchart.md
│   │   └── team1_bom_sbom.md
│   ├── team2/
│   │   ├── team2_flusso.md
│   │   ├── team2_flowchart.md
│   │   └── team2_bom_sbom.md
│   └── team3/
│       ├── team3_flusso.md
│       ├── team3_flowchart.md
│       └── team3_bom_sbom.md
├── README.md              # README tecnico con protocollo e profili launch
├── INTRO.md               # Questo file: introduzione e guida rapida
└── INSTALL.md             # Installazione e deployment completo
```

---