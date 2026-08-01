# Bug solutions — Chinese Word Synonyms

Imported and adapted from sibling **Chinese Character Relations**. Same Anki pitfalls apply; CSS/`pycmd`/menu names differ so both add-ons can coexist.

## About tab Name shows “Chinese Word” (truncated)

**Symptom:** About → Name reads `Chinese Word` instead of `Chinese Word Synonyms`.

**Cause:** `ADDON_NAME` was already correct. The About value `QLabel` used `setWordWrap(True)` inside a scroll area whose content has horizontal `Ignored` size policy, so the name wrapped and the second line (`Synonyms`) was clipped.

**Fix:** `_meta_row` keeps meta values on one line (`setWordWrap(False)`), expanding size policy, tooltip with full text. Dialog min width 520 / resize 560. Menu, window title, and rebuild tooltip read `about_meta.ADDON_NAME`.

---

## Synonyms title larger / left-aligned vs Relatives

**Symptom:** “Synonyms” sits top-left and looks bigger than Relatives’ top-right label.

**Cause:** Title used `--ws-char-size` (Appearance default `1.05em`) instead of Relatives’ fixed `0.9em`, and the heading was alone in a `justify-content: space-between` row (first flex child stays left). Relatives gets right alignment because the character is on the left and the title is the second child.

**Fix:** `.word-synonyms-heading` uses `justify-content: flex-end`; `.word-synonyms-title` uses fixed `font-size: 0.9em` (same as Relatives). Keep `preview/preview.html` in sync.

---

## Indexed 0 notes, 0 meaning keys

**Symptom:** Rebuild Index tooltip shows `indexed 0 notes, 0 meaning keys`.

**Root causes (in order of likelihood):**

1. **Wrong Meaning field** — defaults to `Meaning`, but decks may use `Definition`, `English`, `Gloss`, `Translation`, `释义`, `Back`, etc.
2. **Wrong Word / Hanzi field** — same as Relatives; notes skipped before meaning is read.
3. **Empty note discovery** — on some Anki builds `col.find_notes("")` returns `[]`. Fixed by preferring `SELECT id FROM notes`.
4. **Deck filter** — Settings has specific decks checked that contain no matching notes.
5. **No usable keys** — meanings that only produce ignored/short keys after normalization.

**Fix shipped:**

- Discover all notes via SQL first (`select id from notes`), with search fallbacks (`*`, `deck:*`).
- Case-insensitive field match + fallbacks for Word and Meaning.
- When index stays empty, show a dialog with scan/skip counts and which note types lack fields.

**User action:** Tools → Chinese Word Synonyms… → set **Word / Hanzi** and **Meaning** → **Rebuild Index** on the General tab.

---

## Index OK but nothing on card back

**Symptom:** Rebuild reports hundreds of notes/keys, but flipping to the answer shows no Synonyms panel.

**Root causes:**

1. **Reviewer field mismatch** — indexer accepted fallbacks but the answer hook required exact field names.
2. **Fragile `web.eval` injection** — Anki’s answer fade/DOM update can wipe content inserted in `reviewer_did_show_answer`.
3. **No shared keys** — current card’s meaning doesn’t overlap any other indexed note after normalization.
4. **Empty meaning on current card** — panel is intentionally omitted.

**Fix shipped:**

- Reviewer uses the same `resolve_field` + fallbacks as the indexer.
- Primary injection via `gui_hooks.card_will_show` (`reviewAnswer`) — HTML appended before paint.
- `web.eval` kept only as a fallback if the panel id is missing.
- Exclude current note by `note_id` as well as headword text / CJK sequence.

**User action:** Restart Anki (**Cmd+Q**), rebuild once, review a word that shares a Meaning sense with another note and flip.

---

## Raw JSON config opened instead of GUI

**Cause:** `setConfigAction` returned `False` or was not registered.

**Fix:** `open_config()` returns `True` after showing the dialog.

---

## Click synonym opens broken Browser search

**Cause:** `dialogs.open("Browser", mw, search="nid:…")` passes a string; Anki does `search_for_terms(*search)`, which unpacks the string into characters.

**Fix:** Pass a one-element tuple: `search=(f"nid:{note_id}",)`.

---

## Multi-deck config misses some decks

**Cause:** Unquoted `deck:` fallback only ran when the whole `note_ids` set was still empty, so after the first deck contributed IDs, later decks that needed the fallback were skipped.

**Fix:** Resolve each deck independently via `_note_ids_for_deck` (quoted search → unquoted → SQL by deck id), then union the results.

---

## Settings toggles look like solid blue pills / deck arrow misaligned

**Cause:** Anki’s Qt stylesheet fights `QCheckBox::indicator` “toggle” CSS and `QToolButton::menu-indicator`.

**Fix:** Use a custom `ToggleSwitch` (`QAbstractButton` + `paintEvent`) and a `QFrame` deck picker with a centered `▾` label.

---

## About tab metadata looks centered

**Cause:** On macOS, `QFormLayout` defaults to horizontal center form alignment.

**Fix:** Use `_about_form()` — `setFormAlignment(AlignLeft | AlignTop)`, left label alignment.

---

## Settings dialog has horizontal scrollbar / fields too wide

**Cause:** `QComboBox` defaults to sizing from longest item; deck summary `QLabel` reported a huge min width.

**Fix:** `AdjustToMinimumContentsLengthWithIcon`, `minimumWidth(0)`, elide deck summary text, disable horizontal scroll on the tab `QScrollArea`.

---

## Both Character Relations and Word Synonyms installed

**Symptom:** CSS or click handlers fight each other; wrong Browser open; menus collide.

**Fix (by design):**

| Concern | Character Relations | Word Synonyms |
| --- | --- | --- |
| Package | `chinese_char_relations` | `chinese_word_synonyms` |
| Tools menu | Character Relations… | Chinese Word Synonyms… |
| Panel id | `#char-relations-panel` | `#word-synonyms-panel` |
| CSS prefix | `.char-relations*` | `.word-synonyms*` |
| pycmd | `char_relations_browse:` | `word_synonyms_browse:` |

Do not reuse Relatives class names or command prefixes.

---

## Front Known/Total card missing on question

**Symptom:** After switching from the old count pill to the Known/Total front card, the question side shows nothing even when synonyms exist on the back.

**Cause:** `reviewer_did_show_question` → `on_show_question` cleaned up leftover answer-panel DOM and also removed `#word-synonyms-front-card` / its styles. That runs *after* `card_will_show` injects the front summary, so the card was deleted immediately.

**Fix:** `on_show_question` only removes the answer panel (`#word-synonyms-panel` and related styles). Leave the front summary alone; Anki replaces `#qa` on the next flip.
