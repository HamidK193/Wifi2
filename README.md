# 2026_ss_se_wifi_team2

Projekt von Team 2 im Kurs Software Engineering.

## Projektthema

WiFi-basierte Outdoor-Lokalisierung mit Python.

## Ziel

Ziel des Projekts ist zu untersuchen, ob WiFi-Signale fuer eine kostenguenstige
Outdoor-Lokalisierung genutzt werden koennen. Dafuer bauen wir schrittweise eine
saubere Datenbasis auf: Rohdaten einlesen, verstehen, vorbereiten und spaeter
fuer Auswertung und Lokalisierung verwenden.

## Aktueller Stand

- GitHub-Repository ist eingerichtet.
- Die lokale Python-Umgebung funktioniert.
- Das Repository ist lokal geklont und mit GitHub verbunden.
- Erste kleine Python-Dateien aus den Uebungsaufgaben sind vorhanden.
- Die Zielstruktur fuer das Projekt wird vorbereitet.
- Eine WiFi-CSV-Datei soll im naechsten Schritt in `data/raw/` abgelegt und
  analysiert werden.

## Projektstruktur

```text
2026_ss_se_wifi_team2/
|- AGENTS.md
|- memory.md
|- CHANGELOG.md
|- README.md
|- .gitignore
|- main.py
|- data/
|  |- raw/
|  |- processed/
|- docs/
|- notebooks/
|- src/
|  |- __init__.py
|  |- io/
|  |  |- __init__.py
|  |  |- load_wifi_csv.py
|  |- preprocessing/
|  |  |- __init__.py
|  |  |- clean_wifi_data.py
|  |- visualization/
|  |  |- __init__.py
|  |  |- plot_wifi_data.py
|- tests/
|- task1.py
|- task2_vending_machine.py
```

## Projektdateien

- `README.md`: zentrale Projektbeschreibung
- `AGENTS.md`: allgemeine Arbeitsregeln und System Instructions
- `memory.md`: kompaktes Projektgedaechtnis mit aktuellem Stand
- `CHANGELOG.md`: Protokoll wichtiger Aenderungen

## Hinweise zur Datenablage

- Rohdaten werden unveraendert in `data/raw/` abgelegt.
- Verarbeitete Daten werden in `data/processed/` gespeichert.
- Falls die CSV-Datei aus einer Android-App stammt, kann die erste Zeile ein
  zusaetzlicher Header sein und beim Einlesen optional uebersprungen werden.

## Benoetigte Python-Pakete

Fuer den CSV-Import wird `pandas` verwendet.

## Naechste Schritte

1. WiFi-CSV-Datei in `data/raw/` ablegen.
2. CSV mit `src/io/load_wifi_csv.py` einlesen.
3. Vorhandene Spalten identifizieren, zum Beispiel MAC-Adresse, SSID, RSSI,
   Latitude, Longitude, Timestamp und Frequency oder Channel.
4. Erste einfache Bereinigung und Auswahl relevanter Spalten vorbereiten.
5. Danach eine Grundlage fuer Visualisierung und spaetere Lokalisierung
   schaffen.
