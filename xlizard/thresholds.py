# -*- coding: utf-8 -*-
"""
Load metric thresholds from a plain-text file next to the executable (or CWD).

Values greater than the threshold are treated as exceeded.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Optional

THRESHOLDS_FILENAME = "thresholds.txt"

# Canonical metric keys used in options.thresholds / HTML
# Baselines tuned for quality C (NIST/HIS/Sonar + p90–p95 of musl/cJSON/redis).
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "cyclomatic_complexity": 15,  # NIST soft / lizard; HIS uses 10
    "cognitive_complexity": 25,  # SonarSource default for C/C++
    "max_nesting_depth": 5,  # HIS LEVEL ≤4; empiric p95 ≈4
    "nloc": 80,  # empiric p95 ≈64 on reference C
    "token_count": 500,  # ≈ empiric p95
    "parameter_count": 5,  # HIS PARAM max
    "length": 150,  # empiric ~p97; old 1000 barely ever fired
    "comment_percentage": 0,  # 0 disables “too few comments” gate
    "max_block_depth": 5,  # file brace depth; empiric p95 ≈5
    "pointer_operations": 100,  # file-level soft gate
    "preprocessor_directives": 40,  # empiric p95
    "logical_operators": 50,  # file totals; old 10 flagged almost all modules
    "conditional_statements": 50,  # file totals; old 8 was unrealistically tight
    "function_count": 40,  # soft modularity gate (musl tiny, redis larger)
}

# Russian label + English short name (for UI)
METRIC_LABELS: Dict[str, str] = {
    "cyclomatic_complexity": "Цикломатическая сложность (CCN)",
    "cognitive_complexity": "Когнитивная сложность (CogC)",
    "max_nesting_depth": "Глубина вложенности (ND)",
    "nloc": "Строки кода (NLOC)",
    "token_count": "Число токенов (Tokens)",
    "parameter_count": "Число параметров (PARAM)",
    "length": "Длина функции (Length)",
    "comment_percentage": "Доля комментариев (Comments %)",
    "max_block_depth": "Глубина блоков (Depth)",
    "pointer_operations": "Операции с указателями (Ptr Ops)",
    "preprocessor_directives": "Директивы препроцессора (PP)",
    "logical_operators": "Логические операторы (Logic)",
    "conditional_statements": "Условные операторы (Cond)",
    "function_count": "Функций в файле (Funcs)",
}

# Hover help: scope + what the metric affects (embedded-oriented)
METRIC_HELP: Dict[str, str] = {
    "cyclomatic_complexity": (
        "Уровень: функция.\n"
        "Число независимых путей выполнения (McCabe).\n"
        "Влияет на: объём unit-тестов ISR/драйверов, риск дефектов "
        "в ветвлениях, сложность ревью и сертификации (MISRA/HIS)."
    ),
    "cognitive_complexity": (
        "Уровень: функция.\n"
        "Нагрузка на понимание потока управления (SonarSource CogC).\n"
        "Влияет на: читаемость обработчиков и state-machine, "
        "вероятность ошибок при правках вложенных условий и циклов."
    ),
    "max_nesting_depth": (
        "Уровень: функция.\n"
        "Максимальная глубина вложенных if / for / while / switch.\n"
        "Влияет на: «пирамиду» в драйверах, ясность логики, "
        "удобство отладки на MCU и выноса хелперов."
    ),
    "nloc": (
        "Уровень: функция.\n"
        "Строки с кодом: без пустых и чисто комментарных строк.\n"
        "Влияет на: обзорность обработчика/функции драйвера и "
        "склонность смешивать несколько обязанностей в одной ISR."
    ),
    "token_count": (
        "Уровень: функция.\n"
        "Число лексических токенов в теле функции.\n"
        "Влияет на: плотность выражений (битовые маски, регистры, "
        "макросы) и сложность чтения даже при умеренном NLOC."
    ),
    "parameter_count": (
        "Уровень: функция.\n"
        "Число параметров в сигнатуре.\n"
        "Влияет на: сложность API драйвера, риск перепутать "
        "аргументы и желание передать контекст структурой."
    ),
    "length": (
        "Уровень: функция.\n"
        "Число строк исходника от начала до конца функции "
        "(включая пустые строки и комментарии внутри).\n"
        "Влияет на: навигацию по модулю, размер диффов и риск "
        "«божественной» функции в .c-файле периферии."
    ),
    "comment_percentage": (
        "Уровень: файл.\n"
        "Доля комментариев в файле (%).\n"
        "Влияет на: документированность модуля; порог 0 отключает "
        "проверку (правило «выше порога = превышение»)."
    ),
    "max_block_depth": (
        "Уровень: файл.\n"
        "Максимальная глубина вложенности блоков { } по файлу.\n"
        "Влияет на: структурную вложенность модуля драйвера, "
        "читаемость и нужду в ранних return / выносе функций."
    ),
    "pointer_operations": (
        "Уровень: файл.\n"
        "Число операций с указателями (* , -> , & и т.п.) по файлу.\n"
        "Влияет на: риск ошибок памяти/алиасинга в register-map "
        "коде, сложность ревью низкоуровневого C."
    ),
    "preprocessor_directives": (
        "Уровень: файл.\n"
        "Число директив препроцессора (#if, #define, #ifdef…).\n"
        "Влияет на: вариативность сборки под платы/MCU, скрытые "
        "ветки компиляции и покрытие конфигураций тестами."
    ),
    "logical_operators": (
        "Уровень: файл.\n"
        "Число логических операторов (&& || !) по файлу.\n"
        "Влияет на: плотность условий статуса/флагов и риск "
        "пропустить крайний случай в проверках железа."
    ),
    "conditional_statements": (
        "Уровень: файл.\n"
        "Сколько раз встречаются if / else / for / while / "
        "switch / case / do (сумма по файлу, не глубина).\n"
        "Влияет на: ветвистость модуля, объём тестов и стоимость "
        "изменения поведения драйвера."
    ),
    "function_count": (
        "Уровень: файл.\n"
        "Число функций в одном .c/.h файле.\n"
        "Влияет на: модульность единицы компиляции, размер ревью "
        "и ясность ответственности файла (один периферийный модуль)."
    ),
}

# Short titles for the «О метриках» notebook tabs
METRIC_TAB_TITLES: Dict[str, str] = {
    "cyclomatic_complexity": "CCN",
    "cognitive_complexity": "CogC",
    "max_nesting_depth": "ND",
    "nloc": "NLOC",
    "token_count": "Tokens",
    "parameter_count": "PARAM",
    "length": "Length",
    "max_block_depth": "Depth",
    "pointer_operations": "Ptr",
    "preprocessor_directives": "PP",
    "logical_operators": "Logic",
    "conditional_statements": "Cond",
    "comment_percentage": "Comm%",
    "function_count": "Funcs",
}

# First tab of «О метриках»: overview (nothing dropped from the old dialog)
METRICS_ABOUT_GENERAL = """xLizard для embedded (MCU)

