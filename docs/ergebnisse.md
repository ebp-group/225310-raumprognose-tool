# Ergebnisse anzeigen

Nach dem Berechnen eines Szenarios stehen zwei Tabs zur Verfügung, die die Rohdaten und die berechneten Ergebnisse anzeigen: **📋 Übersicht** und **📊 Ergebnisse**.

---

## Tab: 📋 Übersicht

Der Tab **Übersicht** zeigt die geladenen Eingabedaten in tabellarischer Form:

### Gebäude & Räume

Tabelle mit dem gefilterten Rauminventar – alle Zeilen mit einem gültigen `Raumtyp EBP`.  
Angezeigte Spalten: `Eigentumsform`, `Abgabeart`, `Eigentümer`, `Raumtyp EBP`, `Fläche (m²)`, `Betriebsaufnahme`, `Betriebsende`.

### Studierende & Mitarbeitende

Tabelle mit den Prognosezahlen im Long-Format (eine Zeile pro Jahr und Kategorie).

### Nutzungsfaktoren

Tabelle der Nutzungsfaktoren für das **aktuell gewählte Szenario** (gefiltert nach `Szenario`).  
Angezeigte Spalten: `Szenario`, `Nutzungsart`, `Faktor_m2_pro_Person`, `Schritt`, `Bezug`.

!!! tip "Scrollbare Tabellen"
    Jede Tabelle ist horizontal und vertikal scrollbar.  Es werden maximal 200 Zeilen angezeigt.

---

<img width="1433" height="1278" alt="Übersicht" src="https://github.com/user-attachments/assets/64126776-2983-4e0e-a20c-72edcdb7f7a3" />


## Tab: 📊 Ergebnisse

Der Tab **Ergebnisse** zeigt die berechneten Flächen-Über- und -Unterschüsse pro Nutzungsart.

### Kennzahlenkarten

Am oberen Rand des Tabs befinden sich vier Kennzahlenkarten für die Jahre **2026, 2030, 2040 und 2050**.  
Jede Karte zeigt:

- Das **Prognosejahr**
- Die **Gesamtdifferenz** in m² (Summe aller Nutzungsarten)
- Eine Beschriftung: *Überschuss* (grün) oder *Defizit* (rot)

### Pivot-Tabelle: Differenz pro Nutzungsart und Jahr

Eine Kreuztabelle mit:

- **Zeilen**: Nutzungsarten
- **Spalten**: Prognosejahre (2026, 2030, 2040, 2050)
- **Werte**: `Differenz_m2` (Ist-Fläche − Bedarf)

Die Zellen sind farblich kodiert:

| Farbe | Bedeutung |
|---|---|
| 🟢 Grün | Flächenüberschuss (`Differenz_m2 > 0`) |
| 🔴 Rot | Flächendefizit (`Differenz_m2 < 0`) |
| Weiss | Keine Differenz |

### Vollständige Ergebnistabelle

Darunter erscheint die detaillierte Ergebnistabelle mit allen Prognosejahren und folgenden Spalten:

| Spalte | Beschreibung |
|---|---|
| `Nutzungsart` | Raumtyp (EBP-Klassifikation) |
| `Jahr` | Prognosejahr |
| `Ist-Fläche (m²)` | Verfügbare Fläche im jeweiligen Jahr |
| `Bedarf (m²)` | Berechneter Flächenbedarf |
| `Differenz (m²)` | Ist-Fläche − Bedarf (positiv = Überschuss) |

Zahlenwerte werden mit Tausendertrennzeichen (Apostroph) formatiert, z. B. `12'500`.

<img width="808" height="1209" alt="Ergebnisse" src="https://github.com/user-attachments/assets/a2b6be5c-571b-48c8-b2e4-794ed5f2fe33" />

