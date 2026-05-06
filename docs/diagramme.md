# Diagramme

Der Tab **📈 Diagramme** bietet vier verschiedene Visualisierungen, die automatisch nach der Berechnung eines Szenarios erstellt werden.  
Alle Diagramme basieren auf [matplotlib](https://matplotlib.org/) und werden als eingebettete PNG-Bilder in der Applikation angezeigt.

---

## 1. Studierendenzahlen & Kategorien im Zeitverlauf

**Diagrammtyp:** Liniendiagramm

Zeigt die Entwicklung der Personenzahlen über alle Prognosejahre, aufgeteilt nach Kategorien.

| Achse | Inhalt |
|---|---|
| X-Achse | Jahr |
| Y-Achse | Anzahl Personen |
| Linien | Eine Linie pro Kategorie (z. B. *Studierende*, *Forschung*, *Services*, *Stundenlohn*) |

**Ziel:** Überblick über das Wachstum oder die Stagnation der einzelnen Personengruppen.

<img width="1234" height="640" alt="Studierendenzahlen & Kategorien" src="https://github.com/user-attachments/assets/4c0abb45-be20-4d52-9ffa-c8c5e121a75a" />


---

## 2. Flächenbedarf nach Nutzungsart und Jahr

**Diagrammtyp:** Gruppiertes Balkendiagramm

Zeigt den prognostizierten Flächenbedarf (m²) für die Stützjahre **2026, 2030, 2040 und 2050**, aufgeteilt nach Nutzungsart.

| Achse | Inhalt |
|---|---|
| X-Achse | Nutzungsart |
| Y-Achse | Bedarf (m²) |
| Balkengruppen | Ein Balken pro Prognosejahr |

Der Titel des Diagramms enthält den Namen des gewählten Szenarios.

**Ziel:** Vergleich des Flächenbedarfs über die Zeit und zwischen den Nutzungsarten.

<img width="1233" height="645" alt="Flächenbedarf nach Nutzungsart und Jahr" src="https://github.com/user-attachments/assets/9063e1c1-4bcb-4b09-a554-b01051b92cac" />


---

## 3. Fläche nach Eigentumsform

**Diagrammtyp:** Gestapeltes Balkendiagramm

Zeigt die verfügbare Gesamtfläche (m²) für die Jahre **2025, 2026, 2030 und 2040**, aufgeteilt nach Eigentumsform.

| Achse | Inhalt |
|---|---|
| X-Achse | Jahr |
| Y-Achse | Fläche (m²) |
| Segmente | Eine Farbe pro Eigentumsform |

**Ziel:** Überblick über die Entwicklung der Flächenstruktur nach Eigentumsform (z. B. Eigentum vs. Miete).

<img width="1249" height="745" alt="Fläche nach Eigentumsform" src="https://github.com/user-attachments/assets/138cd479-4e4a-4ef1-93e4-67a79e5451db" />

---

## 4. Über-/Unterschuss nach Nutzungsart

**Diagrammtyp:** Vier einzelne Balkendiagramme (eines pro Stützjahr)

Für jedes der Stützjahre **2026, 2030, 2040 und 2050** wird ein separates Balkendiagramm erstellt.

| Achse | Inhalt |
|---|---|
| X-Achse | Nutzungsart |
| Y-Achse | Differenz (m²): Ist-Fläche − Bedarf |
| Balkenfarbe | Grün = Überschuss, Rot = Defizit |

Eine horizontale Nulllinie trennt Über- und Unterschuss visuell.

**Ziel:** Schnelle Identifikation von problematischen Nutzungsarten in einem bestimmten Jahr.

<img width="1290" height="1081" alt="Über-/Unterschuss nach Nutzungsart" src="https://github.com/user-attachments/assets/06a5d0bb-a2b1-49bb-8036-25723165a7bc" />


---

## Technische Hinweise

- Alle Diagramme werden auf dem Server (ohne Display) mit dem `Agg`-Backend von matplotlib gerendert.
- Die Auflösung beträgt 150 DPI.
- Nach dem Aufbau der Ansicht werden alle matplotlib-Figuren aus dem Arbeitsspeicher freigegeben (`plt.close("all")`).
- Die Diagramme können im Tab **⬇️ Export** als PNG-Dateien gespeichert werden (siehe [Export](export.md)).
