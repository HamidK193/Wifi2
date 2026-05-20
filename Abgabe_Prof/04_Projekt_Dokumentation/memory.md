# memory.md

## Projektgedaechtnis

### Projekt

- Name: `2026_ss_se_wifi_team2`
- Thema: WiFi-basierte Outdoor-Lokalisierung
- Sprache: Python 3

### Aktueller Stand

- Die Datei `WigleWifi_20260408161721.csv` ist der aktuelle relevante
  Kalibrierungsdatensatz in `data/raw/`.
- Die Dateien `map.osm` und `map_innenstadt.osm` liegen in `data/raw/`.
- Es handelt sich um einen Wigle-WiFi-Export mit einer zusaetzlichen ersten
  Metazeile.
- Der alte kleine Datensatz wird fachlich nicht weiterverfolgt.
- Die Pipeline filtert auf `Type = WIFI` und verwirft ungueltige
  `1970-01-01`-Zeitstempel.
- `main.py` nutzt Roh-GPS nur fuer die Offline-Kalibrierung.
- Die Runtime-Artefakte liegen in `data/processed/` und enthalten:
  - `triangulated_access_points.csv`
  - `triangulated_scan_positions.csv`
  - `wifi_scans_clean.csv`
  - `scan_summary.csv`
  - `network_observations.csv`
  - `network_summary.csv`
- Die App nutzt im Hauptmodus nur noch die Artefakte aus `data/processed/`.
- Der normale Standort-Test ist GPS-frei und arbeitet ueber
  AP-Multilateration aus `SSID+BSSID+RSSI`.
- Der Dev-Benchmark ist getrennt und darf vorhandene GPS-Daten nur fuer
  Leave-one-scan-out und Fehlervergleich verwenden.
- Die App nutzt `map_innenstadt.osm` als fokussierten Innenstadt-Ausschnitt.
- Die App berechnet in der Defaultansicht `Alle / Alle` keine Radiuskreise und
  keine Overlap-Punkte, damit sie mit dem grossen Datensatz sichtbar bleibt.
- Die App hat zwei Karten-Tabs:
  - `Standort-Schaetzung` fuer den aktuell geschaetzten WLAN-Standort
  - `GPS-vs-WLAN-Vergleich` fuer GPS-Route, WLAN-Schaetzpunkte und
    Verbindungslinien/Pfeile zur Fehlerbewertung
- Sichtbare Netzwerke, APs und Radiuskreise werden bei einer konkreten
  Standortschaetzung standardmaessig auf 60 m um die Schaetzung begrenzt.
- `src/evaluation.py` enthaelt die testbare Logik fuer Route-Comparison,
  Fehlerkennzahlen und Radiusfilter.
- In `.github/workflows/ci.yml` ist ein GitHub-Action-Workflow fuer
  automatische Tests angelegt. Die CI fuehrt zusaetzlich `python main.py` als
  Pipeline-Smoke-Test aus.

### Bekannte Fakten zur CSV

- Datei: `WigleWifi_20260408161721.csv`
- enthaelt `WIFI`, `BLE`, `GSM` und `BT`; aktuell wird nur `WIFI` genutzt
- beinhaltet ungueltige Zeitstempel wie `1970-01-01`, die verworfen werden
- dieselbe SSID kommt mit vielen verschiedenen BSSIDs vor
- deshalb ist `SSID + BSSID` die relevante Netzwerkeinheit
- relevante Felder: `MAC`, `SSID`, `FirstSeen`, `RSSI`, `Channel`,
  `Frequency`, `CurrentLatitude`, `CurrentLongitude`, `AccuracyMeters`, `Type`

### Aktuelle Ziele

- Kalibrierungsdaten robust einlesen
- aus Roh-GPS stabile AP-Positionen triangulieren
- GPS-freie Laufzeit-Artefakte in `data/processed/` pflegen
- OSM-Karte und Scan-Daten interaktiv im Browser darstellen
- Standort-Test ohne Roh-GPS im Hauptmodus betreiben
- Dev-Benchmark fuer kontrollierte Vergleiche beibehalten
- automatische Tests und GitHub Actions stabil betreiben
- Genauigkeit und Funktionalitaet per `pytest` absichern
- Projekt klein und kursgerecht halten

### Spaetere Erweiterungen

- mehrere CSV-Dateien zusammenfuehren
- AP-Qualitaetsmetriken verbessern
- mehrere Messlaeufe vergleichen
.\.venv\Scripts\python.exe -m streamlit run app.py
