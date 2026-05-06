# Szenario wählen & berechnen

Nachdem die drei Eingabedateien erfolgreich geladen wurden, kann ein **Szenario** gewählt und die Flächenprognose berechnet werden.

---

## Szenario auswählen

Das Dropdown **„Szenario wählen"** in der linken Seitenleiste wird automatisch mit den verfügbaren Szenarien aus der Nutzungsfaktoren-Datei befüllt.

Typische Szenarien:

| Szenario | Beschreibung |
|---|---|
| **Basis** | Konservative Annahmen, aktueller Standard |
| **Wachstum** | Erhöhter Flächenbedarf durch Wachstum |
| **Digital** | Reduktion des Flächenbedarfs durch Digitalisierung |

!!! note
    Die verfügbaren Szenarien hängen vollständig von der geladenen `nutzungsfaktoren.xlsx` ab.  
    Wenn eine neue Datei geladen wird und das vorherige Szenario darin nicht mehr enthalten ist, wird automatisch das erste verfügbare Szenario ausgewählt.

---

## Berechnung auslösen

Klicken Sie auf **„Szenario berechnen"** (mit dem Taschenrechner-Symbol).

Die Applikation führt dann drei aufeinanderfolgende Berechnungen durch:

```
1. current_area_by_nutzungsart()  →  Ist-Fläche je Raumtyp und Jahr
2. future_demand()                →  Flächenbedarf je Nutzungsart und Jahr
3. surplus_deficit()              →  Differenz: Ist-Fläche − Bedarf
```

---

## Berechnungslogik

### 1. Ist-Fläche (`current_area_by_nutzungsart`)

Für jedes Prognosejahr wird die verfügbare Fläche summiert, wobei nur Räume berücksichtigt werden, die im jeweiligen Jahr in Betrieb sind:

```sql
SELECT "Raumtyp EBP", Jahr, SUM("Fläche") AS "Fläche"
FROM gebaeude
CROSS JOIN years
WHERE (Betriebsaufnahme IS NULL OR Betriebsaufnahme <= Jahr)
  AND (Betriebsende    IS NULL OR Betriebsende    >= Jahr)
GROUP BY "Raumtyp EBP", Jahr
```

### 2. Flächenbedarf (`future_demand`)

Der zukünftige Flächenbedarf wird pro Nutzungsart und Jahr berechnet:

```
Bedarf (m²) = Rundung(Anzahl_Personen, Schritt) × Faktor_m2_pro_Person
```

Die **Stufung** (`Schritt`) modelliert diskrete Kapazitätsstufen: z. B. benötigt man erst ab 3 000 Studierenden einen zweiten Hörsaal. Eine `Schritt`-Grösse von `0` deaktiviert die Stufung.

```sql
SELECT Nutzungsart, Jahr,
       CEIL(Anzahl / Schritt) * Schritt * Faktor_m2_pro_Person AS Bedarf_m2
FROM studierende
JOIN faktoren ON Kategorie = Bezug
WHERE Szenario = '<gewähltes Szenario>'
```

### 3. Über-/Unterschuss (`surplus_deficit`)

```
Differenz (m²) = Ist-Fläche − Bedarf
```

- **Positiv (grün)** → Flächenüberschuss: mehr Fläche vorhanden als nötig
- **Negativ (rot)** → Flächendefizit: Fläche reicht nicht aus

---

## Prognosejahre

Die Berechnungen werden für **alle Jahre** durchgeführt, die in der Studierenden-Datei vorhanden sind.  
In den Ergebnisansichten und Diagrammen werden standardmässig die Stützjahre **2026, 2030, 2040 und 2050** hervorgehoben.

---

## Fehlerbehandlung

| Situation | Meldung |
|---|---|
| Daten noch nicht geladen | *„Bitte zuerst alle Daten laden."* (rote Benachrichtigung) |
| Kein Szenario ausgewählt | Berechnung wird nicht gestartet |
| Bezug-Kategorie fehlt in Studierenden-Daten | Fehlermeldung mit den fehlenden Kategorien |
| Szenario enthält keine gültigen Bezug-Werte | Fehlermeldung |
