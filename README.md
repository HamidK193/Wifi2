# 2026_ss_se_wifi_team2

Projekt von Team 2 im Kurs Software Engineering.

## Projektthema

WiFi-basierte Outdoor-Lokalisierung mit Python.

## Ziel

Ziel des Projekts ist es, WiFi-Messdaten aus einer CSV-Datei einzulesen,
offline zu kalibrieren und daraus eine GPS-freie Laufzeit-Lokalisierung
aufzubauen.

Wichtige fachliche Idee:

- Eine einzelne Messung liefert keinen exakten Routerpunkt.
- Eine einzelne Messung liefert nur einen moeglichen Radiusbereich.
- Erst mehrere Beobachtungen desselben Netzwerks koennen einen
  wahrscheinlicheren Bereich ergeben.

## Aktueller Stand

- Die CSV `WigleWifi_20260408161721.csv` liegt in `data/raw/`.
- Der aktuelle OpenStreetMap-Export `map_innenstadt.osm` liegt in `data/raw/`.
- `main.py` fuehrt die Kalibrierungs- und Build-Pipeline aus:
  - CSV inspizieren
  - nur `WIFI`-Eintraege weiterverarbeiten
  - ungueltige `1970-01-01`-Zeitstempel entfernen
  - GPS nur fuer die Offline-Kalibrierung verwenden
  - triangulierte Access-Point-Positionen erzeugen
  - GPS-freie Laufzeit-Artefakte in `data/processed/` schreiben
- `app.py` startet die interaktive Browser-Anwendung auf Basis von
  `data/processed/`.
- Die App enthaelt:
  - einen GPS-freien Standort-Test ueber manuelle `SSID,BSSID,RSSI`-Eingabe
  - einen getrennten Dev-Benchmark mit GPS-Referenz fuer Leave-one-scan-out
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
|- pytest.ini
|- main.py
|- app.py
|- Abgaben/
|- data/
|  |- raw/
|  |  |- WigleWifi_20260408161721.csv
|  |  |- map.osm
|  |  |- map_innenstadt.osm
|  |- processed/
|  |  |- wifi_scans_clean.csv
|  |  |- scan_summary.csv
|  |  |- network_observations.csv
|  |  |- network_summary.csv
|  |  |- triangulated_access_points.csv
|  |  |- triangulated_scan_positions.csv
|  |  |- dataset_summary.txt
|- docs/
|  |- professor_erklaerung.txt
|- src/
|  |- __init__.py
|  |- fingerprint_localization.py
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

Wichtige Hinweise:

- Rohdaten in `data/raw/` nicht veraendern.
- Wigle-Exporte koennen eine zusaetzliche erste Metazeile enthalten.
- Ungueltige Zeitstempel wie `1970-01-01` werden beim Bereinigen verworfen.
- `map_innenstadt.osm` wird aktuell als Standard-Kartengrundlage fuer die
  interaktive OSM-Ueberlagerung verwendet.
- GPS aus der Roh-CSV dient nur der Offline-Kalibrierung und nicht der
  normalen Laufzeit-Lokalisierung.

## Verarbeitungsschritte

Beim aktuellen MVP werden diese Schritte ausgefuehrt:

1. CSV-Datei erkennen und Metazeile behandeln
2. Relevante Spalten einlesen
3. Spalten in ein internes Schema umbenennen
4. `SSID + BSSID` als gemeinsame Netzwerk-ID modellieren
5. Laufzeitdaten ohne Roh-GPS bereinigen und nach Scans gruppieren
6. Aus GPS-Kalibrierungsdaten triangulierte Access-Point-Positionen schaetzen
7. Aus den triangulierten APs GPS-freie Scan-Positionen und
   Netzwerk-Beobachtungen ableiten
8. Interaktive OSM-Karte im Browser aus den triangulierten Artefakten anzeigen

## Ausgabe in `data/processed/`

Nach `py main.py` werden diese Dateien erzeugt:

- `wifi_scans_clean.csv`
- `scan_summary.csv`
- `network_observations.csv`
- `network_summary.csv`
- `triangulated_access_points.csv`
- `triangulated_scan_positions.csv`
- `dataset_summary.txt`

## Browser-Anwendung

Die Browser-Anwendung zeigt:

- den lokalen OSM-Export `map_innenstadt.osm` als Kartenbasis
- triangulierte Scan-Punkte
- triangulierte Access-Point-Positionen
- fuer ein ausgewaehltes Netzwerk die moeglichen Radiuskreise
- Ueberlappungspunkte mehrerer Kreise desselben Netzwerks
- einen GPS-freien Standort-Testrun ueber AP-Multilateration

Wichtig:

- Die Laufzeitansicht nutzt keine Roh-GPS-Koordinaten aus der Eingabe.
- GPS wird nur in `main.py` fuer die Offline-Kalibrierung der Access Points
  verwendet.
- Die Kreise beschreiben moegliche Distanzbereiche eines Scans zu einem
  Netzwerk.
- Die finale Standortschaetzung im Hauptmodus kommt aus geometrischer
  Multilateration gegen triangulierte Access Points.

## Standort-Test in der App

In der linken Seitenleiste gibt es den Bereich `Standort-Test`.

Moeglichkeiten:

- `Manuelle Eingabe`: WLAN-Werte koennen zeilenweise als `SSID,BSSID,RSSI`
  eingegeben werden. Die Positionsschaetzung laeuft dann GPS-frei gegen
  `triangulated_access_points.csv`.
- `Dev-Benchmark`: Ein vorhandener GPS-Scan wird nur fuer die Entwicklung per
  Leave-one-scan-out getestet und danach mit seiner GPS-Referenz verglichen.

Die App markiert danach:

- den geschaetzten Standort
- im Dev-Benchmark zusaetzlich den echten Referenzpunkt
- die gematchten Access Points fuer die aktuelle Schaetzung

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
py -m pip install -r requirements.txt
```

## Ausfuehrung Datenpipeline

```bash
py main.py
```

## Ausfuehrung Browser-App

```bash
py -m streamlit run app.py
```

## Tests

Lokal:

```bash
py -m pytest
```

GitHub Actions:

- Bei jedem `push` und `pull request` startet automatisch der Workflow
  `.github/workflows/ci.yml`.
- Dort werden die Abhaengigkeiten installiert und die `pytest`-Tests
  ausgefuehrt.

## Kurze Erklaerung fuer Rueckfragen

Die wichtigsten Projektentscheidungen sind kompakt dokumentiert in:

```text
docs/professor_erklaerung.txt
```

## Naechste moegliche Erweiterungen

- mehrere CSV-Dateien in `data/raw/` aufnehmen
- mehrere Messlaeufe vergleichen
- die AP-Triangulation mit staerkeren Qualitaetsmetriken absichern
- die Selbstlokalisierung mit weiteren Testlaeufen evaluieren
- optional eine Smartphone-App als zusaetzliches Projektpaket ergaenzen
