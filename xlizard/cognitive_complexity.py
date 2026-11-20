# -*- coding: utf-8 -*-
"""
Cognitive Complexity for C/C++ (SonarSource specification v1.2+).

Primary integration is the lizard-style extension:

    xlizard -Ecognitive ...

Rules (summary):
  * Structural (+1 + nesting): if, ternary, switch, for/while/do, catch
  * Hybrid (+1, no nesting penalty): else, else if
  * Fundamental (+1): sequences of like &&/||, goto, labeled break/continue,
    direct recursion
  * case / plain break / continue / return do not increment
  * Preprocessor #if/#ifdef are not counted (reader resolves them)

See: https://www.sonarsource.com/docs/CognitiveComplexity.pdf
     clang-tidy readability-function-cognitive-complexity
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


DEFAULT_COGNITIVE_THRESHOLD = 15


def get_complexity_interpretation(score: int) -> str:
    if score <= 5:
        return "Очень низкая — код читается линейно"
    if score <= 10:
        return "Низкая — код легко понимается"
    if score <= 15:
        return "Умеренная — в пределах типичного порога Sonar (15)"
    if score <= 25:
        return "Высокая — стоит упростить ветвления / вложенность"
    return "Очень высокая — рекомендуется рефакторинг"


def analyze_file_functions(path: str, extensions: Optional[List] = None):
    """Analyze a source file and return FunctionInfo objects with CogC."""
    from xlizard.xlizard import analyze_files, get_extensions

    exts = extensions or get_extensions(["cognitive"])
    results = list(analyze_files([path], threads=1, exts=exts))
    if not results:
        return []
    return results[0].function_list


def analyze_cognitive_complexity(c_code: str) -> Tuple[int, List[Dict]]:
    """
    Analyze a C snippet as a single synthetic function.

    Returns (total_score, per-function summaries). Prefer analyze_file_functions
    for real files — nesting and function boundaries are more accurate there.
    """
    import os
    import tempfile

    wrapped = "void __xlizard_snippet__(void) {\n%s\n}\n" % c_code
    fd, path = tempfile.mkstemp(suffix=".c", prefix="xlizard_cogc_")
    try:
        os.write(fd, wrapped.encode("utf-8"))
        os.close(fd)
        functions = analyze_file_functions(path)
        if not functions:
            return 0, []
        func = functions[0]
        score = int(getattr(func, "cognitive_complexity", 0) or 0)
        return score, [{
            "name": func.name,
            "cognitive_complexity": score,
            "interpretation": get_complexity_interpretation(score),
            "nloc": getattr(func, "nloc", 0),
            "cyclomatic_complexity": getattr(func, "cyclomatic_complexity", 0),
        }]
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def summarize_functions(functions) -> Dict:
    scores = [int(getattr(f, "cognitive_complexity", 0) or 0) for f in functions]
    total = sum(scores)
    return {
        "function_count": len(scores),
        "total_cognitive_complexity": total,
        "max_cognitive_complexity": max(scores) if scores else 0,
        "avg_cognitive_complexity": (total / len(scores)) if scores else 0.0,
        "interpretation": get_complexity_interpretation(
            max(scores) if scores else 0),
    }
