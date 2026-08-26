#!/usr/bin/env bash
# Запросы к публичным API App Store. Платные сервисы не нужны.
#
#   store-query.sh suggest <страна|storefrontId> "<префикс>"   — автосаджест
#   store-query.sh apps    <country> "<запрос>" [limit] — приложения в выдаче
#   store-query.sh live    <appId> <country> [country…] — что реально живёт в сторе
#
# suggest принимает код страны (us, de, jp…) или числовой ID стора;
# полная карта — в references/locales.md
# ВАЖНО: у автосаджеста жёсткие лимиты. Пауза 15–20 с между вызовами,
# иначе Apple молча вернёт пустой ответ, похожий на «ничего не найдено».

set -uo pipefail

enc() { python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$1"; }

# Код страны → ID стора. Проверенные на практике — без пометки;
# помеченные "?" не проверялись: при пустом ответе сначала прогони
# контрольный префикс what, чтобы отличить неверный ID от лимитов.
storefront_id() {
  case "$1" in
    us) echo 143441 ;;  fr) echo 143442 ;;  de) echo 143443 ;;
    gb|uk) echo 143444 ;;  ca) echo 143455 ;;  au) echo 143460 ;;
    it) echo 143450 ;;  ru) echo 143469 ;;  ua) echo 143492 ;;
    jp) echo 143462 ;;
    es) echo 143454 ;;  mx) echo "143468?" ;;  br) echo "143503?" ;;
    nz) echo "143461?" ;;  kr) echo "143466?" ;;  nl) echo "143452?" ;;
    pl) echo "143478?" ;;  tr) echo "143480?" ;;  in) echo "143467?" ;;
    *) echo "" ;;
  esac
}

case "${1:-}" in

suggest)
  sf="${2:?нужен код страны или ID стора}"; term="${3:?нужен префикс}"
  if ! [[ "$sf" =~ ^[0-9]+$ ]]; then
    mapped=$(storefront_id "$(echo "$sf" | tr '[:upper:]' '[:lower:]')")
    if [ -z "$mapped" ]; then
      echo "Неизвестный код страны «$sf». Знаю: us fr de gb ca au it ru ua jp es mx br nz kr nl pl tr in" >&2
      echo "Либо передай числовой ID стора напрямую (карта в references/locales.md)." >&2
      exit 1
    fi
    if [[ "$mapped" == *"?" ]]; then
      mapped="${mapped%\?}"
      echo "⚠️  ID $mapped для «$sf» не проверен на практике: пустой ответ может значить" >&2
      echo "   и неверный ID, и лимиты — сначала прогони контрольный префикс what." >&2
    fi
    sf="$mapped"
  fi
  body=$(curl -s -H "X-Apple-Store-Front: ${sf}-1,29" \
    "https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?clientApplication=Software&term=$(enc "$term")")
  hits=$(printf '%s' "$body" | grep -A1 '<key>term</key>' | grep -o '<string>[^<]*</string>' | sed 's/<[^>]*>//g')
  if [ -z "$hits" ]; then
    echo "(пусто) — проверь: не превышены ли лимиты (подожди 20 с) и верен ли ID стора."
    echo "Контрольный запрос заведомо популярного префикса: $0 suggest $sf what"
  else
    printf '%s\n' "$hits"
  fi
  ;;

apps)
  c="${2:?нужен код страны}"; term="${3:?нужен запрос}"; lim="${4:-10}"
  tmp=$(mktemp)
  curl -s "https://itunes.apple.com/search?country=${c}&entity=software&limit=${lim}&term=$(enc "$term")" >"$tmp"
  python3 - "$tmp" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if not d.get("resultCount"):
    print("(ничего не найдено)"); raise SystemExit
for i, r in enumerate(d["results"], 1):
    print(f'{i:>3}. {r["trackId"]}  {r["trackName"][:58]}')
    print(f'      {r.get("sellerName","")[:44]} | {", ".join(r.get("genres", [])[:2])}')
PY
  rm -f "$tmp"
  ;;

live)
  app="${2:?нужен id приложения}"; shift 2
  tmp=$(mktemp)
  for c in "$@"; do
    printf '%-4s ' "$c"
    curl -s "https://itunes.apple.com/lookup?id=${app}&country=${c}" >"$tmp"
    python3 - "$tmp" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if not d.get("resultCount"):
    print("недоступно в этом сторе"); raise SystemExit
r = d["results"][0]
print(f'{r.get("trackName")!r} | v{r.get("version")} | '
      f'{r.get("currentVersionReleaseDate","")[:10]} | '
      f'локали: {",".join(r.get("languageCodesISO2A", []))}')
PY
    # Subtitle API не отдаёт — берём из HTML витрины. У Apple живут две
    # вёрстки (старая: h2 после h1; новая: p class="subtitle") — пробуем обе.
    # Если обе мимо, это сигнал обновить regex, а не что сабтайтла нет.
    # Имя тоже берём из HTML: lookup API кэшируется дольше витрины и после
    # релиза может сутки отдавать прошлую версию — витрина первичнее.
    curl -sL "https://apps.apple.com/${c}/app/id${app}" >"$tmp"
    python3 - "$tmp" <<'PY'
import html, re, sys
t = open(sys.argv[1], encoding='utf-8', errors='replace').read()
h1 = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
name = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', h1.group(1))).split()) if h1 else '?'
m = (re.search(r'<p class="subtitle[^"]*"[^>]*>([^<]*)</p>', t)
     or re.search(r'<h1[^>]*>.*?</h1>\s*<h2[^>]*>([^<]*)</h2>', t, re.S))
sub = html.unescape(m.group(1)).strip() if m else 'не разобран (пустой или вёрстка изменилась)'
print(f'     витрина: {name!r} | subtitle: {sub}')
PY
    sleep 2
  done
  rm -f "$tmp"
  ;;

*)
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
  ;;
esac
