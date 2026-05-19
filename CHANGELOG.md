# CHANGELOG.md

Alle wichtigen Aenderungen am Projekt werden hier kurz protokolliert.

## 2026-05-18

- Code vereinfacht: gemeinsame Laufweg-Artefakt-Erzeugung eingefuehrt und
  doppelte Ausreisserlogik zusammengezogen.
- Fachfremde `Abgaben/`-Uebungsdateien entfernt, damit das Repository den
  WLAN-MVP klarer zeigt.
- kompaktes Handover fuer den naechsten Chat in
  `docs/handover_next_chat.md` dokumentiert.
- README und Projektgedaechtnis um den Handover-Verweis, `route_estimation.py`
  und den naechsten fachlichen Schwerpunkt fuer die WLAN-Routenlogik ergaenzt.
- WKNN-Fingerprinting so verschaerft, dass Netzwerke mit weniger als
  3 Kalibrierungs-Scans nicht mehr in die WLAN-Routenlogik eingehen.
- `main.py` aktualisiert schnelle WKNN-Laufweg-Artefakte nun bei jedem Lauf
  neu, damit Logikaenderungen nicht an alten CSV-Dateien haengen bleiben.
- Dokumentation erweitert: 3 Scans sind nur die Mindestbedingung; fuer gute
  Streckenabschnitte ist niedriger Router-RMSE aussagekraeftiger als reine
  Scan-Anzahl.
- Laufweg-Demo weiter verschaerft: bereinigte WKNN-Routen behalten nur noch
  Scans mit `median_router_rmse_m <= 15`, sodass schwach kalibrierte
  Routerbereiche aus der Hauptansicht verschwinden.

## 2026-05-12

- route-aware Map-Matching fuer GPS- und WLAN-Laufweg ergaenzt:
  GPS wird auf plausible begehbare Wege gesetzt, WLAN danach ebenfalls.
- neue Artefakte erzeugt: `gps_route_raw.csv`, `gps_route_matched.csv`,
  `route_comparison_wknn_matched.csv`,
  `route_comparison_wknn_matched_clean.csv` und
  `route_comparison_wknn_matched_outliers.csv`.
- Laufweg-Tab nutzt bevorzugt die matched WKNN-Route und zeigt unter der Karte
  eine Legende fuer Farben, Strichelungen und Punktqualitaet.
- WKNN-Fingerprinting fuer den Laufweg-Vergleich ergaenzt:
  aehnliche RSSI-Fingerabdruecke aus Referenzscans werden gewichtet gemittelt.
- Laufweg-Schaetzungen werden nach WKNN zeitlich geglaettet und danach wieder
  auf begehbare OSM-Wege gesnappt.
- neue gespeicherte Artefakte erzeugt:
  `route_comparison_wknn.csv`, `route_comparison_wknn_clean.csv` und
  `route_comparison_wknn_outliers.csv`.
- App nutzt im Laufweg-Tab bevorzugt die bereinigte WKNN-Route und faellt bei
  fehlender Datei auf die alte Triangulationsroute zurueck.
- rechte Laufweg-Auswertung erweitert um aktive Methode, Rohpunkte,
  entfernte Ausreisser, 90%-Fehler und Qualitaetslabel.
- `main.py` inkrementell gemacht: vorhandene schwere Basisdaten werden
  wiederverwendet, fehlende Laufweg-Artefakte werden schnell nacherzeugt.
- Tests fuer WKNN, Glaettung und Laufweg-Qualitaet ergaenzt.

## 2026-05-07

- neuen Tab `Laufweg-Vergleich` ergaenzt: reale GPS-Route als rote Linie,
  WLAN-geschaetzte Route als blaue Linie und orange Abweichungslinien mit
  Richtungspfeilen.
- `route_comparison.csv` als gespeichertes Runtime-Artefakt ergaenzt, damit
  der Laufweg-Vergleich nicht bei jedem App-Start neu berechnet wird.
- Laufweg-Karte performanter gemacht: falsches Weit-Snapping auf entfernte
  OSM-Wege verhindert und Detailmarker/Fehlerlinien reduziert.
- Ausreisser-Filter fuer den Laufweg-Vergleich ergaenzt:
  `route_comparison_clean.csv` fuer die App und
  `route_comparison_outliers.csv` fuer entfernte Punkte mit Begruendung.
- Feder-/Fallback-Logik fuer wenige Kreise ergaenzt: bei 2 Kreisen wird ein
  Schnitt-/Zwischenpunkt genutzt, bei unsicheren Kreisen eine gewichtete
  Feder-Schaetzung.
- Standort-Schaetzung kann nun auch mit weniger als 3 Treffern eine schwache
  Fallback-Schaetzung liefern, wenn der Nutzer die Mindesttreffer entsprechend
  niedrig setzt.
- Tests fuer WLAN-Laufweg und Fallback-Schaetzung ergaenzt.
- neuen App-Tab `Router-Schaetzung` ergaenzt: SSID/BSSID filtern,
  Messpunkte, RSSI-Kreisradien, Ueberlappung und geschaetzten Routerstandort
  anzeigen.
- Router-Schaetzung nutzt mindestens 3 Scanpunkte derselben `SSID+BSSID`-
  Einheit und snappt Router nicht auf Strassen, da Router auch in Gebaeuden
  liegen koennen.
- Overlap-Logik erweitert: Ueberlappungspunkte koennen jetzt explizit
  mindestens 3 stuetzende Kreise verlangen.
- Tests fuer Router-Schaetzung, Mindestanzahl an Scanpunkten und
  3-Kreis-Ueberlappung ergaenzt.
- App auf eine einfache Standort-Demo reduziert: WLAN-Werte eingeben,
  `Standort schaetzen`, Ergebnis auf Karte sehen.
- Analysefilter fuer SSID, BSSID, Messpunkte, triangulierte Punkte, AP-Layer,
  Radiuskreise und Kreisueberlappungen aus der Hauptbedienung entfernt.
- Tolerantes WLAN-Matching ergaenzt: BSSID-Format wird normalisiert, SSID darf
  leichte Schreib- oder Leerzeichenabweichungen haben.
- Strassen-Snapping ergaenzt: die geschaetzte Position wird auf den naechsten
  begehbaren OSM-Weg gesetzt.
- Tests fuer Matching, Strassen-Snapping und den einfachen Standortfluss
  ergaenzt.

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
