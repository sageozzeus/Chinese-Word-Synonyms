# Chinese Word Synonyms

Anki desktop add-on that shows **synonyms from your own deck** that share the same normalized meaning with the card you’re reviewing.

Example: reviewing **快乐** (happy) → under the answer you see 高兴, 开心, 愉快… if those notes exist and their Meaning fields normalize to the same sense.

Works offline. Uses only your collection — no external dictionary, no AnkiConnect, no CEDICT download.

Pairs well with **[Chinese Character Relations](https://github.com/sageozzeus/Chinese-Character-Relations)** (shared characters). Both can be installed together; they use separate menus, indexes, panel IDs, and `pycmd` prefixes.

## Requirements

- Anki Desktop **23.10+** (Qt6 preferred)
- macOS, Windows, or Linux
- Notes with a Word/Hanzi field **and** a Meaning/Definition/English field

## Install

### From GitHub (recommended until AnkiWeb is live)

1. Open the latest [Release](https://github.com/sageozzeus/Chinese-Word-Synonyms/releases/latest).
2. Download the **`.ankiaddon`** asset (e.g. `chinese_word_synonyms-0.1.0.ankiaddon`), not Source code.
3. Double-click the file, or open it with Anki / drag it onto the Anki window.
4. Restart Anki when prompted.
5. Open **Tools → Chinese Word Synonyms…**
6. On the **General** tab, set Word / Hanzi, Meaning (and optional Pinyin) fields, then click **Rebuild Index**.

### From AnkiWeb

When the listing is live: **Tools → Add-ons → Get Add-ons…**, search for *Chinese Word Synonyms*, or open the listing from the About tab after install.

### Manual (developers)

```bash
./scripts/link-anki-addon.sh
```

Or copy the `chinese_word_synonyms` folder into your Anki add-ons folder, then restart Anki (**Cmd+Q**, reopen):

- **macOS:** `~/Library/Application Support/Anki2/addons21/`
- **Windows:** `%APPDATA%\Anki2\addons21\`
- **Linux:** `~/.local/share/Anki2/addons21/`

## Settings

**Tools → Chinese Word Synonyms…** (or **Tools → Add-ons → Config**):

| Tab | What it’s for |
| --- | --- |
| **General** | Decks, Word / Meaning fields, display limits, **Rebuild Index** |
| **Appearance** | Panel width, type sizes, colors, optional custom CSS |
| **About** | Version, changelog, bug reports, links |

After changing decks or fields, rebuild when prompted (or use **Rebuild Index**). Appearance changes apply on the next answer flip — no rebuild needed.

Defaults assume `Word`, `Pinyin`, and `Meaning`. Fallbacks include `Definition`, `English`, `Gloss`, `Translation`, `含义`, `释义`, `Back`, and common Word field names.

## How matching works

Meaning text is normalized into keys: strip HTML, lowercase, drop POS prefixes (`adj.`, `v.`, …), split on `;` `|` `/` `；` `、`, then index the note under each key. At review time, other notes sharing a key are shown (current note and identical headword excluded). Empty meaning → no panel.

## Tips

- Click a synonym to open that note in the Browser.
- If nothing appears, check Word + Meaning field names and rebuild; words with unique meanings simply show no panel.
- Suspended notes can be included or hidden on the General tab.
- Safe alongside Character Relations — panels may both appear under the answer.

## Support

- **Bugs:** [GitHub Issues](https://github.com/sageozzeus/Chinese-Word-Synonyms/issues)
- **Updates / short questions:** [X @sageozzeus](https://x.com/sageozzeus)
- **Source:** [github.com/sageozzeus/Chinese-Word-Synonyms](https://github.com/sageozzeus/Chinese-Word-Synonyms)

Maintainer docs: [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) · QA checklist: [`docs/TESTING.md`](docs/TESTING.md)

## License

MIT — see [`LICENSE`](LICENSE).
