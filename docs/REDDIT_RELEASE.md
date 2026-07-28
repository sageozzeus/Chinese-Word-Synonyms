# Reddit release posts

Copy-paste for [r/Anki](https://www.reddit.com/r/Anki/). Update this file when you ship a new version.

---

## v0.1.1 — update post

**Title:** Chinese Word Synonyms add-on v0.1.1 — synonym count on the card front

**Body:**

Small update to **Chinese Word Synonyms**, the offline add-on that shows synonyms from your own deck when notes share the same normalized meaning (e.g. reviewing 快乐 → 高兴, 开心, 愉快 on the back).

**What’s new in v0.1.1**

- Pill on the **question** side: e.g. `4 Synonyms` (when “Show only on back” is on)
- **Show synonym counts** toggle in Tools → Chinese Word Synonyms… → General → Display options
- Full scrollable Synonyms panel unchanged on the **answer** side

Pairs well with [Chinese Character Relations](https://github.com/sageozzeus/Chinese-Character-Relations) (shared characters vs shared meanings). Both can run together.

**Install:** download `chinese_word_synonyms-0.1.1.ankiaddon` from the latest GitHub Release, double-click or drag onto Anki, restart, then **Tools → Chinese Word Synonyms…** → set Word + Meaning fields → **Rebuild Index**.

- Release: https://github.com/sageozzeus/Chinese-Word-Synonyms/releases/latest
- Issues: https://github.com/sageozzeus/Chinese-Word-Synonyms/issues

Anki Desktop 23.10+, macOS / Windows / Linux. MIT.

---

## v0.1.0 — launch post

**Title:** [Add-on] Chinese Word Synonyms — deck synonyms by shared meaning (offline)

**Body:**

I made an Anki add-on for Chinese learners: **Chinese Word Synonyms**. While you review, it shows **other words from your own deck** that share the same normalized English/meaning field — not a downloaded dictionary, just your notes.

Example: meaning `happy` on 快乐 → on the answer you see 高兴, 开心, 愉快 if those cards exist with the same normalized sense.

**Features**

- Offline, indexes your collection in RAM after **Rebuild Index**
- Synonyms panel on the card back (optional front/back via settings)
- Click a synonym → opens that note in the Browser
- General + Appearance settings GUI (decks, fields, colors, custom CSS)
- Works alongside my **Chinese Character Relations** add-on

**Install:** GitHub Release `.ankiaddon` → double-click → restart Anki → **Tools → Chinese Word Synonyms…** → configure fields → **Rebuild Index**.

- https://github.com/sageozzeus/Chinese-Word-Synonyms/releases/latest

Needs Word/Hanzi + Meaning (or similar) fields. Anki 23.10+.
