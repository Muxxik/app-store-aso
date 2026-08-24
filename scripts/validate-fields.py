#!/usr/bin/env python3
"""Валидатор пакета метаданных перед отправкой в App Store Connect.

  validate-fields.py <файл-с-полями>

Проверяет то, что человек надёжно проверить не может:
  1. Лимиты: Name ≤30, Subtitle ≤30, Keywords ≤100.
  2. Синтаксис keywords: пробелы вокруг запятых, пустые токены.
  3. Пустой Subtitle (стор молча подставит жанр — 30 символов индексации сгорят).
  4. Дубли внутри локали: токен keywords, уже лежащий в Name/Subtitle той же
     локали, — чистое сжигание символов.
  5. Дубли между локалями одной страны: страна индексирует несколько локалей
     (карта ниже, источник — references/locales.md), и токен, пришедший из
     двух локалей, во второй раз ничего не добавляет. Валидатор показывает
     баланс, решение оставить/убрать — за тобой: слово может быть балластом
     в одной стране и рабочим в другой, а дубль «основная + вторичная локаль»
     может быть осознанной ставкой на гипотезу 1 (вес основной локали выше).

Формат входного файла (значения как в ASC, локали — как в ASC):

    [en-US]
    name: 28 Nights: Roguelike Survival
    subtitle: Turn based RPG & tower defense
    keywords: survive,night,craft,strategy

    [fr-FR]
    name: ...

Выход 1 — есть жёсткие ошибки (лимиты, синтаксис); 0 — только предупреждения.
"""
import re
import sys

# Какие локали индексируются в какой стране (references/locales.md).
# «French» в таблице США считаем fr-FR; если у тебя открыт fr-CA — поправь.
COUNTRY_LOCALES = {
    'США':            ['en-US', 'ar', 'zh-Hans', 'zh-Hant', 'fr-FR', 'ko', 'pt-BR', 'ru', 'es-MX', 'vi'],
    'Великобритания': ['en-GB'],
    'Австралия/НЗ':   ['en-AU', 'en-GB'],
    'Канада':         ['en-CA', 'fr-CA'],
    'Франция':        ['fr-FR', 'en-GB'],
    'Германия/Австрия': ['de-DE', 'en-GB'],
    'Швейцария':      ['de-DE', 'en-GB', 'fr-FR', 'it-IT'],
    'Италия':         ['it-IT', 'en-GB'],
    'Испания':        ['es-ES', 'en-GB'],
    'Мексика/LatAm':  ['es-MX', 'en-GB'],
    'Бразилия':       ['pt-BR', 'en-GB'],
    'Португалия':     ['pt-PT', 'en-GB'],
    'Нидерланды':     ['nl-NL', 'en-GB'],
    'Бельгия':        ['en-GB', 'fr-FR', 'nl-NL'],
    'Люксембург':     ['en-GB', 'fr-FR', 'de-DE'],
    'Россия':         ['ru', 'uk'],
    'Украина':        ['en-GB', 'uk', 'ru'],
    'Япония':         ['ja', 'en-US'],
    'Корея':          ['ko', 'en-GB'],
    'Китай':          ['zh-Hans', 'en-GB'],
}
# Основная локаль страны — для пометки дублей «основная+вторичная» (гипотеза 1).
PRIMARY = {c: locs[0] for c, locs in COUNTRY_LOCALES.items()}

LIMITS = {'name': 30, 'subtitle': 30, 'keywords': 100}
STOP = {'the', 'a', 'an', 'and', 'or', 'of', 'de', 'du', 'le', 'la', 'et', 'y', 'и'}


def parse(path):
    locales, cur = {}, None
    for ln, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.match(r'\[(.+)\]\s*$', line.strip())
        if m:
            cur = m.group(1).strip()
            locales[cur] = {}
            continue
        m = re.match(r'(name|subtitle|keywords)\s*:\s?(.*)$', line, re.I)
        if m and cur:
            locales[cur][m.group(1).lower()] = m.group(2)
        elif cur is None:
            sys.exit(f"строка {ln}: данные до первого заголовка [локаль]")
        else:
            sys.exit(f"строка {ln}: не разобрал «{line.strip()}» — жду name:/subtitle:/keywords:")
    return locales


def tokens(text):
    """Токены = слова без регистра и диакритики не трогаем (é ≠ e у Apple —
    неизвестно; сравниваем как есть, только lowercase)."""
    return [t for t in re.split(r'[^\w]+', text.lower(), flags=re.UNICODE)
            if t and t not in STOP]


