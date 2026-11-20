# -*- coding: utf-8 -*-
"""File-level SourceMonitor-style metrics on C fixture."""
from xlizard.sourcemonitor_metrics import FileAnalyzer


def test_file_metrics_sample(file_metrics_c):
    m = FileAnalyzer.analyze(str(file_metrics_c))
    assert m is not None
    assert m["comment_percentage"] > 0
    assert m["preprocessor_directives"] >= 2
    assert m["pointer_operations"] >= 1
    assert m["logical_operators"] >= 1
    assert m["conditional_statements"] >= 2
    assert m["max_block_depth"] >= 1
    assert m["lines_of_code"] > 0
    assert m["total_lines"] >= m["lines_of_code"]


def test_braceless_if_counted(file_metrics_c):
    m = FileAnalyzer.analyze(str(file_metrics_c))
    # if (a) + if (a && b) + else + while  >= 4
    assert m["conditional_statements"] >= 4
