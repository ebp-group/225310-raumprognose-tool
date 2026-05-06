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

---

## Technische Hinweise

- Alle Diagramme werden auf dem Server (ohne Display) mit dem `Agg`-Backend von matplotlib gerendert.
- Die Auflösung beträgt 150 DPI.
- Nach dem Aufbau der Ansicht werden alle matplotlib-Figuren aus dem Arbeitsspeicher freigegeben (`plt.close("all")`).
- Die Diagramme können im Tab **⬇️ Export** als PNG-Dateien gespeichert werden (siehe [Export](export.md)).
