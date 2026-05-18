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
  - `route_comparison.csv`
  - `route_comparison_wknn.csv`
  - `route_comparison_wknn_clean.csv`
  - `route_comparison_wknn_outliers.csv`
  - `gps_route_raw.csv`
  - `gps_route_matched.csv`
  - `route_comparison_wknn_matched.csv`
  - `route_comparison_wknn_matched_clean.csv`
  - `route_comparison_wknn_matched_outliers.csv`
  - `wifi_scans_clean.csv`
  - `scan_summary.csv`
  - `network_observations.csv`
  - `network_summary.csv`
- Die App nutzt im Hauptmodus nur noch die Artefakte aus `data/processed/`.
- Der normale Standort-Test ist GPS-frei und arbeitet ueber
  AP-Multilateration aus `SSID+BSSID+RSSI`.
- Die App nutzt `map_innenstadt.osm` als fokussierten Innenstadt-Ausschnitt.
- Die App ist jetzt eine einfache Standort-Demo ohne Analysefilter:
  WLAN-Werte eingeben, Standort schaetzen, Ergebnis auf Karte sehen.
- Zusaetzlich gibt es den Tab `Router-Schaetzung`, der bewusst wieder
  Messpunkte, RSSI-Kreise und geschaetzte Routerstandorte zeigt.
- Der Tab `Laufweg-Vergleich` zeigt echte GPS-Route gegen WLAN-geschaetzte
  Route:
  - GPS-Laufweg nach Weg-Matching rot
  - Roh-GPS optional hellrot gestrichelt
  - WLAN-Laufweg nach Weg-Matching blau
  - Abweichung zwischen beiden orange gestrichelt
  - Pfeile zeigen die Bewegungsrichtung
- Der Laufweg-Vergleich wird in `data/processed/route_comparison.csv`
  gespeichert und in der App nur geladen, nicht jedes Mal neu berechnet.
- Fuer die Anzeige nutzt die App `route_comparison_clean.csv`; entfernte
  Ausreisser werden in `route_comparison_outliers.csv` mit Grund gespeichert.
- Fuer die Standardanzeige wird inzwischen bevorzugt
  `route_comparison_wknn_matched_clean.csv` genutzt. Diese Route verwendet
  WKNN-Fingerprinting, zeitliche Glaettung und danach route-aware
  Strassen-/Fussweg-Matching fuer GPS und WLAN.
- Roh-GPS bleibt in `gps_route_raw.csv`; die plausiblere GPS-Referenz fuer
  den Vergleich liegt in `gps_route_matched.csv`.
- Die alte Triangulationsroute bleibt als Fallback und Vergleich erhalten.
- `main.py` arbeitet inkrementell: Wenn die schweren Basis-Artefakte bereits
  existieren, werden nur fehlende schnelle Runtime-Artefakte wie WKNN-Routen
  erzeugt.
- Die Router-Schaetzung nutzt GPS-Kalibrierungsdaten, nicht gesnappte
  Nutzerstandorte.
- Eine Router-Schaetzung ist erst gueltig, wenn mindestens 3 Scanpunkte fuer
  dieselbe Kombination `SSID + BSSID` vorhanden sind.
- Bei weniger als 3 Scanpunkten gibt es eine Fallback-Schaetzung:
  - 2 Kreise: Schnitt-/Zwischenpunkt
  - unsichere oder nicht beruehrende Kreise: einfache Feder-/Gewichtungslogik
  - 1 Kreis: schwache Orientierung am Messpunkt
- Routerstandorte werden nicht auf Strassen gesnappt, weil Access Points auch
  in Gebaeuden liegen koennen.
- Messpunkte, triangulierte Scan-Punkte, AP-Layer, Radiuskreise und
  Kreisueberlappungen bleiben intern, werden aber nicht mehr als UI-Filter
  angeboten.
- Eingaben werden tolerant gematcht:
  - BSSID/MAC wird normalisiert
  - SSID darf leichte Schreib- oder Leerzeichenabweichungen haben
  - RSSI darf ein neuer aktueller Messwert sein
- Die geschaetzte Position wird auf die naechste begehbare OSM-Strasse oder
  einen Fussweg gesetzt.
- `src/evaluation.py` enthaelt die testbare Logik fuer Route-Comparison,
  Fehlerkennzahlen und Radiusfilter.
- `src/wifi_input_matching.py` enthaelt die tolerante Eingabelogik.
- `src/road_constraints.py` enthaelt das Strassen-/Fussweg-Snapping.
- In `.github/workflows/ci.yml` ist ein GitHub-Action-Workflow fuer
  automatische Tests angelegt. Die CI fuehrt zusaetzlich einen schnellen
  synthetischen Pipeline-Smoke-Test aus.

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
- OSM-Karte und geschaetzte Nutzerposition einfach im Browser darstellen
- Standort-Test ohne Roh-GPS im Hauptmodus betreiben
- Router-Schaetzung mit Kreisprinzip im eigenen Tab demonstrieren
- GPS-Laufweg und WLAN-Laufweg im eigenen Tab vergleichen
- WLAN-Laufweg mit WKNN-Fingerprinting stabiler darstellen
- GPS- und WLAN-Laufweg route-aware auf begehbare Wege begrenzen
- automatische Tests und GitHub Actions stabil betreiben
- Genauigkeit und Funktionalitaet per `pytest` absichern
- Projekt klein und kursgerecht halten

### Spaetere Erweiterungen

- mehrere CSV-Dateien zusammenfuehren
- AP-Qualitaetsmetriken verbessern
- mehrere Messlaeufe vergleichen
- Smartphone-App optional spaeter ergaenzen
