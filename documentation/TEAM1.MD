# Team 1 - RoboMaster EP Core

Le parti comuni del progetto (pipeline drone, detector YOLO, HUD condiviso, protocollo logico dei comandi) sono descritte in [README.MD](../README.MD). Questo documento copre solo le scelte implementative specifiche della soluzione RoboMaster.

Diagramma di flusso: [TEAM1_FLOW.svg](TEAM1_FLOW.svg).

## In breve

Questa variante e la piu diretta del progetto: il server che vede e decide invia i comandi direttamente al RoboMaster tramite SDK DJI. Non c'e un client separato sul rover.

In pratica:

- il server calcola `cmd` (azione) e `v_mult` (intensita);
- passa subito questi valori all'adapter RoboMaster;
- l'adapter converte il comando in movimento del chassis.

## Flusso operativo

Il ciclo resta semplice e ripetitivo: ogni frame video aggiorna la decisione, e la nuova decisione viene applicata subito al rover.

Questo mantiene la latenza contenuta e rende il flusso particolarmente lineare da analizzare.

## Dettagli tecnici essenziali

- Adapter usato: `team1/robomaster_api.py`.
- API principali: `connect()`, `send(command, speed_multiplier)`, `close()`.
- Sicurezza opzionale ToF: blocco dei comandi forward sotto soglia distanza.

Il mapping completo tra comandi simbolici e velocita chassis resta nel codice dell'adapter, per non appesantire questo documento con dettagli troppo di basso livello.

## Simulatore Team 1

Team 1 include un backend simulato compatibile con la stessa interfaccia dell'API reale:

- `team1/simulator_api.py`
- avvio server con `--transport robomaster-sim`

Questo consente di validare la logica di guida anche senza hardware DJI collegato.

## Parametri configurabili

I principali parametri configurabili della soluzione sono:

- velocita base del rover (aggressivita della risposta a `v_mult`);
- soglia ToF di blocco forward (se attivata);
- soglie di decisione lato HUD nel server.

La configurazione di questi tre punti determina la dinamica finale di guida in arena.

## Punti di forza Team 1

- catena software corta: decisione e attuazione sono nello stesso stack server;
- latenza ridotta grazie all'assenza di un client rover separato;
- integrazione diretta con SDK DJI e piattaforma RoboMaster.