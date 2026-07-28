# Manual testing — Chinese Word Synonyms

Run these after any change to indexing, rendering, or hooks. Use a Chinese vocab deck with a Meaning/English field and at least two notes that share a sense (e.g. 快乐 / 高兴 both “happy”).

## Setup

1. Symlink or install the add-on; restart Anki (**Cmd+Q**, reopen)
2. Config Word + Meaning fields to match your note type
3. **Tools → Chinese Word Synonyms…** → General → **Rebuild Index** — tooltip should show note/key counts

## Cases

### 0. Settings GUI

- Open **Tools → Chinese Word Synonyms…**
- **Expect:** dialog with General / Appearance / About tabs (not a JSON editor)
- Change a field, Save, rebuild when asked (or use **Rebuild Index** on General)
- Open **Tools → Add-ons → Chinese Word Synonyms → Config**
- **Expect:** same GUI dialog (not raw JSON)

### 1. Shared meaning

- Review a note whose Meaning normalizes to a key shared by another note (e.g. happy)
- Flip to answer
- **Expect:** Synonyms section lists other headwords (高兴, 开心, …)
- **Expect:** Current word itself is not listed

### 2. Multi-sense meaning

- Note with Meaning `happy; glad` where other notes match either key
- **Expect:** union of matches for both keys (deduped by note_id / headword)

### 3. No empty state noise

- Review a word whose meaning appears nowhere else
- **Expect:** No Synonyms box, no “0 synonyms” message

### 4. Empty meaning

- Note with blank Meaning (or missing field)
- **Expect:** No panel (do not guess from word alone)

### 5. Front stays clean

- On question side with “Show only on back” on and “Show synonym counts” on: **Expect:** count pill only (no full Synonyms panel)
- Turn “Show synonym counts” off: **Expect:** no pill on the front
- After answer, go to next card question — **Expect:** previous back panel gone

### 6. Suspended filter

- Suspend all cards of a synonym note
- Rebuild index
- Set Include suspended off (no rebuild required for this flag)
- **Expect:** that note no longer appears
- Set back on — **Expect:** it returns

### 7. Missing field names

- Set Meaning to a name that does not exist
- Rebuild
- **Expect:** no crash; zero-index explain dialog if nothing indexed
- Review still works; Synonyms simply absent

### 8. Rebuild picks up new notes

- Add a new note sharing a normalized meaning with an existing card
- **Rebuild Index**
- **Expect:** new word appears in Synonyms

### 9. Deck filter

- Set decks to one deck name only; rebuild
- **Expect:** synonyms only from that deck

### 10. HTML in fields

- Meaning containing `<b>happy</b>` or Word with tags
- **Expect:** indexed/displayed as plain text (no raw tags in panel)

### 11. Click → Browser

- Click a synonym
- **Expect:** Browser opens on that note (`nid:…`)

### 12. Coexistence with Character Relations

- Install both add-ons
- Review a card that has both relatives and synonyms
- **Expect:** both panels can appear; clicks open the correct notes; no CSS collisions

### 13. UI preview parity

- Open `preview/preview.html` (**Cmd+O**)
- Compare spacing/typography to Anki answer panel
- If you changed CSS in only one place, sync `PANEL_CSS` ↔ preview

## Regression smoke (2 minutes)

Rebuild → review a shared-meaning pair → flip → click synonym → next card front clear → Config open/save without error.
