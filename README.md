# pycar-aruco

![version](https://img.shields.io/badge/version-0.4.0-blue)

Questo progetto usa una webcam per leggere un marker ArUco e trasformarlo in comandi di guida inviati via TCP a un rover basato su Picar-X. Il protocollo resta volutamente semplice e stabile: `W`, `A`, `S`, `D`, `STOP`.

## Componenti

- `server.py`: acquisisce il video, rileva il marker ArUco e invia i comandi `W`, `A`, `S`, `D`, `STOP`.
- `client.py`: si collega al server TCP e converte i comandi in movimenti del rover con watchdog di sicurezza e riconnessione automatica.
- `settings.py`: file principale con tutti i parametri runtime, documentati in dettaglio.
- `tools/simulator_client.py`: client TCP con simulazione visiva 2D per test senza rover reale.
- `tools/generate_markers.py`: genera marker ArUco stampabili in `tools/printables`.

## Come funziona

Il server osserva un marker ArUco con ID configurabile. Sono disponibili due modalita:

- `dpad`: in base alla direzione del lato superiore del marker, il sistema divide la rotazione in quattro settori.
- `chase`: allinea il rover orizzontalmente al target e poi avanza verso una distanza obiettivo, con STOP automatico se il marker viene perso.

Per evitare che il rover si fermi quando il comando resta uguale (caso tipico in `dpad`), il server invia un heartbeat periodico del comando corrente.

In `dpad`, la mappatura e:

- alto -> `W` -> avanti
- destra -> `D` -> destra
- basso -> `S` -> indietro
- sinistra -> `A` -> sinistra

Se il marker non viene rilevato, il server invia `STOP`.

## Requisiti

### Server

- Python 3.10+
- OpenCV con modulo ArUco
- NumPy
- webcam collegata

Installazione tipica:

```bash
pip install opencv-contrib-python numpy
```

### Client

- Python 3.10+
- libreria `picarx`
- rover Picar-X configurato correttamente

## Avvio

### 1. Avviare il server sul PC con webcam

```bash
python server.py --host 0.0.0.0 --port 9999 --camera 0 --marker-id 0 --mode dpad
```

### 2. Avviare il client sul rover

Sostituisci `192.168.1.105` con l'IP del PC che esegue il server.

```bash
python client.py --host 192.168.1.105 --port 9999
```

Validazione senza hardware:

```bash
python client.py --host 192.168.1.105 --dry-run
```

Simulazione visiva senza hardware:

```bash
python tools/simulator_client.py --host 192.168.1.105 --port 9999
```

## Profili Launch VS Code

Nel file `.vscode/launch.json` sono disponibili profili separati per simulazione e hardware reale.

### Simulazione

- `Sim | Vision Server`: avvia `server.py` con parametri di tracking.
- `Sim | Visual Rover Client`: avvia `tools/simulator_client.py` senza hardware.
- `Sim | Full Stack (Server + Visual Client)`: avvio combinato server + simulatore.

### Hardware reale

- `HW | Vision Server`: avvia `server.py` per acquisizione camera reale.
- `HW | Rover Client (Picar-X)`: avvia `client.py` per pilotare il rover.

Ogni profilo usa input runtime modificabili al momento del lancio:

- rete: host/port, camera, marker-id, mode

Per tutti i parametri di tuning e sicurezza (server/client/simulatore), fai riferimento a `settings.py`.

## Uso pratico

- avvia prima il server
- avvia poi il client sul rover oppure il simulatore visivo
- usa `--mode dpad` per guida direzionale manuale a 4 direzioni
- usa `--mode chase` per inseguimento rapido del target con allineamento automatico
- premi `Q` sulla finestra del server per fermare il sistema

Quando il server termina, prova a inviare `STOP` al rover prima di chiudere la connessione.