def main(path):
    locales = parse(path)
    errors, warnings = [], []

    # --- 1–4: пофайловые проверки
    print(f"{'':4}{'локаль':<10}{'поле':<10}{'длина':>9}")
    for loc, fields in locales.items():
        for f in ('name', 'subtitle', 'keywords'):
            if f not in fields:
                if f == 'subtitle':
                    warnings.append(f"{loc}: нет subtitle — стор подставит жанр, 30 символов сгорят")
                continue
            v = fields[f]
            n = len(v)
            ok = n <= LIMITS[f]
            print(f"{'OK' if ok else '!!!':4}{loc:<10}{f:<10}{n:>5}/{LIMITS[f]}")
            if not ok:
                errors.append(f"{loc} {f}: {n} символов при лимите {LIMITS[f]}")
            if f == 'subtitle' and not v.strip():
                warnings.append(f"{loc}: subtitle пуст — стор подставит жанр, 30 символов сгорят")
            if f == 'keywords':
                if re.search(r'\s,|,\s', v):
                    errors.append(f"{loc} keywords: пробел вокруг запятой — символы тратятся впустую")
                if ',,' in v or v.strip(',') != v:
                    errors.append(f"{loc} keywords: пустой токен (двойная или крайняя запятая)")
                if n < 90:
                    warnings.append(f"{loc} keywords: заполнено {n}/100 — добей до ~100, "
                                    f"незанятые символы это подаренная индексация")

        # дубли внутри локали
        nm = set(tokens(fields.get('name', '')))
        sub = set(tokens(fields.get('subtitle', '')))
        kw = set(tokens(fields.get('keywords', '')))
        for t in sorted(kw & (nm | sub)):
            warnings.append(f"{loc}: «{t}» в keywords уже есть в name/subtitle этой локали — сжигает символы keywords")
        for t in sorted(nm & sub):
            warnings.append(f"{loc}: «{t}» и в name, и в subtitle — осмысленно только ради точной фразы в name")

    # --- 5: дубли между локалями одной страны
    # Локаль-контейнер (name+subtitle скопированы из другой локали, работают
    # только keywords) участвует в анализе только своими keywords — иначе
    # весь вывод затопит «дублями» самой копии.
    containers = set()
    seen_ns = {}
    for loc, fields in locales.items():
        ns = (fields.get('name', ''), fields.get('subtitle', ''))
        if ns in seen_ns and any(ns):
            containers.add(loc)
        else:
            seen_ns[ns] = loc

    name_tokens = {loc: set(tokens(f.get('name', ''))) for loc, f in locales.items()}
    all_tokens = {}
    for loc, fields in locales.items():
        fs = ('keywords',) if loc in containers else ('name', 'subtitle', 'keywords')
        all_tokens[loc] = set().union(*(tokens(fields.get(f, '')) for f in fs))

    cross = {}
    for country, locs in COUNTRY_LOCALES.items():
        present = [l for l in locs if l in all_tokens]
        if len(present) < 2:
            continue
        seen = {}
        for l in present:
            for t in all_tokens[l]:
                seen.setdefault(t, []).append(l)
        for t, ls in seen.items():
            if len(ls) < 2:
                continue
            # Бренд лежит в Name каждой локали по определению — не дубль.
            if all(t in name_tokens[l] for l in ls):
                continue
            cross.setdefault(t, {})[country] = ls

    if containers:
        print(f"\nКонтейнеры (name/subtitle скопированы, анализируются только keywords): "
              f"{', '.join(sorted(containers))}")
    if cross:
        print(f"\nДубли между локалями одной страны ({len(cross)} токенов).")
        print("Дубль ничего не добавляет там, где слово уже есть, но может работать в другой")
        print("стране того же поля; 🎲 = слово есть и в основной локали страны — копия во")
        print("вторичной осмысленна только как ставка на гипотезу 1 (вес основной выше).")
        for t in sorted(cross):
            parts = []
            for country, ls in cross[t].items():
                mark = '🎲' if PRIMARY.get(country) in ls else ''
                parts.append(f"{country}: {'+'.join(ls)}{mark}")
            print(f"  «{t}» — {'; '.join(parts)}")

    # --- итог
    if warnings:
        print(f"\nПредупреждения ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️  {w}")
    if errors:
        print(f"\nОшибки ({len(errors)}) — с ними не отправлять:")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    print("\nЖёстких ошибок нет." + ("" if not warnings else " Предупреждения выше — решения за тобой."))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
