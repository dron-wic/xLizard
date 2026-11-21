# xLizard - Extended Metric Analyzer

![Version](https://img.shields.io/badge/version-1.1.8-blue.svg)
![License](https://img.shields.io/badge/license-MIT-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)

**xLizard** — расширенный анализатор метрик сложности кода для C/C++ с метриками SourceMonitor, опциональным пакетом HIS и HTML-отчётами.

## Происхождение и лицензия

xLizard основан на [Lizard](https://github.com/terryyin/lizard) (Terry Yin и contributors, [lizard.ws](https://www.lizard.ws)).

Код распространяется под **MIT** — см. файл [`LICENSE`](LICENSE). Сохранён copyright исходного Lizard; добавлены авторы производной работы (Xor1no, dron-wic). Это не официальный релиз Lizard.

Когнитивная сложность (CogC) считается по открытой спецификации SonarSource.

История версий: [`CHANGES.rst`](CHANGES.rst).

## Безопасность и Конфиденциальность

**ВАЖНО: ВСЕ АНАЛИЗЫ ВЫПОЛНЯЮТСЯ ЛОКАЛЬНО**

- Весь анализ только на вашем компьютере
- Исходники никуда не отправляются
- Интернет для отчётов не нужен

## Поддерживаемые метрики

### Базовые (на функцию)
- **CCN** — цикломатическая сложность
- **CogC** — когнитивная сложность (SonarSource v1.2; `-Ecognitive`, в GUI по умолчанию)
- **NLOC** — строки кода без комментариев
- **token** — число токенов
- **PARAM** — число параметров
- **length** — длина функции в строках (колонка **Length** в HTML)
- **ND** — макс. глубина вложенности (расширение `-End`, в GUI включено по умолчанию)

Когнитивная сложность считает «насколько трудно читать»: +1 и штраф за вложенность для `if`/`for`/`while`/`switch`/`?`/`catch`; `else`/`else if` без штрафа вложенности; последовательности одинаковых `&&`/`||` — как одна единица. Не считает `case` и обычные `break`/`return`. См. [SonarSource PDF](https://www.sonarsource.com/docs/CognitiveComplexity.pdf).

**Заметки по точности (C):**
- **CCN** — стиль lizard: каждый `case`, `&&`, `||`, `?` даёт +1; сам `switch` в дефолте не считается. Строгий McCabe fall-through: `-Emccabe`. Весь switch как одно решение: `-m`.
- **CogC** — SonarSource v1.2 (как clang-tidy); эталон для «понятности».
- **ND** — глубина управляющих конструкций (`if`/`for`/`while`/…), без `&&`/`||`.
- Метрики файла (комментарии, pointers, conditionals) — эвристики в духе SourceMonitor, не полный AST.

### На файл (SourceMonitor, в HTML/XML)
- **comment_percentage** — доля комментариев (%)
- **max_block_depth** — макс. глубина блоков `{ }`
- **pointer_operations** — операции с указателями
- **preprocessor_directives** — директивы препроцессора
- **logical_operators** / **conditional_statements** — логика и ветвления
- **lines_of_code** / **comment_lines** / **total_lines**

### Пакет HIS (опционально)

Метрики Hersteller Initiative Software (автопром / embedded). В GUI: окно **«Пороги»** → чекбокс **«HIS-метрики»**. В `xlizard.json`: `"features": { "his_metrics": true|false }` (по умолчанию `false`).

| Ключ | HIS | Смысл |
|------|-----|--------|
| `goto_count` | GOTO ≤ 0 | Число `goto` |
| `return_count` | RETURN ≤ 1 | Число `return` |
| `path_count` | PATH ≤ 80 | Оценка ациклических путей (упрощённая, не Polyspace) |
| `calls` | CALLS ≤ 7 | Уникальные вызываемые функции (по именам в проекте) |
| `calling` | CALLING ≤ 5 | Уникальные вызывающие (fan-in) |

- **Включено** — метрики считаются, колонки в HTML, участвуют в суммарной оценке.
- **Выключено** — не считаются; в HTML пометка «HIS-метрики отключены», колонок нет.

Подробности и примеры — в GUI **«О метриках»** (вкладки GOTO…CALLING и раздел «Общее»).

### Суммарная оценка качества (HTML «Обзор»)

На вкладке **«Обзор»** показывается балл **0–100**, текстовый статус и топ метрик с превышениями. Считается модулем `quality_score.py` по активным функциям (вне `XLIZARD_DISABLE`) и по файловым метрикам. Настройки: **«Пороги»** / `xlizard.json` (`metrics.*.limit`, `metrics.*.soft_pct`). В подсказках колонок и бейджей файлов — порог и **Мягкое: N%**.

#### Какие метрики входят

| Уровень | Метрики |
|---------|---------|
| Функция | CCN, CogC, ND, NLOC, Tokens, PARAM, Length |
| Функция (только при HIS вкл.) | GOTO, RETURN, PATH, CALLS, CALLING |
| Файл | глубина блоков, pointer ops, PP, logic, conditionals, число активных функций |

`comment_percentage` в оценку **не** входит; при `limit = 0` для неё проверка отключена и в других местах.

#### Мягкое и жёсткое превышение

Для каждой пары «значение / limit / soft_pct»:

1. `value ≤ limit` — норма (штрафа нет).
2. `value > limit`, но превышение не больше `soft_pct` % от limit — **мягкое**  
   (пример: CCN limit=15, soft_pct=25 → мягкая зона до **18.75**, т.е. 16…18 мягкие).
3. Сильнее мягкой зоны — **жёсткое**.
4. Особый случай **limit = 0** (GOTO): любое значение > 0 — сразу **жёсткое** (мягкой зоны нет).
5. Метрики из `DISABLE_GATE_WHEN_LIMIT_ZERO` при `limit ≤ 0` полностью игнорируются.

Функция учитывается как «мягкая», если есть хотя бы одно мягкое превышение и **нет** жёстких; как «жёсткая» — если есть хотя бы одно жёсткое (даже при наличии мягких).

#### Формула балла

```
score = 100
      − 15 × (доля функций с мягким превышением)
      − 45 × (доля функций с жёстким превышением)
      − min(20, 2×N_soft_file + 6×N_hard_file)
```

- Доли считаются от числа **активных** функций.
- Файловый штраф: +2 за каждое мягкое и +6 за каждое жёсткое файловое превышение, потолок **20**.
- Итог округляется и ограничивается диапазоном **0…100**.

Примеры смысла весов: одна жёсткая функция из десяти снимает ~4.5 балла; мягкая — ~1.5. Жёсткие нарушения бьют по баллу сильнее мягких.

#### Статусы

| Балл / условие | Статус |
|----------------|--------|
| ≥ 95 и нет превышений вообще | **Норма** |
| ≥ 80 и почти нет жёстких (нет hard или ≤ 2% функций с hard) | **Допустимо** |
| ≥ 55 | **Внимание** |
| < 55 | **Критично** |

«Допустимо» допускает незначительные мягкие превышения (бейджи в таблице остаются), но высокий балл сохраняется.

#### Топ превышений

В карточке качества — до **6** метрик с наибольшим числом soft+hard срабатываний; для каждой показаны лимит и `soft_pct`. HIS-метрики попадают в топ и в формулу **только** если HIS включён.

### Опциональные расширения CLI (`-E…`)
statements, exits, goto, fan-in/out (`-Eio`), pathcount, returncount, duplicates, dependency count и др. Пакет HIS в GUI/JSON подключает нужные расширения сам.

## Настройки (`xlizard.json`)

Все настройки рядом с `xLizard.exe` (или в CWD при запуске из исходников):

- пороги и `soft_pct` по метрикам;
- тема UI (`theme`: `dark` / `light`);
- флаг HIS (`features.his_metrics`).

Редактирование: окно **«Пороги»**, кнопка **xlizard.json**, или вручную. При первом запуске без JSON возможна миграция со старых `thresholds.txt` / `ui_theme.txt`.

Значение метрики **выше** `limit` считается превышением (`comment_percentage: 0` отключает эту проверку; у GOTO лимит `0` — любое `goto` = превышение).

Пример структуры:

```json
{
  "version": 1,
  "theme": "dark",
  "features": { "his_metrics": false },
  "metrics": {
    "cyclomatic_complexity": { "limit": 15, "soft_pct": 25 },
    "length": { "limit": 150, "soft_pct": 25 }
  }
}
```

## Быстрый старт

### Установка

```bash
pip install xlizard
# или из исходников:
pip install -e ".[dev]"
```

### Тесты

```bash
pytest
```

C-фикстуры: `tests/fixtures/c/` (CCN, CogC, ND, SourceMonitor, McCabe, `-m`).
Крупный набор: `tests/fixtures/c/large/` (~1.8k+ строк, 80+ функций) — `tests/test_large_metrics.py`.

### GUI — выбор файла или папки

```bash
xlizard-gui
# или:
python -m xlizard.gui
```

Укажите файл/папку → **«Анализировать»** → откроется HTML-отчёт.

Кнопки: **«Пороги»** (лимиты, soft %, HIS), **«О метриках»** (справка), **xlizard.json**. Окна «Пороги» и «О метриках» немодальные. Журнал можно скопировать кнопкой **Копировать** или Ctrl+C.

### Портативный .exe (Windows 10/11, без Python)

```bat
build_exe.bat
```

Результат: `dist\xLizard\xLizard.exe` и рядом `xlizard.json`.

Скопируйте всю папку `dist\xLizard\` на другой ПК. Настройки — в `xlizard.json` (или через GUI «Пороги»).

### CLI

```bash
xlizard --html -Ecognitive -End <path> -o <path>\<file_name>.html
xlizard -Ecognitive --CogC 15 <path>
xlizard --xml <path> -o <path>\<file_name>.xml
```

Флаг HIS и пороги читаются из `xlizard.json` в CWD / рядом с exe.

Возможности HTML-отчёта: суммарная оценка качества, колонка Length, подсказки с soft %, диаграммы, heatmap по директориям, поиск, топ функций, пороги, колонки HIS (если включены), тёмная/светлая тема.

### Исключения и потоки

```bash
xlizard -x "*/test/*" -x "*.bak" -x "*/build/*" <path>
xlizard -t 4 <project_path>/
```

Автоматически исключаются: `.git`, `venv`, `__pycache__`, `include`.
