# -*- coding: utf-8 -*-
"""
Project-level quality score from metric thresholds and soft exceedance bands.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from xlizard.thresholds import (
    DEFAULT_SOFT_PCT,
    DEFAULT_THRESHOLDS,
    DISABLE_GATE_WHEN_LIMIT_ZERO,
    HIS_METRIC_KEYS,
    METRIC_LABELS,
)

# Metrics scored on each active function
FUNCTION_METRICS: Tuple[str, ...] = (
    "cyclomatic_complexity",
    "cognitive_complexity",
    "max_nesting_depth",
    "nloc",
    "token_count",
    "parameter_count",
    "length",
)

HIS_FUNCTION_METRICS: Tuple[str, ...] = tuple(HIS_METRIC_KEYS)

# Metrics scored once per file
FILE_METRICS: Tuple[str, ...] = (
    "max_block_depth",
    "pointer_operations",
    "preprocessor_directives",
    "logical_operators",
    "conditional_statements",
    "function_count",
)

# Weights for the 0–100 score (editable via xlizard.json / «Пороги»)
DEFAULT_QUALITY_WEIGHTS: Dict[str, float] = {
    "soft_func_weight": 15.0,  # −W × (доля функций только с мягким превышением)
    "hard_func_weight": 45.0,  # −W × (доля функций с жёстким превышением)
    "file_soft_penalty": 2.0,  # −P за каждое мягкое файловое превышение
    "file_hard_penalty": 6.0,  # −P за каждое жёсткое файловое превышение
    "file_penalty_cap": 20.0,  # потолок суммарного файлового штрафа
}

QUALITY_WEIGHT_LABELS: Dict[str, str] = {
    "soft_func_weight": "Вес мягких функций",
    "hard_func_weight": "Вес жёстких функций",
    "file_soft_penalty": "Штраф за мягкое (файл)",
    "file_hard_penalty": "Штраф за жёсткое (файл)",
    "file_penalty_cap": "Потолок файлового штрафа",
}

QUALITY_WEIGHT_ORDER: Tuple[str, ...] = (
    "soft_func_weight",
    "hard_func_weight",
    "file_soft_penalty",
    "file_hard_penalty",
    "file_penalty_cap",
)

# Map quality keys → fields on function / file dicts
_FUNC_FIELD = {
    "cyclomatic_complexity": "cyclomatic_complexity",
    "cognitive_complexity": "cognitive_complexity",
    "max_nesting_depth": "max_nesting_depth",
    "nloc": "nloc",
    "token_count": "token_count",
    "parameter_count": "parameter_count",
    "length": "length",
    "goto_count": "goto_count",
    "return_count": "return_count",
    "path_count": "path_count",
    "calls": "calls",
    "calling": "calling",
}

_FILE_FIELD = {
    "max_block_depth": "max_block_depth",
    "pointer_operations": "pointer_operations",
    "preprocessor_directives": "preprocessor_directives",
    "logical_operators": "logical_operators",
    "conditional_statements": "conditional_statements",
    "function_count": "active_functions_count",
}


def _as_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_quality_weights(raw: Optional[Mapping[str, Any]] = None) -> Dict[str, float]:
    """Clamp and fill quality-score weights from JSON / GUI."""
    out = dict(DEFAULT_QUALITY_WEIGHTS)
    if not isinstance(raw, Mapping):
        return out
    for key in QUALITY_WEIGHT_ORDER:
        if key not in raw:
            continue
        num = _as_number(raw[key])
        if num is None:
            continue
        if key == "file_penalty_cap":
            out[key] = max(0.0, min(100.0, num))
        else:
            out[key] = max(0.0, min(200.0, num))
    return out


def format_quality_formula(weights: Optional[Mapping[str, float]] = None) -> str:
    """Human-readable formula with current weights (for HTML / docs)."""
    w = normalize_quality_weights(weights)
    return (
        "Балл = 100 − {soft}×(доля мягких функций) − {hard}×(доля жёстких функций) "
        "− min({cap}, {fs}×Nмягк.файл + {fh}×Nжёстк.файл)"
    ).format(
        soft=_fmt_num(w["soft_func_weight"]),
        hard=_fmt_num(w["hard_func_weight"]),
        cap=_fmt_num(w["file_penalty_cap"]),
        fs=_fmt_num(w["file_soft_penalty"]),
        fh=_fmt_num(w["file_hard_penalty"]),
    )


def _fmt_num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return ("%g" % value)


def _function_length(func: Mapping[str, Any]) -> float:
    length = _as_number(func.get("length"))
    if length is not None and length > 0:
        return length
    start = _as_number(func.get("start_line")) or 0
    end = _as_number(func.get("end_line")) or 0
    if end >= start and end > 0:
        return end - start + 1
    return _as_number(func.get("nloc")) or 0


def _classify_excess(
    value: float,
    limit: float,
    soft_pct: float,
    metric: Optional[str] = None,
) -> Optional[str]:
    """Return 'soft', 'hard', or None if within limit / disabled."""
    if metric in DISABLE_GATE_WHEN_LIMIT_ZERO and limit <= 0:
        return None
    if limit < 0:
        return None
    if value <= limit:
        return None
    # limit == 0 (e.g. GOTO): any value above is a hard exceedance
    if limit == 0:
        return "hard"
    excess = (value - limit) / limit
    band = max(1.0, min(100.0, soft_pct)) / 100.0
    if excess <= band:
        return "soft"
    return "hard"


def compute_quality_score(
    file_list: Sequence[Mapping[str, Any]],
    thresholds: Optional[Mapping[str, float]] = None,
    soft_pcts: Optional[Mapping[str, float]] = None,
    *,
    his_enabled: bool = False,
    weights: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute 0–100 quality score for an analyzed project.

    Returns dict with score, status, badge flag, counts, top exceedances,
    and the formula/weights used.
    """
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        limits.update(thresholds)
    soft = dict(DEFAULT_SOFT_PCT)
    if soft_pcts:
        soft.update(soft_pcts)
    w = normalize_quality_weights(weights)

    func_metrics = list(FUNCTION_METRICS)
    if his_enabled:
        func_metrics.extend(HIS_FUNCTION_METRICS)

    soft_by_metric: MutableMapping[str, int] = defaultdict(int)
    hard_by_metric: MutableMapping[str, int] = defaultdict(int)

    total_functions = 0
    soft_func_hits = 0
    hard_func_hits = 0
    file_soft = 0
    file_hard = 0

    for source_file in file_list:
        functions = source_file.get("functions") or []
        active = [f for f in functions if not f.get("in_disable_block", False)]

        for func in active:
            total_functions += 1
            func_soft = False
            func_hard = False
            for metric in func_metrics:
                field = _FUNC_FIELD[metric]
                if metric == "length":
                    value = _function_length(func)
                else:
                    value = _as_number(func.get(field))
                if value is None:
                    continue
                kind = _classify_excess(
                    value,
                    float(limits.get(metric, 0)),
                    float(soft.get(metric, DEFAULT_SOFT_PCT.get(metric, 25))),
                    metric=metric,
                )
                if kind == "soft":
                    soft_by_metric[metric] += 1
                    func_soft = True
                elif kind == "hard":
                    hard_by_metric[metric] += 1
                    func_hard = True
            if func_hard:
                hard_func_hits += 1
            elif func_soft:
                soft_func_hits += 1

        for metric in FILE_METRICS:
            field = _FILE_FIELD[metric]
            if metric == "function_count":
                value = _as_number(source_file.get(field))
                if value is None:
                    value = float(len(active))
            else:
                value = _as_number(source_file.get(field))
            if value is None:
                continue
            kind = _classify_excess(
                value,
                float(limits.get(metric, 0)),
                float(soft.get(metric, DEFAULT_SOFT_PCT.get(metric, 25))),
                metric=metric,
            )
            if kind == "soft":
                soft_by_metric[metric] += 1
                file_soft += 1
            elif kind == "hard":
                hard_by_metric[metric] += 1
                file_hard += 1

    soft_func_rate = (soft_func_hits / total_functions) if total_functions else 0.0
    hard_func_rate = (hard_func_hits / total_functions) if total_functions else 0.0
    file_penalty_raw = (
        w["file_soft_penalty"] * file_soft + w["file_hard_penalty"] * file_hard
    )
    file_penalty = min(w["file_penalty_cap"], file_penalty_raw)
    score = (
        100.0
        - (w["soft_func_weight"] * soft_func_rate + w["hard_func_weight"] * hard_func_rate)
        - file_penalty
    )
    score = int(round(max(0.0, min(100.0, score))))

    exceedance_count = sum(soft_by_metric.values()) + sum(hard_by_metric.values())
    has_exceedances = exceedance_count > 0

    if score >= 95 and not has_exceedances:
        status = "Норма"
        status_class = "safe"
    elif score >= 80 and (sum(hard_by_metric.values()) == 0 or hard_func_rate <= 0.02):
        status = "Допустимо"
        status_class = "warning"
    elif score >= 55:
        status = "Внимание"
        status_class = "warning"
    else:
        status = "Критично"
        status_class = "danger"

    ranked: List[Tuple[str, int, int]] = []
    for metric in list(func_metrics) + list(FILE_METRICS):
        s = soft_by_metric.get(metric, 0)
        h = hard_by_metric.get(metric, 0)
        if s or h:
            ranked.append((metric, s, h))
    ranked.sort(key=lambda row: (row[1] + row[2], row[2]), reverse=True)

    top_exceedances = [
        {
            "key": metric,
            "label": METRIC_LABELS.get(metric, metric),
            "soft": soft_n,
            "hard": hard_n,
            "limit": limits.get(metric),
            "soft_pct": soft.get(metric),
        }
        for metric, soft_n, hard_n in ranked[:6]
    ]

    formula_text = format_quality_formula(w)

    return {
        "score": score,
        "status": status,
        "status_class": status_class,
        "has_exceedances": has_exceedances,
        "exceedance_count": exceedance_count,
        "soft_count": sum(soft_by_metric.values()),
        "hard_count": sum(hard_by_metric.values()),
        "total_functions": total_functions,
        "soft_func_rate": soft_func_rate,
        "hard_func_rate": hard_func_rate,
        "file_soft": file_soft,
        "file_hard": file_hard,
        "file_penalty": file_penalty,
        "top_exceedances": top_exceedances,
        "soft_by_metric": dict(soft_by_metric),
        "hard_by_metric": dict(hard_by_metric),
        "weights": w,
        "formula": formula_text,
        "formula_detail": (
            "Мягкое превышение — value выше limit, но не больше soft_pct%% от limit; "
            "жёсткое — сильнее (при limit=0 любое value>0 жёсткое). "
            "Доли — от числа активных функций. Настройка весов: xlizard.json → "
            "quality_score или окно «Пороги»."
        ),
    }
