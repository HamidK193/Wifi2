# AGENTS.md

## Zweck

Diese Datei enthaelt allgemeine Arbeitsregeln fuer Personen und spaetere
KI-Agenten, die an diesem Repository arbeiten.

## Allgemeine System Instructions

- Halte den Code einfach, lesbar und gut erweiterbar.
- Bevorzuge kleine Funktionen statt komplexer Klassenstrukturen.
- Veraendere Rohdaten in `data/raw/` niemals direkt.
- Speichere aufbereitete Daten nur in `data/processed/`.
- Dokumentiere wichtige Projektentscheidungen im `README.md`.
- Pflege den aktuellen Projektkontext in `memory.md`.
- Trage relevante Aenderungen im `CHANGELOG.md` ein.
- Fuehre neue Schritte nachvollziehbar und schrittweise ein.
- Vermeide Overengineering und unnoetige Abhaengigkeiten.
- Nutze Python 3.

## Arbeitsweise

1. Zuerst bestehende Struktur und Dateien verstehen.
2. Danach nur die minimal notwendigen Aenderungen vornehmen.
3. Neue Dateien und Funktionen klar benennen.
4. Dokumentation aktuell halten.

## Handover Bei Grossem Kontext

Wenn der Kontext zu gross wird oder ein Agent die Arbeit an einen naechsten
Agenten uebergibt, muss ein kompaktes, aber vollstaendiges Handover erstellt
werden.

### Ziel des Handovers

Der naechste Agent soll ohne lange Rueckfragen verstehen:

- worum es im Projekt geht
- was bereits umgesetzt wurde
- welche Dateien relevant sind
- welche Annahmen gelten
- was als naechstes zu tun ist
- welche Probleme, Risiken oder offenen Fragen bestehen

### Immer Einbeziehen

Das Handover soll diese Dateien und Inhalte beruecksichtigen, wenn vorhanden:

- `README.md`
- `AGENTS.md`
- `memory.md`
- `CHANGELOG.md`
- relevante Dateien in `src/`
- relevante Datenpfade in `data/raw/` und `data/processed/`
- offene To-dos, Fehler oder Blocker

### Handover-Regeln

- Das Handover soll kurz, klar und konkret sein.
- Keine irrelevanten Details aufnehmen.
- Bereits getroffene Entscheidungen deutlich nennen.
- Offene Aufgaben in sinnvoller Reihenfolge auffuehren.
- Wichtige Dateipfade immer explizit nennen.
- Wenn Daten fehlen, das klar vermerken.

### Handover Prompt Vorlage

```text
Du uebernimmst das Projekt `2026_ss_se_wifi_team2`.

Projektkontext:
- Thema: WiFi-basierte Outdoor-Lokalisierung mit Python
- Ziel: WiFi-Messdaten sauber einlesen, verstehen, vorbereiten und spaeter fuer Lokalisierung und Auswertung nutzen

Lies zuerst diese Dateien:
- README.md
- AGENTS.md
- memory.md
- CHANGELOG.md

Danach pruefe diese relevanten Projektbereiche:
- main.py
- src/io/
- src/preprocessing/
- src/visualization/
- data/raw/
- data/processed/

Aktueller Stand:
- [hier den aktuellen technischen Stand in 3 bis 8 Punkten einfuegen]

Wichtige Entscheidungen und Regeln:
- Rohdaten in `data/raw/` nicht veraendern
- Verarbeitete Daten in `data/processed/` speichern
- Keine unnoetige Komplexitaet, zuerst MVP
- Einfache Funktionen statt Overengineering

Offene Aufgaben:
1. [naechste konkrete Aufgabe]
2. [danach folgende Aufgabe]
3. [optionale weitere Aufgabe]

Offene Fragen oder Risiken:
- [offene Frage oder Risiko]

Wichtige Hinweise:
- [z. B. fehlende CSV-Datei, fehlendes Paket, bekannte Annahmen]

Arbeite auf Basis des vorhandenen Codes weiter und vermeide unnoetige Umstrukturierungen.
```

## Aktueller Fokus

- WiFi-CSV-Datei einlesen
- Spalten analysieren
- einfache Datenvorbereitung schaffen
- Grundlage fuer spaetere Auswertung und Lokalisierung aufbauen
