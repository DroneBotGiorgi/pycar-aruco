# rover-aruco

![version](https://img.shields.io/badge/version-1.0-blue)

Questo progetto usa una webcam per leggere un marker ArUco e trasformarlo in comandi di guida. Il server supporta due backend: TCP per client esterni e API RoboMaster via SDK.

Per installazione, requisiti runtime, caveat RoboMaster e note di deployment, vedi [install.md](install.md).

## Componenti

- `server/server.py`: acquisisce il video, rileva il marker ArUco e invia comandi radar con protocollo `cmd,v_mult,distanza`.
- `server/settings.py`: file principale con i parametri runtime (rete, calibrazione camera, HUD, ponte, velocita, client).
- `robomaster/robomaster_api.py`: adapter API per RoboMaster con supporto comandi estesi e sicurezza ToF opzionale.
- `picar/client_picar.py`: client TCP Picar-X con parsing `cmd,v_mult,distanza`, anti ostacolo e riconnessione automatica.
- `arduino/client_arduino.c`: firmware client TCP per rover Arduino con anti-lag, anti ostacolo e comandi estesi.
- `arduino/settings.h`: configurazione centralizzata del client Arduino (Wi-Fi, server, pin, sensore, timing evasione).
- `arduino_c_compat.h`: utility C minimale per confronto stringhe lato firmware Arduino.

- `tools/simulator_client.py`: client TCP con simulazione visiva 2D per test senza rover reale.
- `tools/robomaster_sim_api.py`: adapter simulato per validare la logica RoboMaster senza hardware.
- `tools/generate_markers.py`: genera marker ArUco stampabili in `tools/printables`.

- `install.md`: guida completa a installazione, caveat runtime e deployment per i vari target.

## Come funziona

Il server usa una logica radar a zone con HUD, stima distanza reale via `solvePnP` e calibrazione camera reale. La guida decide il comando in base alla zona ArUco e alla distanza, con velocita dinamica e modalita "salto ponte" temporizzata per ostacoli sospesi.

Protocollo TCP inviato ai client:

- `cmd,v_mult,distanza`
- comandi possibili: `W`, `W_MAX`, `S`, `A`, `D`, `WA`, `WD`, `STOP`
- `v_mult` e un moltiplicatore tra 0.0 e 1.0
- `distanza` e la distanza stimata in cm

## Profili Launch VS Code

Nel file `.vscode/launch.json` sono disponibili profili separati per simulazione e hardware reale.

### Simulazione

- `Sim | Vision Server`: avvia `server/server.py` (via modulo `server.server`) con parametri di tracking.
- `Sim | Visual Rover Client`: avvia `tools/simulator_client.py` senza hardware.
- `Sim | Vision Server (RoboMaster Sim API)`: avvia `server/server.py` con backend RoboMaster simulato (senza device).
- `Sim | Full Stack (Server + Visual Client)`: avvio combinato server + simulatore.

### Hardware reale

- `HW | Vision Server (Pycar TCP)`: avvia `server/server.py` per acquisizione camera reale.
- `HW | Vision Server (Arduino TCP)`: avvia `server/server.py` per integrazione rover Arduino via TCP.
- `HW | Vision Server (RoboMaster API)`: avvia `server/server.py` con backend RoboMaster SDK.

Ogni profilo usa input runtime modificabili al momento del lancio:

- rete: host/port, camera, marker-id, mode

Per tutti i parametri di tuning e sicurezza (server/client/simulatore), fai riferimento a [server/settings.py](server/settings.py).

## Uso pratico

- avvia prima il server
- avvia poi il client sul rover oppure il simulatore visivo
- usa i parametri in `server/settings.py` per tuning rapido di calibrazione, ponte, velocita e sicurezza
- scegli il backend con `--transport tcp|robomaster|robomaster-sim`
- premi `Q` sulla finestra del server per fermare il sistema

Quando il server termina, prova a inviare `STOP` al rover prima di chiudere la connessione.