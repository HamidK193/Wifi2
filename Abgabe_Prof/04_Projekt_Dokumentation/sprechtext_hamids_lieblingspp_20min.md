# Sprechtext zur Präsentation `Hamids_Lieblingspp.pptx`

Zielzeit: ca. 20 Minuten  
Fokus: technische Umsetzung des WiFi-Lokalisierungsprojekts  
Hinweis: Der fachliche Präsentationsteil liegt auf Folie 1 bis 21. Die Folien ab 22 wirken wie Template-/Infografik-Restfolien und sind hier nicht eingeplant.

## Folie 1 - Einstieg und Thema

Guten Tag zusammen, wir stellen heute unser Projekt zur WiFi-basierten Outdoor-Lokalisierung vor. Die Grundidee ist, dass man eine Position nicht nur über GPS bestimmen kann, sondern auch über WLAN-Signale, die in der Umgebung sichtbar sind.

Unser System nutzt dafür WLAN-Messdaten aus der WiGLE-App. Diese App speichert unter anderem, welche WLAN-Netzwerke an einem bestimmten Ort sichtbar waren und wie stark deren Signal war. Aus diesen Informationen bauen wir eine kleine Python-Pipeline und eine Streamlit-Webanwendung.

Wichtig ist direkt am Anfang: Wir behaupten nicht, dass WLAN-Signale eine perfekte oder zentimetergenaue Position liefern. WLAN ist stark von Umgebung, Gebäuden, Reflexionen und Messfehlern abhängig. Deshalb geht es bei unserem Projekt um eine nachvollziehbare technische Schätzung: Daten einlesen, bereinigen, Netzwerke erkennen, Routerpositionen annähern, WLAN-Positionen schätzen und am Ende mit einer GPS-Referenzroute vergleichen.

## Folie 2 - Agenda

Unsere Präsentation ist in fünf Teile aufgebaut. Zuerst geben wir einen Überblick über das Projekt und erklären, welches Problem wir lösen wollten. Danach zeigen wir unsere Vorgehensweise, also wie wir von Rohdaten zu verarbeiteten Daten kommen.

Der wichtigste Teil ist dann die technische Umsetzung. Dort gehen wir Schritt für Schritt durch die Pipeline: Einlesen der WiGLE-Daten, Bereinigung, Bildung von Scans, Router-Schätzung, WLAN-Positionsschätzung, Map-Matching und Visualisierung.

Danach erklären wir noch die Ausreißerproblematik. Das ist bei WLAN-Lokalisierung besonders wichtig, weil einzelne Schätzpunkte stark danebenliegen können. Zum Schluss zeigen wir, wie man das Projekt startet und wie die Live-Demo in der Streamlit-App funktioniert.

## Folie 3 - Ziel des Projektes

Das Ziel des Projektes war die Entwicklung eines Systems zur Outdoor-Lokalisierung auf Basis vorhandener WLAN-Signale. Wir wollten also nicht selbst neue Hardware bauen, sondern vorhandene Signale aus der Umgebung auswerten.

Die Datenquelle ist die WiGLE-App. Sie liefert Messpunkte mit Koordinaten, Zeitstempel, sichtbaren WLAN-Netzwerken und RSSI-Werten. RSSI steht für Received Signal Strength Indicator, also die empfangene Signalstärke.

Als Kartengrundlage verwenden wir OpenStreetMap. Das ist wichtig, weil eine geschätzte Position nicht einfach irgendwo auf einer Karte liegen sollte. Wenn es um eine Person geht, ist es plausibler, dass sie sich auf Straßen, Wegen oder Fußwegen bewegt. Deshalb nutzen wir OSM später auch für das Snapping und Map-Matching.

Die Anwendung selbst ist in Python umgesetzt. Für die interaktive Darstellung verwenden wir Streamlit, weil man damit schnell eine Browser-App bauen kann, ohne eine komplette Webfrontend-Architektur aufzusetzen.

## Folie 4 - Grundlagen und Begriffe

Bevor wir in die Pipeline gehen, sind ein paar Begriffe wichtig. Die SSID ist der sichtbare Name eines WLAN-Netzwerks, zum Beispiel eduroam oder ein Routername. Die BSSID ist die technische MAC-Adresse des konkreten Access Points.

Warum ist das wichtig? Die SSID allein reicht nicht aus, weil viele Access Points denselben Netzwerknamen haben können. Gerade eduroam kommt an vielen Orten vor. Die BSSID allein ist zwar eindeutig, aber für die Darstellung weniger verständlich. Deshalb modellieren wir ein Netzwerk im Projekt immer als Kombination aus SSID und BSSID. Daraus entsteht unsere `network_id`.

