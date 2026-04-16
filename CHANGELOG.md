# CHANGELOG.md

Alle wichtigen Aenderungen am Projekt werden hier kurz protokolliert.

## 2026-04-01

- lokale Git-Identitaet auf `HamidK193 / karatasabdulhamid@gmail.com` gesetzt.
- statische PNG-Visualisierung zugunsten einer interaktiven Streamlit-Anwendung ersetzt.
- neue Datenlogik fuer `SSID + BSSID` als Netzwerkeinheit eingefuehrt.
- Radius-Schaetzungen und Kreis-Ueberlagerungslogik fuer moegliche Routerbereiche vorbereitet.
- gemeinsame Datenpipeline fuer CLI und Browser-Anwendung eingefuehrt.

## 2026-04-08

- neuen WiGLE-Datensatz `WigleWifi_20260408161721.csv` nach `data/raw/` uebernommen und als Standarddatensatz gesetzt.
- `main.py` und `app.py` auf den neuen Datensatz umgestellt.
- Datenbereinigung fuer neue WiGLE-Exporte erweitert: nur `WIFI`, ungueltige `1970-01-01`-Zeitstempel werden entfernt.
- erste `pytest`-Tests fuer CSV-Import, Bereinigung, Netzwerklogik, Pipeline und App-Import angelegt.
- GitHub-Action-Workflow in `.github/workflows/ci.yml` fuer automatische Tests bei `push` und `pull_request` hinzugefuegt.
- neuen OSM-Export `map_innenstadt.osm` als fokussierte Standardkarte fuer die App uebernommen.
- App-Defaultansicht performant gemacht: `Alle / Alle` zeigt nur Messpunkte, Radius- und Overlap-Berechnung startet erst bei konkreter Auswahl.
- erste Fingerprint-basierte Standortschätzung ergaenzt: Testscan oder manuelle `SSID,BSSID,RSSI`-Eingabe kann gegen Referenz-Scans gematcht werden.
- Erklaerdatei `docs/professor_erklaerung.txt` mit den wichtigsten Punkten zu Daten, Code, Triangulation und Fingerprinting erstellt.

## 2026-03-31

- Projektstruktur fuer den Visualisierungs-MVP vereinfacht.
- CSV `T1_zu_W1.csv` nach `data/raw/` uebernommen.
- `map.osm` nach `data/raw/` uebernommen.
- neue flache Module fuer Laden, Vorverarbeitung und Visualisierung angelegt.
- `task1.py` in vier unterschiedliche Team-Versionen aufgeteilt.
- `task2_vending_machine.py` in vier unterschiedliche Team-Versionen aufgeteilt.
