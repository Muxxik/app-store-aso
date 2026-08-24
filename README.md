# app-store-aso

**App Store ASO skill for Claude Code — a field-tested methodology, not a keyword listicle.**
Metadata, keyword research, locale expansion, and honest measurement — with free scripts that replace paid ASO tools for the core loop. Built from real experiments and real App Store Connect data; every rule in here was paid for with a measurement.

*Русская версия — [ниже](#по-русски). The methodology core (SKILL.md, references) is currently in Russian — Claude reads it natively and works with you in any language.*

## What it does

When this skill is active, Claude follows a strict **diagnose-before-prescribing** workflow:

1. **Demand** — is anyone searching for this in that country? (Search Ads popularity index, ASC impressions by source)
2. **Visibility** — do you rank for the keys with confirmed demand?
3. **Conversion** — do people choose you when they see you?

…and only then touches your Name / Subtitle / Keywords. It knows the indexing model (tokens combine within one locale only, name outweighs keywords, merged vs. split word forms, regional spellings like *defence/defense*), the locale-to-country indexing map (e.g. the US store indexes 9 extra locales — each is +100 free keyword characters), and the traps: platform events masquerading as your growth, brand collisions in keyword exports, the empty-subtitle genre substitution.

## Scripts (no paid services required)

| Script | What it does |
|---|---|
| `store-query.sh suggest us "night surv"` | Live App Store autosuggest for any storefront — what people actually type |
| `store-query.sh apps us "tower defense rpg"` | Store search results with app IDs — competitor keyword bets in plain sight |
| `store-query.sh live <appId> us fr jp` | What's actually live per country, including the subtitle (or the genre the store substituted for a missing one) |
| `analyze.py asc <csv…>` | App Store Connect export analysis: periods, funnels, country ranking |
| `analyze.py event <csv> <csv>` | **Platform-event detector**: finds the date impressions stepped up across unrelated countries without downloads following — so you don't credit Apple's iOS release to your metadata |
| `analyze.py keywords <xlsx…>` | Competitor keyword export digest with brand-collision filtering |
| `validate-fields.py fields.txt` | Pre-submission package validator: char limits, underfilled keywords, syntax, duplicates within a locale **and across locales indexed in the same country** |

All scripts are stdlib-only Python 3 + bash + curl. The autosuggest and search endpoints are public but undocumented — treat them as a convenience, not a guarantee.

## Install

```bash
git clone https://github.com/Muxxik/app-store-aso.git ~/.claude/skills/app-store-aso
```

Then in Claude Code just start talking about your app's ASO, or invoke explicitly with `/app-store-aso`.

## Scope

App Store only. Google Play's indexing works differently — this methodology does not transfer.

---

<a name="по-русски"></a>

# По-русски

**ASO-скилл для Claude Code: методология, собранная на реальных замерах.**
Метаданные, подбор ключей, открытие локалей, честные замеры — плюс бесплатные скрипты, закрывающие основной цикл без платных ASO-сервисов.

## Что делает

Скилл заставляет Claude работать по правилу **«диагноз до решений»** — три вопроса по данным, а не по интуиции:

1. **Спрос** — ищут ли это в стране? (индекс Search Ads, показы из ASC с разбивкой по источнику)
2. **Видимость** — ранжируешься ли по ключам с подтверждённым спросом?
3. **Конверсия** — выбирают ли тебя, когда видят?

И только потом трогает Name / Subtitle / Keywords. Внутри — модель индексации (фраза собирается только из токенов одной локали, вес имени выше ключей, слитные/раздельные формы и региональные написания вроде defence/defense — разные токены), карта индексации локалей по странам (стор США индексирует 9 дополнительных локалей — каждая даёт +100 символов ключей) и ловушки: платформенные события, маскирующиеся под твой рост, брендовые коллизии в выгрузках, подстановка жанра вместо пустого сабтайтла.

## Скрипты

Все скрипты — голый Python 3 + bash + curl, без внешних библиотек. Таблица команд — в английской части выше; подробности — в `SKILL.md` и докстрингах.

## Установка

```bash
git clone https://github.com/Muxxik/app-store-aso.git ~/.claude/skills/app-store-aso
```

Дальше просто говори с Claude Code про ASO своего приложения — или вызывай явно через `/app-store-aso`.

## Границы

Только App Store. Google Play индексируется иначе — методология не переносится.

## Лицензия / License

MIT — см. [LICENSE](LICENSE).
