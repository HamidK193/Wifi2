# memory.md

## Projektgedaechtnis

### Projekt

- Name: `2026_ss_se_wifi_team2`
- Thema: WiFi-basierte Outdoor-Lokalisierung
- Sprache: Python 3

### Aktueller Stand

- Repository ist lokal eingerichtet und mit GitHub verbunden.
- Eine einfache Projektstruktur mit `data/`, `src/`, `docs/`, `notebooks/`
  und `tests/` wurde vorbereitet.
- Ein erster CSV-Loader liegt in `src/io/load_wifi_csv.py`.
- Eine einfache Vorverarbeitungsstruktur liegt in
  `src/preprocessing/clean_wifi_data.py`.
- `main.py` prueft bereits, ob eine CSV-Datei in `data/raw/` vorhanden ist.
- Eine echte WiFi-CSV-Datei ist aktuell noch nicht im Repository sichtbar.

### Wichtige Regeln

- Rohdaten bleiben unveraendert in `data/raw/`.
- Verarbeitete Dateien kommen nach `data/processed/`.
- Erst MVP, spaeter Erweiterungen.

### Naechste sinnvolle Schritte

- WiFi-CSV-Datei in `data/raw/` ablegen.
- Spaltennamen analysieren.
- Pruefen, ob die erste Zeile ein App-spezifischer Zusatzheader ist.
- Relevante Spalten fuer Lokalisierung identifizieren.
