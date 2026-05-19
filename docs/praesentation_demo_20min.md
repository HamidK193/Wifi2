# Praesentation und Live-Demo fuer den Professor

Diese Datei beschreibt einen moeglichen 20-Minuten-Ablauf fuer die Vorstellung
des Projekts. Ziel ist, nicht nur die App zu zeigen, sondern nachvollziehbar zu
erklaeren, wie aus Code, Tests und GitHub Actions ein gepruefter Softwarestand
entsteht.

## 1. Einstieg: Was ist das Ziel? ca. 2 Minuten

- Thema: WiFi-basierte Outdoor-Lokalisierung.
- Idee: Ein Smartphone sieht WLAN-Netzwerke mit `SSID`, `BSSID` und `RSSI`.
- Aus der Signalstaerke wird kein exakter Standort, sondern nur eine
  unsichere Distanz abgeleitet.
- Mehrere Signale zusammen ergeben eine grobe Standort-Schaetzung.
- GPS wird im Projekt nur zur Kalibrierung und zum Vergleich verwendet.

Wichtiger Satz:

> RSSI ist wie Lautstaerke: nah ist meistens lauter, weit weg meistens leiser,
> aber Waende, Menschen und Umgebung stoeren stark.

## 2. Datenpipeline zeigen ca. 3 Minuten

In VS Code `main.py` zeigen.

Erklaeren:

- CSV wird eingelesen.
- WiGLE-Metazeile wird erkannt.
- Nur `WIFI` wird verwendet.
- Ungueltige Zeitstempel werden entfernt.
- `SSID + BSSID` wird als eindeutige Netzwerkeinheit genutzt.
- Ergebnisse werden in `data/processed/` gespeichert.

Terminal-Befehl:

```powershell
.\.venv\Scripts\python.exe main.py
```

Was man danach zeigt:

- `data/processed/wifi_scans_clean.csv`
- `data/processed/triangulated_access_points.csv`
- `data/processed/gps_route_matched.csv`
- `data/processed/route_comparison_wknn_matched_clean.csv`

## 3. Eine konkrete Funktion testen ca. 4 Minuten

Gute Funktion fuer die Live-Demo:

```python
estimate_radius_from_rssi()
```

Datei:

```text
src/localization_logic.py
```

Test:

```text
tests/test_localization_logic.py
```

Warum diese Funktion gut ist:

- Sie ist fachlich leicht erklaerbar.
- Sie uebersetzt RSSI in einen Radius.
- Sie zeigt direkt das Lautstaerke-Prinzip.
- Der Test ist kurz und verstaendlich.

Live-Test nur fuer diese Funktion:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_localization_logic.py::test_estimate_radius_from_rssi_shrinks_for_stronger_signal
```

Erwartete Aussage:

- Starkes Signal, z. B. `-50 dBm`, ergibt kleineren Radius.
- Schwaches Signal, z. B. `-80 dBm`, ergibt groesseren Radius.

## 4. Triangulation und Router-Schaetzung zeigen ca. 4 Minuten

In VS Code zeigen:

```text
src/localization_logic.py
```

Wichtige Funktionen:

- `estimate_radius_from_rssi()`
- `triangulate_access_points()`
- `estimate_router_position_from_observations()`
- `estimate_position_from_access_points()`

Erklaerung:

- Ein Messpunkt erzeugt einen Kreis.
- Ein Kreis allein reicht nicht fuer einen Routerstandort.
- Mehrere Kreise derselben `SSID+BSSID`-Einheit werden kombiniert.
- Der wahrscheinlichste Routerstandort ist der Punkt, der am besten zu allen
  Kreisen passt.
- Mindestens 3 Scans sind nur die Mindestvoraussetzung. Fuer gute
  Lokalisierung ist zusaetzlich wichtig, dass die Router-Kalibrierung einen
  niedrigen RMSE hat.
- In den aktuellen Messdaten sind die guten Streckenabschnitte vor allem dort,
  wo die gesehenen Router im Mittel besser kalibriert sind; viele Scans allein
  garantieren noch keine gute Routerposition.
- Router duerfen in Gebaeuden liegen, deshalb werden Router nicht auf Strassen
  verschoben.

Passender Test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_localization_logic.py::test_router_position_requires_at_least_three_scan_points
```

