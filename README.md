# app-store-aso

**App Store ASO skill for Claude Code — a field-tested methodology, not a keyword listicle.**
Metadata, keyword research, locale expansion, and honest measurement — with free scripts that replace paid ASO tools for the core loop. Built on three live release cycles of two real apps (a 14-locale utility and a 9-locale game), with App Store Connect exports and ASO-service positions as evidence. **Every rule in here was paid for with a measurement — and the ones that failed are recorded as failures.**

*Русская версия — [ниже](#по-русски). The methodology core (SKILL.md, references) is in Russian — Claude reads it natively and works with you in any language.*

## What it does

When this skill is active, Claude follows a strict **diagnose-before-prescribing** workflow:

1. **Demand** — is anyone searching for this in that country? (Search Ads popularity index, ASC impressions by source)
2. **Visibility** — do you rank for the keys with confirmed demand?
3. **Conversion** — do people choose you when they see you?

…and only then touches your Name / Subtitle / Keywords. Each step of the workflow comes with its own trap and the check that closes it — from "run the platform-event detector before any before/after comparison" to "re-check the live storefront 2–3 days after release, because App Store Connect can silently drop a locale's Name".

## Rules that were paid for

A sample of what's inside, each with the measurement behind it:

- **Field weight is Name > Subtitle > Keywords — measured.** Phrases placed in a new Name reached top-3 within 4 weeks in five locales; a phrase living only in Subtitle sat at #22 while the same locale's Name phrase was #3; keyword-only phrases reach #1 only against 3–7 competing apps.
- **A fresh-metadata "honeymoon".** Positions in weeks 1–2 are inflated; the settled level at week 3–4 is 1.5–3× lower (#73 → #198). Early snapshots diagnose indexing, they don't measure effect.
- **Don't put a commoditized phrase in your Name.** The niche's biggest phrase moved from Keywords to Name — and fell from #29 to #141, because 17 of the top-20 apps carried it in their names, 11 with zero ratings. When everyone wears the phrase, the name stops being a differentiator.
- **A live local term is not your intent.** Terms with 250-app ecosystems gave ×8–19 impressions and **zero downloads** when the ecosystem belonged to another genre. The same move in a niche where the term matched the product converted at 13%.
- **Local name vs. English anchor is decided by demand ratio, not by rule.** Both constructions converted at ~13% when they matched the market's search language (Spain: local term dominates → local name; Italy: English 103:1 → English anchor).
- **Primary locale outweighs secondary — confirmed twice.** The same English term matched via secondary en-GB at #8, then #3 once it sat in the primary locale's Name; a core added to en-AU keywords moved a phrase from >100 to #42.
- **Countries without your locale are a control group.** When a release coincides with an iOS launch, the control group isolates your contribution (target countries ×3.9, control ×2.6 → the package ≈ ×1.5).
- **Slow markets exist.** Two locales sat near zero for 3–5 weeks and then converted at 10% — don't bury a locale before week 5–6.
- Plus the indexing model (phrases form inside one locale only; diacritics are normalized, *defence/defense* are not; punctuation in Name doesn't change tokens), a verified locale-to-country indexing map with storefront IDs for 20 stores, and a Search Ads popularity index that Apple quietly floored at ~44 — and how to read it anyway.

## How rules get in

A rule enters the skill as a **hypothesis with a pass/fail criterion written before the release** ("local-term positions appear and conversion ≥ the US level within 4 weeks, otherwise move the English anchor into Name"). It becomes a rule only after the measurement — with the numbers attached — or gets recorded as refuted. The skill keeps a live list of **open hypotheses** with their criteria, so the next user can test rather than trust. This is the difference from a guide: a guide tells you what works; this tells you what was measured, how, and what is still unknown.

## Scripts (no paid services required)

| Script | What it does |
|---|---|
| `store-query.sh suggest us "night surv"` | Live App Store autosuggest for any storefront — what people actually type. Accepts country codes (20 verified storefront IDs built in) |
| `store-query.sh apps us "tower defense rpg"` | Store search results with app IDs — competitor keyword bets in plain sight. Tells you plainly when Apple rate-blocks the endpoint (HTTP 403) and what to use instead |
| `store-query.sh live <appId> us fr jp` | What's actually live per country: name and subtitle from the storefront HTML (the API caches a day behind) — catches silently dropped fields and the genre the store substitutes for an empty subtitle |
| `store-query.sh versions <appId> fr` | Full version history of any app with dates and release notes, pulled from the store page HTML (the page shows only the latest). For diagnosing a downloads drop at stable rankings: who in the top 3 shipped new screenshots, and when |
| `analyze.py event <impressions.csv> <downloads.csv>` | **Platform-event detector**: finds the date impressions stepped up across unrelated countries without downloads following, and tells you the clean window. Run before any before/after comparison |
| `analyze.py asc <csv…>` | App Store Connect export analysis: periods, funnels, country ranking |
| `analyze.py keywords <xlsx…>` | Competitor keyword export digest with brand-collision filtering |
| `validate-fields.py fields.txt` | Pre-submission package validator: char limits, underfilled keywords, syntax, duplicates within a locale **and across locales indexed in the same country**, container locales. It found two burned duplicates in a package assembled "clean" by hand |

All scripts are stdlib-only Python 3 + bash + curl. The autosuggest and search endpoints are public but undocumented — treat them as a convenience, not a guarantee.

## Install

```bash
git clone https://github.com/Muxxik/app-store-aso.git ~/.claude/skills/app-store-aso
```

Claude Code picks the skill up on the next launch. From then on just talk about your app's App Store visibility — the skill triggers on the topic, not the word "ASO" — or invoke it explicitly with `/app-store-aso`.

## Scope

App Store only. Google Play's indexing works differently — this methodology does not transfer.

---

<a name="по-русски"></a>

# По-русски

**ASO-скилл для Claude Code: методология, собранная на реальных замерах.**
Метаданные, подбор ключей, открытие локалей, честные замеры — плюс бесплатные скрипты, закрывающие основной цикл без платных ASO-сервисов. Построено на трёх живых циклах релизов двух реальных приложений (утилита на 14 локалей и игра на 9) — с выгрузками App Store Connect и позициями из ASO-сервиса в качестве доказательств. **Каждое правило оплачено замером — а то, что не сработало, записано как не сработавшее.**

## Что делает

Скилл заставляет Claude работать по правилу **«диагноз до решений»** — три вопроса по данным, а не по интуиции:

1. **Спрос** — ищут ли это в стране? (индекс Search Ads, показы из ASC с разбивкой по источнику)
2. **Видимость** — ранжируешься ли по ключам с подтверждённым спросом?
3. **Конверсия** — выбирают ли тебя, когда видят?

И только потом трогает Name / Subtitle / Keywords. У каждого шага — своя ловушка и проверка, которая её закрывает: от «прогони детектор платформенных событий до любого сравнения до/после» до «через 2–3 дня после релиза перепроверь витрину — App Store Connect умеет молча терять Name локали».

## Правила, оплаченные замерами

Несколько из тех, что внутри, — с замером за каждым:

- **Вес полей Name > Subtitle > Keywords — измерен.** Фразы из нового Name встали в топ-3 за 4 недели в пяти локалях; фраза только из Subtitle стояла #22 при Name-фразе той же локали на #3; из одних keywords до #1 доходят только при 3–7 конкурентах.
- **«Медовый месяц» свежих метаданных.** Позиции 1–2 недели завышены, осевший уровень на 3–4 неделе ниже в 1.5–3 раза (#73 → #198). Ранний срез диагностирует индексацию, но не меряет эффект.
- **Не ставь в Name коммодитизированную фразу.** Крупнейшая фраза ниши переехала из Keywords в Name — и упала с #29 на #141: 17 из 20 приложений в топе носили её в имени, 11 — с нулём оценок.
- **Живой местный термин ≠ твой интент.** Термины с экосистемами по 250 приложений дали ×8–19 показов и **ноль загрузок**, когда экосистема принадлежала другому жанру. Тот же приём в нише, где термин совпадал с продуктом, конвертил на 13%.
- **Местное имя или английский якорь — решает соотношение спроса.** Обе конструкции дали ~13% конверсии, когда совпали с языком рынка (Испания — местное имя; Италия, где английский в 103 раза больше, — английский якорь).
- **Основная локаль весит больше вторичной — подтверждено дважды.** Один и тот же английский термин матчился через вторичную en-GB на #8, а из Name основной локали — #3; ядро в en-AU keywords подняло фразу с >100 на #42.
- **Страны без твоей локали — контрольная группа.** Когда релиз совпал с выходом iOS, контроль отделил твой вклад (целевые ×3.9, контроль ×2.6 → пакет ≈ ×1.5).
- **Медленные рынки бывают.** Две локали стояли на нуле 3–5 недель, потом конвертили на 10% — не хорони локаль раньше 5–6 недели.
- Плюс модель индексации (фраза собирается только внутри одной локали; диакритика нормализуется, defence/defense — нет; пунктуация в Name токенов не меняет), проверенная карта индексации локалей по странам с ID 20 сторов и индекс Search Ads, которому Apple тихо подняла пол до ~44, — и как его всё равно читать.

## Как правила попадают внутрь

Правило входит в скилл как **гипотеза с критерием, записанным до релиза** («позиции по местному термину появятся и конверсия ≥ уровня США за 4 недели, иначе переносим английский якорь в Name»). Правилом оно становится только после замера — с цифрами — или записывается как опровергнутое. В скилле живёт список **открытых гипотез** с критериями, чтобы следующий пользователь проверял, а не верил. В этом отличие от гайда: гайд говорит, что работает; здесь — что измерено, как, и что пока неизвестно.

## Скрипты

Все скрипты — голый Python 3 + bash + curl, без внешних библиотек. Таблица команд — в английской части выше; подробности — в `SKILL.md` и докстринге каждого скрипта.

## Установка

```bash
git clone https://github.com/Muxxik/app-store-aso.git ~/.claude/skills/app-store-aso
```

Claude Code подхватит скилл при следующем запуске. Дальше просто говори про видимость приложения в App Store — скилл срабатывает на тему, а не на слово «ASO» — или вызывай явно через `/app-store-aso`.

## Границы

Только App Store. Google Play индексируется иначе — методология не переносится.

## Лицензия / License

MIT — см. [LICENSE](LICENSE).
