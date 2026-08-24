#!/usr/bin/env python3
"""Разбор выгрузок App Store Connect и ASO-сервисов. Внешних библиотек не требует.

  analyze.py asc <показы.csv> [загрузки.csv] [просмотры.csv]
      Агрегация по периодам и странам, воронка показ→страница→загрузка.
      Границы периодов задаются в PERIODS ниже — впиши даты своих релизов
      и внешних событий (например, выхода iOS), иначе сравнение до/после поедет.

  analyze.py rank <показы_по_странам.csv>
      Рейтинг стран за период: показы, доля, в день.

  analyze.py event <показы_по_странам.csv> [загрузки_по_странам.csv]
      Поиск платформенных событий: даты, когда показы ступенькой выросли
      сразу в нескольких несвязанных странах. Если при этом загрузки не
      выросли пропорционально — это событие Apple (релиз iOS и т.п.),
      а не эффект метаданных; такую ступеньку исключают из сравнения
      до/после. Печатает кандидатов, множители по странам и чистый период.

  analyze.py xlsx <файл.xlsx> [--rows N]
      Чтение xlsx без openpyxl (это zip с xml).

  analyze.py keywords <файл.xlsx> [файл.xlsx ...] [--all]
      Сводка выгрузок ключей конкурентов: индекс, трафик, позиции всех
      участников по каждому ключу.
      По умолчанию отсеивает коллизии с чужими приложениями: если по ключу
      НИ ОДНО отслеживаемое приложение не входит в топ-20, это не наша ниша,
      а совпадение по общему токену. --all отключает фильтр.
"""
import csv, sys, re, zipfile, datetime
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

# Впиши сюда свои даты: релизы метаданных и внешние события.
PERIODS = [
    # ("до релиза",      "2026-06-21", "2026-07-09"),
    # ("после релиза",   "2026-07-10", "2026-07-26"),
    # ("после iOS 26.6", "2026-07-27", "2026-08-03"),
]

# Дополнительный чёрный список поверх автофильтра (см. cmd_keywords).
# Это пример из одной конкретной ниши — ЗАМЕНИ на брендовые коллизии своей:
# чужие приложения, которые цепляются за общие с тобой токены.
JUNK = ('get your guide', 'get contact', 'getcontact', 'contacts', 'photo recovery')

# Ключ считается своим, только если хоть кто-то из отслеживаемых
# приложений стоит по нему не глубже этой позиции.
RELEVANT_TOP = 20


def read_csv(path):
    """ASC-выгрузка: шапка, потом строка 'Дата', потом данные по дням."""
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    hdr, data = None, {}
    for r in rows:
        if r and r[0] == 'Дата':
            hdr = [c.split('— ')[-1].strip() for c in r[1:]]
            continue
        if hdr and r and '.' in r[0]:
            d = datetime.datetime.strptime(r[0], '%d.%m.%Y').date()
            data[d] = {hdr[i]: float(r[1 + i] or 0) for i in range(min(len(hdr), len(r) - 1))}
    return hdr or [], data


