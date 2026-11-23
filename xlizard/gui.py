# -*- coding: utf-8 -*-
"""
Desktop UI for xLizard: выбор файла/папки и HTML-отчёт.
Пороги и тема — в xlizard.json рядом с программой.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import (
    BooleanVar,
    Frame,
    IntVar,
    Menu,
    StringVar,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
    ttk,
)
from tkinter.scrolledtext import ScrolledText

from xlizard.quality_score import (
    DEFAULT_QUALITY_WEIGHTS,
    QUALITY_WEIGHT_LABELS,
    QUALITY_WEIGHT_ORDER,
    format_quality_formula,
)
from xlizard.thresholds import (
    DEFAULT_HIS_METRICS,
    DEFAULT_QUALITY_SCORE,
    DEFAULT_SOFT_PCT,
    DEFAULT_THRESHOLDS,
    HIS_METRIC_KEYS,
    METRIC_HELP,
    METRIC_LABELS,
    METRIC_ORDER,
    config_path,
    load_app_config,
    metrics_about_tabs,
    write_app_config,
)


APP_TITLE = "xLizard"
SUPPORTED_EXTS = (".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".mm")
HIS_METRIC_SET = frozenset(HIS_METRIC_KEYS)

THEMES = {
    "dark": {
        "bg": "#1a1d23",
        "card": "#242830",
        "field": "#2d323c",
        "fg": "#e8eaed",
        "muted": "#9aa0a6",
        "compact": "#c5c8ce",
        "accent": "#ff6b35",
        "accent_active": "#e55a28",
        "accent_disabled": "#5a463c",
        "button": "#2d323c",
        "button_active": "#3a4050",
        "log_bg": "#12151a",
        "log_fg": "#c5c8ce",
        "tooltip_bg": "#3a4050",
        "tab": "#2d323c",
        "tab_selected": "#3a4050",
        "tab_active": "#343a46",
        "border": "#3a4050",
    },
    "light": {
        "bg": "#d9dde3",
        "card": "#c8ced6",
        "field": "#e8ebf0",
        "fg": "#1a1d23",
        "muted": "#4a5058",
        "compact": "#2c3138",
        "accent": "#ff6b35",
        "accent_active": "#e55a28",
        "accent_disabled": "#f5c4b0",
        "button": "#b8bfc8",
        "button_active": "#a8b0bc",
        "log_bg": "#e4e7ec",
        "log_fg": "#1a1d23",
        "tooltip_bg": "#e8ebf0",
        "tab": "#c8ced6",
        "tab_selected": "#e8ebf0",
        "tab_active": "#d9dde3",
        "border": "#8a919c",
    },
}

# Icon reflects current theme: moon = dark, sun = light
THEME_ICONS = {"dark": "☾", "light": "☀"}
THEME_ICON_TIPS = {
    "dark": "Тёмная тема (нажмите для светлой)",
    "light": "Светлая тема (нажмите для тёмной)",
}


class _StdoutRedirect:
    """File-like sink for print/tqdm/logging during GUI analysis."""

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, write_fn):
        self._write_fn = write_fn

    def write(self, text):
        if text:
            self._write_fn(text)
        return len(text) if text else 0

    def flush(self):
        pass

    def isatty(self):
        return False

    def fileno(self):
        raise OSError("no fileno for GUI redirect")


class _GuiLogHandler(logging.Handler):
    """Forward logging records into the GUI journal."""

    def __init__(self, write_fn):
        super().__init__()
        self._write_fn = write_fn
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            if msg:
                self._write_fn(msg + "\n")
        except Exception:
            self.handleError(record)


class _HoverTooltip:
    """Simple hover tip for ttk/tk widgets (multiline)."""

    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = (text or "").strip()
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip: Toplevel | None = None
        if not self.text:
            return
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

    def _show(self):
        self._after_id = None
        if self._tip is not None or not self.widget.winfo_exists():
            return
        tip = Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        root = self.widget.winfo_toplevel()
        theme_name = getattr(root, "_xlizard_theme", "dark")
        colors = THEMES.get(theme_name, THEMES["dark"])
        try:
            tip.configure(bg=colors["tooltip_bg"])
        except Exception:
            pass
        label = ttk.Label(
            tip,
            text=self.text,
            style="Tooltip.TLabel",
            justify="left",
            wraplength=360,
            padding=(8, 6),
        )
        label.pack()
        tip.update_idletasks()
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        tip.geometry("+%d+%d" % (x, y))
        self._tip = tip


class XLizardApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(900, 640)
        self.root.geometry("960x680")

        self.path_var = StringVar()
        self.output_var = StringVar()
        self.threads_var = IntVar(value=max(1, (os.cpu_count() or 2) // 2))
        self.open_browser_var = BooleanVar(value=True)
        self.config_file = config_path()
        self.thresholds_file = self.config_file
        cfg = load_app_config(create_if_missing=True)
        self.thresholds = dict(cfg["thresholds"])
        self.soft_pcts = dict(cfg["soft_pcts"])
        self.his_metrics = bool(cfg.get("his_metrics", DEFAULT_HIS_METRICS))
        self.his_metrics_var = BooleanVar(value=self.his_metrics)
        self.quality_weights = dict(cfg.get("quality_score") or DEFAULT_QUALITY_SCORE)
        self.threshold_vars: dict[str, IntVar] = {}
        self.soft_pct_vars: dict[str, IntVar] = {}
        self.quality_weight_vars: dict[str, IntVar] = {}
        self._his_spinboxes: list = []
        for key in METRIC_ORDER:
            self.threshold_vars[key] = IntVar(
                value=int(self.thresholds.get(key, DEFAULT_THRESHOLDS[key]))
            )
            self.soft_pct_vars[key] = IntVar(
                value=int(self.soft_pcts.get(key, DEFAULT_SOFT_PCT[key]))
            )
        for key in QUALITY_WEIGHT_ORDER:
            self.quality_weight_vars[key] = IntVar(
                value=int(
                    self.quality_weights.get(
                        key, DEFAULT_QUALITY_WEIGHTS.get(key, DEFAULT_QUALITY_SCORE[key])
                    )
                )
            )

        self._busy = False
        self._last_report: str | None = None
        self._thresholds_win: Toplevel | None = None
        self._about_win: Toplevel | None = None
        theme = str(cfg.get("theme", "dark")).lower()
        self.theme_name = theme if theme in THEMES else "dark"

        self._build_style(self.theme_name)
        self._build_ui()
        self._center()

    def _save_theme_name(self, name: str) -> None:
        self.theme_name = name if name in THEMES else "dark"
        try:
            write_app_config(
                self.config_file,
                thresholds=self._current_thresholds(),
                soft_pcts=self._current_soft_pcts(),
                theme=self.theme_name,
                his_metrics=bool(self.his_metrics_var.get()),
                quality_score=self._current_quality_weights(),
            )
        except OSError:
            pass

    def _colors(self) -> dict:
        return THEMES[self.theme_name]

    def _build_style(self, theme_name: str = "dark"):
        self.theme_name = theme_name if theme_name in THEMES else "dark"
        self.root._xlizard_theme = self.theme_name  # type: ignore[attr-defined]
        c = THEMES[self.theme_name]
        self.root.configure(bg=c["bg"])
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 10))
        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["card"])
        style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"], font=("Segoe UI", 9))
        style.configure("Card.Muted.TLabel", background=c["card"], foreground=c["muted"], font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=c["card"], foreground=c["fg"], font=("Segoe UI", 10))
        style.configure("Compact.TLabel", background=c["card"], foreground=c["compact"], font=("Segoe UI", 10))
        style.configure(
            "Title.TLabel",
            background=c["bg"],
            foreground=c["accent"],
            font=("Segoe UI Semibold", 18),
        )
        style.configure("Subtitle.TLabel", background=c["bg"], foreground=c["muted"], font=("Segoe UI", 10))
        style.configure(
            "Tooltip.TLabel",
            background=c["tooltip_bg"],
            foreground=c["fg"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "TEntry",
            fieldbackground=c["field"],
            foreground=c["fg"],
            insertcolor=c["fg"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
        )
        style.configure(
            "TCheckbutton",
            background=c["bg"],
            foreground=c["fg"],
            font=("Segoe UI", 10),
            focuscolor=c["bg"],
        )
        style.map(
            "TCheckbutton",
            background=[("active", c["bg"]), ("pressed", c["bg"]), ("selected", c["bg"])],
            foreground=[("active", c["fg"]), ("pressed", c["fg"]), ("selected", c["fg"])],
        )
        style.configure(
            "Card.TCheckbutton",
            background=c["card"],
            foreground=c["fg"],
            font=("Segoe UI", 10),
            focuscolor=c["card"],
        )
        # clam default: active → white text/bg; keep card colors so label stays readable
        style.map(
            "Card.TCheckbutton",
            background=[("active", c["card"]), ("pressed", c["card"]), ("selected", c["card"])],
            foreground=[("active", c["fg"]), ("pressed", c["fg"]), ("selected", c["fg"])],
        )
        style.configure("TButton", background=c["button"], foreground=c["fg"], padding=(10, 4))
        style.map("TButton", background=[("active", c["button_active"])], foreground=[("active", c["fg"])])
        style.configure(
            "Accent.TButton",
            background=c["accent"],
            foreground="#ffffff",
            padding=(14, 6),
        )
        style.map(
            "Accent.TButton",
            background=[("active", c["accent_active"]), ("disabled", c["accent_disabled"])],
            foreground=[("disabled", "#ffffff")],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=c["field"],
            foreground=c["fg"],
            arrowcolor=c["fg"],
            background=c["field"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            insertcolor=c["fg"],
        )
        style.map("TSpinbox", foreground=[("active", c["fg"]), ("readonly", c["fg"])])
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=c["field"],
            background=c["accent"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            borderwidth=1,
        )
        style.configure(
            "Theme.TButton",
            background=c["button"],
            foreground=c["accent"],
            padding=(6, 2),
            font=("Segoe UI Symbol", 14),
        )
        style.map(
            "Theme.TButton",
            background=[("active", c["button_active"])],
            foreground=[("active", c["accent"])],
        )
        if hasattr(self, "progress_border"):
            self.progress_border.configure(
                highlightbackground=c["border"],
                highlightcolor=c["border"],
                bg=c["field"],
            )
        if hasattr(self, "theme_btn"):
            self.theme_btn.configure(text=THEME_ICONS[self.theme_name])
        if hasattr(self, "_theme_tip"):
            self._theme_tip.text = THEME_ICON_TIPS[self.theme_name]
        style.configure("TNotebook", background=c["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=c["tab"],
            foreground=c["fg"],
            padding=(5, 3),
            font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["tab_selected"]), ("active", c["tab_active"])],
            foreground=[("selected", c["fg"]), ("active", c["fg"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=c["field"],
            background=c["button"],
            foreground=c["fg"],
            arrowcolor=c["fg"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["field"])],
            foreground=[("readonly", c["fg"]), ("active", c["fg"])],
            background=[("active", c["button_active"])],
        )
        if hasattr(self, "log"):
            self.log.configure(
                bg=c["log_bg"],
                fg=c["log_fg"],
                insertbackground=c["fg"],
            )

    def _toggle_theme(self):
        name = "light" if self.theme_name == "dark" else "dark"
        self._build_style(name)
        self._save_theme_name(name)

    def _build_ui(self):
        outer = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True, padx=10, pady=8)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        title_row = ttk.Frame(header)
        title_row.pack(fill="x")
        ttk.Label(title_row, text="xLizard", style="Title.TLabel").pack(side="left")
        self.theme_btn = ttk.Button(
            title_row,
            text=THEME_ICONS[self.theme_name],
            style="Theme.TButton",
            command=self._toggle_theme,
            width=3,
        )
        self.theme_btn.pack(side="right")
        self._theme_tip = _HoverTooltip(self.theme_btn, THEME_ICON_TIPS[self.theme_name])
        ttk.Label(
            header,
            text="Локальный анализ метрик сложности C/C++ — укажите файл или папку",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            header,
            text="Значение выше порога = превышение. Пакет HIS — опционально (окно «Пороги»).",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        card = ttk.Frame(outer, style="Card.TFrame")
        card.pack(fill="x", pady=(8, 4))

        path_controls = ttk.Frame(card, style="Card.TFrame")
        path_controls.pack(fill="x", padx=10, pady=(8, 4))
        ttk.Label(path_controls, text="Цель", style="Card.TLabel", width=8).pack(side="left")
        ttk.Entry(path_controls, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(path_controls, text="Файл…", command=self._pick_file).pack(side="left")
        ttk.Button(path_controls, text="Папка…", command=self._pick_folder).pack(side="left", padx=(4, 0))

        out_controls = ttk.Frame(card, style="Card.TFrame")
        out_controls.pack(fill="x", padx=10, pady=4)
        ttk.Label(out_controls, text="Отчёт", style="Card.TLabel", width=8).pack(side="left")
        ttk.Entry(out_controls, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(out_controls, text="Как…", command=self._pick_output).pack(side="left")

        opts = ttk.Frame(card, style="Card.TFrame")
        opts.pack(fill="x", padx=10, pady=(4, 8))
        ttk.Label(opts, text="Потоки", style="Card.TLabel").pack(side="left")
        ttk.Spinbox(opts, from_=1, to=64, textvariable=self.threads_var, width=5).pack(side="left", padx=(4, 12))
        ttk.Checkbutton(
            opts,
            text="Открыть в браузере",
            variable=self.open_browser_var,
            style="Card.TCheckbutton",
        ).pack(side="left")
        ttk.Button(opts, text="xlizard.json", command=self._open_thresholds_file).pack(side="right")
        ttk.Button(opts, text="Пороги", command=self._show_thresholds_dialog).pack(
            side="right", padx=(0, 6)
        )
        ttk.Button(opts, text="О метриках", command=self._show_thresholds_origin).pack(
            side="right", padx=(0, 6)
        )

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(4, 2))
        self.analyze_btn = ttk.Button(
            actions, text="Анализировать", style="Accent.TButton", command=self._start_analysis
        )
        self.analyze_btn.pack(side="left")
        self.open_btn = ttk.Button(
            actions, text="Последний отчёт", command=self._open_last, state="disabled"
        )
        self.open_btn.pack(side="left", padx=(8, 0))
        c = self._colors()
        self.progress_border = Frame(
            actions,
            highlightthickness=1,
            highlightbackground=c["border"],
            highlightcolor=c["border"],
            bg=c["field"],
            bd=0,
        )
        self.progress_border.pack(side="right")
        self.progress = ttk.Progressbar(
            self.progress_border, mode="indeterminate", length=120
        )
        self.progress.pack(padx=1, pady=1)

        log_hdr = ttk.Frame(outer)
        log_hdr.pack(fill="x", pady=(4, 0))
        ttk.Label(log_hdr, text="Журнал", style="Muted.TLabel").pack(side="left")
        ttk.Button(log_hdr, text="Копировать", command=self._copy_log).pack(side="right")
        self.log = ScrolledText(
            outer,
            height=6,
            bg=c["log_bg"],
            fg=c["log_fg"],
            insertbackground=c["fg"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
            undo=False,
        )
        self.log.pack(fill="both", expand=True, pady=(2, 0))
        # Selectable / copyable; block typing so it stays a journal
        self.log.bind("<Key>", self._log_block_edit)
        self.log.bind("<<Paste>>", lambda _e: "break")
        self.log.bind("<Control-c>", self._copy_log_selection_event)
        self.log.bind("<Control-C>", self._copy_log_selection_event)
        self.log.bind("<Control-a>", self._log_select_all)
        self.log.bind("<Control-A>", self._log_select_all)
        self.log.bind("<Button-3>", self._log_context_menu)
        self._log_menu = Menu(self.root, tearoff=0)
        self._log_menu.add_command(label="Копировать всё", command=self._copy_log)
        self._log_menu.add_command(
            label="Копировать выделенное", command=self._copy_log_selection
        )
        self._log_menu.add_separator()
        self._log_menu.add_command(label="Выделить всё", command=self._log_select_all_cmd)
        self._log_menu.add_command(label="Очистить", command=self._clear_log)
        self._log(
            "Выберите файл/папку и нажмите «Анализировать». "
            f"Расширения: {', '.join(SUPPORTED_EXTS)}\n"
        )

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 3}")

    def _log(self, text: str):
        def append():
            self.log.insert("end", text)
            self.log.see("end")

        if threading.current_thread() is threading.main_thread():
            append()
        else:
            self.root.after(0, append)

    def _log_block_edit(self, event):
        # Allow shortcuts; block ordinary typing
        if event.state & 0x4:  # Control
            return None
        if event.keysym in (
            "Left", "Right", "Up", "Down", "Home", "End",
            "Prior", "Next", "Shift_L", "Shift_R", "Control_L", "Control_R",
        ):
            return None
        return "break"

    def _copy_to_clipboard(self, text: str) -> bool:
        text = text or ""
        if not text.strip():
            return False
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            return True
        except Exception:
            return False

    def _copy_log(self):
        text = self.log.get("1.0", "end-1c")
        if not self._copy_to_clipboard(text):
            messagebox.showinfo(APP_TITLE, "Журнал пуст — нечего копировать.")

    def _copy_log_selection(self):
        try:
            text = self.log.get("sel.first", "sel.last")
        except Exception:
            text = ""
        if not text:
            self._copy_log()
            return
        self._copy_to_clipboard(text)

    def _copy_log_selection_event(self, _event=None):
        self._copy_log_selection()
        return "break"

    def _log_select_all(self, _event=None):
        self._log_select_all_cmd()
        return "break"

    def _log_select_all_cmd(self):
        self.log.tag_add("sel", "1.0", "end-1c")
        self.log.mark_set("insert", "1.0")
        self.log.see("insert")

    def _clear_log(self):
        self.log.delete("1.0", "end")

    def _log_context_menu(self, event):
        try:
            self._log_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._log_menu.grab_release()

    def _install_gui_logging(self, redirect: _StdoutRedirect):
        """Route logging into the journal; drop broken StreamHandlers (stderr=None)."""
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        gui_handler = _GuiLogHandler(self._log)
        gui_handler.setLevel(logging.INFO)

        attached = []
        for name in ("", "xlizard.sourcemonitor"):
            log = logging.getLogger(name)
            # Remove handlers whose stream is None (pythonw) or stale
            for h in list(log.handlers):
                stream = getattr(h, "stream", None)
                if isinstance(h, logging.StreamHandler) and stream is None:
                    log.removeHandler(h)
            log.addHandler(gui_handler)
            log.setLevel(logging.INFO)
            attached.append(log)
        # Also point sourcemonitor stream handlers at redirect if present
        sm = logging.getLogger("xlizard.sourcemonitor")
        for h in sm.handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h, _GuiLogHandler):
                try:
                    h.setStream(redirect)
                except Exception:
                    h.stream = redirect
                h.setFormatter(fmt)
        return gui_handler, attached

    def _uninstall_gui_logging(self, gui_handler, loggers):
        for log in loggers:
            try:
                log.removeHandler(gui_handler)
            except Exception:
                pass

    def _reload_thresholds(self):
        cfg = load_app_config(create_if_missing=True)
        self.thresholds = dict(cfg["thresholds"])
        self.soft_pcts = dict(cfg["soft_pcts"])
        self.his_metrics = bool(cfg.get("his_metrics", DEFAULT_HIS_METRICS))
        self.his_metrics_var.set(self.his_metrics)
        self.quality_weights = dict(cfg.get("quality_score") or DEFAULT_QUALITY_SCORE)
        for key in METRIC_ORDER:
            self.threshold_vars[key].set(
                int(self.thresholds.get(key, DEFAULT_THRESHOLDS[key]))
            )
            self.soft_pct_vars[key].set(
                int(self.soft_pcts.get(key, DEFAULT_SOFT_PCT[key]))
            )
        for key in QUALITY_WEIGHT_ORDER:
            self.quality_weight_vars[key].set(
                int(
                    self.quality_weights.get(
                        key, DEFAULT_QUALITY_WEIGHTS.get(key, DEFAULT_QUALITY_SCORE[key])
                    )
                )
            )
        self._sync_his_spinbox_state()
        self._log("Настройки перечитаны из %s\n" % self.config_file)

    def _current_thresholds(self) -> dict:
        values = dict(DEFAULT_THRESHOLDS)
        for key, var in self.threshold_vars.items():
            try:
                values[key] = int(var.get())
            except (TypeError, ValueError):
                values[key] = int(DEFAULT_THRESHOLDS[key])
        return values

    def _current_soft_pcts(self) -> dict:
        values = dict(DEFAULT_SOFT_PCT)
        for key, var in self.soft_pct_vars.items():
            try:
                values[key] = max(1, min(100, int(var.get())))
            except (TypeError, ValueError):
                values[key] = int(DEFAULT_SOFT_PCT[key])
        return values

    def _current_quality_weights(self) -> dict:
        values = dict(DEFAULT_QUALITY_SCORE)
        for key, var in self.quality_weight_vars.items():
            try:
                values[key] = max(0, int(var.get()))
            except (TypeError, ValueError):
                values[key] = int(DEFAULT_QUALITY_SCORE[key])
        return values

    def _persist_thresholds(self) -> dict:
        thr = self._current_thresholds()
        soft = self._current_soft_pcts()
        his = bool(self.his_metrics_var.get())
        quality = self._current_quality_weights()
        try:
            write_app_config(
                self.config_file,
                thresholds=thr,
                soft_pcts=soft,
                theme=self.theme_name,
                his_metrics=his,
                quality_score=quality,
            )
        except OSError:
            pass
        self.thresholds = thr
        self.soft_pcts = soft
        self.his_metrics = his
        self.quality_weights = quality
        return thr

    def _sync_his_spinbox_state(self):
        state = "normal" if self.his_metrics_var.get() else "disabled"
        for widget in self._his_spinboxes:
            try:
                widget.configure(state=state)
            except Exception:
                pass

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Выберите исходный файл",
            filetypes=[
                ("C/C++", "*.c *.h *.cpp *.hpp *.cc *.cxx *.mm"),
                ("Все файлы", "*.*"),
            ],
        )
        if path:
            self.path_var.set(path)
            self._suggest_output(path)

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Выберите папку проекта")
        if path:
            self.path_var.set(path)
            self._suggest_output(path)

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Куда сохранить HTML-отчёт",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            initialfile=Path(self.output_var.get() or "xlizard_report.html").name,
        )
        if path:
            self.output_var.set(path)

    def _suggest_output(self, target: str):
        if self.output_var.get().strip():
            return
        p = Path(target)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if p.is_file():
            out = p.with_name(f"{p.stem}_xlizard_{stamp}.html")
        else:
            out = p / f"xlizard_report_{stamp}.html"
        self.output_var.set(str(out))

    def _default_output(self, target: str) -> str:
        p = Path(target)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if p.is_file():
            return str(p.with_name(f"{p.stem}_xlizard_{stamp}.html"))
        return str(p / f"xlizard_report_{stamp}.html")

    def _start_analysis(self):
        if self._busy:
            return
        target = self.path_var.get().strip().strip('"')
        if not target:
            messagebox.showwarning(APP_TITLE, "Укажите файл или папку для анализа.")
            return
        if not os.path.exists(target):
            messagebox.showerror(APP_TITLE, "Путь не найден:\n%s" % target)
            return

        output = self.output_var.get().strip().strip('"') or self._default_output(target)
        if not output.lower().endswith(".html"):
            output += ".html"
        self.output_var.set(output)

        out_dir = os.path.dirname(os.path.abspath(output))
        if out_dir and not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError as exc:
                messagebox.showerror(APP_TITLE, "Не удалось создать папку отчёта:\n%s" % exc)
                return

        self._busy = True
        self.analyze_btn.configure(state="disabled")
        self.progress.start(12)
        self._log("\n=== Анализ: %s ===\nОтчёт: %s\n" % (target, output))

        threading.Thread(
            target=self._run_analysis,
            args=(target, output),
            daemon=True,
        ).start()

    def _open_thresholds_file(self):
        path = Path(self.config_file)
        if not path.is_file():
            write_app_config(
                path,
                thresholds=self._current_thresholds(),
                soft_pcts=self._current_soft_pcts(),
                theme=self.theme_name,
                his_metrics=bool(self.his_metrics_var.get()),
                quality_score=self._current_quality_weights(),
            )
        try:
            os.startfile(str(path))
        except OSError:
            messagebox.showinfo(APP_TITLE, "Файл настроек:\n%s" % path)

    def _show_thresholds_dialog(self):
        if self._thresholds_win is not None and self._thresholds_win.winfo_exists():
            self._thresholds_win.lift()
            self._thresholds_win.focus_set()
            return

        c = self._colors()
        win = Toplevel(self.root)
        self._thresholds_win = win
        win.title("Пороги метрик")
        win.configure(bg=c["bg"])
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        outer = ttk.Frame(win)
        outer.pack(fill="both", expand=True, padx=12, pady=10)
        ttk.Label(outer, text="Пороги метрик", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Лимит — превышение при значении выше. Мягкое % — зона незначительного превышения для оценки.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 4))
        ttk.Label(outer, text=str(self.config_file), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        his_row = ttk.Frame(outer)
        his_row.pack(fill="x", pady=(0, 8))
        his_cb = ttk.Checkbutton(
            his_row,
            text="HIS-метрики (GOTO / RETURN / PATH / CALLS / CALLING)",
            variable=self.his_metrics_var,
            command=self._sync_his_spinbox_state,
        )
        his_cb.pack(side="left")
        ttk.Label(
            his_row,
            text="Считать и показывать в HTML только при включении",
            style="Muted.TLabel",
        ).pack(side="left", padx=(10, 0))

        scroll_wrap = ttk.Frame(outer)
        scroll_wrap.pack(fill="both", expand=True)
        from tkinter import Canvas

        canvas_widget = Canvas(scroll_wrap, bg=c["bg"], highlightthickness=0)
        vscroll = ttk.Scrollbar(scroll_wrap, orient="vertical", command=canvas_widget.yview)
        canvas_widget.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas_widget.pack(side="left", fill="both", expand=True)
        card = ttk.Frame(canvas_widget, style="Card.TFrame")
        card_id = canvas_widget.create_window((0, 0), window=card, anchor="nw")

        def _on_card_configure(_event=None):
            canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))

        def _on_canvas_configure(event):
            canvas_widget.itemconfigure(card_id, width=event.width)

        card.bind("<Configure>", _on_card_configure)
        canvas_widget.bind("<Configure>", _on_canvas_configure)

        def _wheel(event):
            delta = -1 if event.delta > 0 else 1
            if getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            canvas_widget.yview_scroll(delta, "units")

        canvas_widget.bind_all("<MouseWheel>", _wheel)
        win.bind("<Destroy>", lambda _e: canvas_widget.unbind_all("<MouseWheel>"), add="+")

        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(header, text="Метрика", style="Card.TLabel", width=36).pack(side="left")
        ttk.Label(header, text="Лимит", style="Card.TLabel", width=8).pack(side="left")
        ttk.Label(header, text="Мягкое, %", style="Card.TLabel", width=10).pack(side="left")

        self._his_spinboxes = []
        for key in METRIC_ORDER:
            row = ttk.Frame(card, style="Card.TFrame")
            row.pack(fill="x", padx=6, pady=1)
            label = ttk.Label(
                row,
                text=METRIC_LABELS[key],
                style="Compact.TLabel",
                width=36,
                cursor="question_arrow",
            )
            label.pack(side="left")
            help_text = METRIC_HELP.get(key, "")
            if help_text:
                tip = (
                    "%s\n\nЛимит по умолчанию: %s. Мягкое %%: насколько выше лимита "
                    "ещё считается незначительным превышением."
                    % (help_text, int(DEFAULT_THRESHOLDS.get(key, 0)))
                )
                _HoverTooltip(label, tip)
            lim = ttk.Spinbox(
                row,
                from_=0,
                to=1000000,
                textvariable=self.threshold_vars[key],
                width=8,
            )
            lim.pack(side="left", padx=(4, 8))
            soft = ttk.Spinbox(
                row,
                from_=1,
                to=100,
                textvariable=self.soft_pct_vars[key],
                width=8,
            )
            soft.pack(side="left")
            if key in HIS_METRIC_SET:
                self._his_spinboxes.extend([lim, soft])

        self._sync_his_spinbox_state()

        q_sep = ttk.Frame(card, style="Card.TFrame")
        q_sep.pack(fill="x", padx=6, pady=(12, 4))
        ttk.Label(q_sep, text="Оценка качества (формула)", style="Card.TLabel").pack(
            anchor="w"
        )
        formula_lbl = ttk.Label(
            q_sep,
            text=format_quality_formula(self._current_quality_weights()),
            style="Muted.TLabel",
            wraplength=640,
        )
        formula_lbl.pack(anchor="w", pady=(2, 6))

        def _refresh_formula(*_args):
            formula_lbl.configure(
                text=format_quality_formula(self._current_quality_weights())
            )

        for key in QUALITY_WEIGHT_ORDER:
            row = ttk.Frame(card, style="Card.TFrame")
            row.pack(fill="x", padx=6, pady=1)
            ttk.Label(
                row,
                text=QUALITY_WEIGHT_LABELS.get(key, key),
                style="Compact.TLabel",
                width=36,
            ).pack(side="left")
            spin = ttk.Spinbox(
                row,
                from_=0,
                to=200,
                textvariable=self.quality_weight_vars[key],
                width=8,
                command=_refresh_formula,
            )
            spin.pack(side="left", padx=(4, 8))
            self.quality_weight_vars[key].trace_add("write", _refresh_formula)

        def save_and_close():
            self._persist_thresholds()
            self._log("Настройки сохранены в %s\n" % self.config_file)
            win.destroy()

        def reload_into_dialog():
            self._reload_thresholds()
            _refresh_formula()

        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Закрыть", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="Сохранить", command=save_and_close).pack(side="right", padx=(0, 6))
        ttk.Button(btns, text="Перечитать", command=reload_into_dialog).pack(side="right", padx=(0, 6))
        ttk.Button(btns, text="Открыть файл", command=self._open_thresholds_file).pack(
            side="left"
        )

        win.minsize(660, 680)
        win.geometry(
            "740x760+%d+%d"
            % (self.root.winfo_rootx() + 40, self.root.winfo_rooty() + 40)
        )
        win.focus_set()

    def _show_thresholds_origin(self):
        if self._about_win is not None and self._about_win.winfo_exists():
            self._about_win.lift()
            self._about_win.focus_set()
            return

        c = self._colors()
        win = Toplevel(self.root)
        self._about_win = win
        win.title("О метриках")
        win.configure(bg=c["bg"])
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        outer = ttk.Frame(win)
        outer.pack(fill="both", expand=True, padx=12, pady=10)
        ttk.Label(outer, text="О метриках", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Общее описание и вкладки по каждой метрике с примером расчёта",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 8))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        for title, text in metrics_about_tabs():
            page = ttk.Frame(notebook)
            notebook.add(page, text=title)
            body = ScrolledText(
                page,
                bg=c["log_bg"],
                fg=c["fg"],
                insertbackground=c["fg"],
                relief="flat",
                font=("Consolas", 10) if title != "Общее" else ("Segoe UI", 10),
                wrap="word",
                padx=8,
                pady=8,
            )
            body.pack(fill="both", expand=True, padx=2, pady=2)
            body.insert("1.0", text.strip() + "\n")
            body.configure(state="disabled")

        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Закрыть", command=win.destroy).pack(side="right")

        # Size matched to approved screenshot with HIS tabs (≈1024×677).
        win.minsize(960, 620)
        win.geometry(
            "1024x677+%d+%d"
            % (self.root.winfo_rootx() + 40, self.root.winfo_rooty() + 40)
        )
        win.focus_set()

    def _run_analysis(self, target: str, output: str):
        from xlizard.thresholds import sync_sourcemonitor_config
        from xlizard.xlizard import main as xlizard_main

        thr = self._persist_thresholds()
        sync_sourcemonitor_config(thr)

        argv = [
            "xlizard",
            "--html",
            "-o", output,
            "-t", str(max(1, int(self.threads_var.get() or 1))),
            "-C", str(int(thr["cyclomatic_complexity"])),
            "-E", "cognitive",
            "--CogC", str(int(thr["cognitive_complexity"])),
            "-E", "nd",
            "-N", str(int(thr["max_nesting_depth"])),
        ]
        for key in (
            "cyclomatic_complexity",
            "cognitive_complexity",
            "max_nesting_depth",
            "nloc",
            "token_count",
            "parameter_count",
            "length",
        ):
            argv.extend(["-T", "%s=%s" % (key, int(thr[key]))])
        argv.append(target)

        old_out, old_err = sys.stdout, sys.stderr
        redirect = _StdoutRedirect(self._log)
        # Frozen GUI (pythonw): stdout/stderr may be None — give logging a sink
        if old_out is None:
            old_out = redirect
        if old_err is None:
            old_err = redirect
        sys.stdout = redirect
        sys.stderr = redirect
        gui_handler, loggers = self._install_gui_logging(redirect)
        exit_code = 0
        error = None
        try:
            try:
                xlizard_main(argv)
            except SystemExit as exc:
                exit_code = int(exc.code or 0) if isinstance(exc.code, int) else 1
            except Exception:
                error = traceback.format_exc()
                exit_code = 2
        finally:
            self._uninstall_gui_logging(gui_handler, loggers)
            sys.stdout = old_out if old_out is not redirect else sys.__stdout__
            sys.stderr = old_err if old_err is not redirect else sys.__stderr__

        self.root.after(0, lambda: self._finish(output, exit_code, error))

    def _finish(self, output: str, exit_code: int, error: str | None):
        self.progress.stop()
        self.analyze_btn.configure(state="normal")
        self._busy = False

        if error:
            self._log("\nОшибка:\n%s\n" % error)
            messagebox.showerror(APP_TITLE, "Анализ завершился с ошибкой. См. журнал.")
            return

        if os.path.isfile(output):
            self._last_report = output
            self.open_btn.configure(state="normal")
            self._log("\nГотово (код выхода: %s). Отчёт: %s\n" % (exit_code, output))
            if self.open_browser_var.get():
                webbrowser.open(Path(output).resolve().as_uri())
        else:
            self._log(
                "\nАнализ завершён (код: %s), но файл отчёта не найден: %s\n"
                % (exit_code, output)
            )
            messagebox.showwarning(
                APP_TITLE,
                "Анализ завершён, но HTML-файл не найден. Проверьте журнал.",
            )

    def _open_last(self):
        if self._last_report and os.path.isfile(self._last_report):
            webbrowser.open(Path(self._last_report).resolve().as_uri())
        else:
            messagebox.showinfo(APP_TITLE, "Пока нет сохранённого отчёта.")


def main():
    root = Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    XLizardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
