# -*- coding: utf-8 -*-
"""
Application settings and metric thresholds (xlizard.json next to the executable).

Values greater than the threshold are treated as exceeded.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional

CONFIG_FILENAME = "xlizard.json"
THRESHOLDS_FILENAME = "thresholds.txt"  # legacy; used only for migration
THEME_FILENAME_LEGACY = "ui_theme.txt"
CONFIG_VERSION = 1

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
    # HIS pack (optional; gated by features.his_metrics)
    "goto_count": 0,  # HIS GOTO ≤ 0
    "return_count": 1,  # HIS RETURN ≤ 1
    "path_count": 80,  # HIS PATH ≤ 80 (estimated)
    "calls": 7,  # HIS CALLS ≤ 7
    "calling": 5,  # HIS CALLING ≤ 5
}

# Metrics computed/shown only when features.his_metrics is enabled
HIS_METRIC_KEYS = (
    "goto_count",
    "return_count",
    "path_count",
    "calls",
    "calling",
)

# Limit 0 disables the gate (not “max allowed 0”)
DISABLE_GATE_WHEN_LIMIT_ZERO = frozenset({"comment_percentage"})

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
    "goto_count": "Операторы goto (GOTO)",
    "return_count": "Точки выхода return (RETURN)",
    "path_count": "Число путей (PATH)",
    "calls": "Вызываемые функции (CALLS)",
    "calling": "Вызывающие функции (CALLING)",
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
    "goto_count": (
        "Уровень: функция. Пакет HIS (включается в «Пороги»).\n"
        "Число операторов goto в теле функции.\n"
        "HIS: допустимо 0. Влияет на: тестируемость и читаемость потока."
    ),
    "return_count": (
        "Уровень: функция. Пакет HIS (включается в «Пороги»).\n"
        "Число операторов return (точек выхода).\n"
        "HIS: ≤ 1. Влияет на: единообразие точек выхода (стиль HIS)."
    ),
    "path_count": (
        "Уровень: функция. Пакет HIS (включается в «Пороги»).\n"
        "Оценка числа ациклических путей выполнения (не полный CFG "
        "Polyspace/Understand).\n"
        "HIS: ≤ 80. Влияет на: ориентир объёма white-box тестов."
    ),
    "calls": (
        "Уровень: функция. Пакет HIS (включается в «Пороги»).\n"
        "Число уникальных вызываемых функций (по именам в проекте).\n"
        "HIS: ≤ 7. Влияет на: связанность модуля; best-effort без препроцессора."
    ),
    "calling": (
        "Уровень: функция. Пакет HIS (включается в «Пороги»).\n"
        "Число уникальных вызывающих функций (fan-in по именам).\n"
        "HIS: ≤ 5. Влияет на: переиспользование API; best-effort call-graph."
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
    "goto_count": "GOTO",
    "return_count": "RETURN",
    "path_count": "PATH",
    "calls": "CALLS",
    "calling": "CALLING",
}

# First tab of «О метриках»: overview (nothing dropped from the old dialog)
METRICS_ABOUT_GENERAL = """xLizard для embedded (MCU)

Программа считает метрики сложности C/C++ для прошивок и
драйверов. Значение метрики ВЫШЕ порога считается превышением.
Все настройки — в xlizard.json рядом с программой (окно «Пороги»).