RSSI ist die Signalstärke. Je näher man ungefähr am Access Point ist, desto stärker ist das Signal. Aber RSSI ist keine exakte Entfernung. Wände, Reflexionen, Geräteausrichtung und Umgebung können den Wert verändern.

Der Messpunkt ist die GPS-Position, an der ein Scan aufgenommen wurde. Ein Scan besteht aus mehreren WLAN-Zeilen, weil an einem Ort mehrere Netzwerke gleichzeitig sichtbar sein können.

## Folie 5 - Die Messroute

Hier sieht man die Messroute, also den Bereich, in dem die WLAN-Daten aufgenommen wurden. Diese Route ist wichtig, weil sie unsere Grundlage für die Kalibrierung und später auch für den Vergleich bildet.

An verschiedenen Punkten entlang dieser Route wurden WLAN-Signale gemessen. Jeder Messpunkt hat eine GPS-Koordinate und mehrere sichtbare WLAN-Netzwerke mit RSSI-Werten.

Technisch gesehen erzeugen wir daraus später zwei Sichtweisen. Erstens eine Referenzroute aus GPS-Daten. Diese nehmen wir als Vergleichsbasis. Zweitens eine WLAN-Route, die aus den gemessenen WLAN-Fingerprints geschätzt wird.

Der Vergleich ist nur sinnvoll, wenn beide Routen in derselben Umgebung betrachtet werden. Deshalb kommt später das Map-Matching auf begehbare OSM-Wege dazu.

## Folie 6 - Technischer Gesamtüberblick

Diese Folie zeigt die gesamte Pipeline. Der erste Schritt sind Rohdaten: eine WiGLE-CSV und eine OSM-Karte. Danach kommt die Bereinigung. Wir filtern nur echte WIFI-Einträge, entfernen ungültige Zeitstempel und bringen die Spalten in ein internes Schema.

Danach werden Routerpositionen geschätzt. Das passiert über RSSI-Kreise. Für einen Access Point sammeln wir mehrere Messpunkte und berechnen aus der Signalstärke jeweils einen geschätzten Radius.

Für die WLAN-Route verwenden wir bevorzugt WKNN-Fingerprinting. WKNN bedeutet Weighted K-Nearest Neighbors. Dabei vergleichen wir einen aktuellen Scan mit alten Referenzscans und suchen die ähnlichsten WLAN-Muster.

Anschließend wird die Route geglättet und auf OSM-Wege gematcht. GPS wird im Laufweg-Vergleich als Referenz genutzt, WLAN ist die geschätzte Route. Am Ende vergleichen wir beide Routen über Fehlerwerte und visualisieren sie in der Streamlit-App.

## Folie 7 - Schritt 1: Rohdaten einlesen

Der erste technische Schritt ist das Einlesen der WiGLE-CSV. Das passiert in `src/load_wifi_csv.py`, und `main.py` startet die Pipeline.

Eine Besonderheit bei WiGLE-Dateien ist, dass nicht immer direkt die echte Tabellenkopfzeile am Anfang steht. Es gibt häufig eine zusätzliche Metazeile. Wenn man diese Datei einfach blind mit `pandas.read_csv` einliest, können die Spalten falsch erkannt werden.

Deshalb erkennt unser Loader die echte Headerzeile und liest die Daten danach sauber als Tabelle ein. In diesem Schritt wird noch keine finale Ausgabedatei erzeugt. Die Rohdaten werden erst intern weitergegeben, damit die nächste Stufe sie bereinigen kann.

Wichtig ist auch: Rohdaten in `data/raw/` werden nicht direkt verändert. Das war eine feste Projektregel. Alles, was bereinigt oder abgeleitet ist, landet in `data/processed/`.

## Folie 8 - Schritt 2: WLAN-Messdaten bereinigen

Nach dem Einlesen werden die Daten bereinigt. Das passiert vor allem in `src/preprocess_wifi_data.py` und wird über `src/project_pipeline.py` gesteuert.

Zuerst behalten wir nur Einträge mit `Type = WIFI`. WiGLE kann auch andere Typen enthalten, aber für unser MVP sollen nur WLAN-Daten verarbeitet werden.

Dann entfernen wir ungültige Zeitstempel. Ein typisches Beispiel ist `1970-01-01`. Solche Werte entstehen oft, wenn ein Gerät oder eine App keinen gültigen Zeitpunkt gespeichert hat. Für eine Route wären solche Zeitpunkte problematisch, weil die zeitliche Reihenfolge dann falsch wäre.

