# -*- coding: utf-8 -*-
"""Optional CCN extensions: McCabe fall-through and modified switch."""
from tests.helpers import analyze_map


def test_mccabe_fallthrough(all_metrics_c):
    f = analyze_map(all_metrics_c, ["mccabe"])["switch_fallthrough"]
    # base + first case; consecutive case subtracted
    assert f.cyclomatic_complexity == 2


def test_mccabe_does_not_change_separate_cases(all_metrics_c):
    f = analyze_map(all_metrics_c, ["mccabe"])["switch_two_cases"]
    assert f.cyclomatic_complexity == 3


def test_modified_switch_counts_as_one_decision(all_metrics_c):
    # -m: each case (+1 CCN, −1 modified) cancels; switch adds +1 → base+1 = 2
    f = analyze_map(all_metrics_c, ["modified"])["switch_two_cases"]
    assert f.cyclomatic_complexity == 2


def test_nonstrict_drops_boolean_from_ccn(all_metrics_c):
    f = analyze_map(all_metrics_c, ["nonstrict"])["if_and"]
    # base + if only (&& removed from conditions)
    assert f.cyclomatic_complexity == 2
