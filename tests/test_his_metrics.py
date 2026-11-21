# -*- coding: utf-8 -*-
"""HIS pack: extensions, scoring gate, HTML visibility."""
from pathlib import Path

from xlizard.thresholds import write_app_config
from xlizard.xlizard import main


HIS_C = r"""
int helper_a(void) { return 1; }
int helper_b(void) { return 2; }

int with_goto(int x) {
    if (x) goto fail;
    return helper_a() + helper_b();
fail:
    return -1;
}
"""


def test_his_extensions_when_enabled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_app_config(tmp_path / "xlizard.json", his_metrics=True)
    src = tmp_path / "his.c"
    src.write_text(HIS_C, encoding="utf-8")
    out = tmp_path / "on.html"
    try:
        main(["xlizard", "--html", "-o", str(out), str(src)])
    except SystemExit as exc:
        assert exc.code in (0, None) or int(exc.code or 0) == 0
    text = out.read_text(encoding="utf-8", errors="ignore")
    assert "HIS вкл" in text or "HIS вкл." in text
    assert ">GOTO<" in text or "GOTO <" in text
    assert "RETURN" in text
    assert "PATH" in text
    assert "CALLS" in text
    assert "CALLING" in text
    assert "HIS-метрики отключены" not in text


def test_his_disabled_note_no_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_app_config(tmp_path / "xlizard.json", his_metrics=False)
    src = tmp_path / "his.c"
    src.write_text(HIS_C, encoding="utf-8")
    out = tmp_path / "off.html"
    try:
        main(["xlizard", "--html", "-o", str(out), str(src)])
    except SystemExit as exc:
        assert exc.code in (0, None) or int(exc.code or 0) == 0
    text = out.read_text(encoding="utf-8", errors="ignore")
    assert "HIS-метрики отключены" in text
    assert "HIS откл" in text or "HIS откл." in text
    # Column headers for HIS should not appear as table headers when off
    assert "tooltip-icon\" data-tooltip=\"HIS GOTO" not in text
