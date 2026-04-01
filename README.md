# Controllo rover con marker ArUco

Questo progetto usa una webcam per leggere l'orientamento di un marker ArUco e trasformarlo in comandi di guida inviati via TCP a un rover basato su Picar-X.

## Componenti

- `server.py`: acquisisce il video, rileva il marker ArUco e invia i comandi `W`, `A`, `S`, `D`, `STOP`.
- `client.py`: si collega al server TCP e converte i comandi in movimenti del rover.
- `config.py`: contiene i valori di default condivisi.
- `casino.py`: entrypoint compatibile per avviare `server` o `client` con un solo comando.

## Come funziona

Il server osserva un marker ArUco con ID configurabile. In base alla direzione del lato superiore del marker, il sistema divide la rotazione in quattro settori:

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
python server.py --host 0.0.0.0 --port 9999 --camera 0 --marker-id 0
```

Oppure:

```bash
python casino.py server
```

### 2. Avviare il client sul rover

Sostituisci `192.168.1.105` con l'IP del PC che esegue il server.

```bash
python client.py --host 192.168.1.105 --port 9999
```

Oppure:

```bash
python casino.py client --host 192.168.1.105
```

## Opzioni utili

### Server

- `--camera`: indice della webcam
- `--marker-id`: ID del marker ArUco da tracciare
- `--window-title`: titolo della finestra OpenCV

### Client

- `--speed`: velocita del rover
- `--steering-angle`: angolo massimo di sterzata
- `--steering-inversion`: usa `1` o `-1` per correggere lo sterzo
- `--retry-delay`: tempo di attesa tra i tentativi di connessione

## Uso pratico

- avvia prima il server
- avvia poi il client sul rover
- punta il marker ArUco verso l'alto, destra, basso o sinistra per guidare il rover
- premi `Q` sulla finestra del server per fermare il sistema

Quando il server termina, prova a inviare `STOP` al rover prima di chiudere la connessione.