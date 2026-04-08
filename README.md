# 2026_ss_se_wifi_team2

Projekt von Team 2 im Kurs Software Engineering.

## Projektthema

WiFi-basierte Outdoor-Lokalisierung mit Python.

## Ziel

Ziel des Projekts ist es, WiFi-Messdaten aus einer CSV-Datei einzulesen,
aufzubereiten und daraus langfristig eine grobe Selbstlokalisierung
vorzubereiten.

Wichtige fachliche Idee:

- Eine einzelne Messung liefert keinen exakten Routerpunkt.
- Eine einzelne Messung liefert nur einen moeglichen Radiusbereich.
- Erst mehrere Beobachtungen desselben Netzwerks koennen einen
  wahrscheinlicheren Bereich ergeben.

## Aktueller Stand

- Die CSV `WigleWifi_20260408161721.csv` liegt in `data/raw/`.
- Der aktuelle OpenStreetMap-Export `map_innenstadt.osm` liegt in `data/raw/`.
- `main.py` fuehrt die Datenpipeline aus:
  - CSV inspizieren
  - CSV bereinigen
  - nur `WIFI`-Eintraege weiterverarbeiten
  - ungueltige `1970-01-01`-Zeitstempel entfernen
  - Scan-Zusammenfassung erzeugen
  - Netzwerk-Beobachtungen und Radius-Schaetzungen erzeugen
- `app.py` startet die interaktive Browser-Anwendung.
- `pytest` und GitHub Actions pruefen die wichtigsten Kernfunktionen automatisch.
- Fuer Task 1 und Task 2 liegen jeweils vier unterschiedliche kleine
  Loesungsdateien im Projekt.

## Vereinfachte Projektstruktur

```text
2026_ss_se_wifi_team2/
|- README.md
|- AGENTS.md
|- memory.md
|- CHANGELOG.md
|- requirements.txt
|- .gitignore
|- main.py
|- app.py
|- Abgaben/
|- data/
|  |- raw/
|  |  |- WigleWifi_20260408161721.csv
|  |  |- map.osm
|  |  |- map_innenstadt.osm
|  |- processed/
|- notebooks/
|- src/
|  |- __init__.py
|  |- load_wifi_csv.py
|  |- localization_logic.py
|  |- preprocess_wifi_data.py
|  |- project_pipeline.py
|  |- visualize_wifi_data.py
|- tests/
|- .github/
|  |- workflows/
|  |  |- ci.yml
```

## Datensatz

Die Datei `WigleWifi_20260408161721.csv` enthaelt:

- eine erste Wigle-Metazeile
- eine echte Headerzeile
- gemischte Messungen, aus denen aktuell nur `Type = WIFI` verwendet wird
- WiFi-Messdaten mit Spalten wie `MAC`, `SSID`, `FirstSeen`, `RSSI`,
  `CurrentLatitude`, `CurrentLongitude`, `Channel`, `Frequency` und
  `AccuracyMeters`

Wichtige Modellierungsregel:

- Eine Netzwerkeinheit wird im Projekt nicht nur ueber `SSID` oder nur ueber
  `BSSID` identifiziert, sondern ueber die Kombination `SSID + BSSID`.

Wichtiger Hinweis:

- Rohdaten in `data/raw/` nicht veraendern.
- Wigle-Exporte koennen eine zusaetzliche erste Metazeile enthalten.
- Ungueltige Zeitstempel wie `1970-01-01` werden beim Bereinigen verworfen.
- `map_innenstadt.osm` wird aktuell als Standard-Kartengrundlage fuer die
  interaktive OSM-Ueberlagerung verwendet.

## Verarbeitungsschritte

Beim aktuellen MVP werden diese Schritte ausgefuehrt:

1. CSV-Datei erkennen und Metazeile behandeln
2. Relevante Spalten einlesen
3. Spalten in ein internes Schema umbenennen
4. `SSID + BSSID` als gemeinsame Netzwerk-ID modellieren
5. Daten bereinigen und nach Scans gruppieren
6. Pro Netzwerk-Beobachtung einen moeglichen Radius aus dem RSSI abschaetzen
7. Interaktive OSM-Karte im Browser anzeigen

## Ausgabe in `data/processed/`

Nach `python main.py` werden diese Dateien erzeugt:

- `wifi_scans_clean.csv`
- `scan_summary.csv`
- `network_observations.csv`
- `network_summary.csv`
- `dataset_summary.txt`

## Browser-Anwendung

Die Browser-Anwendung zeigt:

- den lokalen OSM-Export `map.osm` als Kartenbasis
- Messpunkte der Scans
- fuer ein ausgewaehltes Netzwerk die moeglichen Radiuskreise
- Ueberlappungspunkte mehrerer Kreise desselben Netzwerks

Wichtig:

- Die Kreise zeigen keine exakten Routerpunkte.
- Jeder Kreis beschreibt nur einen moeglichen Bereich aus einer einzelnen
  Beobachtung.
- Erst die Ueberlagerung mehrerer Kreise bereitet eine spaetere
  Router- oder Standortabschaetzung vor.

## Uebungsdateien

Im Repository liegen ausserdem mehrere kleine Uebungsloesungen aus dem Kurs:

- Task 1:
  - `Abgaben/task1_hamid.py`
  - `Abgaben/task1_rojhat.py`
  - `Abgaben/task1_lamia.py`
  - `Abgaben/task1_aysel.py`
- Task 2:
  - `Abgaben/task2_vending_machine_hamid.py`
  - `Abgaben/task2_vending_machine_rojhat.py`
  - `Abgaben/task2_vending_machine_lamia.py`
  - `Abgaben/task2_vending_machine_aysel.py`

## Benoetigte Python-Pakete

Fuer den aktuellen MVP werden benoetigt:

- `pandas`
- `streamlit`
- `folium`
- `streamlit-folium`
- `pytest`

Installation:

```bash
python -m pip install -r requirements.txt
```

## Ausfuehrung Datenpipeline

```bash
python main.py
```

## Ausfuehrung Browser-App

```bash
python -m streamlit run app.py
```

## Tests

Lokal:

```bash
python -m pytest
```

GitHub Actions:

- Bei jedem `push` und `pull request` startet automatisch der Workflow
  `.github/workflows/ci.yml`.
- Dort werden die Abhaengigkeiten installiert und die `pytest`-Tests ausgefuehrt.

## Naechste moegliche Erweiterungen

- weitere CSV-Dateien in `data/raw/` aufnehmen
- mehrere Messlaeufe vergleichen
- die Kreis-Ueberlagerung in eine explizite Routerbereichs-Schaetzung
  ueberfuehren
- spaeter die Selbstlokalisierung gegen bekannte Messpunkte testen
- optional eine Smartphone-App als zusaetzliches Projektpaket ergaenzen