Außerdem entfernen wir Zeilen, in denen wichtige Felder fehlen, also SSID, BSSID oder RSSI. Danach vereinheitlichen wir die Spaltennamen. Das Ergebnis ist `data/processed/wifi_scans_clean.csv`. Ab hier arbeitet der Rest der Pipeline mit einem stabilen internen Schema.

## Folie 9 - Schritt 3: WLAN-Netz eindeutig erkennen

In diesem Schritt erzeugen wir die `network_id`. Das ist fachlich wichtig, weil ein WLAN-Netzwerk nicht nur über die SSID modelliert werden sollte.

Wenn wir nur die SSID nutzen würden, könnten unterschiedliche Access Points mit gleichem Namen vermischt werden. Bei eduroam wäre das besonders problematisch. Wenn wir nur die BSSID nutzen würden, hätten wir zwar eine eindeutige technische ID, aber die Zuordnung zum sichtbaren Netzwerknamen wäre weniger nachvollziehbar.

Deshalb kombinieren wir SSID und BSSID. Diese Kombination wird in den verarbeiteten Daten überall als Netzwerkeinheit verwendet. Dadurch können wir später Messpunkte pro Access Point sammeln, Routerpositionen schätzen und WLAN-Fingerprints vergleichen.

Das Ergebnis sieht man in mehreren Dateien: `wifi_scans_clean.csv`, `network_observations.csv` und `network_summary.csv`.

## Folie 10 - Schritt 4: Einzelne WLAN-Zeilen zu Scans bilden

Eine WiGLE-Datei enthält viele einzelne Zeilen. Jede Zeile beschreibt ein sichtbares Netzwerk an einem Ort. Für die Lokalisierung brauchen wir aber den kompletten Scan an einem Messzeitpunkt.

Deshalb gruppieren wir die Daten zu Scans. Ein Scan bekommt eine `scan_id`, einen Zeitstempel, eine Position und die Liste der sichtbaren Netzwerke. So wird aus vielen Einzelbeobachtungen ein Messpunkt mit mehreren WLAN-Signalen.

Das ist später für zwei Dinge wichtig. Erstens können wir pro Scan eine WLAN-Position schätzen. Zweitens können wir GPS- und WLAN-Route punktweise vergleichen, weil jeder Scan einen Zeitpunkt und eine Position hat.

Das Ergebnis dieses Schritts ist `scan_summary.csv`. Diese Datei ist eine kompakte Übersicht über die aufgenommenen Messpunkte.

## Folie 11 - Schritt 5: Router-Standorte schätzen

Jetzt kommen wir zur Router-Schätzung. Hier ist eine wichtige Unterscheidung: Routerstandorte werden bei uns nicht mit WKNN geschätzt. WKNN verwenden wir später für die WLAN-Laufwegpunkte. Routerpositionen entstehen über RSSI-Kreise.

Für jede `network_id`, also für jede Kombination aus SSID und BSSID, sammeln wir Messpunkte. Jeder Messpunkt enthält die Koordinate, den RSSI-Wert und daraus einen geschätzten Radius.

Die Idee ist: Wenn ein Signal stark ist, war der Messpunkt wahrscheinlich näher am Access Point. Wenn das Signal schwach ist, war der Messpunkt wahrscheinlich weiter entfernt.

Aber RSSI ist ungenau. Deshalb sagen wir nicht: Der Router liegt exakt an einem Schnittpunkt. Stattdessen suchen wir einen Punkt, der insgesamt am besten zu allen Messkreisen passt. Das Ergebnis wird in Dateien wie `network_observations.csv`, `network_summary.csv` und `triangulated_access_points.csv` gespeichert.

## Folie 12 - Schritt 5: Messkreise schätzen

Hier sieht man genauer, wie die Router-Schätzung funktioniert. Zuerst wählen wir eine `network_id` aus. Dann werden alle Messpunkte gesammelt, an denen genau dieses Netzwerk gesehen wurde.

Aus dem RSSI-Wert wird ein Radius berechnet. Die verwendete Formel ist das Log-Distance Path-Loss-Modell:

`d = 10 ^ ((A - RSSI) / (10 * n))`

Dabei ist `d` die geschätzte Entfernung, `A` ist der angenommene RSSI-Wert in einem Meter Entfernung und `n` ist der Dämpfungsfaktor der Umgebung. In unserem Projekt verwenden wir als Standardwerte `A = -45` und `n = 3.0`.

Ganz wichtig: Dieser Radius ist keine echte gemessene Distanz. Er ist nur eine Näherung. Deshalb vergleichen wir mehrere Kreise. Bei weniger als drei Messpunkten ist die Router-Schätzung besonders unsicher, weil kein stabiler Schnittbereich entsteht.

