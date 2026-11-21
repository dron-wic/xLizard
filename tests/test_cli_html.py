# -*- coding: utf-8 -*-
"""Smoke: HTML report generation for the C fixture."""
import os
from pathlib import Path

from xlizard.xlizard import main


def test_html_report_contains_cogc(all_metrics_c, tmp_path):
    out = tmp_path / "report.html"
    try:
        main([
            "xlizard",
            "--html",
            "-o", str(out),
            "-E", "cognitive",
            "-E", "nd",
            str(all_metrics_c),
        ])
    except SystemExit as exc:
        assert exc.code in (0, None) or int(exc.code or 0) == 0

    text = out.read_text(encoding="utf-8", errors="ignore")
    assert "CogC" in text
    assert "nested_if" in text
    assert "Суммарная оценка качества" in text
    assert "quality-score-value" in text
    assert "Длина (Length)" in text
    assert "Мягкое:" in text
    # Default config has HIS off → note present, HIS column tooltips absent
    assert "HIS-метрики отключены" in text or "HIS откл" in text
    assert out.stat().st_size > 1000
