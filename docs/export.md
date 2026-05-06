# Export

Der Tab **⬇️ Export** ermöglicht das Speichern der Berechnungsergebnisse und Diagramme auf dem lokalen Dateisystem.

!!! warning "Voraussetzung"
    Der Export steht nur zur Verfügung, wenn Daten geladen und ein Szenario berechnet wurden.

---

## Excel-Export

**Schaltfläche:** `📥 Ergebnisse als Excel speichern`

Klicken Sie auf die Schaltfläche und wählen Sie einen Speicherort.  
Der vorgeschlagene Dateiname lautet `raumprognose_<Szenario>.xlsx`.

### Inhalt der Excel-Datei

Die Excel-Datei enthält drei Tabellenblätter:

| Blatt | Inhalt |
|---|---|
| **Ergebnisse** | Vollständige Über-/Unterschuss-Tabelle mit Farbkodierung der `Differenz_m2`-Spalte |
| **Studierende** | Geladene Prognosezahlen (Long-Format) |
| **Flächenbedarf** | Berechneter Flächenbedarf pro Nutzungsart und Jahr |

### Formatierung

- **Kopfzeilen**: Weisse Schrift auf dunklem Blau (`#1F4E79`), zentriert
- **Positive Differenz** (Überschuss): Grüner Hintergrund (`#C6EFCE`)
- **Negative Differenz** (Defizit): Roter Hintergrund (`#FFC7CE`)

---

## PNG-Export (Diagramme)

Es stehen drei Schaltflächen für den Diagramm-Export zur Verfügung:

| Schaltfläche | Dateiname | Inhalt |
|---|---|---|
| `📥 Studierendenzahlen (PNG)` | `studierende.png` | Liniendiagramm der Personenzahlen nach Kategorie |
| `📥 Flächenbedarf (PNG)` | `flaechenbedarf_<Szenario>.png` | Gruppiertes Balkendiagramm des Flächenbedarfs |
| `📥 Eigentumsform (PNG)` | `eigentumsform.png` | Gestapeltes Balkendiagramm nach Eigentumsform |

### Exporteinstellungen

- **Format**: PNG
- **Auflösung**: 150 DPI
- **Layout**: `bbox_inches="tight"` (Diagramm wird ohne überschüssige Ränder gespeichert)

---

## Ablauf

1. Klicken Sie auf die gewünschte Export-Schaltfläche.
2. Es öffnet sich ein nativer Datei-Speicherdialog.
3. Wählen Sie den Zielordner und bestätigen Sie.
4. Nach dem Speichern erscheint eine grüne Benachrichtigung mit dem vollständigen Pfad.
