# AGENTS.md

## Zweck

Diese Datei enthaelt allgemeine Arbeitsregeln und den verbindlichen Projektplan
fuer dieses Repository.

## Allgemeine Arbeitsregeln

- Halte den Code einfach, lesbar und gut erweiterbar.
- Bevorzuge kleine Funktionen statt komplexer Klassenstrukturen.
- Veraendere Rohdaten in `data/raw/` niemals direkt.
- Speichere verarbeitete Daten und Visualisierungen in `data/processed/`.
- Pflege `README.md`, `memory.md` und `CHANGELOG.md` nach groesseren Schritten.
- Vermeide Overengineering. Das Projekt ist ein kleiner Kurs-MVP.
- Nutze Python 3.

## Verbindlicher Projektplan

### Aktueller MVP

- CSV-Datei aus `data/raw/` einlesen
- Wigle-Metazeile korrekt behandeln
- relevante Spalten bereinigen und vereinheitlichen
- Messpunkte und Scans zusammenfassen
- Visualisierungen speichern
- OSM-Export aus `data/raw/map.osm` einlesen und Scan-Punkte darueberlegen

### Relevante Quelldateien

- `main.py`
- `src/load_wifi_csv.py`
- `src/preprocess_wifi_data.py`
- `src/visualize_wifi_data.py`

### Aktuelle Arbeitsschritte

1. Datensatz in `data/raw/` ablegen
2. CSV inspizieren und echte Spalten erkennen
3. Daten auf ein internes Schema abbilden
4. Bereinigte Daten in `data/processed/` speichern
5. Scan-Zusammenfassung erzeugen
6. Visualisierungen erzeugen
7. OSM-Karten mit Scan-Punkten erzeugen
8. Dokumentation aktualisieren

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