Пакет HIS (GOTO / RETURN / PATH / CALLS / CALLING) включается
чекбоксом в «Пороги». Пока выключен — эти метрики не считаются
и в HTML показывается пометка об отключении.

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
Пакет HIS (опционально)
────────────────────────────────
Включается в «Пороги» → «HIS-метрики». Источник: Hersteller
Initiative Software (автопром / ISO 26262 контекст).
• GOTO ≤ 0 — запрет goto.
• RETURN ≤ 1 — одна точка выхода.
• PATH ≤ 80 — оценка ациклических путей (упрощённая, не Polyspace).
• CALLS ≤ 7 — уникальные вызываемые функции (по именам).
• CALLING ≤ 5 — уникальные вызывающие (fan-in по именам).

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
    "goto_count": """Операторы goto (GOTO) — HIS
Уровень: функция (пакет HIS)

Как считается
+1 за каждый токен goto в теле функции.

Пример
  if (err) goto fail;
  …
fail:
  cleanup();
GOTO = 1 → превышение лимита HIS (0).

Базовый порог: 0 (HIS).
Влияет на: тестируемость и читаемость потока управления.
Включается чекбоксом «HIS-метрики» в окне «Пороги».
""",
    "return_count": """Точки выхода return (RETURN) — HIS
Уровень: функция (пакет HIS)

Как считается
Число токенов return в теле функции.

Пример
  if (!ok) return -1;
  return 0;
RETURN = 2 → превышение лимита HIS (≤ 1).

Базовый порог: 1 (HIS).
Влияет на: единообразие точек выхода по стилю HIS/MISRA-ориентированных правил.
Включается чекбоксом «HIS-метрики» в окне «Пороги».
""",
    "path_count": """Число путей (PATH) — HIS
Уровень: функция (пакет HIS)

Как считается
Оценка числа ациклических путей по упрощённому разбору
ветвлений (if / else / switch / case / циклы / ?:).
Это не полный CFG industrial-инструментов (Polyspace, Understand).

Пример
  Два независимых if подряд дают больше путей, чем один if.
HIS: PATH ≤ 80.

Базовый порог: 80 (HIS).
Влияет на: оценку объёма white-box тестов.
Включается чекбоксом «HIS-метрики» в окне «Пороги».
""",
    "calls": """Вызываемые функции (CALLS) — HIS
Уровень: функция (пакет HIS)

Как считается
Число уникальных имён функций из текущего проекта, которые
встречаются в теле как вызовы. Повторный вызов той же функции
не увеличивает счётчик. Без раскрытия макросов и через указатели
на функции — best-effort.

Пример
  foo(); bar(); foo();  → CALLS = 2 (если foo и bar есть в проекте).

Базовый порог: 7 (HIS).
Включается чекбоксом «HIS-метрики» в окне «Пороги».
""",
    "calling": """Вызывающие функции (CALLING) — HIS
Уровень: функция (пакет HIS)

Как считается
Сколько других функций проекта содержат вызов данной
(уникальный fan-in по именам). Best-effort call-graph.

Пример
  Если bar и baz вызывают foo, у foo CALLING = 2.

Базовый порог: 5 (HIS).
Включается чекбоксом «HIS-метрики» в окне «Пороги».
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
    "goto_count",
    "return_count",
    "path_count",
    "calls",
    "calling",
]

# Soft exceedance band (% above limit) used by quality score; per metric.
DEFAULT_SOFT_PCT_VALUE = 25
DEFAULT_SOFT_PCT: Dict[str, float] = {key: DEFAULT_SOFT_PCT_VALUE for key in METRIC_ORDER}
DEFAULT_SOFT_PCT["goto_count"] = 1
DEFAULT_SOFT_PCT["return_count"] = 1
SOFT_PCT_SUFFIX = "_soft_pct"
DEFAULT_HIS_METRICS = False
DEFAULT_THEME = "dark"


def soft_pct_key(metric: str) -> str:
    return "%s%s" % (metric, SOFT_PCT_SUFFIX)


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
    "goto": "goto_count",
    "gotos": "goto_count",
    "return": "return_count",
    "returns": "return_count",
    "path": "path_count",
    "paths": "path_count",
    "call": "calls",
    "callee": "calls",
    "callees": "calls",
    "caller": "calling",
    "callers": "calling",
}


def application_dir() -> Path:
    """Directory of the .exe (frozen) or project/CWD for source runs."""
    if getattr(sys, "frozen", False):
        # onedir: exe in dist/xLizard/; onefile: exe next to extracted _MEIPASS
        return Path(sys.executable).resolve().parent
    # Prefer process CWD so a local config overrides package defaults
    return Path.cwd()


def config_path(explicit: Optional[str] = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return application_dir() / CONFIG_FILENAME


def thresholds_path(explicit: Optional[str] = None) -> Path:
    """Path to settings file (xlizard.json). Name kept for callers."""
    return config_path(explicit)


def default_app_config() -> Dict[str, Any]:
    metrics: Dict[str, Dict[str, float]] = {}
    for key in METRIC_ORDER:
        limit_val = DEFAULT_THRESHOLDS[key]
        soft_val = DEFAULT_SOFT_PCT[key]
        metrics[key] = {
            "limit": int(limit_val) if float(limit_val).is_integer() else float(limit_val),
            "soft_pct": int(soft_val),
        }
    return {
        "version": CONFIG_VERSION,
        "theme": DEFAULT_THEME,
        "features": {"his_metrics": DEFAULT_HIS_METRICS},
        "metrics": metrics,
    }


def normalize_key(key: str) -> str:
    k = key.strip().lower().replace("-", "_").replace(" ", "_")
    if k.startswith("soft_pct_"):
        base = k[len("soft_pct_") :]
        base = _ALIASES.get(base, base)
        return soft_pct_key(base)
    if k.endswith(SOFT_PCT_SUFFIX):
        base = k[: -len(SOFT_PCT_SUFFIX)]
        if base.endswith("_"):
            base = base[:-1]
        base = _ALIASES.get(base, base)
        return soft_pct_key(base)
    return _ALIASES.get(k, k)


def parse_thresholds_text(text: str) -> Dict[str, float]:
    """Legacy thresholds.txt parser (migration / tests)."""
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


def split_limits_and_soft_pcts(
    data: Mapping[str, float],
) -> tuple[Dict[str, float], Dict[str, float]]:
    """Split flat key→value map into metric limits and soft_pct maps."""
    limits = dict(DEFAULT_THRESHOLDS)
    soft = dict(DEFAULT_SOFT_PCT)
    for key, value in data.items():
        if key.endswith(SOFT_PCT_SUFFIX):
            metric = key[: -len(SOFT_PCT_SUFFIX)]
            if metric in DEFAULT_SOFT_PCT:
                soft[metric] = max(1, min(100, float(value)))
        elif key in DEFAULT_THRESHOLDS:
            limits[key] = float(value)
    return limits, soft


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return default


def _merge_metrics_from_json(
    raw_metrics: Any,
) -> tuple[Dict[str, float], Dict[str, float]]:
    limits = dict(DEFAULT_THRESHOLDS)
    soft = dict(DEFAULT_SOFT_PCT)
    if not isinstance(raw_metrics, dict):
        return limits, soft
    for key, entry in raw_metrics.items():
        canon = normalize_key(str(key))
        if canon not in DEFAULT_THRESHOLDS:
            continue
        if isinstance(entry, dict):
            if "limit" in entry:
                try:
                    limits[canon] = float(entry["limit"])
                except (TypeError, ValueError):
                    pass
            if "soft_pct" in entry:
                try:
                    soft[canon] = max(1, min(100, float(entry["soft_pct"])))
                except (TypeError, ValueError):
                    pass
        else:
            try:
                limits[canon] = float(entry)
            except (TypeError, ValueError):
                pass
    return limits, soft


def _migrate_legacy_files(base_dir: Path) -> Optional[Dict[str, Any]]:
    """Build config dict from legacy thresholds.txt / ui_theme.txt if present."""
    cfg = default_app_config()
    legacy_thr = base_dir / THRESHOLDS_FILENAME
    legacy_theme = base_dir / THEME_FILENAME_LEGACY
    changed = False
    if legacy_thr.is_file():
        try:
            loaded = parse_thresholds_text(legacy_thr.read_text(encoding="utf-8"))
            limits, soft = split_limits_and_soft_pcts(loaded)
            for key in METRIC_ORDER:
                cfg["metrics"][key] = {
                    "limit": int(limits[key])
                    if float(limits[key]).is_integer()
                    else limits[key],
                    "soft_pct": int(soft[key]),
                }
            changed = True
        except OSError:
            pass
    if legacy_theme.is_file():
        try:
            theme = legacy_theme.read_text(encoding="utf-8").strip().lower()
            if theme in ("dark", "light"):
                cfg["theme"] = theme
                changed = True
        except OSError:
            pass
    return cfg if changed else None


def write_app_config(
    path: Optional[Path] = None,
    *,
    thresholds: Optional[Mapping[str, float]] = None,
    soft_pcts: Optional[Mapping[str, float]] = None,
    theme: Optional[str] = None,
    his_metrics: Optional[bool] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Write full xlizard.json (limits, soft_pct, theme, HIS flag)."""
    file_path = Path(path) if path else config_path()
    if config is not None:
        payload = dict(config)
    else:
        payload = default_app_config()
        data = dict(DEFAULT_THRESHOLDS)
        soft = dict(DEFAULT_SOFT_PCT)
        if thresholds:
            parsed_limits, parsed_soft = split_limits_and_soft_pcts(thresholds)
            data.update(parsed_limits)
            soft.update(parsed_soft)
            for key, value in thresholds.items():
                if key in DEFAULT_THRESHOLDS:
                    data[key] = value
        if soft_pcts:
            for key, value in soft_pcts.items():
                if key in DEFAULT_SOFT_PCT:
                    soft[key] = max(1, min(100, float(value)))
        metrics: Dict[str, Dict[str, float]] = {}
        for key in METRIC_ORDER:
            limit_val = data[key]
            if isinstance(limit_val, float) and limit_val.is_integer():
                limit_val = int(limit_val)
            metrics[key] = {"limit": limit_val, "soft_pct": int(soft[key])}
        payload["metrics"] = metrics
        if theme is not None:
            payload["theme"] = theme if theme in ("dark", "light") else DEFAULT_THEME
        if his_metrics is not None:
            payload["features"] = {"his_metrics": bool(his_metrics)}

    payload.setdefault("version", CONFIG_VERSION)
    payload.setdefault("theme", DEFAULT_THEME)
    payload.setdefault("features", {"his_metrics": DEFAULT_HIS_METRICS})
    payload.setdefault("metrics", default_app_config()["metrics"])

    file_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    file_path.write_text(text, encoding="utf-8")
    return file_path


