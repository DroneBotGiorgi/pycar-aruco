# DroneBotGiorgi - INSTALLAZIONE E DEPLOYMENT

![version](https://img.shields.io/badge/version-1.0-blue)

Questa guida raccoglie tutte le istruzioni di installazione e i caveat runtime.
Il file [README.MD](README.MD) descrive il flusso completo: il drone rileva il fuoco e poi guida il rover selezionato verso il target usando il marker ArUco.

## 1. Prerequisiti

- Windows 10/11
- Python 3.10 per stack principale (server TCP, simulatore, client PyCar)
- Python 3.8 per stack RoboMaster API
- Webcam per il server vision

## 2. Setup base progetto (Python 3.10)

Crea e attiva il venv principale:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installa dipendenze principali:

```powershell
python -m pip install --upgrade pip
python -m pip install opencv-contrib-python numpy
```

## 3. Setup RoboMaster (venv separato Python 3.8)

Per questo workspace e consigliato un venv separato: il pacchetto `robomaster`
risulta installabile con wheel su Python 3.8, mentre su Python 3.10 non e disponibile
una wheel compatibile in questa macchina.

```powershell
py -3.8 -m venv .venv-robomaster38
.\.venv-robomaster38\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-robomaster38\Scripts\python.exe -m pip install --index-url https://pypi.org/simple robomaster
```

Verifica import SDK:

```powershell
.\.venv-robomaster38\Scripts\python.exe -c "from robomaster import robot; print('robomaster-import-ok')"
```

### Caveat RoboMaster

- Se compare errore legato a `libmedia_codec`, seguire la sezione Windows della doc ufficiale RoboMaster SDK e installare i runtime VC richiesti.
- Repo ufficiale: https://github.com/dji-sdk/RoboMaster-SDK
- Doc installazione: https://robomaster-dev.readthedocs.io/en/latest/python_sdk/installs.html

## 4. Deployment: PyCar (TCP client)

Flusso operativo:

1. Avvia [server/server.py](server/server.py) sul PC con webcam (venv principale `.venv`).
2. Avvia [team2/client_picar.py](team2/client_picar.py) sul rover PiCar.

Esempio server:

```powershell
python -m server.server --host 0.0.0.0 --port 9999 --camera 0 --marker-id 0
```

Esempio client PyCar:

```powershell
python -m team2.client_picar --host 192.168.1.105 --port 9999
```

## 5. Deployment: Arduino (TCP client)

File firmware: [team3/client_arduino.c](team3/client_arduino.c)

Configurazione centralizzata firmware:

- rete, pin e velocita in [team3/settings.h](team3/settings.h)

Passi:

1. Compila e carica [team3/client_arduino.c](team3/client_arduino.c) sulla board Arduino con WiFi.
2. Avvia [server/server.py](server/server.py) sul PC (venv principale `.venv`) con transport TCP (default).

## 6. Deployment: RoboMaster API (senza client TCP separato)

Flusso operativo:

1. Avvia [server/server.py](server/server.py) in modalita `--transport robomaster`.
2. Usa il venv dedicato `.venv-robomaster38`.

Esempio:

```powershell
.\.venv-robomaster38\Scripts\python.exe -m server.server --transport robomaster --camera 0 --marker-id 0 --robomaster-ip 192.168.1.101 --robomaster-speed 0.5
```

In VS Code e gia presente il profilo launch dedicato RoboMaster che usa quel venv.

## 7. Simulazione senza hardware

Per test funzionale del protocollo comandi senza rover reale:

```powershell
python team1/simulator_client.py --host 127.0.0.1 --port 9999
```

Per testare il mapping RoboMaster senza device fisico:

```powershell
python -m server.server --transport robomaster-sim --camera 0 --marker-id 0 --robomaster-speed 0.5
```

Puoi anche usare direttamente i due profili launch di simulazione in [.vscode/launch.json](.vscode/launch.json):

- `Simulation | TCP Rover`
- `Simulation | RoboMaster`

## 8. Modulo Fire Detect integrato

La cartella [detector](detector) fa parte del repository e contiene il modulo di rilevamento fuoco usato dal drone nella prima fase operativa.

Installa dipendenze dedicate:

```powershell
python -m pip install -r detector/requirements.txt
```

Avvio rapido webcam:

```powershell
python -m detector.main --source webcam --webcam-index 0 --gui
```

Avvio con Android ADB + FFmpeg (se i tool sono disponibili in `tools/`):

```powershell
python -m detector.main --source adb --gui
```

In VS Code puoi avviare direttamente il profilo `Drone | Fire Detect`.
