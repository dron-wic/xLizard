# -*- coding: utf-8 -*-
"""Function-level metrics: CCN, CogC, ND, PARAM against C fixtures."""
from tests.helpers import analyze_map


EXTS = ["cognitive", "nd"]


def test_plain(all_metrics_c):
    fns = analyze_map(all_metrics_c, EXTS)
    f = fns["plain_fn"]
    assert f.cyclomatic_complexity == 1
    assert f.cognitive_complexity == 0
    assert f.max_nesting_depth == 0
    assert f.parameter_count == 0


def test_parameters(all_metrics_c):
    fns = analyze_map(all_metrics_c, EXTS)
    assert fns["one_param"].parameter_count == 1
    assert fns["three_params"].parameter_count == 3


def test_if_simple(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["if_simple"]
    assert f.cyclomatic_complexity == 2
    assert f.cognitive_complexity == 1
    assert f.max_nesting_depth == 1


def test_if_and(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["if_and"]
    assert f.cyclomatic_complexity == 3
    assert f.cognitive_complexity == 2
    assert f.max_nesting_depth == 1  # && must not inflate ND


def test_if_and_or(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["if_and_or"]
    assert f.cyclomatic_complexity == 4
    assert f.cognitive_complexity == 3


def test_nested_if(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["nested_if"]
    assert f.cyclomatic_complexity == 3
    assert f.cognitive_complexity == 3
    assert f.max_nesting_depth == 2


def test_if_else(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["if_else"]
    assert f.cyclomatic_complexity == 2
    assert f.cognitive_complexity == 2
    assert f.max_nesting_depth == 1


def test_ternary(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["ternary_op"]
    assert f.cyclomatic_complexity == 2
    assert f.cognitive_complexity == 1


def test_loops(all_metrics_c):
    fns = analyze_map(all_metrics_c, EXTS)
    assert fns["for_loop"].cyclomatic_complexity == 2
    assert fns["for_loop"].cognitive_complexity == 1
    assert fns["while_loop"].cyclomatic_complexity == 2
    assert fns["while_loop"].cognitive_complexity == 1
    assert fns["do_while"].cyclomatic_complexity == 2
    assert fns["do_while"].cognitive_complexity == 1


def test_switch_default_ccn_and_cogc(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["switch_two_cases"]
    # lizard-style: each case +1, switch keyword itself not counted
    assert f.cyclomatic_complexity == 3
    assert f.cognitive_complexity == 1


def test_goto(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["goto_label"]
    assert f.cyclomatic_complexity == 2
    assert f.cognitive_complexity == 2


def test_nested_for_if(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["nested_for_if"]
    # base + for + if + &&
    assert f.cyclomatic_complexity == 4
    assert f.cognitive_complexity == 4
    assert f.max_nesting_depth == 2


def test_recursion(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["recursion_self"]
    assert f.cognitive_complexity >= 2  # if + recursion


def test_nloc_and_tokens_positive(all_metrics_c):
    f = analyze_map(all_metrics_c, EXTS)["nested_if"]
    assert f.nloc >= 3
    assert f.token_count >= 10
    assert f.length >= f.nloc
