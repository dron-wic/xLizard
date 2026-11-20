# -*- coding: utf-8 -*-
from xlizard.thresholds import (
    DEFAULT_THRESHOLDS,
    METRIC_HELP,
    METRIC_ORDER,
    METRICS_ABOUT_DETAIL,
    METRICS_ABOUT_GENERAL,
    METRIC_TAB_TITLES,
    THRESHOLDS_ORIGIN_TEXT,
    load_thresholds,
    metrics_about_tabs,
    parse_thresholds_text,
    write_thresholds_file,
)


def test_parse_aliases():
    text = """
    CCN=25
    CogC=12
    ND=5
    # comment
    nloc=80
    """
    got = parse_thresholds_text(text)
    assert got["cyclomatic_complexity"] == 25
    assert got["cognitive_complexity"] == 12
    assert got["max_nesting_depth"] == 5
    assert got["nloc"] == 80


def test_load_creates_and_merges(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    values = load_thresholds(create_if_missing=True)
    assert (tmp_path / "thresholds.txt").is_file()
    assert values["cyclomatic_complexity"] == DEFAULT_THRESHOLDS["cyclomatic_complexity"]

    (tmp_path / "thresholds.txt").write_text("CCN=42\n", encoding="utf-8")
    values2 = load_thresholds(create_if_missing=False)
    assert values2["cyclomatic_complexity"] == 42
    assert values2["cognitive_complexity"] == DEFAULT_THRESHOLDS["cognitive_complexity"]


def test_write_roundtrip(tmp_path):
    path = tmp_path / "t.txt"
    write_thresholds_file(path, {"cyclomatic_complexity": 33})
    text = path.read_text(encoding="utf-8")
    assert "cyclomatic_complexity=33" in text


def test_metric_help_and_origin_text():
    assert set(METRIC_HELP.keys()) == set(METRIC_ORDER)
    file_keys = {
        "comment_percentage",
        "max_block_depth",
        "pointer_operations",
        "preprocessor_directives",
        "logical_operators",
        "conditional_statements",
        "function_count",
    }
    for key in METRIC_ORDER:
        text = METRIC_HELP[key]
        assert text.strip()
        assert "Влияет" in text
        if key in file_keys:
            assert "Уровень: файл" in text
        else:
            assert "Уровень: функция" in text
    assert "NIST" in METRICS_ABOUT_GENERAL
    assert "Sonar" in METRICS_ABOUT_GENERAL
    assert "HIS" in METRICS_ABOUT_GENERAL
    assert "уровня ФУНКЦИЯ" in METRICS_ABOUT_GENERAL
    assert "уровня ФАЙЛ" in METRICS_ABOUT_GENERAL
    assert set(METRICS_ABOUT_DETAIL.keys()) == set(METRIC_ORDER)
    assert set(METRIC_TAB_TITLES.keys()) == set(METRIC_ORDER)
    tabs = metrics_about_tabs()
    assert tabs[0][0] == "Общее"
    assert len(tabs) == 1 + len(METRIC_ORDER)
    for key in METRIC_ORDER:
        detail = METRICS_ABOUT_DETAIL[key]
        assert "Как считается" in detail
        assert "Пример" in detail
        assert "Базовый порог" in detail
    assert "NIST" in THRESHOLDS_ORIGIN_TEXT
    assert "NLOC" in THRESHOLDS_ORIGIN_TEXT
    assert "Length" in THRESHOLDS_ORIGIN_TEXT