## 5. Mapping und Laufweg-Vergleich zeigen ca. 4 Minuten

In der App den Tab `Laufweg-Vergleich` zeigen.

Start:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Erklaeren:

- Rote Linie: GPS-Referenzroute auf begehbare Wege gematcht.
- Hellrot gestrichelt: Roh-GPS vor dem Weg-Matching.
- Blaue Linie: WLAN-geschaetzte Route.
- Orange gestrichelt: Fehler zwischen GPS und WLAN.
- Gruene/blaue/orange/rote Punkte: Qualitaet der WLAN-Schaetzung.

Wichtige Logik:

- GPS ist in der Stadt verrauscht und kann neben dem echten Weg liegen.
- Deshalb wird GPS fuer den Vergleich auf plausible Wege gesetzt.
- WLAN wird ebenfalls auf begehbare Wege gesetzt, weil der Mensch draussen auf
  Fusswegen oder Strassen laeuft.
- Der Vergleich ist dadurch fairer als Roh-GPS gegen WLAN.
- Wenn der Professor nach den noch sichtbaren Fehlerlinien fragt:
  Router mit mindestens 3 Scans sind bereits gefiltert, aber die Analyse zeigt,
  dass Abschnitte mit niedrigerem Router-RMSE deutlich bessere WLAN-Punkte
  liefern als Abschnitte mit vielen `weak`-Routern.
- Fuer die aktuelle Demo-Ansicht werden deshalb nur noch WLAN-Punkte gezeigt,
  deren gesehene Router einen medianen Kalibrierungs-RMSE von hoechstens
  `15 m` haben.

Passender Test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_road_constraints.py::test_route_matching_keeps_route_on_plausible_same_way
```

## 6. Gesamte Testsuite und GitHub Actions ca. 3 Minuten

Lokal zeigen:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Erklaeren:

- Tests pruefen CSV-Import, Bereinigung, Triangulation, Mapping,
  WLAN-Matching, Laufweg-Vergleich und App-Import.
- Damit sehen wir frueh, wenn eine Codeaenderung etwas kaputt macht.

GitHub Action zeigen:

Datei:

```text
.github/workflows/ci.yml
```

Erklaeren:

- Bei Push auf `main` oder `master` startet GitHub automatisch die Tests.
- Bei Pull Requests auf `main` oder `master` startet GitHub ebenfalls die Tests.
- GitHub richtet Python ein, installiert Abhaengigkeiten und fuehrt `pytest`
  aus.

Wichtige Stelle:

```yaml
on:
  push:
    branches: ["main", "master"]
  pull_request:
    branches: ["main", "master"]
```

Demo-Aussage:

> Wenn wir eine Aenderung pushen, prueft GitHub automatisch, ob die Pipeline
> und unsere Lokalisierungsfunktionen noch funktionieren.

## 7. Falls der Professor eine echte Live-Aenderung sehen will

Nur machen, wenn genug Zeit ist.

Sicherer Ablauf:

1. In einem Test kurz einen erwarteten Wert kaputt machen.
2. Test lokal laufen lassen und zeigen, dass er fehlschlaegt.
3. Wert wieder korrigieren.
4. Test erneut laufen lassen und zeigen, dass er gruen wird.
5. Danach committen und pushen.
6. Auf GitHub zeigen, dass die Action automatisch startet.

Nicht empfohlen:

- In der Praesentation echte Produktlogik kaputt editieren.
- Grosse Datenpipeline live neu berechnen.
- Neue CSV-Dateien live aufnehmen.

## Kurzer Praesentationstext fuer das Fazit

Unser Projekt zeigt eine komplette kleine Software-Engineering-Kette:

- Daten aufnehmen
- Daten bereinigen
- RSSI in Radiuslogik uebersetzen
- Router und Nutzerposition grob schaetzen
- GPS und WLAN auf einer Karte vergleichen
- Ausreisser und Ungenauigkeiten sichtbar machen
- Funktionen automatisch testen
- GitHub Actions als automatische Qualitaetskontrolle nutzen
