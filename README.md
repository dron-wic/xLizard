# xLizard - Extended Metric Analyzer

![Version](https://img.shields.io/badge/version-1.1.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)

**xLizard** — расширенный анализатор метрик сложности кода для C/C++ с метриками SourceMonitor и HTML-отчётами.

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
- **length** — длина функции в строках
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

### Опциональные расширения CLI (`-E…`)
statements, exits, goto, fan-in/out (`-Eio`), duplicates, dependency count и др.

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

### GUI — выбор файла или папки

```bash
xlizard-gui
# или:
python -m xlizard.gui
```

Укажите файл/папку → «Анализировать» → откроется HTML-отчёт.

### Портативный .exe (Windows 10/11, без Python)

```bat
build_exe.bat
```

Результат: `dist\xLizard\xLizard.exe` и рядом `thresholds.txt`.

Скопируйте всю папку `dist\xLizard\` на другой ПК. Пороги правятся в `thresholds.txt` (значение **выше** порога = превышение).

### CLI

```bash
xlizard --html -Ecognitive -End <path> -o <path>\<file_name>.html
xlizard -Ecognitive --CogC 15 <path>
xlizard --xml <path> -o <path>\<file_name>.xml
```

Возможности HTML-отчёта: диаграммы, heatmap по директориям, поиск, топ-5, пороги, тёмная/светлая тема.

### Исключения и потоки

```bash
xlizard -x "*/test/*" -x "*.bak" -x "*/build/*" <path>
xlizard -t 4 <project_path>/
```

Автоматически исключаются: `.git`, `venv`, `__pycache__`, `include`.
