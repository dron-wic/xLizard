# -*- coding: utf-8 -*-
"""
Comprehensive metric tests on the large C suite (helpers + driver + bulk).

Covers function metrics, file-level SourceMonitor heuristics, HIS pack,
quality score sensitivity, and full HTML pipeline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from xlizard.quality_score import compute_quality_score
from xlizard.sourcemonitor_metrics import FileAnalyzer
from xlizard.thresholds import DEFAULT_SOFT_PCT, DEFAULT_THRESHOLDS, write_app_config
from xlizard.xlizard import main

from tests.helpers import (
    CORE_EXTS,
    HIS_EXTS,
    analyze_file_list,
    analyze_map,
    analyze_project_map,
    c_files_in,
)

LARGE = Path(__file__).parent / "fixtures" / "c" / "large"


@pytest.fixture(scope="module")
def large_dir():
    assert LARGE.is_dir()
    files = c_files_in(LARGE)
    assert len(files) >= 3
    return LARGE


@pytest.fixture(scope="module")
def large_files(large_dir):
    return c_files_in(large_dir)


@pytest.fixture(scope="module")
def his_fns(large_files):
    return analyze_project_map(large_files, HIS_EXTS)


@pytest.fixture(scope="module")
def core_fns(large_files):
    return analyze_project_map(large_files, CORE_EXTS)


# ---------------------------------------------------------------------------
# Scale
# ---------------------------------------------------------------------------

def test_suite_is_large_enough(large_files):
    total_lines = 0
    for path in large_files:
        total_lines += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    assert total_lines >= 1500
    assert any(p.name == "bulk_module.c" for p in large_files)


def test_project_has_many_functions(his_fns):
    # helpers(~14) + complex landmarks/callers(~15) + bulk(60+) + entry
    assert len(his_fns) >= 80
    assert "landmark_hub" in his_fns
    assert "bulk_fn_00" in his_fns
    assert "bulk_fn_59" in his_fns


# ---------------------------------------------------------------------------
# Landmark function metrics (core)
# ---------------------------------------------------------------------------

def test_landmark_plain(core_fns):
    f = core_fns["landmark_plain"]
    assert f.cyclomatic_complexity == 1
    assert int(getattr(f, "cognitive_complexity", 0) or 0) == 0
    assert int(getattr(f, "max_nesting_depth", 0) or 0) == 0
    assert f.parameter_count == 0


def test_landmark_params6(core_fns):
    assert core_fns["landmark_params6"].parameter_count == 6


def test_landmark_nested4(core_fns):
    f = core_fns["landmark_nested4"]
    assert f.cyclomatic_complexity >= 5
    assert int(f.max_nesting_depth) >= 4
    assert int(f.cognitive_complexity) >= 8


def test_landmark_fat_size(core_fns):
    f = core_fns["landmark_fat"]
    assert f.nloc >= 40
    assert f.length >= 50
    assert f.token_count >= 80


def test_bulk_functions_have_branching(core_fns):
    f = core_fns["bulk_fn_10"]
    assert f.cyclomatic_complexity >= 4
    assert int(f.cognitive_complexity) >= 2
    assert f.parameter_count == 3


# ---------------------------------------------------------------------------
# HIS metrics on landmarks
# ---------------------------------------------------------------------------

def test_his_goto_count(his_fns):
    f = his_fns["landmark_goto2"]
    assert int(getattr(f, "goto_count", 0)) == 2
    assert int(getattr(f, "return_count", 0)) >= 2


def test_his_return_count(his_fns):
    assert int(getattr(his_fns["landmark_returns3"], "return_count", 0)) == 3
    assert int(getattr(his_fns["landmark_plain"], "return_count", 0)) == 1


def test_his_path_estimate(his_fns):
    pathy = int(getattr(his_fns["landmark_pathy"], "path_count", 1))
    plain = int(getattr(his_fns["landmark_plain"], "path_count", 1))
    assert pathy > plain
    assert pathy >= 16  # sequential ifs inflate estimate


def test_his_calls_unique(his_fns):
    hub = his_fns["landmark_hub"]
    calls = int(getattr(hub, "calls", 0))
    # util_a..h + shared_api_read + shared_api_write (unique; util_a repeats ignored)
    assert calls >= 8
    assert calls <= 12


def test_his_calling_fan_in(his_fns):
    # shared_api_read is used from hub, fat, peripheral callers, etc.
    api = his_fns["shared_api_read"]
    calling = int(getattr(api, "calling", 0))
    assert calling >= 3


def test_core_analysis_omits_his_fields_by_default(core_fns):
    f = core_fns["landmark_goto2"]
    # Without HIS extensions goto_count is not populated by gotocount
    assert getattr(f, "goto_count", 0) == 0
    assert getattr(f, "return_count", 0) == 0


# ---------------------------------------------------------------------------
# File-level SourceMonitor-style
# ---------------------------------------------------------------------------

def test_file_metrics_complex_driver(large_dir):
    path = large_dir / "complex_driver.c"
    m = FileAnalyzer.analyze(str(path))
    assert m is not None
    assert m["preprocessor_directives"] >= 6
    assert m["pointer_operations"] >= 5
    assert m["logical_operators"] >= 2
    assert m["conditional_statements"] >= 10
    assert m["max_block_depth"] >= 2
    assert m["comment_percentage"] > 0
    assert m["lines_of_code"] >= 100


def test_file_metrics_bulk_module(large_dir):
    m = FileAnalyzer.analyze(str(large_dir / "bulk_module.c"))
    assert m is not None
    assert m["lines_of_code"] >= 800
    assert m["preprocessor_directives"] >= 3
    assert m["conditional_statements"] >= 100
    assert m["pointer_operations"] >= 1


# ---------------------------------------------------------------------------
# Quality score + HIS gate
# ---------------------------------------------------------------------------

def _as_func_dicts(fns):
    rows = []
    for name, f in fns.items():
        rows.append(
            {
                "name": name,
                "cyclomatic_complexity": f.cyclomatic_complexity,
                "cognitive_complexity": int(getattr(f, "cognitive_complexity", 0) or 0),
                "max_nesting_depth": int(getattr(f, "max_nesting_depth", 0) or 0),
                "nloc": f.nloc,
                "token_count": f.token_count,
                "parameter_count": f.parameter_count,
                "length": f.length,
                "goto_count": int(getattr(f, "goto_count", 0) or 0),
                "return_count": int(getattr(f, "return_count", 0) or 0),
                "path_count": int(getattr(f, "path_count", 1) or 1),
                "calls": int(getattr(f, "calls", 0) or 0),
                "calling": int(getattr(f, "calling", 0) or 0),
                "in_disable_block": False,
            }
        )
    return [{"filename": "suite.c", "functions": rows,
             "max_block_depth": 1, "pointer_operations": 0,
             "preprocessor_directives": 0, "logical_operators": 0,
             "conditional_statements": 0,
             "active_functions_count": len(rows)}]


def test_quality_score_his_off_ignores_goto(his_fns):
    files = _as_func_dicts(his_fns)
    off = compute_quality_score(files, DEFAULT_THRESHOLDS, DEFAULT_SOFT_PCT, his_enabled=False)
    on = compute_quality_score(files, DEFAULT_THRESHOLDS, DEFAULT_SOFT_PCT, his_enabled=True)
    assert on["hard_by_metric"].get("goto_count", 0) >= 1
    assert off["hard_by_metric"].get("goto_count", 0) == 0
    assert on["score"] <= off["score"]


def test_quality_score_flags_params_and_nesting(his_fns):
    files = _as_func_dicts(his_fns)
    result = compute_quality_score(files, DEFAULT_THRESHOLDS, DEFAULT_SOFT_PCT, his_enabled=True)
    # landmark_params6 PARAM=6 > 5; nested4 / fat / bulk add more
    assert result["has_exceedances"] is True
    assert result["exceedance_count"] >= 1


# ---------------------------------------------------------------------------
# Full HTML pipeline on the large suite
# ---------------------------------------------------------------------------

def test_html_his_on_large_suite(large_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_app_config(tmp_path / "xlizard.json", his_metrics=True)
    out = tmp_path / "large_on.html"
    try:
        main(["xlizard", "--html", "-o", str(out), str(large_dir)])
    except SystemExit as exc:
        assert exc.code in (0, None) or int(exc.code or 0) == 0
    text = out.read_text(encoding="utf-8", errors="ignore")
    assert out.stat().st_size > 50000
    assert "landmark_hub" in text
    assert "bulk_fn_00" in text
    assert "Суммарная оценка качества" in text
    assert "Длина (Length)" in text
    assert "Мягкое:" in text
    assert "Порог: 15.0. Мягкое: 25%" in text or "Порог: 15. Мягкое: 25%" in text
    assert "HIS вкл" in text or "HIS вкл." in text
    assert "HIS GOTO" in text or ">GOTO<" in text
    assert "CALLING" in text
    assert "HIS-метрики отключены" not in text


def test_html_his_off_large_suite(large_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_app_config(tmp_path / "xlizard.json", his_metrics=False)
    out = tmp_path / "large_off.html"
    try:
        main(["xlizard", "--html", "-o", str(out), str(large_dir)])
    except SystemExit as exc:
        assert exc.code in (0, None) or int(exc.code or 0) == 0
    text = out.read_text(encoding="utf-8", errors="ignore")
    assert "landmark_nested4" in text
    assert "HIS-метрики отключены" in text
    assert "tooltip-icon\" data-tooltip=\"HIS GOTO" not in text


def test_single_file_map_helpers(large_dir):
    fns = analyze_map(large_dir / "helpers.c", HIS_EXTS)
    assert "util_a" in fns
    assert "shared_api_read" in fns
    assert fns["util_a"].cyclomatic_complexity == 1