def load_app_config(
    path: Optional[str] = None,
    *,
    create_if_missing: bool = True,
) -> Dict[str, Any]:
    """
    Load xlizard.json. Migrates legacy txt once if JSON is missing.
    Returns dict with keys: version, theme, features, metrics, plus
    convenience: thresholds, soft_pcts, his_metrics.
    """
    file_path = config_path(path)
    cfg = default_app_config()

    if not file_path.is_file():
        migrated = _migrate_legacy_files(file_path.parent)
        if migrated is not None:
            cfg = migrated
            if create_if_missing:
                try:
                    write_app_config(file_path, config=cfg)
                except OSError:
                    pass
        elif create_if_missing:
            try:
                write_app_config(file_path, config=cfg)
            except OSError:
                pass
    else:
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}
        if isinstance(raw, dict):
            theme = str(raw.get("theme", DEFAULT_THEME)).strip().lower()
            cfg["theme"] = theme if theme in ("dark", "light") else DEFAULT_THEME
            features = raw.get("features") if isinstance(raw.get("features"), dict) else {}
            cfg["features"] = {
                "his_metrics": _coerce_bool(
                    features.get("his_metrics", DEFAULT_HIS_METRICS),
                    DEFAULT_HIS_METRICS,
                )
            }
            limits, soft = _merge_metrics_from_json(raw.get("metrics"))
            for key in METRIC_ORDER:
                cfg["metrics"][key] = {
                    "limit": int(limits[key])
                    if float(limits[key]).is_integer()
                    else limits[key],
                    "soft_pct": int(soft[key]),
                }

    limits = {k: float(cfg["metrics"][k]["limit"]) for k in METRIC_ORDER}
    soft = {k: float(cfg["metrics"][k]["soft_pct"]) for k in METRIC_ORDER}
    cfg["thresholds"] = limits
    cfg["soft_pcts"] = soft
    cfg["his_metrics"] = bool(cfg["features"].get("his_metrics", False))
    return cfg


def load_threshold_config(
    path: Optional[str] = None,
    *,
    create_if_missing: bool = True,
) -> tuple[Dict[str, float], Dict[str, float]]:
    """Load metric limits and soft_pct from xlizard.json."""
    cfg = load_app_config(path, create_if_missing=create_if_missing)
    return dict(cfg["thresholds"]), dict(cfg["soft_pcts"])


def load_thresholds(
    path: Optional[str] = None,
    *,
    create_if_missing: bool = True,
) -> Dict[str, float]:
    """Load metric limits (soft_pct ignored in the return value)."""
    limits, _soft = load_threshold_config(path, create_if_missing=create_if_missing)
    return limits


def write_thresholds_file(
    path: Optional[Path] = None,
    thresholds: Optional[Mapping[str, float]] = None,
    soft_pcts: Optional[Mapping[str, float]] = None,
    *,
    theme: Optional[str] = None,
    his_metrics: Optional[bool] = None,
) -> Path:
    """Write settings to xlizard.json (API kept for callers)."""
    return write_app_config(
        path,
        thresholds=thresholds,
        soft_pcts=soft_pcts,
        theme=theme,
        his_metrics=his_metrics,
    )


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
