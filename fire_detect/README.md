# fire_detect

Modulo del repository dedicato al rilevamento del fuoco nel flusso video del drone.

Ruolo nel flusso completo:
- prima il drone rileva il fuoco con questo modulo
- poi lo stesso drone usa il marker ArUco per guidare uno dei rover verso il target

Contenuto operativo:
- pipeline YOLO (acquisizione, detection, overlay, GUI)
- config YAML singolo
- modello di esempio in fire_detect/models/best_test.pt

## Avvio rapido

1. Installa dipendenze:

```powershell
python -m pip install -r fire_detect/requirements.txt
```

2. Avvia con webcam:

```powershell
python -m fire_detect.main --source webcam --webcam-index 0 --gui
```

3. Avvia con Android ADB + FFmpeg (se i tool sono presenti in tools/):

```powershell
python -m fire_detect.main --source adb --gui
```

In VS Code e disponibile anche il profilo `Drone | Fire Detect`.

Config runtime: fire_detect/settings.yaml
