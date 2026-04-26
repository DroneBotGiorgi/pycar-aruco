# DroneBotGiorgi - QUICKSTART

Questa guida serve ad avviare rapidamente il progetto in demo locale.
Per la descrizione generale del lavoro RomeCup26, vedi README.MD.
Per dettagli su materiali e componenti software, vedi documentation/BOM.MD e documentation/SBOM.MD.

Questa guida assume che le installazioni siano gia state completate seguendo INSTALL.MD.

## 1) Prerequisiti minimi

- Windows con Python 3.10 installato
- VS Code (consigliato, con i profili launch gia configurati)
- Repository clonato in locale

Per setup completo, dipendenze avanzate e note RoboMaster, vedi INSTALL.MD.

## 2) Fase 1: rilevamento fuoco

Da terminale:

```powershell
python -m detector.main --source webcam --webcam-index 0 --gui
```

Oppure usa il profilo VS Code: Drone | Fire Detect.

## 3) Fase 2: guida rover

Avvia il server:

```powershell
python server/server.py --transport tcp
```

Poi usa il rover desiderato:

- Team 2 (PiCar-X): avvia il client su Raspberry Pi
- Team 3 (Arduino): carica e avvia il firmware su Arduino Uno R4 WiFi
- Team 1 (RoboMaster): usa backend diretto RoboMaster

Per RoboMaster da PC:

```powershell
python server/server.py --transport robomaster
```

Profili Launch VS Code consigliati:

- Drone | Fire Detect
- Drone | Guide PiCar
- Drone | Guide Arduino
- Drone | Guide RoboMaster

## 4) Simulazione senza hardware

```powershell
python server/server.py --transport tcp
python team1/simulator_client.py --host 127.0.0.1 --port 9999
```

In alternativa:

- Simulation | TCP Rover
- Simulation | RoboMaster

## 5) Dove guardare dopo

- README.MD: panoramica non tecnica
- documentation/BOM.MD: materiali hardware unificati
- documentation/SBOM.MD: componenti software e dipendenze
- documentation/TEAM1.MD, documentation/TEAM2.MD, documentation/TEAM3.MD: flussi specifici di ciascun team