def _colidx(ref):
    """A→0, B→1, …, AA→26. Из ссылки на ячейку вида 'G12'."""
    m = re.match(r'([A-Z]+)', ref or '')
    if not m:
        return None
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path, per_sheet=False):
    """Две ловушки формата, на обеих легко обжечься:
    1. Пустые ячейки физически отсутствуют в xml — читать подряд нельзя,
       значения съедут влево. Раскладываем по индексу из атрибута r.
    2. Строки бывают либо в общей таблице sharedStrings, либо инлайн
       (t="inlineStr"). Выгрузки одного и того же сервиса встречаются в обоих
       вариантах — поддерживаем оба, иначе получишь KeyError или пустые ячейки.

    per_sheet=True вернёт {имя листа: строки} — многие выгрузки кладут
    каждую страну на свой лист.
    """
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(f'{NS}si'):
            shared.append(''.join(t.text or '' for t in si.iter(f'{NS}t')))

    def cellval(c):
        t = c.get('t')
        if t == 'inlineStr':
            return ''.join(x.text or '' for x in c.iter(f'{NS}t'))
        v = c.find(f'{NS}v')
        if v is None:
            return ''
        return shared[int(v.text)] if t == 's' else v.text

    names = re.findall(r'<sheet name="([^"]+)"', z.read('xl/workbook.xml').decode('utf-8'))
    sheets = sorted((n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$', n)),
                    key=lambda n: int(re.search(r'(\d+)', n).group(1)))
    out = {}
    for idx, sh in enumerate(sheets):
        rows = []
        for row in ET.fromstring(z.read(sh)).iter(f'{NS}row'):
            cells = {}
            for c in row.findall(f'{NS}c'):
                i = _colidx(c.get('r'))
                if i is not None:
                    cells[i] = cellval(c)
            if cells:
                rows.append([cells.get(i, '') for i in range(max(cells) + 1)])
        out[names[idx] if idx < len(names) else sh] = rows
    if per_sheet:
        return out
    return [r for rows in out.values() for r in rows]


def num(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def cmd_asc(paths):
    imp = read_csv(paths[0])[1]
    dl = read_csv(paths[1])[1] if len(paths) > 1 else {}
    pv = read_csv(paths[2])[1] if len(paths) > 2 else {}
    countries = sorted({c for v in imp.values() for c in v},
                       key=lambda c: -sum(v.get(c, 0) for v in imp.values()))
    periods = PERIODS or [("весь период",
                           min(imp).isoformat(), max(imp).isoformat())]
    for name, a, b in periods:
        a = datetime.date.fromisoformat(a); b = datetime.date.fromisoformat(b)
        days = (b - a).days + 1
        print(f"\n=== {name}  {a}…{b}  ({days} дн.)")
        print(f"{'страна':<18}{'показы/д':>10}{'стр/д':>8}{'загр/д':>8}{'показ→загр':>12}")
        for c in countries:
            s = lambda d: sum(v.get(c, 0) for k, v in d.items() if a <= k <= b)
            i, p, g = s(imp), s(pv), s(dl)
            if not i and not g:
                continue
            conv = f"{100 * g / i:.1f}%" if i else "—"
            print(f"{c:<18}{i/days:>10.1f}{p/days:>8.1f}{g/days:>8.1f}{conv:>12}")
    if not PERIODS:
        print("\n⚠️  PERIODS пуст — впиши даты релизов и внешних событий в начало скрипта,"
              "\n    иначе эффект изменений не отделить от фона.")


def cmd_event(paths):
    """Ступенька ищется сравнением средних за окно до и после каждой даты.
    Одиночные всплески на день так отсеиваются сами. Критерий события:
    в ≥4 странах средние выросли в ≥2.5 раза до уровня ≥2/д — порог по
    уровню отсеивает шум малых чисел (0.1/д → 1/д это ещё не ступенька)."""
    WIN, MULT, MIN_COUNTRIES, MIN_AFTER = 7, 2.5, 4, 2.0
    imp = read_csv(paths[0])[1]
    dl = read_csv(paths[1])[1] if len(paths) > 1 else {}
    days = sorted(imp)
    countries = sorted({c for v in imp.values() for c in v})

    def mean(data, country, a, b):
        span = [d for d in days if a <= d <= b]
        if not span:
            return 0.0, 0
        return sum(data.get(d, {}).get(country, 0) for d in span) / len(span), len(span)

    def jumps(d):
        out = []
        for c in countries:
            before, nb = mean(imp, c, d - datetime.timedelta(days=WIN), d - datetime.timedelta(days=1))
            after, na = mean(imp, c, d, d + datetime.timedelta(days=WIN - 1))
            if nb < 4 or na < 4 or after < MIN_AFTER:
                continue
            if after / max(before, 0.1) >= MULT:
                out.append((c, before, after))
        return out

    cand = [(d, jumps(d)) for d in days]
    cand = [(d, j) for d, j in cand if len(j) >= MIN_COUNTRIES]
    if not cand:
        print(f"Ступенек не найдено (критерий: ≥{MIN_COUNTRIES} стран выросли ≥×{MULT} "
              f"по средним за {WIN} дн.). Период чист, сравнивать до/после можно целиком.")
        return
    # Соседние даты описывают одну и ту же ступеньку — оставляем в кластере
    # ту, где стран-скачков больше всего.
    best = []
    for d, j in cand:
        if best and (d - best[-1][0]).days <= WIN:
            if len(j) > len(best[-1][1]):
                best[-1] = (d, j)
        else:
            best.append((d, j))

    for d, j in best:
        print(f"\n=== кандидат: {d.strftime('%d.%m.%Y')} — ступенька в {len(j)} странах")
        print(f"{'страна':<22}{'до/д':>8}{'после/д':>9}{'множитель':>11}")
        for c, b, a in sorted(j, key=lambda x: -x[2]):
            print(f"{c:<22}{b:>8.1f}{a:>9.1f}{a / max(b, 0.1):>10.1f}x")
        ti_b = sum(mean(imp, c, d - datetime.timedelta(days=WIN), d - datetime.timedelta(days=1))[0] for c in countries)
        ti_a = sum(mean(imp, c, d, d + datetime.timedelta(days=WIN - 1))[0] for c in countries)
        ti_r = ti_a / max(ti_b, 0.1)
        line = f"показы суммарно: {ti_b:.0f}/д → {ti_a:.0f}/д (×{ti_r:.1f})"
        if dl:
            dc = sorted({c for v in dl.values() for c in v})
            td_b = sum(mean(dl, c, d - datetime.timedelta(days=WIN), d - datetime.timedelta(days=1))[0] for c in dc)
            td_a = sum(mean(dl, c, d, d + datetime.timedelta(days=WIN - 1))[0] for c in dc)
            td_r = td_a / max(td_b, 0.1)
            line += f"; загрузки: {td_b:.1f}/д → {td_a:.1f}/д (×{td_r:.1f})"
            if ti_r >= 1.5 and td_r < ti_r / 2:
                line += "\n⚠️  Показы скакнули, загрузки нет — похоже на платформенное событие, не на твой результат."
            elif td_r >= ti_r:
                line += "\n    Загрузки выросли не слабее показов — на платформенное событие не похоже."
        else:
            line += "\n    Загрузки не переданы — без них не отличить событие Apple от реального роста."
        print(line)
        print(f"Чистый период для замера до/после: {min(days).strftime('%d.%m.%Y')}…{(d - datetime.timedelta(days=1)).strftime('%d.%m.%Y')},")
        print(f"либо сравнивай с после-событийным уровнем начиная с {d.strftime('%d.%m.%Y')}.")


def cmd_rank(path):
    hdr, data = read_csv(path)
    tot = {h: sum(v.get(h, 0) for v in data.values()) for h in hdr}
    total, days = sum(tot.values()), len(data) or 1
    print(f"дней {days}, стран {len(hdr)}, показов {total:.0f}\n")
    print(f"{'#':<4}{'страна':<30}{'показы':>9}{'/день':>8}{'доля':>7}")
    for i, (h, v) in enumerate(sorted(tot.items(), key=lambda x: -x[1]), 1):
        if v <= 0:
            continue
        print(f"{i:<4}{h:<30}{v:>9.0f}{v/days:>8.1f}{100*v/total:>6.1f}%")


def cmd_keywords(paths):
    show_all = '--all' in paths
    paths = [p for p in paths if p != '--all']
    kw = {}
    for f in paths:
        rows = read_xlsx(f)
        hdr = rows[0]
        pos_cols = [(i, str(h).replace('Позиция', '').strip())
                    for i, h in enumerate(hdr) if 'Позиция' in str(h)]
        ai = next((i for i, h in enumerate(hdr) if 'Search Ads' in str(h)), None)
        for r in rows[1:]:
            if not r or not r[0]:
                continue
            k = r[0].strip().lower()
            if any(j in k for j in JUNK):
                continue
            e = kw.setdefault(k, {'a': None, 't': None, 'pos': {}})
            if num(r[1]):
                e['t'] = max(e['t'] or 0, num(r[1]))
            if ai is not None and len(r) > ai and num(r[ai]):
                e['a'] = max(e['a'] or 0, num(r[ai]))
            for i, nm in pos_cols:
                if len(r) > i and num(r[i]):
                    e['pos'][nm] = min(e['pos'].get(nm, 10**6), num(r[i]))
    total = len(kw)
    if not show_all:
        kw = {k: v for k, v in kw.items()
              if v['pos'] and min(v['pos'].values()) <= RELEVANT_TOP}
    rel = sorted(kw.items(), key=lambda x: -(x[1]['a'] or 0))
    print(f"файлов {len(paths)}, ключей {total}, "
          f"относятся к нише {len(kw)} (кто-то в топ-{RELEVANT_TOP})\n")
    for k, v in rel[:40]:
        if not v['a'] and not v['t']:
            continue
        print(f"■ «{k}»  индекс {v['a'] or '—'}, трафик {v['t'] or '—'}")
        for nm, p in sorted(v['pos'].items(), key=lambda x: x[1]):
            print(f"     #{p:<5} {nm[:50]}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'asc':
        cmd_asc(args)
    elif cmd == 'rank':
        cmd_rank(args[0])
    elif cmd == 'event':
        cmd_event(args)
    elif cmd == 'keywords':
        cmd_keywords(args)
    elif cmd == 'xlsx':
        n = int(args[args.index('--rows') + 1]) if '--rows' in args else 15
        for r in read_xlsx(args[0])[:n]:
            print(r)
    else:
        print(__doc__)
        sys.exit(1)
