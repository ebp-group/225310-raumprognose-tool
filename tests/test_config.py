"""Tests for the configuration loader in ``app/config.py``."""

from pathlib import Path

import config


def test_missing_file_falls_back_to_defaults(tmp_path: Path) -> None:
    """A missing config.yml must not raise -- it degrades to the defaults.

    Regression test: the previous loader returned a 2-tuple on every error path
    but unpacked 3 values, so a missing config crashed the app at import time.
    """
    cfg = config.load_config(tmp_path / "does-not-exist.yml")

    assert cfg["years"]["prognose"] == [2026, 2030, 2040, 2050]
    assert cfg["excel"]["rounding_step"] == 5
    assert config.nutzungsart_display_map(cfg) == {}
    assert config.nutzungsart_key_order(cfg) == []


def test_invalid_yaml_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text("years: [unclosed\n", encoding="utf-8")

    cfg = config.load_config(path)

    assert cfg["years"]["prognose"] == config._DEFAULTS["years"]["prognose"]


def test_non_mapping_yaml_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    cfg = config.load_config(path)

    assert cfg["app"]["name"] == config._DEFAULTS["app"]["name"]


def test_partial_config_is_deep_merged(tmp_path: Path) -> None:
    """Only the keys present in the file are overridden."""
    path = tmp_path / "config.yml"
    path.write_text(
        "years:\n"
        "  prognose: [2027, 2035]\n"
        "app:\n"
        "  organization: 'Uni Musterstadt'\n",
        encoding="utf-8",
    )

    cfg = config.load_config(path)

    assert cfg["years"]["prognose"] == [2027, 2035]
    # untouched sibling keys survive
    assert cfg["years"]["flaechenpotenzial"] == 2040
    assert cfg["app"]["organization"] == "Uni Musterstadt"
    assert cfg["app"]["name"] == "Raumprognose Tool"


def test_invalid_color_is_dropped_but_rest_survives(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "nutzungsarten:\n"
        "  - name: Gut\n"
        "    column_name: A\n"
        "    color: '#00ff00'\n"
        "  - name: Kaputt\n"
        "    column_name: B\n"
        "    color: 'nicht-eine-farbe'\n",
        encoding="utf-8",
    )

    cfg = config.load_config(path)

    assert config.nutzungsart_color_map(cfg) == {"A": "00FF00"}
    # the entry itself is still there, just without a color
    assert config.nutzungsart_display_map(cfg) == {"A": "Gut", "B": "Kaputt"}


def test_sort_order_zero_is_respected(tmp_path: Path) -> None:
    """A falsy-but-valid sort_order of 0 must not be silently dropped."""
    path = tmp_path / "config.yml"
    path.write_text(
        "nutzungsarten:\n"
        "  - name: Erste\n"
        "    column_name: A\n"
        "    sort_order: 0\n"
        "  - name: Zweite\n"
        "    column_name: B\n"
        "    sort_order: 1\n",
        encoding="utf-8",
    )

    assert config.nutzungsart_key_order(config.load_config(path)) == ["A", "B"]


def test_entries_without_column_name_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "nutzungsarten:\n  - name: Ohne Rohwert\n    sort_order: 1\n",
        encoding="utf-8",
    )

    cfg = config.load_config(path)

    assert config.nutzungsart_display_map(cfg) == {}
    assert config.nutzungsart_key_order(cfg) == []


def test_group_members_and_multipliers(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "nutzungsarten:\n"
        "  - column_name: Lehre1\n"
        "    gruppe: lehre\n"
        "  - column_name: Buero1\n"
        "    gruppe: buero\n"
        "    faktor_multiplikator: 14.5\n",
        encoding="utf-8",
    )

    cfg = config.load_config(path)

    assert config.nutzungsart_group_members("buero", cfg) == ["Buero1"]
    assert config.nutzungsart_group_members("lehre", cfg) == ["Lehre1"]
    assert config.nutzungsart_multipliers(cfg) == {"Buero1": 14.5}


def test_eigentumsform_mapping_and_colors(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "eigentumsformen:\n"
        "  mapping:\n"
        "    - from: Roh\n"
        "      to: Anzeige\n"
        "      color: '#8cb48c'\n",
        encoding="utf-8",
    )

    cfg = config.load_config(path)

    assert config.eigentumsform_rename_map(cfg) == {"Roh": "Anzeige"}
    # colors are keyed on the *renamed* label, which is what the charts see
    assert config.eigentumsform_color_map(cfg) == {"Anzeige": "#8CB48C"}


def test_incomplete_eigenmiete_rule_is_ignored(tmp_path: Path) -> None:
    """A partial rule is rejected outright rather than half-inherited.

    The rule is atomic: a site overriding only ``eigentumsform`` must not
    silently keep another site's ``eigentuemer``.
    """
    path = tmp_path / "config.yml"
    path.write_text(
        "eigentumsformen:\n  eigenmiete_rule:\n    eigentumsform: Miete\n",
        encoding="utf-8",
    )

    assert config.eigenmiete_rule(config.load_config(path)) is None


def test_eigenmiete_rule_is_replaced_wholesale(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "eigentumsformen:\n"
        "  eigenmiete_rule:\n"
        "    eigentumsform: Miete\n"
        "    eigentuemer: Hochbauamt Musterstadt\n"
        "    as: Eigenmiete\n",
        encoding="utf-8",
    )

    assert config.eigenmiete_rule(config.load_config(path)) == {
        "eigentumsform": "Miete",
        "eigentuemer": "Hochbauamt Musterstadt",
        "as": "Eigenmiete",
    }


def test_eigenmiete_rule_can_be_disabled(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text("eigentumsformen:\n  eigenmiete_rule: null\n", encoding="utf-8")

    assert config.eigenmiete_rule(config.load_config(path)) is None


def test_default_input_paths_are_none_when_unset(tmp_path: Path) -> None:
    cfg = config.load_config(tmp_path / "missing.yml")

    assert config.default_input_paths(cfg) == {
        "gebaeude": None,
        "studierende": None,
        "faktoren": None,
    }


def test_default_input_paths_resolve_relative_names_against_base(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "data:\n"
        "  defaults:\n"
        "    base_path: /daten/areal\n"
        "    gebaeude: inventar.xlsx\n"
        "    studierende: /woanders/stud.xlsx\n",
        encoding="utf-8",
    )

    resolved = config.default_input_paths(config.load_config(path))

    assert resolved["gebaeude"] == Path("/daten/areal/inventar.xlsx")
    # absolute entries ignore base_path
    assert resolved["studierende"] == Path("/woanders/stud.xlsx")
    assert resolved["faktoren"] is None


def test_stichjahre_unknown_key_falls_back(tmp_path: Path) -> None:
    cfg = config.load_config(tmp_path / "missing.yml")

    assert config.stichjahre("prognose", cfg) == [2026, 2030, 2040, 2050]
    assert config.stichjahre("gibt-es-nicht", cfg) is None


def test_shipped_config_is_loadable() -> None:
    """The config.yml that ships with the app must parse and be complete."""
    cfg = config.load_config()

    assert config.nutzungsart_key_order(cfg), "expected a Nutzungsart catalogue"
    assert config.nutzungsart_group_members("buero", cfg), "expected a Büro group"
    assert config.eigenmiete_rule(cfg) is not None
    assert config.eigentumsform_rename_map(cfg)
