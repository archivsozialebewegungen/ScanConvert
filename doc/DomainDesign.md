Die Domäne
==========

Beim Input des Scan-Konverters handelt es sich - wenig überraschend - um Scans.
Scans sind einfach Bilddateien, in der Regel im JFIF- (oft als JPG bezeichnet)
oder TIF-Format. Charakterisiert sind diese Dateien durch ihre Dimension (Höhe
und Breite), sowie die Auflösung und die Farbtiefe (RGB oder Graustufen; Schwarz-Weiß
ist eigentlich nicht zu empfehlen).

Möglicherweise liefern manche Spezialscanner auch andere Formate oder Farbräume,
vor allem Photoscanner, doch um diese geht es uns hier nicht. Uns geht es um
Scans von Texten, die eventuelle durch Abbildungen angereichert sind. Und die
Scanner dafür produzieren exakt diese Formate.

Es liegt deshalb auf der Hand, einfach eine Image-Klasse zu verwenden um Scans
abzubilden, die über die entsprechenden Eigenschaften verfügt. Doch die erste
Version dieses Scan-Konverters hat gezeigt, dass diese Annahme falsch ist.
Beim Scannen von Zeitschriften oder Broschüren haben wir in einer Image-Datei
möglicherweise zwei Seiten. Und diese zwei Seiten wollen wir möglicherweise
jeweils unterschiedlich verarbeiten.

Dazu kommt, dass die Seitennummern der Seiten eines Scans von den anderen
Scans abhängt. Wesentliche Informationen zur Verarbeitung des Scans hängen
also vom Gesamtprojekt ab. Wir benötigen deshalb eine Project-Klasse,
die als Container für die Scans/Seiten dient und die auch über die notwendigen
Informationen verfügt, was ein einzelner Scan wie repräsentiert.

Um auf einzelnen Seiten Operationen auszuführen, benötigen wir außerdem
eine Page-Klasse. Die erste Intuition wäre, die Page-Klasse sehr ähnlich zur
Scan-Klasse zu konzipieren, sozusagen als vereinfachter Scan. Doch genau
das wäre ebenfalls kurzschlüssig. Die Page-Klasse sollte einfach Meta-Daten
enthalten zur Verarbeitung enthalten. Tatsächlich sollte die Klasse besser
TargetPage heißen, weil hier vor allem das Ziel der Verarbeitung festgelegt
wird.

Eine abhängige Klasse der Page-Klasse wird die Region-Klasse sein, in der
für einzelne Bereiche der Page abweichende Algorithmen für die Berechnung
des Target-Outputs.

Um die Komplexität zu reduzieren, sollte der ScanConverter II für die
ersten Schritte als Assistent programmiert werden. Im ersten Schritt wird
das Ziel ausgewählt: Eine Pdf-Datei in einer bestimmten Auflösung oder
eine Reihe von tif-Dateien in einer bestimmten Auflösung. Außerdem wird
hier der Zielmodus (Farbe, Grau, SW) angegeben und bei SW, wie die Vorlagen
beschaffen sind (das bestimmt dann den Standardalgorithmus für die
Seitenverarbeitung).

Im zweiten Schritt wird dann angegeben, um was für einen Typ von Scans
es sich handelt:

* Ein- oder zweiseitig
* Overhead bzw. Flachbettscanner oder aber Einzugsscanner

Im dritten Schritt werden alle Scans geladen.

Ein optionaler vierter Schritt erlaubt es noch einmal, die Scans
umzusortieren - das wird im MVP nicht implementiert.

Ebenfalls nicht im MVP implementiert wird die eigentliche
Benutzeroberfläche. Diese besteht aus zwei Panels
Links eine Liste von Seiten, rechts dann die Anzeige
der jeweils aktuellen Seite. Für die Seiten können jetzt
abweichende Algorithmen ausgewählt werden bzw. Regionen markiert,
die anders verarbeitet werden sollen: Photos beispielsweise oder
Überschriften mit fetten Lettern (die für Sauvola nicht tauglich sind).

Für die Nutzer:innen sollte die Algorithmus-Frage allerdings völlig
transparent sein. Sie markieren nur den Type der Seite und eventuell
davon abweichende Regionentypen. Für jeden Typ ist dann im Projekt
festgelegt, welcher Algorithmus angewandt werden soll.

Der Ablauf
==========

Die scan-Klasse wird komplett immutable konzipiert. Sie enthält im
wesentlichen die URI der Scan-Datei. Bei Instantiierung einer
scan-Instanz wird dann einmal kurz die Scan-Datei geöffnet und
die relevanten Informationen zu Breite, Höhe, Auflösung und Modus
eingelesen. Dann wird die Datei selbst wieder dem garbage collector
zum Wegwerfen übergeben. Der Grund dafür ist, dass Scans sehr
groß sein können und einzelne Projekte aus sehr vielen Scans
bestehen können. Die erste Version des Scan-Konverters lief ab
ca. 200 Scans pro Projekt in out-of-memory-Probleme hinein.
(Das kann uns immer noch passieren beim Zusammensetzen der pdf-Dateien
mit ReportLab - dann müssen wir uns etwas überlegen.)

Alle Informationen über die Weiterverarbeitung der scans (und
auch die entsprechenden Funktionen) sind Teil der page-Klasse.
Die project-Klasse erzeugt aus den Informationen beim Anlegen
des Projektes sowie des Einlesens der scans dann die page-Instanzen.
Jede page-Instanz bekommt ihren Scan zugeordnet, die Region im
Scan, die die Seite repräsentiert (das kann der ganze scan sein
oder eben die entsprechende Hälfte), den notwendigen Rotationswinkel,
die Zielauflösung und den Zielmodus. Damit kann die page-Klasse
prinzipiell eine Image-Instanz erzeugen, die dann als tif-Datei
abgespeichert oder in eine pdf-Datei integriert werden kann.

Das wäre das MVP - einfach ein Projekt-Instantierungs-Assistent,
der entweder tif-Dateien oder eine pdf-Datei erzeugt.

