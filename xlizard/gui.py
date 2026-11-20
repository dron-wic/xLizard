# -*- coding: utf-8 -*-
"""
Desktop UI for xLizard: выбор файла/папки и HTML-отчёт.
Все метрики анализируются всегда; пороги — из thresholds.txt / панели.
"""
from __future__ import annotations

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
    StringVar,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
    ttk,
)
from tkinter.scrolledtext import ScrolledText

from xlizard.thresholds import (
    DEFAULT_THRESHOLDS,
    METRIC_HELP,
    METRIC_LABELS,
    METRIC_ORDER,
    metrics_about_tabs,
    load_thresholds,
    thresholds_path,
    write_thresholds_file,
)


APP_TITLE = "xLizard"
SUPPORTED_EXTS = (".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".mm")
THEME_FILENAME = "ui_theme.txt"

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
    def __init__(self, write_fn):
        self._write_fn = write_fn

    def write(self, text):
        if text:
            self._write_fn(text)

    def flush(self):
        pass


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
        self.thresholds_file = thresholds_path()
        self.thresholds = load_thresholds(create_if_missing=True)
        self.threshold_vars: dict[str, IntVar] = {}
        for key in METRIC_ORDER:
            self.threshold_vars[key] = IntVar(
                value=int(self.thresholds.get(key, DEFAULT_THRESHOLDS[key]))
            )

        self._busy = False
        self._last_report: str | None = None
        self.theme_name = self._load_theme_name()

        self._build_style(self.theme_name)
        self._build_ui()
        self._center()

    def _theme_path(self) -> Path:
        from xlizard.thresholds import application_dir

        return application_dir() / THEME_FILENAME

    def _load_theme_name(self) -> str:
        path = self._theme_path()
        try:
            raw = path.read_text(encoding="utf-8").strip().lower()
            if raw in THEMES:
                return raw
            if raw in ("тёмная", "темная"):
                return "dark"
            if raw in ("светлая",):
                return "light"
        except OSError:
            pass
        return "dark"

    def _save_theme_name(self, name: str) -> None:
        try:
            self._theme_path().write_text(name + "\n", encoding="utf-8")
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
            text="Все метрики считаются всегда. Значение выше порога = превышение.",
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
        ttk.Button(opts, text="thresholds.txt", command=self._open_thresholds_file).pack(side="right")
        ttk.Button(opts, text="Обновить пороги", command=self._reload_thresholds).pack(side="right", padx=(0, 6))
        ttk.Button(opts, text="О метриках", command=self._show_thresholds_origin).pack(
            side="right", padx=(0, 6)
        )

        thr_card = ttk.Frame(outer, style="Card.TFrame")
        thr_card.pack(fill="x", pady=4)
        thr_head = ttk.Frame(thr_card, style="Card.TFrame")
        thr_head.pack(fill="x", padx=10, pady=(6, 2))
        ttk.Label(thr_head, text="Пороги метрик", style="Card.TLabel").pack(side="left")
        ttk.Label(
            thr_head,
            text="наведите на название — подсказка",
            style="Card.Muted.TLabel",
        ).pack(side="left", padx=(8, 0))
        ttk.Label(thr_head, text=str(self.thresholds_file), style="Card.Muted.TLabel").pack(
            side="left", padx=(8, 0)
        )

        grid = ttk.Frame(thr_card, style="Card.TFrame")
        grid.pack(fill="x", padx=8, pady=(2, 8))
        cols = 3
        for i, key in enumerate(METRIC_ORDER):
            row, col = divmod(i, cols)
            cell = ttk.Frame(grid, style="Card.TFrame")
            cell.grid(row=row, column=col, sticky="ew", padx=4, pady=1)
            label = ttk.Label(cell, text=METRIC_LABELS[key], style="Compact.TLabel", cursor="question_arrow")
            label.pack(side="left", fill="x", expand=True)
            help_text = METRIC_HELP.get(key, "")
            if help_text:
                default = int(DEFAULT_THRESHOLDS.get(key, 0))
                tip = "%s\n\nБазовый порог: %s (значение выше = превышение)." % (help_text, default)
                _HoverTooltip(label, tip)
            ttk.Spinbox(
                cell,
                from_=0,
                to=1000000,
                textvariable=self.threshold_vars[key],
                width=7,
            ).pack(side="right")
        for c in range(cols):
            grid.columnconfigure(c, weight=1)

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

        ttk.Label(outer, text="Журнал", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
        self.log = ScrolledText(
            outer,
            height=6,
            bg=c["log_bg"],
            fg=c["log_fg"],
            insertbackground=c["fg"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
        )
        self.log.pack(fill="both", expand=True, pady=(2, 0))
        self.log.configure(state="disabled")
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
            self.log.configure(state="normal")
            self.log.insert("end", text)
            self.log.see("end")
            self.log.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            append()
        else:
            self.root.after(0, append)

    def _reload_thresholds(self):
        self.thresholds = load_thresholds(create_if_missing=True)
        for key, var in self.threshold_vars.items():
            var.set(int(self.thresholds.get(key, DEFAULT_THRESHOLDS[key])))
        self._log("Пороги перечитаны из %s\n" % self.thresholds_file)

    def _current_thresholds(self) -> dict:
        values = dict(DEFAULT_THRESHOLDS)
        for key, var in self.threshold_vars.items():
            try:
                values[key] = int(var.get())
            except (TypeError, ValueError):
                values[key] = int(DEFAULT_THRESHOLDS[key])
        return values

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
        path = Path(self.thresholds_file)
        if not path.is_file():
            write_thresholds_file(path, self._current_thresholds())
        try:
            os.startfile(str(path))
        except OSError:
            messagebox.showinfo(APP_TITLE, "Файл порогов:\n%s" % path)

    def _show_thresholds_origin(self):
        c = self._colors()
        win = Toplevel(self.root)
        win.title("О метриках")
        win.configure(bg=c["bg"])
        win.transient(self.root)

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

        # Size matched to the approved screenshot (tabs fit, «Закрыть» visible).
        win.minsize(720, 600)
        win.geometry(
            "753x652+%d+%d"
            % (self.root.winfo_rootx() + 40, self.root.winfo_rooty() + 40)
        )
        win.focus_set()
        win.grab_set()

    def _run_analysis(self, target: str, output: str):
        from xlizard.thresholds import sync_sourcemonitor_config
        from xlizard.xlizard import main as xlizard_main

        thr = self._current_thresholds()
        # Persist current UI values so thresholds.txt stays in sync
        try:
            write_thresholds_file(self.thresholds_file, thr)
        except OSError:
            pass
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
        sys.stdout = redirect
        sys.stderr = redirect
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
            sys.stdout = old_out
            sys.stderr = old_err

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
