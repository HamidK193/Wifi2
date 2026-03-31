# 2026_ss_se_wifi_team2

Projekt von Team 2 im Kurs Software Engineering.

## Projektthema

WiFi-basierte Outdoor-Lokalisierung mit Python.

## Ziel

Ziel des Projekts ist es, WiFi-Messdaten aus einer CSV-Datei einzulesen,
aufzubereiten und zunaechst visuell auszuwerten. Fuer den ersten MVP liegt der
Fokus auf Datenverstaendnis und Visualisierung, nicht auf einer Smartphone-App
oder einer komplexen Lokalisierungslogik.

## Aktueller Stand

- Die CSV `T1_zu_W1.csv` liegt in `data/raw/`.
- Der OpenStreetMap-Export `map.osm` liegt in `data/raw/`.
- Die Datei stammt aus der App Wigle WiFi und besitzt eine zusaetzliche erste
  Metazeile.
- `main.py` fuehrt die aktuelle Mini-Pipeline aus:
  - CSV inspizieren
  - CSV bereinigen
  - Scan-Zusammenfassung erzeugen
  - Visualisierungen speichern
  - OSM-Karte mit Scan-Punkten ueberlagern
- Fuer Task 1 und Task 2 liegen jeweils vier unterschiedliche kleine
  Loesungsdateien im Projekt.
- Die Ergebnisse werden in `data/processed/` abgelegt.

## Vereinfachte Projektstruktur

```text
2026_ss_se_wifi_team2/
|- README.md
|- AGENTS.md
|- memory.md
|- CHANGELOG.md
|- .gitignore
|- main.py
|- data/
|  |- raw/
|  |  |- T1_zu_W1.csv
|  |  |- map.osm
|  |- processed/
|- notebooks/
|- src/
|  |- __init__.py
|  |- load_wifi_csv.py
|  |- preprocess_wifi_data.py
|  |- visualize_wifi_data.py
|- tests/
|- task1_hamid.py
|- task1_rojhat.py
|- task1_lamia.py
|- task1_aysel.py
|- task2_vending_machine_hamid.py
|- task2_vending_machine_rojhat.py
|- task2_vending_machine_lamia.py
|- task2_vending_machine_aysel.py
```

## Datensatz

Die Datei `T1_zu_W1.csv` enthaelt:

- eine erste Wigle-Metazeile
- eine echte Headerzeile
- WiFi-Messdaten mit Spalten wie `MAC`, `SSID`, `FirstSeen`, `RSSI`,
  `CurrentLatitude`, `CurrentLongitude`, `Channel`, `Frequency` und
  `AccuracyMeters`

Wichtiger Hinweis:

- Rohdaten in `data/raw/` nicht veraendern.
- Wigle-Exporte koennen eine zusaetzliche erste Metazeile enthalten.
- `map.osm` wird als Kartengrundlage fuer die OSM-Ueberlagerung verwendet.

## Verarbeitungsschritte

Beim aktuellen MVP werden diese Schritte ausgefuehrt:

1. CSV-Datei erkennen und Metazeile behandeln
2. Relevante Spalten einlesen
3. Spalten in ein kleines internes Schema umbenennen
4. Daten bereinigen und nach Scans gruppieren
5. Visuelle Auswertung als PNG-Dateien speichern
6. OSM-Karte mit GPS- und WLAN-Scanpunkten ueberlagern

## Ausgabe in `data/processed/`

Nach `python main.py` werden diese Dateien erzeugt:

- `wifi_scans_clean.csv`
- `scan_summary.csv`
- `dataset_summary.txt`
- `scan_positions.png`
- `top_ssids.png`
- `rssi_distribution.png`
- `osm_scans_visible_networks.png`
- `osm_scans_mean_rssi.png`

## Uebungsdateien

Im Repository liegen ausserdem mehrere kleine Uebungsloesungen aus dem Kurs:

- Task 1:
  - `task1_hamid.py`
  - `task1_rojhat.py`
  - `task1_lamia.py`
  - `task1_aysel.py`
- Task 2:
  - `task2_vending_machine_hamid.py`
  - `task2_vending_machine_rojhat.py`
  - `task2_vending_machine_lamia.py`
  - `task2_vending_machine_aysel.py`

Diese Dateien sind bewusst einfach gehalten und voneinander leicht
unterschiedlich umgesetzt.

## Benötigte Python-Pakete

Fuer den aktuellen MVP werden benoetigt:

- `pandas`
- `matplotlib`

Installation:

```bash
python -m pip install pandas matplotlib
```

## Ausfuehrung

```bash
python main.py
```

## Naechste moegliche Erweiterungen

- weitere CSV-Dateien in `data/raw/` aufnehmen
- mehrere Messlaeufe vergleichen
- spaeter eine einfache Lokalisierungs-Baseline testen
- optional eine Smartphone-App als zusaetzliches Projektpaket ergaenzen
