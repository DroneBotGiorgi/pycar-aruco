# Fire Detect

Modulo del repository dedicato al rilevamento del fuoco nel flusso video del drone.

Ruolo nel flusso completo:
- prima il drone rileva il fuoco con questo modulo
- poi lo stesso drone usa il marker ArUco per guidare uno dei rover verso il target

Contenuto operativo:
- pipeline YOLO (acquisizione, detection, overlay, GUI)
- config YAML singolo
- modello di esempio in `fire_detect/models/best_test.pt`

## Architettura

- **Capture** — stream ADB `screenrecord --output-format=h264` decodificato via FFmpeg (`rawvideo`); nessuna duplicazione della finestra scrcpy
- **Detector** — wrapper Ultralytics YOLOv8 con switch modello a runtime
- **Overlay** — finestra OpenCV dedicata con bounding box persistenti (nessun lampeggio tra un'inferenza e la successiva)
- **GUI** — pannello Tkinter opzionale: hotkey `1..9` per switch rapido modello, slider live per `conf`, `iou`, `max_det`, `imgsz`, Hz inferenza
- **Hardware** — auto-detect: CUDA se disponibile, altrimenti CPU
- **Config** — YAML singolo `fire_detect/settings.yaml`

## Struttura

```
fire_detect/
├── main.py          # Entry point CLI
├── pipeline.py      # Loop capture → detect → overlay
├── capture.py       # Stream ADB+FFmpeg e webcam
├── detector.py      # Wrapper YoloDetector (model switch)
├── gui.py           # Pannello Tkinter opzionale
├── config.py        # Caricamento e validazione settings.yaml
├── settings.yaml    # Configurazione runtime
└── models/
    └── best_test.pt # Pesi YOLOv8 (fire detection)
```

## Prerequisiti

1. Android con USB debug attivo (o `adb tcpip`) per la sorgente ADB
2. Tool locali in `tools/`:
   - `tools/platform-tools/adb.exe`
   - `tools/ffmpeg/bin/ffmpeg.exe`
   - `tools/scrcpy/scrcpy.exe`
3. Modelli `.pt` in `fire_detect/models/`

## Avvio rapido

1. Installa dipendenze:

```powershell
python -m pip install -r fire_detect/requirements.txt
```

2. Avvia con webcam:

```powershell
python -m fire_detect.main --source webcam --webcam-index 0 --gui
```

3. Avvia con Android ADB (tool presenti in `tools/`):

```powershell
python -m fire_detect.main --source adb --gui
```

In VS Code è disponibile anche il profilo `Drone | Fire Detect`.

## Utilizzo runtime

- `q` — arresta la pipeline
- `1..9` — switch rapido al modello N-esimo del registry YAML

Dalla GUI (se avviata con `--gui`):

| Parametro | Descrizione |
|---|---|
| Modello | Switch checkpoint senza riavvio |
| `conf` | Soglia confidence (precisione vs recall) |
| `iou` | Soglia NMS (valori bassi riducono box sovrapposte) |
| `max_det` | Numero massimo di bounding box per frame |
| `imgsz` | Risoluzione inferenza YOLO (consigliato 640) |
| Hz | Frequenza inferenza; `0` = ogni frame |

Default consigliati (profilo preciso, box pulite):

```yaml
runtime:
  detection_conf_threshold: 0.6
  detection_iou_threshold: 0.30
  detection_max_det: 12
  yolo_interval_sec: 0.0   # inferenza a ogni frame
  detection_imgsz: 640
```

## Note su latenza

- Lo stream ADB entra come H264 e viene decodificato direttamente, senza catturare la finestra scrcpy
- Per ridurre la latenza:
  - aumenta `capture.bitrate_mbps`
  - abbassa la risoluzione (`use_original_resolution: false`)
  - aumenta `runtime.yolo_interval_sec` (es. `0.5` = YOLO ogni 500 ms)
  - usa GPU CUDA quando disponibile

Config runtime: `fire_detect/settings.yaml`
