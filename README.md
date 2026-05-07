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
  - einen einfachen GPS-freien Standort-Test ueber `SSID,BSSID,RSSI`
  - einen eigenen Tab `Router-Schaetzung` fuer Messkreise und geschaetzte
    Router-/Access-Point-Standorte
  - einen Tab `Laufweg-Vergleich` fuer GPS-Route gegen WLAN-geschaetzte Route
  - tolerantes Matching fuer aehnliche SSID- und BSSID-Schreibweisen
  - Snapping der Schaetzung auf die naechste begehbare Strasse oder Fussweg
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
|  |  |- route_comparison.csv
|  |  |- dataset_summary.txt
|- docs/
|  |- professor_erklaerung.txt
|- src/
|  |- __init__.py
|  |- evaluation.py
|  |- fingerprint_localization.py
|  |- load_wifi_csv.py
|  |- localization_logic.py
|  |- preprocess_wifi_data.py
|  |- project_pipeline.py
|  |- road_constraints.py
|  |- visualize_wifi_data.py
|  |- wifi_input_matching.py
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
- `route_comparison.csv`
- `dataset_summary.txt`

## Browser-Anwendung

Die Browser-Anwendung ist bewusst einfach gehalten:

- WLAN-Werte im Format `SSID,BSSID,RSSI` eingeben
- auf `Standort schaetzen` klicken
- geschaetzten Standort auf der Karte sehen
- Ergebnis liegt auf der naechsten begehbaren Strasse oder einem Fussweg
- technische Details sind nur in einem ausklappbaren Bereich sichtbar

Die App zeigt keine Analysefilter fuer Messpunkte, triangulierte Scan-Punkte,
Access-Point-Layer, Radiuskreise oder Kreisueberlappungen mehr. Diese Daten
bleiben intern wichtig fuer Kalibrierung und Tests, werden aber nicht mehr als
Hauptbedienung angeboten.

Ausnahme:

- Im Tab `Router-Schaetzung` werden diese Messkreise bewusst wieder sichtbar,
  weil dort das Professor-Prinzip demonstriert wird: mehrere RSSI-Kreise
  desselben `SSID+BSSID`-Netzwerks ergeben einen geschaetzten Routerstandort.

Wichtig:

- Die Laufzeitansicht nutzt keine Roh-GPS-Koordinaten aus der Eingabe.
- GPS wird nur in `main.py` fuer die Offline-Kalibrierung der Access Points
  verwendet.
- Die finale Standortschaetzung im Hauptmodus kommt aus geometrischer
  Multilateration gegen triangulierte Access Points.
- Die angezeigte Position wird anschliessend auf einen begehbaren OSM-Weg
  projiziert, weil die Person realistisch auf Strassen oder Fusswegen laeuft.

## Standort-Test in der App

In der linken Seitenleiste gibt es nur noch:

- Textfeld fuer WLAN-Werte
- Regler fuer minimale AP-Treffer
- Button `Standort schaetzen`

Die Eingabe darf leicht von den Kalibrierungsdaten abweichen:

- BSSID/MAC darf mit `:`, `-`, Gross- oder Kleinschreibung eingegeben werden
- SSID darf kleine Schreib- oder Leerzeichenabweichungen haben
- RSSI ist der aktuelle Messwert und muss nicht exakt einem alten Wert
  entsprechen

## Router-Schaetzung in der App

Der Tab `Router-Schaetzung` zeigt, wie Access-Point-/Routerstandorte aus den
Kalibrierungsdaten geschaetzt werden:

- nach `SSID` und `BSSID / Router` filtern
- Messpunkte des gewaehlten Netzwerks sehen
- RSSI-Radiuskreise um die Messpunkte sehen
- geschaetzten Routerstandort sehen, sobald mindestens 3 Scanpunkte vorhanden
  sind
- bei weniger als 3 Scanpunkten eine einfache Fallback-Schaetzung sehen:
  Schnitt-/Zwischenpunkt bei 2 Kreisen oder Feder-/Gewichtungslogik bei
  unsicheren Kreisen
- Schnitt-/Ueberlappungspunkte werden nur bei mindestens 3 stuetzenden Kreisen
  als relevant angezeigt

Wichtig:

- Routerstandorte werden nicht auf Strassen gesnappt.
- Router duerfen logisch in Gebaeuden liegen.
- Die Kreisfarben richten sich nach der SSID.
- Die eindeutige technische Einheit bleibt trotzdem `SSID + BSSID`.

## Laufweg-Vergleich in der App

Der Tab `Laufweg-Vergleich` zeigt zwei Routen:

- rote Linie: echter GPS-Laufweg aus den Kalibrierungsdaten
- blaue Linie: WLAN-geschaetzter Laufweg
- orange Linien: Abweichung zwischen GPS-Punkt und WLAN-Schaetzung
- Pfeile auf den Linien zeigen die Laufrichtung

Die WLAN-Route wird mit einer einfachen Feder-/Kreislogik berechnet:

- starke Signale ziehen die Schaetzung staerker zu einem Access Point
- schwache Signale ziehen weniger stark
- ab mehreren APs wird der Punkt gesucht, der am besten zu den RSSI-Radien
  passt
- die resultierende Nutzerposition wird danach auf Strasse/Fussweg gesnappt

Der Laufweg-Vergleich wird nicht bei jedem App-Start neu berechnet. `main.py`
erzeugt die Datei `data/processed/route_comparison.csv`; die App laedt danach
nur noch diese gespeicherten Daten.

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
- Dort werden die Abhaengigkeiten installiert, ein schneller synthetischer
  Pipeline-Smoke-Test ausgefuehrt und danach die `pytest`-Tests gestartet.
- Die Tests pruefen Import, Bereinigung, Pipeline, AP-Triangulation,
  Standort-Schaetzung, tolerantes WLAN-Matching, Strassen-Snapping,
  Route-Comparison, Radiusfilter und einfache Genauigkeitskennzahlen.

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
