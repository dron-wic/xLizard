# -*- coding: utf-8 -*-
import json

from xlizard.thresholds import (
    CONFIG_FILENAME,
    DEFAULT_SOFT_PCT,
    DEFAULT_THRESHOLDS,
    HIS_METRIC_KEYS,
    METRIC_HELP,
    METRIC_ORDER,
    METRICS_ABOUT_DETAIL,
    METRICS_ABOUT_GENERAL,
    METRIC_TAB_TITLES,
    THRESHOLDS_ORIGIN_TEXT,
    load_app_config,
    load_threshold_config,
    load_thresholds,
    metrics_about_tabs,
    parse_thresholds_text,
    soft_pct_key,
    write_app_config,
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


def test_load_creates_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    values = load_thresholds(create_if_missing=True)
    assert (tmp_path / CONFIG_FILENAME).is_file()
    assert values["cyclomatic_complexity"] == DEFAULT_THRESHOLDS["cyclomatic_complexity"]
    raw = json.loads((tmp_path / CONFIG_FILENAME).read_text(encoding="utf-8"))
    assert "metrics" in raw
    assert "features" in raw
    assert raw["features"]["his_metrics"] is False
    assert "quality_score" in raw
    assert raw["quality_score"]["soft_func_weight"] == 15


def test_migrate_from_legacy_txt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "thresholds.txt").write_text("CCN=42\nCCN_soft_pct=11\n", encoding="utf-8")
    (tmp_path / "ui_theme.txt").write_text("light\n", encoding="utf-8")
    cfg = load_app_config(create_if_missing=True)
    assert cfg["thresholds"]["cyclomatic_complexity"] == 42
    assert cfg["soft_pcts"]["cyclomatic_complexity"] == 11
    assert cfg["theme"] == "light"
    assert (tmp_path / CONFIG_FILENAME).is_file()


def test_write_json_roundtrip(tmp_path):
    path = tmp_path / "xlizard.json"
    write_app_config(
        path,
        thresholds={"cyclomatic_complexity": 33},
        soft_pcts={"cyclomatic_complexity": 12},
        theme="light",
        his_metrics=True,
        quality_score={"soft_func_weight": 20, "hard_func_weight": 50},
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["metrics"]["cyclomatic_complexity"]["limit"] == 33
    assert raw["metrics"]["cyclomatic_complexity"]["soft_pct"] == 12
    assert raw["theme"] == "light"
    assert raw["features"]["his_metrics"] is True
    assert raw["quality_score"]["soft_func_weight"] == 20
    assert raw["quality_score"]["hard_func_weight"] == 50
    for key in HIS_METRIC_KEYS:
        assert key in raw["metrics"]

    limits, soft = load_threshold_config(str(path), create_if_missing=False)
    assert limits["cyclomatic_complexity"] == 33
    assert soft["cyclomatic_complexity"] == 12
    cfg = load_app_config(str(path), create_if_missing=False)
    assert cfg["quality_score"]["soft_func_weight"] == 20


def test_soft_pct_aliases_legacy_text():
    text = """
    CCN=18
    CCN_soft_pct=5
    soft_pct_nloc=33
    """
    parsed = parse_thresholds_text(text)
    assert parsed["cyclomatic_complexity"] == 18
    assert parsed[soft_pct_key("cyclomatic_complexity")] == 5
    assert parsed[soft_pct_key("nloc")] == 33


def test_write_thresholds_file_alias_writes_json(tmp_path):
    path = tmp_path / "settings.json"
    write_thresholds_file(path, {"nloc": 90}, {"nloc": 30}, his_metrics=False)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["metrics"]["nloc"]["limit"] == 90
    assert raw["metrics"]["nloc"]["soft_pct"] == 30


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
    assert "xlizard.json" in METRICS_ABOUT_GENERAL
    assert "GOTO" in METRICS_ABOUT_GENERAL
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
    assert "CALLING" in THRESHOLDS_ORIGIN_TEXT
