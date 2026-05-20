# Abgabeordner für die Präsentation

Dieser Ordner bündelt die wichtigsten Dateien für die Abgabe und Erklärung des Projekts
„WiFi-basierte Outdoor-Lokalisierung“.

## Inhalt

- `01_Praesentation/`
  - Hier liegt die PowerPoint-Datei, falls im Projekt eine `.pptx` vorhanden ist.
  - Aktuell wurde im Repository keine fertige `.pptx` gefunden.
  - Die vorbereiteten Foliengrafiken liegen deshalb in `03_Grafiken/`.

- `02_Word_Dokumente_KORRIGIERT/`
  - Diese Word-Dokumente bitte für die Abgabe verwenden.
  - Erklärende Word-Dokumente zur Pipeline, zum Laufwegvergleich, zu WKNN,
    zu Softwaretests und zu GitHub Actions.
  - Die Dokumente wurden direkt in der DOCX-Struktur auf deutsche Umlaute geprüft.

- `02_Word_Dokumente/`
  - Nur alte Arbeitskopien.
  - Falls Word eine Datei noch geöffnet hatte, konnte Windows sie nicht direkt
    überschreiben. Deshalb liegen die sauberen Endversionen im korrigierten Ordner.

- `03_Grafiken/`
  - Fertige Visualisierungen für die Präsentation.
  - Enthält unter anderem Grafiken zu WKNN, Router-Standortschätzung,
    Map-Matching/Snapping, Pipeline, Ausreißerbehandlung und SSID+BSSID.

- `04_Projekt_Dokumentation/`
  - README, Projektregeln, Changelog, Memory-Datei und Erklärungstexte.
  - Diese Dateien helfen, den Projektstand und die technischen Entscheidungen
    nachvollziehbar zu erklären.

- `05_Testnachweis/`
  - `pytest_ausgabe.txt` enthält den aktuellen Testlauf.
  - Ergebnis beim Erstellen dieses Ordners: `51 passed`.

## Wichtige Projektpunkte

- Rohdaten in `data/raw/` werden nicht direkt verändert.
- WLAN-Netzwerke werden über `SSID + BSSID` als `network_id` modelliert.
- Routerstandorte werden aus RSSI-Radien geschätzt und nicht auf Straßen gesnappt.
- Nutzerpositionen und Laufwege werden auf begehbare OSM-Wege gematcht.
- Der Laufwegvergleich nutzt WKNN-Fingerprinting, Glättung und Map-Matching.
- GitHub Actions startet die Tests automatisch über `main.py`.

## Startbefehle

Pipeline und Tests:

```powershell
.\.venv\Scripts\python.exe main.py
```

Nur Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Streamlit-App:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
