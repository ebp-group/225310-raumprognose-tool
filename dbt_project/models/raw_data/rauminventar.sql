-- Lädt die Rauminventardaten aus der Excel-Datei und bereitet sie für die weitere Verarbeitung vor

{{ config(materialized='table') }}

SELECT
    *
FROM read_xlsx(
    '{{ "..\\data\\gebaeude_raeume.xlsx" }}',
    header=True,
    all_varchar = true,
    stop_at_empty = true
)