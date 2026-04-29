# CHANGELOG.md

Alle wichtigen Aenderungen am Projekt werden hier kurz protokolliert.

## 2026-04-29

- Streamlit-App in zwei Karten-Tabs getrennt: `Standort-Schaetzung` und
  `GPS-vs-WLAN-Vergleich`.
- Evaluationslogik in `src/evaluation.py` ausgelagert, damit Route-Comparison,
  Fehlerkennzahlen und 60-m-Radiusfilter automatisch testbar sind.
- Performance-Schutz erweitert: Radius- und AP-Layer werden bei einer
  konkreten Schaetzung auf den relevanten 60-m-Umkreis begrenzt.
- GitHub Action erweitert: Vor der gesamten Testsuite laeuft nun der schnelle
  synthetische Pipeline-Smoke-Test.
- Tests fuer Route-Comparison, Genauigkeitskennzahlen, Radiusfilter und
  synthetische Lokalisierungsgenauigkeit ergaenzt.

## 2026-04-22

- Pipeline in zwei Phasen getrennt: GPS nur noch fuer die Offline-Kalibrierung,
  Laufzeitdaten GPS-frei.
- triangulierte Access-Point-Artefakte und triangulierte Scan-Positionen in
  `data/processed/` als neue Standard-Ausgaben eingefuehrt.
- Haupt-Lokalisierung von Fingerprint-Matching auf AP-Multilateration
  umgestellt.
- App so umgebaut, dass sie im Hauptmodus nur noch `data/processed/` laedt und
  ohne Roh-GPS arbeiten kann.
- getrennten Dev-Benchmark mit Leave-one-scan-out und GPS-Fehleranzeige
  eingefuehrt.
- Tests auf GPS-freie Laufzeitdaten, AP-Triangulation und neue Pipeline
  erweitert.

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
- Routenvergleich in der App ergaenzt: GPS-Route als rote Linie, WLAN-Schaetzpunkte und Pfeile zwischen GPS- und WLAN-Position.

## 2026-03-31

- Projektstruktur fuer den Visualisierungs-MVP vereinfacht.
- CSV `T1_zu_W1.csv` nach `data/raw/` uebernommen.
- `map.osm` nach `data/raw/` uebernommen.
- neue flache Module fuer Laden, Vorverarbeitung und Visualisierung angelegt.
- `task1.py` in vier unterschiedliche Team-Versionen aufgeteilt.
- `task2_vending_machine.py` in vier unterschiedliche Team-Versionen aufgeteilt.
