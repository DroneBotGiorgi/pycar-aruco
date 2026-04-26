# Team 3 - Arduino Uno R4 WiFi

Le parti comuni del progetto (detector, tracking ArUco, logica HUD, protocollo logico dei comandi) sono descritte in [README.MD](../README.MD). Questo documento riporta solo i dettagli specifici della variante firmware Arduino.

Diagramma di flusso: [TEAM3_FLOW.svg](TEAM3_FLOW.svg).

## In breve

Questa variante sposta l'attuazione su firmware Arduino: il server invia i comandi e il microcontrollore li trasforma direttamente in segnali motore.

In pratica:

- server: decide `cmd` e `v_mult`;
- TCP: invia il comando come testo;
- firmware: converte il comando in direzione e PWM su DRV8833.

## Flusso operativo

Il ciclo e continuo e lineare: il firmware legge lo stream, prende l'ultimo comando completo e aggiorna subito i motori. Questo approccio evita accumulo di comandi vecchi e mantiene il comportamento reattivo.

## Dettagli tecnici essenziali

- Firmware principale: `team3/client_arduino.c`.
- Parsing char-by-char con strategia last-message-only.
- Conversione `v_mult` in PWM 8 bit e controllo differenziale ruote.

I dettagli piu fini di implementazione (buffer, formule e funzioni di basso livello) restano nel codice sorgente.

## Sicurezza locale

La protezione anti-collisione e gestita sul rover:

- controllo distanza con ultrasuoni;
- evasione automatica sotto soglia;
- stop e ripartenza del loop normale dopo la manovra di sicurezza.

## Parametri configurabili

I principali parametri configurabili della soluzione sono:

- soglia di emergenza ultrasuoni;
- velocita minima utile (evita quasi-fermo a bassi `v_mult`);
- bilanciamento tra lato sinistro e destro.

Questi parametri determinano risposta dinamica e sicurezza del rover in scenario reale.

## Punti di forza Team 3

- architettura embedded autonoma con controllo locale a bassa latenza;
- nessuna dipendenza da runtime Python sul rover;
- controllo diretto di parsing, PWM e logica di sicurezza a livello firmware.