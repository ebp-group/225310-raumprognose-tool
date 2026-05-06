# Daten laden

Bevor Berechnungen durchgeführt werden können, müssen drei Excel-Dateien in die Applikation geladen werden.  
Die Dateien können über die **linke Seitenleiste** ausgewählt werden.

---

## Schritt-für-Schritt

### 1. Dateien auswählen

Klicken Sie in der Seitenleiste auf die jeweilige Schaltfläche und wählen Sie die entsprechende `.xlsx`-Datei:

| Schaltfläche | Datei | Beschreibung |
|---|---|---|
| **Gebäude & Räume** | `gebaeude_raeume.xlsx` | Rauminventar mit Eigentumsform, Raumtypen und Betriebszeiten |
| **Studierende & Mitarbeitende** | `studierende.xlsx` | Prognosezahlen nach Jahr und Kategorie |
| **Nutzungsfaktoren** | `nutzungsfaktoren.xlsx` | Flächenbedarf (m²) pro Person je Szenario und Nutzungsart |

Nach der Auswahl erscheint der Dateiname unterhalb der jeweiligen Schaltfläche.

### 2. Laden auslösen

Klicken Sie auf **„Daten laden"** (mit dem Taschenrechner-Symbol).

- Bei Erfolg erscheint eine grüne Benachrichtigung: *„Daten erfolgreich geladen."*
- Bei einem Fehler erscheint eine rote Benachrichtigung mit der Fehlermeldung.

!!! tip "Fehlerbehebung"
    Wenn der Ladevorgang fehlschlägt, prüfen Sie, ob alle drei Dateien ausgewählt wurden und ob die erwarteten Spalten vorhanden sind (siehe unten).

---

## Dateiformate

### Gebäude & Räume (`gebaeude_raeume.xlsx`)

Die Datei muss mindestens die folgenden Spalten enthalten (Spalten A–S werden eingelesen):

| Spalte | Beschreibung |
|---|---|
| `Eigentumsform` | Eigentumsform des Raums (z. B. *Eigentum*, *Miete*) |
| `Abgabeart` | Art der Nutzungsabgabe |
| `Eigentümer` | Name des Eigentümers |
| `Raumtyp EBP` | Nutzungsart des Raums (interne Klassifikation) |
| `Fläche m²` | Bruttogeschossfläche in m² |
| `Betriebsaufnahme` | Jahr der Inbetriebnahme (leer = unbegrenzt in der Vergangenheit) |
| `Betriebsende` | Jahr der Ausserbetriebnahme (leer = unbegrenzt in der Zukunft) |

Zeilen ohne Raumtyp werden automatisch herausgefiltert.

!!! info "Betriebszeiten"
    Ein Raum wird für ein Prognosejahr *y* berücksichtigt, wenn gilt:  
    `Betriebsaufnahme ≤ y ≤ Betriebsende`.  
    Ein leeres Feld wird als unbegrenzt interpretiert.

### Studierende & Mitarbeitende (`studierende.xlsx`)

Die Datei muss im **Long-Format** vorliegen (eine Zeile pro Jahr und Kategorie):

| Spalte | Beschreibung |
|---|---|
| `Jahr` | Prognosejahr (ganzzahlig) |
| `Anzahl` | Anzahl Personen (wird auf ganze Zahlen gerundet) |
| `Beschreibung` | Optionale Beschreibung der Zeile |
| `Kategorie` | Personenkategorie (z. B. *Studierende*, *Forschung*, *Services*, *Stundenlohn*) |

### Nutzungsfaktoren (`nutzungsfaktoren.xlsx`)

| Spalte | Beschreibung |
|---|---|
| `szenario` | Szenariobezeichnung (z. B. *Basis*, *Wachstum*, *Digital*) |
| `nutzungsart` | Raumtyp, für den der Faktor gilt |
| `faktor_m2_pro_person` | Flächenbedarf in m² pro Person |
| `schritt` | Stufengrösse (z. B. Anzahl Personen pro Einheit; `0` = keine Stufung) |
| `bezug` | Personenkategorie aus der Studierenden-Datei, auf die sich der Faktor bezieht |

---

## Was passiert intern?

Beim Laden werden die Dateien mit der Python-Bibliothek **pandas** und dem `openpyxl`-Engine eingelesen.  
Anschliessend wird geprüft, ob alle Pflichtfelder vorhanden sind.  
Das Szenario-Dropdown wird automatisch mit den verfügbaren Szenarien aus der Nutzungsfaktoren-Datei befüllt.

```
load_gebaeude_raeume()  → DataFrame mit Rauminventar
load_studierende()      → DataFrame mit Prognosezahlen
load_nutzungsfaktoren() → DataFrame mit Nutzungsfaktoren
```
