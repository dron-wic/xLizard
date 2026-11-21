# -*- coding: utf-8 -*-
from xlizard.quality_score import compute_quality_score
from xlizard.thresholds import DEFAULT_SOFT_PCT, DEFAULT_THRESHOLDS


def _func(**kwargs):
    base = {
        "cyclomatic_complexity": 1,
        "cognitive_complexity": 1,
        "max_nesting_depth": 1,
        "nloc": 10,
        "token_count": 20,
        "parameter_count": 1,
        "length": 20,
        "start_line": 1,
        "end_line": 20,
        "in_disable_block": False,
    }
    base.update(kwargs)
    return base


def _file(functions=None, **kwargs):
    funcs = functions or [_func()]
    base = {
        "filename": "a.c",
        "functions": funcs,
        "max_block_depth": 1,
        "pointer_operations": 0,
        "preprocessor_directives": 0,
        "logical_operators": 0,
        "conditional_statements": 0,
        "active_functions_count": len(
            [f for f in funcs if not f.get("in_disable_block")]
        ),
        "comment_percentage": 10,
    }
    base.update(kwargs)
    return base


def test_clean_project_is_norma():
    result = compute_quality_score([_file()], DEFAULT_THRESHOLDS, DEFAULT_SOFT_PCT)
    assert result["score"] == 100
    assert result["status"] == "Норма"
    assert result["has_exceedances"] is False
    assert result["soft_count"] == 0
    assert result["hard_count"] == 0


def test_soft_ccn_exceedance_with_default_band():
    # limit 15, soft 25% → up to 18.75 is soft; 18 is soft
    result = compute_quality_score(
        [_file(functions=[_func(cyclomatic_complexity=18)])],
        DEFAULT_THRESHOLDS,
        DEFAULT_SOFT_PCT,
    )
    assert result["has_exceedances"] is True
    assert result["soft_count"] >= 1
    assert result["hard_count"] == 0
    assert result["status"] == "Допустимо"
    assert result["score"] >= 80


def test_hard_ccn_when_soft_pct_tight():
    soft = dict(DEFAULT_SOFT_PCT)
    soft["cyclomatic_complexity"] = 5  # 15 * 1.05 = 15.75 → 18 is hard
    result = compute_quality_score(
        [_file(functions=[_func(cyclomatic_complexity=18)])],
        DEFAULT_THRESHOLDS,
        soft,
    )
    assert result["hard_count"] >= 1
    assert result["soft_by_metric"].get("cyclomatic_complexity", 0) == 0
    assert result["hard_by_metric"]["cyclomatic_complexity"] == 1
    assert result["score"] < 100


def test_comment_percentage_zero_ignored():
    result = compute_quality_score(
        [_file(comment_percentage=0)],
        {**DEFAULT_THRESHOLDS, "comment_percentage": 0},
        DEFAULT_SOFT_PCT,
    )
    assert result["soft_by_metric"].get("comment_percentage", 0) == 0
    assert result["hard_by_metric"].get("comment_percentage", 0) == 0
    assert "comment_percentage" not in result["soft_by_metric"]
    assert result["score"] == 100


def test_his_goto_ignored_when_disabled():
    result = compute_quality_score(
        [_file(functions=[_func(goto_count=2)])],
        DEFAULT_THRESHOLDS,
        DEFAULT_SOFT_PCT,
        his_enabled=False,
    )
    assert result["hard_by_metric"].get("goto_count", 0) == 0
    assert result["score"] == 100


def test_his_goto_hard_when_enabled():
    result = compute_quality_score(
        [_file(functions=[_func(goto_count=1)])],
        DEFAULT_THRESHOLDS,
        DEFAULT_SOFT_PCT,
        his_enabled=True,
    )
    assert result["hard_by_metric"].get("goto_count", 0) == 1
    assert result["has_exceedances"] is True
    assert result["score"] < 100
