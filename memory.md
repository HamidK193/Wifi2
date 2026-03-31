# memory.md

## Projektgedaechtnis

### Projekt

- Name: `2026_ss_se_wifi_team2`
- Thema: WiFi-basierte Outdoor-Lokalisierung
- Sprache: Python 3

### Aktueller Stand

- Die Datei `T1_zu_W1.csv` liegt in `data/raw/`.
- Die Datei `map.osm` liegt in `data/raw/`.
- Es handelt sich um einen Wigle-WiFi-Export mit einer zusaetzlichen ersten
  Metazeile.
- Der aktuelle MVP konzentriert sich auf Einlesen, Bereinigung, Scan-Zusammen-
  fassung, Visualisierung und OSM-Ueberlagerung.
- Die aktive Pipeline laeuft ueber `main.py`.
- Die aktiven Module liegen direkt in `src/`.
- In `data/processed/` wurden bereits bereinigte Daten, eine Scan-Zusammen-
  fassung und drei PNG-Visualisierungen erzeugt.
- Zusaetzlich wurden zwei OSM-basierte Karten mit Scan-Punkten erzeugt.
- Fuer Task 1 und Task 2 existieren jeweils vier kleine unterschiedliche
  Loesungsdateien fuer die Teammitglieder.

### Bekannte Fakten zur CSV

- 305 Datenzeilen
- 19 Zeitstempel
- 19 Messpunkte
- relevante Felder: MAC, SSID, FirstSeen, RSSI, Channel, Frequency,
  CurrentLatitude, CurrentLongitude, AccuracyMeters

### Aktuelle Ziele

- CSV robust einlesen
- Daten bereinigen und vereinheitlichen
- Visualisierungen erzeugen
- OSM-Karte und Scan-Daten deckungsgleich darstellen
- Projekt klein und kursgerecht halten
- Dokumentation und Git-Stand sauber halten

### Spaetere Erweiterungen

- mehrere CSV-Dateien zusammenfuehren
- einfache Lokalisierungs-Baseline pruefen
- Smartphone-App optional spaeter ergaenzen
