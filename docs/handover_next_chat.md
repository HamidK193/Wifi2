# Handover fuer den naechsten Chat

## Projekt

- Repository: `2026_ss_se_wifi_team2`
- Thema: WiFi-basierte Outdoor-Lokalisierung
- Aktueller Branch: `main`
- Letzter Commit: `e0d407d Improve route matching and presentation docs`
- Git-Identitaet lokal gesetzt auf:
  - `HamidK193`
  - `karatasabdulhamid@gmail.com`

## Wichtigste Projektidee

- Ziel ist nicht nur Visualisierung, sondern grobe Selbstlokalisierung aus
  WLAN-Signalen.
- Rohdaten stammen aus WiGLE und liegen in `data/raw/`.
- GPS dient nur fuer Kalibrierung und Vergleich, die eigentliche
  WLAN-Schaetzung soll GPS-frei funktionieren.
- Netzwerke werden ueber `SSID + BSSID` identifiziert.
- RSSI ist nur eine ungenaue Distanznaeherung. Deshalb:
  - Router-Schaetzung mit Kreisen
  - Nutzer-Schaetzung zusaetzlich mit WKNN-Fingerprinting
  - zeitliche Glaettung
  - route-aware Map-Matching auf begehbare Wege

## Relevante Dateien zuerst lesen

1. `AGENTS.md`
2. `README.md`
3. `memory.md`
4. `CHANGELOG.md`
5. `docs/professor_erklaerung.txt`
6. `docs/praesentation_demo_20min.md`

## Zentrale Code-Dateien

- `main.py`
  - baut bzw. aktualisiert die Runtime-Artefakte
  - arbeitet inkrementell, damit schwere Basisdaten nicht immer neu berechnet
    werden
- `app.py`
  - Streamlit-App mit Tabs:
    - `Standort-Test`
    - `Router-Schaetzung`
    - `Laufweg-Vergleich`
- `src/localization_logic.py`
  - RSSI-Radius, Kreislogik, Router-Schaetzung, AP-Multilateration
- `src/route_estimation.py`
  - WKNN-Fingerprinting, Glaettung, Laufweg-Vergleich
- `src/road_constraints.py`
  - Snapping und route-aware Map-Matching auf begehbare OSM-Wege
- `src/project_pipeline.py`
  - erzeugt und laedt Dateien aus `data/processed/`
- `src/visualize_wifi_data.py`
  - Kartenaufbau und Laufweg-Visualisierung

## Relevante Rohdaten

- `data/raw/WigleWifi_20260408161721.csv`
- `data/raw/map_innenstadt.osm`

## Wichtige verarbeitete Dateien

- `wifi_scans_clean.csv`
- `triangulated_access_points.csv`
- `triangulated_scan_positions.csv`
- `gps_route_raw.csv`
- `gps_route_matched.csv`
- `route_comparison_wknn.csv`
- `route_comparison_wknn_clean.csv`
- `route_comparison_wknn_matched.csv`
- `route_comparison_wknn_matched_clean.csv`
- `route_comparison_wknn_matched_outliers.csv`

## App-Stand

### Standort-Test

- Nutzer gibt `SSID,BSSID,RSSI` ein.
- Eingabe wird tolerant gematcht.
- Standort wird aus triangulierten APs geschaetzt.
- Nutzerstandort wird auf begehbaren Weg gesnappt.

### Router-Schaetzung

- Filter nach SSID und BSSID.
- Messpunkte, Kreise, Ueberlappung und geschaetzter Routerstandort sichtbar.
- Ab 3 Kreisen regulaere Schaetzung.
- Bei weniger Kreisen Fallback:
  - 1 Kreis: schwache Orientierung
  - 2 Kreise: Schnitt-/Zwischenpunkt oder Federlogik
- Router werden nicht auf Strassen gesnappt.

### Laufweg-Vergleich

- rote Linie: gematchte GPS-Referenzroute
- hellrot gestrichelt: Roh-GPS
- blau: WLAN-Laufweg
- orange gestrichelt: Fehler zwischen GPS und WLAN
- Standarddatei:
  - `route_comparison_wknn_matched_clean.csv`
- Unter der Karte gibt es eine Legende.

## Tests und GitHub Action

- Lokaler Testbefehl:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

