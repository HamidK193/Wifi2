# memory.md

## Projektgedaechtnis

### Projekt

- Name: `2026_ss_se_wifi_team2`
- Thema: WiFi-basierte Outdoor-Lokalisierung
- Sprache: Python 3

### Aktueller Stand

- Die Datei `WigleWifi_20260408161721.csv` ist der aktuelle relevante Arbeitsdatensatz in `data/raw/`.
- Die Dateien `map.osm` und `map_innenstadt.osm` liegen in `data/raw/`.
- Es handelt sich um einen Wigle-WiFi-Export mit einer zusaetzlichen ersten
  Metazeile.
- Der alte kleine Datensatz wird fachlich nicht weiterverfolgt.
- Die aktuelle Pipeline filtert auf `Type = WIFI` und verwirft ungueltige
  `1970-01-01`-Zeitstempel.
- Die App nutzt aktuell `map_innenstadt.osm` als fokussierten Innenstadt-
  Ausschnitt.
- Der aktuelle Stand konzentriert sich auf Einlesen, Bereinigung, Scan-Zusammen-
  fassung, Radius-Schaetzung, interaktive OSM-Ueberlagerung und erste
  automatisierte Tests.
- Die aktive Datenpipeline laeuft ueber `main.py`.
- Die interaktive Browser-Anwendung laeuft ueber `app.py`.
- In `.github/workflows/ci.yml` ist ein erster GitHub-Action-Workflow fuer
  automatische Tests angelegt.
- Die aktiven Module liegen direkt in `src/`.
- In `data/processed/` werden bereinigte Daten, Scan-Zusammenfassungen und
  Netzwerk-Beobachtungen gespeichert.
- Fuer Task 1 und Task 2 existieren jeweils vier kleine unterschiedliche
  Loesungsdateien fuer die Teammitglieder.

### Bekannte Fakten zur neuen CSV

- Datei: `WigleWifi_20260408161721.csv`
- enthaelt `WIFI`, `BLE`, `GSM` und `BT`; aktuell wird nur `WIFI` genutzt
- beinhaltet ungueltige Zeitstempel wie `1970-01-01`, die verworfen werden
- dieselbe SSID kommt mit vielen verschiedenen BSSIDs vor
- deshalb ist `SSID + BSSID` die relevante Netzwerkeinheit
- relevante Felder: MAC, SSID, FirstSeen, RSSI, Channel, Frequency,
  CurrentLatitude, CurrentLongitude, AccuracyMeters, Type

### Aktuelle Ziele

- neuen WiGLE-Datensatz robust einlesen
- Daten bereinigen und vereinheitlichen
- moegliche Router-Radien aus RSSI abschaetzen
- OSM-Karte und Scan-Daten interaktiv im Browser darstellen
- Kreis-Ueberlagerungen fuer spaetere Router- oder Standortabschaetzung
  nutzbar machen
- erste automatische Tests und GitHub Actions stabil betreiben
- Projekt klein und kursgerecht halten
- Dokumentation und Git-Stand sauber halten

### Spaetere Erweiterungen

- mehrere CSV-Dateien zusammenfuehren
- einfache Lokalisierungs-Baseline pruefen
- Smartphone-App optional spaeter ergaenzen
