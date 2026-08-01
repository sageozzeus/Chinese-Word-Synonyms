# Chinese Word Synonyms — Config

Settings are edited in a **GUI dialog** (no JSON editing required):

- **Tools → Chinese Word Synonyms…**
- or **Tools → Add-ons → Chinese Word Synonyms → Config**

## General tab

| Setting | Default | Meaning |
| --- | --- | --- |
| Decks | All decks | Dropdown with checkboxes; empty list in storage = all decks |
| Word / Hanzi field | `Word` | Headword field on notes |
| Pinyin field | `Pinyin` | Reading (optional) |
| Meaning field | `Meaning` | Definition / English gloss used for synonym matching (required) |
| Max synonyms | `12` | Cap on synonyms shown in the panel |
| Include suspended | yes | Show notes whose cards are all suspended |
| Min word length | `1` | Minimum CJK length for synonym candidates |
| Show only on back | yes | Off = show full Synonyms panel on front and back during review |
| Show synonym counts | yes | Front card: Known (unsuspended) + Total Synonyms when Show only on back is on |
| Meaning delimiters | `; , \| / ； 、` | Checkboxes (+ optional Extra) for sense separators in the Meaning field |
| Rebuild Index | button | Scans decks and refreshes the meaning → notes index |

After changing decks, fields, or meaning delimiters, rebuild when prompted (or use **Rebuild Index** on this tab).

Advanced meaning-normalization knobs (`min_key_length`, `ignore_keys`, `strip_leading_to`) live in config defaults and are preserved on Save; edit via Add-ons config storage if you need to tweak them. Default `ignore_keys` drops filler/meta gloss tokens (`etc`, `sth`, `sb`, dictionary shorthand, …); installs still on the old three-item list are upgraded on merge.

## Appearance tab

Customize Synonyms panel look. Applies on the next answer flip (no rebuild).

| Setting | Default | Notes |
| --- | --- | --- |
| Max width | `100%` | e.g. `100%`, `36em`, `650px` — match your card template |
| Corner radius | `12` px | |
| Gap between cards | `0.65` em | Label in UI: **Card gaps** |
| Type sizes | title / word / pinyin | Relative `em` sizes |
| Colors | light + dark | 4×2 grid; background, border, mature, suspended |
| Custom CSS | empty | Advanced overrides for `.word-synonyms*` |

## About tab

Read-only. Version, license, changelog, and links (Anki page, Rate, GitHub Issues, repo, X).

`config.json` supplies defaults for first install. User values live in `meta.json`.
