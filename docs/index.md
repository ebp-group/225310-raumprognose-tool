# Raumprognose Tool

Das **Raumprognose Tool** ist eine interaktive Desktop-Applikation (entwickelt mit [Flet](https://flet.dev/)), die Flächenprognosen für Universitäts- und Campusgebäude berechnet und visualisiert.

---

## Überblick

Mit dem Tool können Planende auf einen Blick beurteilen, ob für eine gegebene Nutzungsart in einem bestimmten Prognosejahr ein Flächenüberschuss oder ein Flächendefizit besteht.

```
 Excel-Dateien laden          Szenario wählen          Ergebnisse & Diagramme
 ──────────────────           ───────────────           ──────────────────────
  Gebäude & Räume   ──►   Szenario berechnen   ──►   Übersicht · Ergebnisse
  Studierende                                         Diagramme · Export
  Nutzungsfaktoren
```

---

## Funktionsumfang

| Tab | Inhalt |
|-----|--------|
| **📋 Übersicht** | Rohdaten-Tabellen: Gebäude & Räume, Studierende & Mitarbeitende, Nutzungsfaktoren |
| **📊 Ergebnisse** | Über-/Unterschuss-Tabelle mit Farbkodierung (grün = Überschuss, rot = Defizit) und Kennzahlenkarten |
| **📈 Diagramme** | Liniendiagramm (Studierendenzahlen), Balkendiagramme (Flächenbedarf, Eigentumsform, Über-/Unterschuss) |
| **⬇️ Export** | Ergebnisse als gestylte Excel-Datei oder Diagramme als PNG-Bilder speichern |

---

## Schnellstart

### 1. Applikation starten

[Aktuellen Release der Applikation via GitHub herunterladen](https://github.com/ebp-group/225310-raumprognose-tool/releases/latest) (`RaumprognoseTool-windows.zip`), entpacken und die Applikation durch Doppelklick auf `RaumprognoseTool.exe` starten.

### 2. Excel-Dateien laden

Klicken Sie in der linken Seitenleiste auf die drei Datei-Schaltflächen und wählen Sie:

- **Gebäude & Räume** – `gebaeude_raeume.xlsx`
- **Studierende & Mitarbeitende** – `studierende.xlsx`
- **Nutzungsfaktoren** – `nutzungsfaktoren.xlsx`

Klicken Sie danach auf **„Daten laden"**.

<img width="286" height="428" alt="Daten laden" src="https://github.com/user-attachments/assets/c9935473-09b4-4ea7-922a-c0fcac413e05" />


### 3. Szenario auswählen und berechnen

Wählen Sie im Dropdown **„Szenario wählen"** ein verfügbares Szenario (z. B. *Basis*, *Wachstum*, *Digital*) und klicken Sie auf **„Szenario berechnen"**.

<img width="278" height="194" alt="Szenario wählen" src="https://github.com/user-attachments/assets/f7f60d11-25a0-44f9-a63f-8d6f7dbea206" />


### 4. Ergebnisse analysieren und exportieren

Wechseln Sie über die Tab-Leiste zu **📊 Ergebnisse**, **📈 Diagramme** oder **⬇️ Export**.

---

## Weiterführende Kapitel

- [Daten laden](datenladen.md) – Dateiformat und Spaltenanforderungen
- [Szenario wählen & berechnen](szenario.md) – Berechnungslogik und Szenarien
- [Ergebnisse anzeigen](ergebnisse.md) – Tabellen und Kennzahlen
- [Diagramme](diagramme.md) – Visualisierungen
- [Export](export.md) – Excel- und PNG-Export
