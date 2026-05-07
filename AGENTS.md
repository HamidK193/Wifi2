# AGENTS.md

## Zweck

Diese Datei enthaelt allgemeine Arbeitsregeln und den verbindlichen Projektplan
fuer dieses Repository.

## Allgemeine Arbeitsregeln

- Halte den Code einfach, lesbar und gut erweiterbar.
- Bevorzuge kleine Funktionen statt komplexer Klassenstrukturen.
- Veraendere Rohdaten in `data/raw/` niemals direkt.
- Speichere verarbeitete Daten in `data/processed/`.
- Pflege `README.md`, `memory.md` und `CHANGELOG.md` nach groesseren Schritten.
- Vermeide Overengineering. Das Projekt ist ein kleiner Kurs-MVP.
- Nutze Python 3.
- Modelliere Netzwerke ueber die Kombination `SSID + BSSID`.
- Behandle Routerstandorte nie als sicher bekannte Punkte, solange nur
  Messkreise vorliegen.

## Verbindlicher Projektplan

### Aktueller MVP

- CSV-Datei aus `data/raw/` einlesen
- Wigle-Metazeile korrekt behandeln
- beim aktuellen Standarddatensatz nur `WIFI`-Eintraege weiterverarbeiten
- ungueltige Zeitstempel wie `1970-01-01` verwerfen
- relevante Spalten bereinigen und vereinheitlichen
- `SSID + BSSID` als Netzwerkeinheit modellieren
- Messpunkte und Scans zusammenfassen
- Radiusbereiche aus RSSI abschaetzen
- OSM-Export aus `data/raw/map.osm` einlesen
- einfache Browser-App fuer WLAN-Eingabe und Standort-Schaetzung bereitstellen
- geschaetzte Position auf begehbare OSM-Strassen oder Fusswege setzen
- eigenen Tab fuer Router-Schaetzung mit Messpunkten, RSSI-Kreisen und
  geschaetztem Routerstandort bereitstellen
- eigenen Tab fuer Laufweg-Vergleich mit GPS-Route, WLAN-Route,
  Richtungspfeilen und Fehlerlinien bereitstellen
- Kreis-Ueberlagerung fuer spaetere Router- oder Standortabschaetzung
  intern vorbereiten und im Router-Schaetzungs-Tab nachvollziehbar anzeigen
- automatisierte Tests und GitHub Actions pflegen

### Relevante Quelldateien

- `main.py`
- `app.py`
- `src/load_wifi_csv.py`
- `src/evaluation.py`
- `src/localization_logic.py`
- `src/preprocess_wifi_data.py`
- `src/project_pipeline.py`
- `src/road_constraints.py`
- `src/visualize_wifi_data.py`
- `src/wifi_input_matching.py`

### Aktuelle Arbeitsschritte

1. Datensatz in `data/raw/` ablegen
2. CSV inspizieren und echte Spalten erkennen
3. Daten auf ein internes Schema abbilden
4. `SSID + BSSID` als Netzwerkeinheit modellieren
5. Scan-Zusammenfassung erzeugen
6. Netzwerk-Beobachtungen und Radius-Schaetzungen erzeugen
7. WLAN-Eingaben tolerant gegen bekannte `SSID+BSSID` matchen
8. Standort per AP-Multilateration schaetzen
9. Standort auf naechste begehbare OSM-Strasse oder Fussweg setzen
10. Einfache Browser-App ohne Analysefilter bereitstellen
11. Router-Schaetzung aus mindestens 3 RSSI-Kreisen im eigenen Tab anzeigen
12. Fallback-Schaetzung fuer weniger als 3 Kreise nachvollziehbar markieren
13. GPS-Laufweg und WLAN-Laufweg im eigenen Tab vergleichen
14. Funktionalitaet, Performance und Genauigkeit per Tests absichern
15. Dokumentation aktualisieren

### Spaetere Erweiterungen

- weitere CSV-Dateien verarbeiten
- Datenlaeufe vergleichen
- einfache Lokalisierungs-Baseline testen
- Smartphone-App nur spaeter und optional

## Handover Bei Grossem Kontext

Wenn der Kontext zu gross wird oder ein Agent die Arbeit an einen naechsten
Agenten uebergibt, muss ein kompaktes, aber vollstaendiges Handover erstellt
werden.

### Immer Einbeziehen

- `README.md`
- `AGENTS.md`
- `memory.md`
- `CHANGELOG.md`
- relevante Dateien in `src/`
- relevante Datenpfade in `data/raw/` und `data/processed/`
- offene To-dos, Fehler oder Blocker

### Handover-Regeln

- Das Handover soll kurz, klar und konkret sein.
- Bereits getroffene Entscheidungen deutlich nennen.
- Offene Aufgaben in sinnvoller Reihenfolge auffuehren.
- Wichtige Dateipfade immer explizit nennen.
- Wenn Daten oder Pakete fehlen, das klar vermerken.