## Folie 13 - Schritt 6: WLAN-Position schätzen

Diese Folie beschreibt die klassische Baseline der WLAN-Positionsschätzung. Dafür nutzen wir die zuvor geschätzten Access Points und die aktuellen RSSI-Werte eines Scans.

Die Idee ist: Wenn ein Access Point stark empfangen wird, liegt die geschätzte Nutzerposition eher in seiner Nähe. Wenn das Signal schwach ist, hat dieser Access Point weniger Einfluss. Aus mehreren sichtbaren Access Points entsteht dann ein gemeinsamer Schätzpunkt.

Diese Methode ist wichtig, weil sie die Grundlogik der Lokalisierung erklärt: Aus mehreren unsicheren Signalbeobachtungen wird ein plausibler Standort berechnet. Gleichzeitig ist sie nicht perfekt, weil sowohl Routerpositionen als auch RSSI-Radien nur Schätzwerte sind.

Für die spätere Laufwegroute nutzen wir deshalb bevorzugt WKNN-Fingerprinting. Diese Folie zeigt also die technische Baseline; die nächste Folie zeigt die robustere Route über WLAN-Muster.

## Folie 14 - Schritt 6: WLAN-Position mit WKNN schätzen

Diese Folie zeigt die Methode, die wir für die WLAN-Laufwegroute bevorzugen: WKNN-Fingerprinting. Hier rechnen wir nicht mit Routerkreisen, sondern vergleichen komplette WLAN-Muster.

Ein Muster besteht aus den sichtbaren `network_id`s und den jeweiligen RSSI-Werten. Für einen neuen Scan suchen wir ähnliche alte Referenzscans. Im Code verwenden wir `k = 5`, also die fünf ähnlichsten Scans.

Diese alten Scans wirken wie gewichtete Referenzpunkte. Je ähnlicher das WLAN-Muster ist, desto stärker zieht dieser Referenzscan die geschätzte Position. Weniger ähnliche Scans haben entsprechend weniger Einfluss.

Am Ende entsteht ein gewichteter Mittelpunkt. WKNN übernimmt also nicht einfach einen alten Messpunkt, sondern kombiniert mehrere ähnliche Scans. Dadurch wird die WLAN-Route meist glatter und robuster als bei einer reinen Kreis- oder Router-Baseline.

## Folie 15 - Schritt 7: GPS und WLAN auf Wege setzen

Nach der WLAN-Schätzung liegen Rohpunkte vor. Diese können neben der Straße oder neben einem Fußweg liegen. Das ist normal, weil GPS und WLAN beide Messfehler haben.

Für den Laufweg-Vergleich ist das aber problematisch. Wenn eine Person real auf einem Weg läuft, sollten wir beide Routen auf plausible begehbare Wege legen. Genau das machen wir mit OpenStreetMap.

Dabei werden GPS- und WLAN-Punkte auf passende OSM-Wege gematcht. Fußwege und begehbare Wege werden bevorzugt. Außerdem wird nicht nur jeder Punkt einzeln betrachtet, sondern der Routenverlauf wird mit einbezogen. Dadurch vermeiden wir, dass einzelne Punkte unplausibel auf Parallelwege springen.

Routerpositionen werden dabei bewusst nicht auf Straßen gesnappt. Nur Nutzerpositionen und Laufwege werden auf begehbare Wege gesetzt.

## Folie 16 - Schritt 8: Laufwege visualisieren

In der Streamlit-App gibt es einen eigenen Tab für den Laufweg-Vergleich. Die App berechnet die Route nicht bei jedem Start neu, sondern lädt vorbereitete CSV-Artefakte aus `data/processed/`.

Die GPS-Route wird rot dargestellt, die WLAN-Route blau. In der technischen Auswertung werden außerdem Fehlerwerte berechnet, zum Beispiel der mittlere Fehler, Median-Fehler, maximale Fehler und der 90-Prozent-Fehler.

Die Visualisierung liegt in `src/visualize_wifi_data.py`, die App-Logik in `app.py`. Dadurch ist die Datenpipeline getrennt von der Darstellung. `main.py` erzeugt die Daten, Streamlit zeigt sie an.

Diese Trennung war für unser Projekt wichtig, weil die App dadurch schneller startet und die Verarbeitung reproduzierbar bleibt.

## Folie 17 - Punkte verbinden und Richtung zeigen

Bei der Laufweg-Visualisierung werden die Punkte zuerst nach Zeit sortiert. Danach bleibt jeder Punkt als Marker sichtbar. Aufeinanderfolgende Punkte werden verbunden, sodass eine Route entsteht.