Программа считает метрики сложности C/C++ для прошивок и
драйверов. Значение метрики ВЫШЕ порога считается превышением.
Пороги правятся в панели UI и в thresholds.txt рядом с программой.

На следующих вкладках — подробный разбор каждой метрики
с примером расчёта. Ниже — общая карта и источники порогов.

────────────────────────────────
Метрики уровня ФУНКЦИЯ
────────────────────────────────
• CCN — число независимых путей (McCabe): +1 за ветвления и циклы.
• CogC — «нагрузка на чтение» потока управления (SonarSource);
  вложенность условий усиливает штраф.
• ND — максимальная глубина вложенных if / for / while / switch
  внутри одной функции.
• NLOC — строки с кодом внутри функции (пустые и чисто
  комментарные строки не считаются).
• Length — строки исходника от первой до последней строки
  функции, включая пустые и комментарии внутри.
• Tokens — число лексических токенов в теле функции.
• PARAM — число параметров в объявлении функции.

────────────────────────────────
Метрики уровня ФАЙЛ
────────────────────────────────
• Depth — максимальная глубина вложенности блоков { } по файлу.
• Cond — сколько раз встречаются if / else / for / while / do /
  switch / case (счётчик вхождений, не глубина).
• Logic — число логических операторов &&, || и ! по файлу.
• Ptr Ops — число операций с указателями (*, ->, & …) по файлу.
• PP — число директив препроцессора (#if, #define, #ifdef…).
• Funcs — сколько функций в файле.
• Comments % — доля комментариев от строк файла (%).
  Порог 0 отключает эту проверку.

────────────────────────────────
Откуда взяты базовые границы
────────────────────────────────
Пороги — мягкий quality gate. Источники:
• NIST SP 500-235 / McCabe — ориентир CCN ≈ 10; на практике
  для C часто допускают до 15 (как в lizard).
• HIS Source Code Metrics (автопром / близко к embedded) —
  CCN ≤ 10, вложенность LEVEL ≤ 4, PARAM ≤ 5, STMT ≤ 50.
• SonarSource Cognitive Complexity — для C/C++/ObjC дефолт 25
  (для других языков обычно 15).
• Lizard — исторически CCN=15; length у нас ужесточён относительно
  старого дефолта 1000.
• Эмпирика xLizard по musl, cJSON, redis/src (~7 тыс. функций):
  ориентиры около p90–p95 «здорового» кода.

Текущие defaults
• CCN = 15, CogC = 25, ND = 5, NLOC = 80, Tokens = 500,
  PARAM = 5, Length = 150, Depth = 5, Ptr Ops = 100, PP = 40,
  Logic = 50, Cond = 50, Funcs = 40, Comments % = 0.

Для жёсткого MCU / MISRA / HIS профиля часто снижают:
CCN=10, ND=4, PARAM=5, NLOC≈50.
"""

# Per-metric tabs: definition + how counted + worked example + threshold note
METRICS_ABOUT_DETAIL: Dict[str, str] = {
    "cyclomatic_complexity": """Цикломатическая сложность (CCN)
Уровень: функция

Как считается
База = 1 (линейный путь). +1 за каждое решение, которое
создаёт новый путь: if, else if, for, while, do, case,
catch, тернарный ?:, а также && и || в условиях.
(Модель McCabe / lizard.)

Пример
  int status_ok(uint32_t flags)
  {
      if (flags & ERR)          /* +1 */
          return 0;
      for (int i = 0; i < 3; i++) /* +1 */
          if (ready[i])         /* +1 */
              return 1;
      return (flags & OK) && !busy; /* +1 за && */
  }
Старт 1 + if + for + if + && → CCN = 5.

Базовый порог: 15 (NIST soft / lizard; HIS часто 10).
Влияет на: объём unit-тестов ISR/драйверов, риск дефектов
в ветвлениях, сложность ревью и сертификации (MISRA/HIS).
""",
    "cognitive_complexity": """Когнитивная сложность (CogC)
Уровень: функция

Как считается
По правилам SonarSource: плоский if/цикл даёт +1, а каждое
вложение добавляет ещё «штраф уровня» (глубже = дороже читать).
else / else if тоже учитываются. Цель — оценить нагрузку на
понимание, а не только число путей (как CCN).

Пример
  void poll(void)
  {
      if (ready) {                 /* +1 */
          while (busy) {           /* +1, вложение +1 → всего +2 */
              if (timeout)         /* +1, вложение +2 → всего +3 */
                  break;
          }
      }
  }
Примерно: 1 + 2 + 3 = CogC 6 (упрощённо; точные правила Sonar
чуть детальнее для switch/catch).

Базовый порог: 25 (дефолт Sonar для C/C++/ObjC).
Влияет на: читаемость обработчиков и state-machine, вероятность
ошибок при правках вложенных условий и циклов.
""",
    "max_nesting_depth": """Глубина вложенности (ND)
Уровень: функция

Как считается
Сколько уровней управляющих конструкций (if / for / while /
switch / do / …) вложены друг в друга. Берётся максимум по
функции — «самый глубокий колодец», а не сумма всех if.

Пример
  void isr(void)
  {
      if (pending) {           /* уровень 1 */
          for (;;) {           /* уровень 2 */
              if (done) {      /* уровень 3 */
                  clear();
              }
          }
      }
      if (error)               /* снова уровень 1 — максимум не растёт */
          halt();
  }
ND = 3.

Базовый порог: 5 (HIS LEVEL ≤ 4; у эталонов p95 ≈ 4).
Влияет на: «пирамиду» в драйверах, ясность логики, удобство
отладки на MCU и выноса хелперов.
""",
    "nloc": """Строки кода (NLOC)
Уровень: функция

Как считается
Число строк внутри функции, на которых есть код. Не считаются:
• полностью пустые строки;
• строки, где есть только комментарий.
Учитываются строки с операторами, объявлениями, return и т.п.

Пример
  int foo(void) {          /* строка с кодом */
      // только комментарий  — не в NLOC
                           /* пустая — не в NLOC */
      int x = 1;           /* код */
      return x;            /* код */
  }
NLOC ≈ 3 (открывающая с '{'/сигнатурой в учёте lizard,
  плюс int x и return — ориентир «три живые строки кода»).

Базовый порог: 80 (около p95 эталонного C).
Влияет на: обзорность обработчика/функции драйвера и склонность
смешивать несколько обязанностей в одной ISR.
""",
    "token_count": """Число токенов (Tokens)
Уровень: функция

Как считается
Лексер режет тело функции на токены: имена, числа, операторы,
скобки, ключевые слова. Каждый такой кусок = +1. Длинные
выражения с масками регистров дают много токенов даже при
небольшом NLOC.

Пример
  uint32_t v = (REG->SR & MASK) >> 2;
Токены примерно:
  uint32_t | v | = | ( | REG | -> | SR | & | MASK | ) | >> | 2 | ;
→ около 13 токенов в одной строке.

Базовый порог: 500 (≈ p95 эталонов).
Влияет на: плотность выражений (битовые маски, регистры, макросы)
и сложность чтения даже при умеренном NLOC.
""",
    "parameter_count": """Число параметров (PARAM)
Уровень: функция

Как считается
Сколько аргументов в списке параметров определения функции.
Пустой список (void) → 0. Тип и имя каждого параметра = один
параметр. Variadic (…) обычно учитывается как отдельный элемент
сигнатуры в зависимости от парсера.

Пример
  void uart_write(UART_TypeDef *uart, const uint8_t *buf, size_t n)
PARAM = 3.

  int ticks(void)
PARAM = 0.

Базовый порог: 5 (верхняя граница HIS PARAM).
Влияет на: сложность API драйвера, риск перепутать аргументы
и желание передать контекст структурой.
""",
    "length": """Длина функции (Length)
Уровень: функция

Как считается
Число строк исходника от первой строки функции до последней
включительно: end_line − start_line + 1. Сюда входят пустые
строки и комментарии внутри функции.

Пример
  10| int foo(void) {     ← start
  11|     // comment
  12|
  13|     int x = 1;
  14|     return x;
  15| }                 ← end
Length = 15 − 10 + 1 = 6.

Базовый порог: 150 (≈ p97 эталонов; старый lizard-дефолт 1000
почти не срабатывал).
Влияет на: навигацию по модулю, размер диффов и риск
«божественной» функции в .c-файле периферии.
""",
    "max_block_depth": """Глубина блоков (Depth)
Уровень: файл

Как считается
По всему файлу отслеживается текущая глубина фигурных скобок
{ … }. Метрика = максимальный уровень вложенности { },
достигнутый в файле (структурная «яма» модуля).

Пример
  void a(void) {           /* depth 1 */
      if (x) {             /* depth 2 */
          {                /* depth 3 — лишний блок */
              use();
          }
      }
  }
Depth файла = 3.

Базовый порог: 5 (p95 на эталонных файлах).
Влияет на: структурную вложенность модуля драйвера, читаемость
и нужду в ранних return / выносе функций.
""",
    "pointer_operations": """Операции с указателями (Ptr Ops)
Уровень: файл

Как считается
Сумма по файлу типичных указательных конструкций после очистки
от строк/комментариев, например:
• объявления вида type *name;
• доступ -> ;
• взятие адреса &var;
• разыменование *ptr.
(Эвристика SourceMonitor-стиля в xLizard.)

Пример
  void copy(uint8_t *dst, const uint8_t *src)
  {
      *dst = *src;           /* два разыменования */
      REG->DR = *src;        /* -> и ещё одно * */
      uint8_t *p = &buf[0];  /* * в объявлении и & */
  }
Ptr Ops растёт на каждое такое вхождение по файлу (не «уникальные»
указатели, а число операций).

Базовый порог: 100 (мягкий file-level gate, p90–p95).
Влияет на: риск ошибок памяти/алиасинга в register-map коде,
сложность ревью низкоуровневого C.
""",
    "preprocessor_directives": """Директивы препроцессора (PP)
Уровень: файл

Как считается
Число строк/директив препроцессора в файле: #include, #define,
#if, #ifdef, #ifndef, #elif, #else, #endif, #pragma и т.п.

Пример
  #include "board.h"     /* +1 */
  #ifdef USE_DMA         /* +1 */
  #define BUF 256        /* +1 */
  void init(void) { … }
  #else                  /* +1 */
  void init(void) { … }
  #endif                 /* +1 */
PP = 5 (плюс другие директивы в том же файле).

Базовый порог: 40 (эмпирический p95).
Влияет на: вариативность сборки под платы/MCU, скрытые ветки
компиляции и покрытие конфигураций тестами.
""",
    "logical_operators": """Логические операторы (Logic)
Уровень: файл

Как считается
Сумма по файлу операторов &&, || и логического ! (не путать
с != и с битовым & / |). Строки и комментарии отбрасываются.

Пример
  if (!ready && (status || override))
    /* !  +  &&  +  ||  → +3 к Logic файла */
  start();

Базовый порог: 50 (сумма по файлу; ориентир ~p90 эталонов).
Влияет на: плотность условий статуса/флагов и риск пропустить
крайний случай в проверках железа.
""",
    "conditional_statements": """Условные операторы (Cond)
Уровень: файл

Как считается
Счётчик вхождений управляющих конструкций по файлу:
if, else if, else, for, while, do, switch, case, default.
Это количество операторов, а не глубина вложенности.

Пример
  if (a) {                 /* +1 */
      for (;;) {           /* +1 */
          if (b) break;    /* +1 */
      }
  } else {                 /* +1 */
      switch (c) {         /* +1 */
      case 1: …; break;    /* +1 */
      default: …;          /* +1 */
      }
  }
Cond = 7 для этого фрагмента (плюс остальное в файле).

Базовый порог: 50 (сумма по файлу).
Влияет на: ветвистость модуля, объём тестов и стоимость
изменения поведения драйвера.
""",
    "comment_percentage": """Доля комментариев (Comments %)
Уровень: файл

Как считается
(число строк комментариев / число строк файла) × 100.
Учитываются // и /* … */. Порог работает как «значение выше
порога = превышение», поэтому 0 фактически отключает проверку
«мало комментариев» (иначе правило пришлось бы инвертировать).

Пример
  Файл из 100 строк, из них 25 — комментарии
  → Comments % = 25.

Базовый порог: 0 (проверка отключена).
Влияет на: документированность модуля; при необходимости
задайте свой минимум отдельно в процессе ревью.
""",
    "function_count": """Функций в файле (Funcs)
Уровень: файл

Как считается
Сколько функций (определений), которые распознал анализатор
в данном .c/.h файле. Макросы-обёртки и inline в заголовках
тоже могут попасть в счёт, если выглядят как функции.

Пример
  static void hw_init(void) { … }
  void uart_irq_handler(void) { … }
  int uart_write(…) { … }
Funcs = 3 для этого файла.

Базовый порог: 40 (компромисс «мелкие файлы musl» vs крупные
модули вроде redis).
Влияет на: модульность единицы компиляции, размер ревью и ясность
ответственности файла (один периферийный модуль).
""",
}

# Order for GUI threshold editors and «О метриках» tabs
METRIC_ORDER = [
    "cyclomatic_complexity",
    "cognitive_complexity",
    "max_nesting_depth",
    "nloc",
    "token_count",
    "parameter_count",
    "length",
    "max_block_depth",
    "pointer_operations",
    "preprocessor_directives",
    "logical_operators",
    "conditional_statements",
    "comment_percentage",
    "function_count",
]


def metrics_about_tabs():
    """Ordered (tab_title, body_text) for the «О метриках» dialog."""
    tabs = [("Общее", METRICS_ABOUT_GENERAL)]
    for key in METRIC_ORDER:
        title = METRIC_TAB_TITLES.get(key, key)
        body = METRICS_ABOUT_DETAIL.get(key, METRIC_HELP.get(key, key))
        tabs.append((title, body))
    return tabs


# Backward-compatible full text (general + all metric pages)
THRESHOLDS_ORIGIN_TEXT = "\n\n".join(
    body for _title, body in metrics_about_tabs()
)

# Friendly aliases accepted in thresholds.txt
_ALIASES = {
    "ccn": "cyclomatic_complexity",
    "cyclomatic": "cyclomatic_complexity",
    "cogc": "cognitive_complexity",
    "cognitive": "cognitive_complexity",
    "nd": "max_nesting_depth",
    "nesting": "max_nesting_depth",
    "nesting_depth": "max_nesting_depth",
    "loc": "nloc",
    "lines": "nloc",
    "tokens": "token_count",
    "param": "parameter_count",
    "params": "parameter_count",
    "parameters": "parameter_count",
    "comments": "comment_percentage",
    "comment_percent": "comment_percentage",
    "depth": "max_block_depth",
    "block_depth": "max_block_depth",
    "pointers": "pointer_operations",
    "pointer": "pointer_operations",
    "preprocessor": "preprocessor_directives",
    "pp": "preprocessor_directives",
    "logical": "logical_operators",
    "conditionals": "conditional_statements",
    "functions": "function_count",
}


def application_dir() -> Path:
    """Directory of the .exe (frozen) or project/CWD for source runs."""
    if getattr(sys, "frozen", False):
        # onedir: exe in dist/xLizard/; onefile: exe next to extracted _MEIPASS
        return Path(sys.executable).resolve().parent
    # Prefer process CWD so a local thresholds.txt overrides package defaults
    return Path.cwd()


def thresholds_path(explicit: Optional[str] = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return application_dir() / THRESHOLDS_FILENAME


def normalize_key(key: str) -> str:
    k = key.strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(k, k)


def parse_thresholds_text(text: str) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "=" not in line:
            continue
        left, right = line.split("=", 1)
        key = normalize_key(left)
        value = right.strip().split("#", 1)[0].strip()
        if not key or not value:
            continue
        try:
            result[key] = float(value) if "." in value else int(value)
        except ValueError:
            continue
    return result


def load_thresholds(
    path: Optional[str] = None,
    *,
    create_if_missing: bool = True,
) -> Dict[str, float]:
    """
    Load thresholds from file. Missing keys fall back to DEFAULT_THRESHOLDS.
    If the file is missing and create_if_missing, write a default file.
    """
    file_path = thresholds_path(path)
    merged = dict(DEFAULT_THRESHOLDS)

    if not file_path.is_file():
        if create_if_missing:
            try:
                write_thresholds_file(file_path, merged)
            except OSError:
                pass
        return merged

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return merged

    loaded = parse_thresholds_text(text)
    merged.update(loaded)
    return merged


def write_thresholds_file(
    path: Optional[Path] = None,
    thresholds: Optional[Mapping[str, float]] = None,
) -> Path:
    path = Path(path) if path else thresholds_path()
    data = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        data.update(thresholds)

    lines = [
        "# Пороги метрик xLizard",
        "# Значение метрики ВЫШЕ указанного порога считается превышением.",
        "# Формат: ключ=число  (синонимы: CCN, CogC, ND, LOC, …)",
        "#",
    ]
    for key in METRIC_ORDER:
        label = METRIC_LABELS.get(key, key)
        lines.append("%s=%s   # %s" % (key, data[key], label))
    lines.append("")
    content = "\n".join(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def apply_to_options(options, thresholds: MutableMapping[str, float]) -> None:
    """Merge loaded thresholds into argparse options object."""
    if not hasattr(options, "thresholds") or options.thresholds is None:
        options.thresholds = {}
    # File values fill gaps; explicit CLI -T already in options.thresholds wins
    for key, value in thresholds.items():
        options.thresholds.setdefault(key, value)

    # Keep classic CLI fields in sync when not overridden
    if hasattr(options, "CCN") and "cyclomatic_complexity" in thresholds:
        if options.CCN == 15 or options.thresholds.get("cyclomatic_complexity") == thresholds[
            "cyclomatic_complexity"
        ]:
            pass
    ccn = options.thresholds.get("cyclomatic_complexity")
    if ccn is not None:
        options.CCN = int(ccn)
    if "length" in options.thresholds and hasattr(options, "length"):
        options.length = int(options.thresholds["length"])
    if "max_nesting_depth" in options.thresholds:
        options.ND = int(options.thresholds["max_nesting_depth"])
    if "cognitive_complexity" in options.thresholds:
        options.CogC = int(options.thresholds["cognitive_complexity"])


def sync_sourcemonitor_config(thresholds: Mapping[str, float]) -> None:
    from xlizard.sourcemonitor_metrics import Config

    for key in Config.THRESHOLDS:
        if key in thresholds:
            Config.THRESHOLDS[key] = thresholds[key]
