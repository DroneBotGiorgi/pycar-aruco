# DroneBotGiorgi — Guida e rilevamento incendi con drone e rover

![version](https://img.shields.io/badge/version-1.0-blue)

Un drone DJI Neo 1 sorvola un'arena, individua una fonte di fuoco con un modello YOLO addestrato su misura, poi si trasforma in sistema di guida visiva: inquadra il rover a terra e lo pilota fino al punto rilevato, usando il solo segnale video come unico sensore. Tutto il sistema gira su un PC Windows standard, senza hardware proprietario aggiuntivo.

Il progetto supporta tre rover intercambiabili — **SunFounder PiCar-X**, **Keyestudio 4WD + Arduino Uno R4 WiFi**, **DJI RoboMaster EP Core** — con la stessa pipeline di visione del drone e protocollo di comando unificato.

---

## Cosa rende questo progetto originale

### Il drone fa due cose con lo stesso hardware

Nessuna telecamera fissa, nessun sensore a terra. Il DJI Neo 1 è fire detector nella prima fase e sistema di guida visiva nella seconda. La stessa catena **drone → O4 → smartphone → ADB/scrcpy → virtual camera PC** viene riusata da entrambi i moduli senza alcuna riconfigurazione: un smartphone qualsiasi e un cavo USB bastano a portare il video del drone dentro OpenCV.

### Rilevamento fuoco con YOLOv8 addestrato per la competizione

Il modello di rilevamento fuoco non è un modello generico. È stato addestrato con una pipeline dedicata, disponibile su [`DroneBotGiorgi/yolo-fire-detector`](https://github.com/DroneBotGiorgi/yolo-fire-detector), progettata specificamente per scenari come questo:

- **Dataset sintetico senza etichettatura manuale** — Immagini di fuoco reale vengono composte programmaticamente su sfondi variabili (anche tematici, simili all'arena e scaricati automaticamente da Unsplash), con augmentazioni geometriche e fotometriche parametrizzate via YAML.
- **Hard negative mining automatico** — La pipeline analizza footage reale del drone e ne estrae frame senza fuoco da includere nel training come hard negative, abbattendo i falsi positivi su scenari simili all'arena.
- **Preset specializzati** — Profili YAML preconfigurati (`fuochi-piccoli.yaml`, `anti-falsi-positivi.yaml`, `alta-recall.yaml`) permettono di ottimizzare sensibilità e precisione senza riscrivere nulla.
- **Training cloud-first** — Il bundle viene preparato localmente e addestrato su Google Colab con GPU CUDA. Il modello esportato viene referenziato da un puntatore `latest.yaml`, aggiornabile senza modificare il codice.
- **Confidence a runtime** — La soglia `--conf` è configurabile a ogni avvio: alzarla riduce i falsi positivi, abbassarla aumenta la sensibilità, senza rigenerare il modello.

### HUD a 8 zone bitmap invece di PID

La guida del rover non usa un controllore proporzionale classico. Il frame video viene partizionato in settori geometrici (un cerchio centrale, wedge angolari, fasce perimetrali) e il marker ArUco viene localizzato intersecando la sua maschera bitmap con quelle delle zone tramite `cv2.bitwise_and` e `np.argmax`. La zona con più pixel in comune determina il comando. Approccio non convenzionale, robusto ai rumori visivi, sintonizzabile modificando solo le geometrie delle zone in `server/settings.py`.

### Bridge mode: navigazione cieca temporizzata

Quando il marker sparisce dal campo visivo (tratto senza visibilità, marker coperto), il sistema entra in **bridge mode**: avanzamento forzato a velocità massima per due secondi fissi. Nessun sistema di localizzazione alternativo, nessun sensore aggiuntivo. Copre autonomamente il tratto di perdita del segnale.

### Protocollo unificato, rover intercambiabili

Il server emette sempre lo stesso messaggio: `cmd,v_mult,distanza`. I comandi (`W`, `S`, `A`, `D`, `WA`, `WD`, `STOP`) e il moltiplicatore di velocità `v_mult ∈ [0.0, 1.0]` sono identici per tutte le soluzioni. La velocità si adatta automaticamente alla distanza: il rover accelera quando è lontano, rallenta avvicinandosi. Cambiare rover richiede solo di avviare un diverso client.

### Parsing last-message-only

Sia il client Python (PiCar) sia il firmware C (Arduino) leggono tutto il buffer TCP disponibile e processano **solo l'ultimo messaggio completo**, scartando quelli in coda. Il rover risponde sempre allo stato più recente del frame, senza accumulare ordini obsoleti.

### Calibrazione reale della telecamera del drone

La stima della distanza via `cv2.solvePnP` è tanto più precisa quanto più i parametri intrinseci della telecamera rispecchiano la realtà. Invece di usare valori sintetici o approssimati, il progetto include `tools/calibration.py`: uno script di calibrazione che acquisisce frame di una scacchiera stampata dal vivo, calcola `camera_matrix` e `dist_coeffs` tramite `cv2.calibrateCamera`, e salva i risultati in un file YAML pronto all'uso.

La calibrazione è eseguibile prima di ogni gara in pochi minuti e migliora la precisione delle soglie di distanza (ponte, STOP, approccio finale) su qualsiasi telecamera.

---

## Le tre soluzioni hardware

| Soluzione | Rover | Client | Documentazione |
|---|---|---|---|
| **PiCar-X** | SunFounder PiCar-X su Raspberry Pi | Python (`team2/client_picar.py`) | [`documentation/team2/team2_flusso.md`](documentation/team2/team2_flusso.md) |
| **Arduino** | Keyestudio 4WD su Arduino Uno R4 WiFi | Firmware C (`team3/client_arduino.c`) | [`documentation/team3/team3_flusso.md`](documentation/team3/team3_flusso.md) |
| **RoboMaster** | DJI RoboMaster EP Core (ruote Mecanum) | SDK DJI diretta (`team1/robomaster_api.py`) | [`documentation/team1/team1_flusso.md`](documentation/team1/team1_flusso.md) |

La soluzione RoboMaster è l'unica senza client separato sul rover: il server Python chiama direttamente la SDK DJI, controlando il chassis in m/s e °/s invece di PWM.

---

## Come lanciare il progetto

### 1. Installazione

Leggi [`INSTALL.md`](INSTALL.md) per setup completo. In sintesi:

```powershell
# Stack principale (server, PiCar, simulatore)
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install opencv-contrib-python numpy ultralytics torch pyyaml

# Stack RoboMaster (Python 3.8 obbligatorio)
py -3.8 -m venv .venv-robomaster38
.\.venv-robomaster38\Scripts\python.exe -m pip install robomaster
```

### 2. Rilevamento fuoco (Fase 1)

Avvia il profilo **`Drone | Fire Detect`** da VS Code, oppure:

```powershell
python -m detector.main --source webcam --webcam-index 0 --gui
```

### 3. Guida rover (Fase 2)

Avvia il profilo VS Code corrispondente al rover in uso:

| Rover | Profilo VS Code | Avvio manuale |
|---|---|---|
| PiCar-X | `Drone \| Guide PiCar` | `python server/server.py --transport tcp` |
| Arduino | `Drone \| Guide Arduino` | `python server/server.py --transport tcp` |
| RoboMaster | `Drone \| Guide RoboMaster` | `python server/server.py --transport robomaster` |

Per PiCar e Arduino, avvia poi il client sul rover (Raspberry Pi o upload firmware Arduino).

### 4. Simulazione (senza hardware)

| Profilo VS Code | Cosa simula |
|---|---|
| `Simulation \| TCP Rover` | Server TCP + rover simulato 2D |
| `Simulation \| RoboMaster` | Server + RoboMaster simulato (no hardware) |

---
