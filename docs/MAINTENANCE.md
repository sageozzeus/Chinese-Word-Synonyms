# Maintenance Guide — Chinese Word Synonyms

This document is the source of truth for maintaining and extending the add-on. Read this before changing behavior. Sibling patterns live in `hanzi-relatives` / Chinese Character Relations — mirror glue, not character-index logic.

## What the add-on does

During review, when the **answer** is shown, the add-on:

1. Reads the current note’s configured **word** and **meaning** fields
2. Normalizes the meaning into one or more synonym keys
3. Looks up other notes in an in-memory inverted index that share those keys
4. Injects a **Synonyms** HTML panel under the card (does not edit notes or templates)

If there are no synonyms, nothing is injected (no empty box).

```
profile open / sync / Tools→Rebuild
        │
        ▼
  indexer.build()  ──►  meaning_key → [SynonymEntry, ...]   (RAM only)
        │
card_will_show (reviewAnswer)  + reviewer_did_show_answer fallback
        │
        ▼
  synonyms_for(meaning) → render_panel() → append / eval
        │
reviewer_did_show_question
        │
        ▼
  remove #word-synonyms-panel
```

## Repository layout

```
chinese-word-synonyms/
├── chinese_word_synonyms/      # THE add-on (this folder is what Anki loads)
│   ├── __init__.py             # Hooks + Tools menu + Config action
│   ├── manifest.json           # Offline install identity
│   ├── about_meta.py           # Version, author links, changelog (About tab)
│   ├── config.json             # Default config (Anki merges user meta.json)
│   ├── config.md               # Short help text
│   ├── config_dialog.py        # GUI settings (General / Appearance / About)
│   ├── cjk.py                  # CJK extract / HTML strip
│   ├── meaning.py              # Meaning normalize / split / keys
│   ├── indexer.py              # Build + query synonym index
│   ├── render.py               # HTML/CSS for Synonyms panel
│   ├── reviewer.py             # Answer/question hooks + injection
│   └── browser.py              # pycmd → Browser
├── preview/
│   ├── preview.html            # Browser UI sandbox — card panel
│   └── config-preview.html     # Settings dialog mock
├── docs/
│   ├── MAINTENANCE.md          # This file
│   ├── TESTING.md              # Manual QA checklist
│   └── BUG_SOLUTIONS.md        # Known fixes / Qt gotchas
├── tests/
│   └── test_meaning.py         # Meaning normalizer unit tests
├── scripts/
│   ├── link-anki-addon.sh
│   └── package-ankiaddon.sh
├── LICENSE                     # MIT
└── README.md                   # End-user install & usage
```

## Development setup (symlink)

```bash
chmod +x scripts/link-anki-addon.sh
./scripts/link-anki-addon.sh
```

Then: edit in this repo → quit Anki fully (**Cmd+Q**) → reopen → flip a card.

Anki loads Python at startup. There is **no hot reload**.

## Module map (change guide)

| Want to change… | Edit |
| --- | --- |
| Meaning → keys | `meaning.py` |
| How fields/decks are scanned | `indexer.py` → `SynonymIndex.build` |
| Sort / filter / caps of synonyms | `indexer.py` → `synonyms_for`, `_sort_key` |
| Panel markup / CSS | `render.py` → `PANEL_CSS`, `render_panel` + sync `preview/preview.html` |
| When panel appears / clears | `reviewer.py` |
| Click synonym → Browser | `browser.py` + `pycmd` in `render.py` PANEL_JS |
| Settings GUI | `config_dialog.py` + `defaults.py` + `about_meta.py` |
| Menu / rebuild / Config button | `__init__.py` |
| Defaults | `config.json` + `config.md` |

## Config contract

| Key | Type | Behavior |
| --- | --- | --- |
| `decks` | `string[]` | Empty → all notes via SQL. Else union per deck. |
| `fields.word` | string | Required; missing → skip note. |
| `fields.pinyin` | string | Optional. |
| `fields.meaning` | string | Required; missing/empty → skip note. |
| `max_synonyms` | int | Cap after filters. |
| `include_suspended` | bool | Applied at **lookup** (no rebuild). |
| `candidate_min_length` | int | Min CJK length on candidates. |
| `show_only_on_back` | bool | On = answer only. |
| `meaning_split_delimiters` | string | Pipe-separated delimiters; `\|` itself via `\|\|`. |
| `min_key_length` | int | Drop short keys. |
| `ignore_keys` | `string[]` | Drop useless keys like `something`. |
| `strip_leading_to` | bool | Strip leading `to ` on short verb glosses. |
| `ui` | object | Appearance; applies next flip. |

## Index algorithm

```
for each note in target decks:
  word = strip_html(note[word_field])
  meaning = strip_html(note[meaning_field])
  keys = normalize_meaning(meaning)
  entry = SynonymEntry(...)
  for key in keys:
    index[key].append(entry)   # dedupe by note_id
sort each list: mature → learning → suspended, then cjk_length, word
```

**Lookup:** keys from current meaning → union candidates → exclude note_id / headword / CJK → filters → sort → `max_synonyms`.

Do **not** scan the collection inside answer hooks.

## Coexistence with Character Relations

Unique package, Tools label, `#word-synonyms-panel`, `.word-synonyms*`, `word_synonyms_browse:`. Never reuse Relatives IDs.

## Hooks (Anki 23.10+)

| Hook | Purpose |
| --- | --- |
| `main_window_did_init` | Tools → Synonyms… |
| `profile_did_open` | Build index (silent) |
| `sync_did_finish` | Rebuild + tooltip |
| `card_will_show` | Primary panel inject |
| `reviewer_did_show_answer` | Fallback inject + bind JS |
| `reviewer_did_show_question` | Clear if back-only |
| `webview_did_receive_js_message` | Browse |
| `setConfigAction` | GUI Config |

## Packaging `.ankiaddon`

```bash
chmod +x scripts/package-ankiaddon.sh
./scripts/package-ankiaddon.sh
```

Archive root must contain `__init__.py` (no wrapping folder). Exclude `__pycache__`, `meta.json`, `.DS_Store`.

## Automated tests (no Anki)

```bash
cd /Users/urfan/Desktop/apps-websites/chinese-word-synonyms
python3 -m unittest tests.test_meaning -v
```

## Debugging on Mac

```bash
/Applications/Anki.app/Contents/MacOS/anki
```

Quit fully with **Cmd+Q** after code changes.