- Aktuell erfolgreich:
  - `48 passed`
- GitHub Action:
  - `.github/workflows/ci.yml`
  - laeuft bei Push und Pull Request auf `main` und `master`
  - fuehrt Pipeline-Smoke-Test und komplette `pytest`-Suite aus

## Startbefehle

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Aktuelle fachliche Entscheidungen

- `SSID + BSSID` ist die Netzwerkeinheit.
- Rohdaten in `data/raw/` niemals direkt aendern.
- Nutzerpositionen auf begehbare Wege setzen.
- Routerpositionen nicht auf Wege setzen.
- Standard-Laufweg-Vergleich bevorzugt WKNN + route-aware Map-Matching.
- Teure Berechnungen nicht live im Browser ausfuehren, sondern vorberechnen und
  CSV-Dateien laden.
- Ausreisser separat dokumentieren, nicht stillschweigend aus Rohdaten loeschen.

## Bekannte offene Probleme / naechste sinnvolle Aufgabe

### 1. Orange Fehlerlinien im Laufweg-Vergleich noch teilweise zu lang

- Problem:
  - Auf der Karte gibt es weiterhin sehr lange orange gestrichelte Linien.
  - Diese zeigen grosse Abweichungen zwischen GPS-Referenz und WLAN-Schaetzung.
- Bereits analysiert:
  - Ursache ist nicht nur GPS, sondern vor allem mehrdeutige WLAN-Fingerprints
    und zu punktweise WKNN-Schaetzung.
  - In der bereinigten matched Route bleiben noch Fehler bis ca. `89 m`.
  - In den Outlier-Dateien existieren noch deutlich groessere Fehler.
- Naechster guter Schritt:
  - WKNN nicht nur pro Scan einzeln anwenden, sondern route-aware:
    mehrere Kandidaten pro Scan + plausible Gesamtbewegung auswaehlen.
  - Zusaetzlich:
    - strengere Demo-Filter testen
    - grosse Fehlerlinien optional nicht auf Hauptkarte zeichnen
    - Punkte mit unsauberem Snap gesondert behandeln

### 2. Praesentation weiter vorbereiten

- `docs/praesentation_demo_20min.md` existiert bereits.
- Der Professor erwartet:
  - Thema erklaeren
  - Codeablauf in Schritten zeigen
  - Triangulation und Mapping erklaeren
  - mindestens eine Funktion live testen
  - GitHub Action nach Push auf Hauptbranch zeigen
- Gute Live-Testfunktion:
  - `estimate_radius_from_rssi()`
- Guter Einzeltest:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_localization_logic.py::test_estimate_radius_from_rssi_shrinks_for_stronger_signal
```

## Achtung im Worktree

- Ungetrackter Ordner vorhanden:
  - `deliverables_biopure_literatur/`
- Dieser gehoert fachlich nicht zum WiFi-Projekt und wurde bewusst nicht
  committed.

## Handover-Prompt fuer den naechsten Agenten

```text
Arbeite im Repository `2026_ss_se_wifi_team2`.

Lies zuerst:
1. AGENTS.md
2. README.md
3. memory.md
4. CHANGELOG.md
5. docs/professor_erklaerung.txt
6. docs/handover_next_chat.md

Aktueller Stand:
- letzter Commit: e0d407d
- Branch: main
- Streamlit-App mit Standort-Test, Router-Schaetzung und Laufweg-Vergleich
- Laufweg-Vergleich nutzt bevorzugt WKNN + route-aware Map-Matching
- Tests zuletzt gruen: 48 passed

Wichtige offene Aufgabe:
- Die orange gestrichelten Fehlerlinien im Laufweg-Vergleich sind teils noch
  zu lang. Analysiere und verbessere die WLAN-Routenlogik, am besten durch
  route-aware WKNN mit mehreren Kandidaten pro Scan und Bewegungsplausibilitaet.

Wichtige Regeln:
- Rohdaten in data/raw/ nicht veraendern.
- `SSID + BSSID` bleibt Netzwerkeinheit.
- Router nicht auf Strassen snappen.
- Nutzerpositionen auf begehbare Wege setzen.
- `deliverables_biopure_literatur/` ignorieren.
- Nach groesseren Schritten README.md, memory.md und CHANGELOG.md pflegen.
```
