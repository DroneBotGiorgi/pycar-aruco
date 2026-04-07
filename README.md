# rover-aruco

![version](https://img.shields.io/badge/version-0.5.1-blue)

Questo progetto usa una webcam per leggere un marker ArUco e trasformarlo in comandi di guida. Il server supporta due backend: TCP (`W`, `A`, `S`, `D`, `STOP`) per client esterni e API RoboMaster via SDK.

Per installazione, requisiti runtime, caveat RoboMaster e note di deployment, vedi [install.md](install.md).

## Componenti

- `server.py`: acquisisce il video, rileva il marker ArUco e invia i comandi `W`, `A`, `S`, `D`, `STOP`.
- `robomaster_api.py`: adapter API per inviare gli stessi comandi a RoboMaster tramite SDK.
- `tools/robomaster_sim_api.py`: adapter simulato per validare la logica RoboMaster senza hardware.
- `client_pycar.py`: si collega al server TCP e converte i comandi in movimenti del rover con watchdog di sicurezza e riconnessione automatica.
- `client_arduino.c`: firmware client TCP per rover Arduino (consuma `W`, `A`, `S`, `D`, `STOP`).
- `settings.h`: configurazione centralizzata del client Arduino (Wi-Fi, server, pin, PWM).
- `arduino_c_compat.h`: utility C minimale per confronto stringhe lato firmware Arduino.
- `settings.py`: file principale con tutti i parametri runtime, documentati in dettaglio.
- `tools/simulator_client.py`: client TCP con simulazione visiva 2D per test senza rover reale.
- `tools/generate_markers.py`: genera marker ArUco stampabili in `tools/printables`.
- `install.md`: guida completa a installazione, caveat runtime e deployment per i vari target.
- `CHANGELOG.md`: storico versioni e modifiche del progetto.

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

## Profili Launch VS Code

Nel file `.vscode/launch.json` sono disponibili profili separati per simulazione e hardware reale.

### Simulazione

- `Sim | Vision Server`: avvia `server.py` con parametri di tracking.
- `Sim | Visual Rover Client`: avvia `tools/simulator_client.py` senza hardware.
- `Sim | Vision Server (RoboMaster Sim API)`: avvia `server.py` con backend RoboMaster simulato (senza device).
- `Sim | Full Stack (Server + Visual Client)`: avvio combinato server + simulatore.

### Hardware reale

- `HW | Vision Server (Pycar TCP)`: avvia `server.py` per acquisizione camera reale.
- `HW | Vision Server (Arduino TCP)`: avvia `server.py` per l'integrazione con rover Arduino via TCP.
- `HW | Vision Server (RoboMaster API)`: avvia `server.py` con backend RoboMaster SDK.

Ogni profilo usa input runtime modificabili al momento del lancio:

- rete: host/port, camera, marker-id, mode

Per tutti i parametri di tuning e sicurezza (server/client/simulatore), fai riferimento a [settings.py](settings.py).

## Uso pratico

- avvia prima il server
- avvia poi il client sul rover oppure il simulatore visivo
- usa `--mode dpad` per guida direzionale manuale a 4 direzioni
- usa `--mode chase` per inseguimento rapido del target con allineamento automatico
- premi `Q` sulla finestra del server per fermare il sistema

Quando il server termina, prova a inviare `STOP` al rover prima di chiudere la connessione.