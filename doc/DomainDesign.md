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
jeweils unterschiedlich verarbeiten. Die Scan-Klasse sollte deshalb eine
Wrapper-Klasse sein, die auch die Eigenschaft number\_of\_pages besitzt und
Methoden bereitstellt, die einem die einzelnen Seiten liefern. 