Zusätzlich zeigen kleine Pfeile die Laufrichtung. Das ist hilfreich, weil man sonst auf einer statischen Karte nicht immer erkennt, in welcher Reihenfolge die Punkte entstanden sind.

Diese Darstellung ist noch kein Fehlervergleich. Es geht erst einmal darum, die Route verständlich sichtbar zu machen: Wo startet sie, wo führt sie entlang und welche Punkte gehören zeitlich zusammen?

Erst danach kann man GPS und WLAN fachlich vergleichen, zum Beispiel über Fehlerlinien oder Fehlerkennzahlen.

## Folie 18 - Vorher vs. Nachher

Diese Folie zeigt den Unterschied zwischen Rohdaten und verarbeiteter Darstellung. Vorher liegen Punkte teilweise unruhig, neben Wegen oder mit einzelnen Sprüngen. Nachher ist die Route bereinigt, geglättet und auf plausible Wege gelegt.

Das heißt aber nicht, dass wir Daten künstlich schön rechnen. Die Rohdaten bleiben erhalten. Die Verarbeitung wird in separaten Dateien dokumentiert. So kann man nachvollziehen, welche Punkte genutzt wurden und welche Punkte als problematisch markiert wurden.

Technisch ist dieser Schritt wichtig, weil eine reine Rohpunktkarte schnell irreführend wirkt. Die bereinigte Darstellung soll zeigen, was die Lokalisierung plausibel leisten kann, ohne die Unsicherheit zu verstecken.

## Folie 19 - Ausreißer in der Standortschätzung

Bei WLAN-Lokalisierung entstehen Ausreißer, weil WLAN-Signale nicht stabil wie eine ideale Kreisgeometrie funktionieren. Ein RSSI-Wert kann schwanken, obwohl man sich kaum bewegt hat. Außerdem können einzelne Access Points schlecht kalibriert sein oder nur in wenigen Scans vorkommen.

Deshalb prüfen wir jeden geschätzten Punkt mit Qualitätsregeln. Bei der WKNN-Route werden zum Beispiel zu wenige passende Access Points, hoher RMSE, sehr große Fehler und unplausible Sprünge erkannt.

Besonders wichtig ist: Ausreißer werden nicht aus den Rohdaten gelöscht. Sie werden markiert und getrennt gespeichert, zum Beispiel in einer `outliers`-Datei. Die Standardansicht nutzt die bereinigte Route, aber die entfernten Punkte bleiben mit Begründung nachvollziehbar.

Damit vermeiden wir zwei Probleme: Einerseits zeigen wir keine offensichtlich falschen Sprünge in der Demo. Andererseits verlieren wir keine Transparenz über die Datenqualität.

## Folie 20 - Ergebnis und Start der Anwendung

Hier sieht man, wie das Projekt auf einem neuen Rechner gestartet werden kann. Zuerst wird das Repository von GitHub geklont. Danach wird eine virtuelle Python-Umgebung erstellt.

Anschließend installieren wir die Abhängigkeiten aus `requirements.txt`. Danach läuft zuerst `main.py`. Dieser Schritt ist wichtig, weil dort die Pipeline ausgeführt wird und die verarbeiteten CSV-Dateien in `data/processed/` entstehen.

Erst danach startet man die Streamlit-App mit `streamlit run app.py`. Die App lädt dann die vorbereiteten Daten und zeigt die Tabs für Standort-Test, Router-Schätzung und Laufweg-Vergleich.

Technisch ist das Ergebnis also kein einzelnes Skript, sondern ein kleiner reproduzierbarer Workflow: Daten vorbereiten, Artefakte speichern, App starten und Ergebnisse interaktiv prüfen.

## Folie 21 - Abschluss

Zusammenfassend haben wir ein System gebaut, das WLAN-Messdaten aus WiGLE einliest, bereinigt und in ein internes Schema überführt. Netzwerke werden über SSID und BSSID eindeutig modelliert.

Routerpositionen werden über RSSI-Kreise geschätzt. Dabei behandeln wir die Positionen ausdrücklich als unsichere Schätzungen und nicht als exakt bekannte Punkte. Für die WLAN-Laufwegroute verwenden wir WKNN-Fingerprinting, zeitliche Glättung und Map-Matching auf begehbare OSM-Wege.

Am Ende steht eine Streamlit-App, in der man die Standortschätzung, Router-Schätzung und den Laufweg-Vergleich nachvollziehen kann. Der technische Kern des Projektes ist also nicht nur die Karte, sondern die komplette Pipeline von Rohdaten bis zur interpretierbaren Visualisierung.

Vielen Dank für die Aufmerksamkeit. Wir freuen uns jetzt auf Fragen.
