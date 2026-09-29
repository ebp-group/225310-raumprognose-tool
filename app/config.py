"""Central configuration for the Raumprognose Tool.

All project- and site-specific values -- Stichjahre, colors, labels, ownership
mappings, Excel styling, default input paths -- live in ``app/assets/config.yml``.
This module loads that file once, deep-merges it over :data:`_DEFAULTS` and
exposes small derived helpers on top.

:data:`_DEFAULTS` mirrors the values that used to be hardcoded across
``flet_app.py``, ``calculations.py`` and ``data_loader.py``.  A missing, empty
or invalid ``config.yml`` therefore degrades to the previous behaviour instead
of crashing the application at import time.
"""

from __future__ import annotations

import copy
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

CONFIG_FILENAME = "config.yml"


def get_assets_dir() -> Path:
    default_assets_dir = Path(__file__).parent / "assets"  # fallback for local runs
    return Path(os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()


# ── Built-in fallbacks ────────────────────────────────────────────────────────

_DEFAULTS: dict[str, Any] = {
    "app": {
        "name": "Raumprognose Tool",
        "title_emoji": "🏛️",
        "organization": "EBP",
        "copyright_year": "2026",
        "license_name": "BSD 3-Clause License",
        "documentation_url": "https://ebp-group.github.io/225310-raumprognose-tool/",
        "window": {"width": 1400, "height": 900},
    },
    "areal": {
        "name": "UniSG",
        "label": "Areal",
    },
    "years": {
        # Bedarfs-/Differenz-Diagramme, Metrik-Karten, Pivot-Tabelle
        "prognose": [2026, 2030, 2040, 2050],
        # Eigentumsform-Diagramme (Balken + Kuchen)
        "bestand": [2025, 2026, 2030, 2040],
        # Stichjahr des Flächenpotenzial-Diagramms
        "flaechenpotenzial": 2040,
        # Im Excel-Export sichtbare Jahresspalten
        "excel_visible": [2025, 2030, 2040, 2050],
    },
    "charts": {
        "dpi": 150,
        "axis_margin": 0.05,
        "fallback_color": "#7f7f7f",
        "fallback_colormap": "tab20",
        "students": {
            "categories": ["Studierende", "Forschung", "Services", "Stundenlohn"],
            "colormap": "tab10",
            "ylim_top": 12000,
            "title": "Entwicklung nach Kategorie",
        },
        "flaechenpotenzial": {
            "bestand_label": "Bestand (Eigentum und Miete)",
            "bestand_color": "#7aa2c0",
            "potenzial_label": "Potenzial (Eigentum und Miete)",
            "potenzial_color": "#8cb48c",
            "bedarf_label": "Flächenbedarf SOLL {areal}",
            "bedarf_color": "#dfa02d",
            "ylabel": "Flächen (m² GF)",
        },
    },
    # Site catalogue -- normally supplied entirely by config.yml.
    "nutzungsarten": [],
    "eigentumsformen": {
        "eigenmiete_rule": {
            "eigentumsform": "Mietliegenschaften",
            "eigentuemer": "Hochbauamt St. Gallen",
            "as": "Eigenmiete",
        },
        "mapping": [
            {
                "from": "Eigenmiete",
                "to": "Eigentum Kanton St.Gallen - Miete temporär",
                "color": "#bad1ba",
            },
            {
                "from": "Mietliegenschaften",
                "to": "Eigentum Dritter - Miete temporär",
                "color": "#7aa2c0",
            },
            {
                "from": "Nutzungsvereinbarung",
                "to": "Eigentum Kanton St.Gallen - langfristige Nutzung",
                "color": "#8cb48c",
            },
            {
                "from": "Stiftungs- und Drittliegenschaften",
                "to": "Eigentum Stiftungen - Miete temporär",
                "color": "#aec7d9",
            },
        ],
    },
    "kategorien": {
        # Diese Kategorie zählt als "Studierende", alle übrigen als "Mitarbeitende".
        "studierende": "Studierende",
        "labels": {
            "Forschung_Monatslohn": "Forschung (Monatslohn)",
            "Forschung_Stundenlohn": "Forschung (Stundenlohn)",
            "Services_Monatslohn": "Services (Monatslohn)",
            "Services_Stundenlohn": "Services (Stundenlohn)",
        },
    },
    "szenarien": {"default": "Basis"},
    "excel": {
        "rounding_step": 5,
        "header_fill": "1F4E79",
        "header_font_color": "FFFFFF",
        "subheader_fill": "D9D9D9",
        "positive_color": "006100",
        "negative_color": "9C0006",
        "number_column_width": 14,
        "m2_number_format": '#,##0" m²"',
        "headcount_number_format": "#,##0",
        "export_prefix": "raumprognose",
        "sheet_names": {
            "ergebnisse": "Ergebnisse",
            "studierende": "Studierende",
            "flaechenbedarf": "Flächenbedarf",
            "gerundet": "Gerundete Flächen",
        },
        "row_labels": {
            "raumtypen": "Raumtypen",
            "total_lehre": "Total Lehre HNF 1 / 3 / 5",
            "total_buero": "Total Büro HNF 2",
            "total_gesamt": "Total Lehre und Büro HNF 1 / 2 / 3 / 5",
            "anzahl_studierende": "Anzahl Studierende",
            "anzahl_mitarbeitende": "Anzahl Mitarbeitende",
        },
    },
    "data": {
        "flaechenpotenzial_sheet": "Flaechenpotenzial_UniSG",
        "gebaeude_usecols": "A:S",
        "defaults": {
            "base_path": None,
            "gebaeude": None,
            "studierende": None,
            "faktoren": None,
        },
    },
}


# ── Loading ───────────────────────────────────────────────────────────────────


# Mappings that describe one indivisible rule rather than a group of settings.
# Merging them key by key would let a site inherit half of another site's rule
# (e.g. keeping the default Eigentümer while overriding only the Eigentumsform),
# so they are replaced wholesale instead.
_ATOMIC_KEYS = frozenset({"eigenmiete_rule"})


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return *base* with *override* merged in recursively.

    Nested mappings are merged key by key; lists, scalars and the mappings
    listed in :data:`_ATOMIC_KEYS` are replaced wholesale, so a config.yml can
    override a catalogue or a rule entirely.
    """
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in _ATOMIC_KEYS:
            merged[key] = copy.deepcopy(value)
        elif (
            key in merged and isinstance(merged[key], dict) and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _read_yaml(config_path: Path) -> dict[str, Any]:
    """Read *config_path*, returning ``{}`` (and logging) on any failure."""
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        log.warning("Config not found: %s - using built-in defaults", config_path)
        return {}
    except PermissionError as exc:
        log.warning("Permission denied while reading config %s: %s", config_path, exc)
        return {}
    except yaml.YAMLError as exc:
        log.warning("Invalid YAML in config %s: %s", config_path, exc)
        return {}
    except OSError as exc:
        log.warning("OS error while reading config %s: %s", config_path, exc)
        return {}

    if data is None:
        return {}
    if not isinstance(data, dict):
        log.warning(
            "Config %s must contain a mapping at the top level, got %s - ignoring",
            config_path,
            type(data).__name__,
        )
        return {}
    return data


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the configuration, deep-merged over :data:`_DEFAULTS`.

    Args:
        path: Optional explicit path to a YAML config. Defaults to
            ``<assets dir>/config.yml``.

    Returns:
        The merged configuration. Never raises -- unreadable or invalid files
        fall back to the built-in defaults.
    """
    config_path = Path(path) if path is not None else get_assets_dir() / CONFIG_FILENAME
    return _deep_merge(_DEFAULTS, _read_yaml(config_path))


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    """Return the process-wide configuration singleton."""
    return load_config()


def reload_config() -> dict[str, Any]:
    """Clear the cache and re-read the config file (used by tests)."""
    get_config.cache_clear()
    return get_config()


# ── Derived helpers ───────────────────────────────────────────────────────────


def _normalize_hex(color: Any, context: str = "") -> str | None:
    """Return *color* as a bare uppercase 6-digit hex string, or ``None``."""
    if not color:
        return None
    normalized = str(color).lstrip("#").upper()
    if re.fullmatch(r"[0-9A-F]{6}", normalized):
        return normalized
    log.warning("Invalid color '%s'%s", color, f" for {context}" if context else "")
    return None


def _nutzungsarten(config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    entries = (config or get_config()).get("nutzungsarten") or []
    return [e for e in entries if isinstance(e, dict) and e.get("column_name")]


def nutzungsart_display_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Map the raw Nutzungsart value to its display label."""
    return {
        str(e["column_name"]): str(e["name"])
        for e in _nutzungsarten(config)
        if e.get("name")
    }


def nutzungsart_color_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Map the raw Nutzungsart value to a bare 6-digit hex color."""
    colors: dict[str, str] = {}
    for entry in _nutzungsarten(config):
        raw_name = str(entry["column_name"])
        color = _normalize_hex(entry.get("color"), f"Nutzungsart '{raw_name}'")
        if color:
            colors[raw_name] = color
    return colors


def nutzungsart_key_order(config: dict[str, Any] | None = None) -> list[str]:
    """Raw Nutzungsart values ordered by their ``sort_order``."""
    ordered: list[tuple[int, str]] = []
    for entry in _nutzungsarten(config):
        raw_name = str(entry["column_name"])
        sort_order = entry.get("sort_order")
        if sort_order is None:
            continue
        try:
            ordered.append((int(sort_order), raw_name))
        except (TypeError, ValueError):
            log.warning(
                "Invalid sort_order '%s' for Nutzungsart '%s'", sort_order, raw_name
            )
    return [name for _, name in sorted(ordered, key=lambda item: item[0])]


def nutzungsart_group_members(
    gruppe: str, config: dict[str, Any] | None = None
) -> list[str]:
    """Raw Nutzungsart values belonging to *gruppe* (e.g. ``"buero"``)."""
    return [
        str(e["column_name"])
        for e in _nutzungsarten(config)
        if str(e.get("gruppe", "")).lower() == gruppe.lower()
    ]


def nutzungsart_multipliers(config: dict[str, Any] | None = None) -> dict[str, float]:
    """Per-Nutzungsart factor multipliers applied when loading Nutzungsfaktoren."""
    multipliers: dict[str, float] = {}
    for entry in _nutzungsarten(config):
        raw_multiplier = entry.get("faktor_multiplikator")
        if raw_multiplier is None:
            continue
        raw_name = str(entry["column_name"])
        try:
            multipliers[raw_name] = float(raw_multiplier)
        except (TypeError, ValueError):
            log.warning(
                "Invalid faktor_multiplikator '%s' for Nutzungsart '%s'",
                raw_multiplier,
                raw_name,
            )
    return multipliers


def _eigentumsform_entries(
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    section = (config or get_config()).get("eigentumsformen") or {}
    entries = section.get("mapping") or []
    return [e for e in entries if isinstance(e, dict) and e.get("from")]


def eigentumsform_rename_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Map raw Eigentumsform values to their display labels."""
    return {
        str(e["from"]): str(e["to"])
        for e in _eigentumsform_entries(config)
        if e.get("to")
    }


def eigentumsform_color_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Map the *renamed* Eigentumsform label to a ``#rrggbb`` color."""
    colors: dict[str, str] = {}
    for entry in _eigentumsform_entries(config):
        label = str(entry.get("to") or entry["from"])
        color = _normalize_hex(entry.get("color"), f"Eigentumsform '{label}'")
        if color:
            colors[label] = f"#{color}"
    return colors


def eigenmiete_rule(config: dict[str, Any] | None = None) -> dict[str, str] | None:
    """The ``Eigentumsform`` + ``Eigentümer`` special case, or ``None``.

    Returns a dict with the keys ``eigentumsform``, ``eigentuemer`` and ``as``.
    """
    section = (config or get_config()).get("eigentumsformen") or {}
    rule = section.get("eigenmiete_rule")
    if not isinstance(rule, dict):
        return None
    required = ("eigentumsform", "eigentuemer", "as")
    if not all(rule.get(key) for key in required):
        log.warning("Incomplete eigenmiete_rule %s - ignoring", rule)
        return None
    return {key: str(rule[key]) for key in required}


def stichjahre(key: str, config: dict[str, Any] | None = None) -> Any:
    """Return the configured year list (or single year) for *key*."""
    years = (config or get_config()).get("years") or {}
    if key not in years:
        log.warning("Unknown Stichjahr key '%s' - falling back to defaults", key)
        return copy.deepcopy(_DEFAULTS["years"].get(key))
    return years[key]


def default_input_paths(config: dict[str, Any] | None = None) -> dict[str, Path | None]:
    """Resolve the optional default input file paths.

    Returns a dict with the keys ``gebaeude``, ``studierende`` and ``faktoren``.
    A value is ``None`` when no default is configured, so the file picker
    starts empty.
    """
    defaults = ((config or get_config()).get("data") or {}).get("defaults") or {}
    raw_base = defaults.get("base_path")
    base = Path(str(raw_base)).expanduser() if raw_base else None

    resolved: dict[str, Path | None] = {}
    for key in ("gebaeude", "studierende", "faktoren"):
        value = defaults.get(key)
        if not value:
            resolved[key] = None
            continue
        candidate = Path(str(value)).expanduser()
        if not candidate.is_absolute() and base is not None:
            candidate = base / candidate
        resolved[key] = candidate
    return resolved
