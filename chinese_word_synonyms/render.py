# -*- coding: utf-8 -*-
"""HTML/CSS for the Synonyms panel injected into the reviewer."""

from __future__ import annotations

from html import escape
from typing import Any, Optional

from .defaults import merge_ui
from .indexer import SynonymEntry

# Structural CSS — colors/sizes come from CSS variables set per render.
# Keep structural rules in sync with preview/preview.html where practical.
PANEL_CSS = """
.word-synonyms {
  margin: 1.25em auto 0;
  max-width: var(--ws-max-width, 100%);
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--ws-gap, 0.75em);
  text-align: left;
  font-size: 0.92em;
  line-height: 1.35;
  color: inherit;
  box-sizing: border-box;
  padding: 0.75em 0.9em 0.85em;
  border: 1px solid var(--ws-border, #b0b0b0);
  border-radius: var(--ws-radius, 12px);
  background: var(--ws-bg, #e4ecf6);
  box-shadow: var(--ws-shadow, 0 3px 8px rgba(40, 35, 30, 0.07));
}
.word-synonyms-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5em;
  margin-bottom: 0.4em;
}
.word-synonyms-title {
  font-weight: 700;
  font-size: var(--ws-char-size, 0.9em);
  margin: 0;
  line-height: 1;
  flex: 0 0 auto;
  color: var(--ws-title, #1a3a6b);
}
.word-synonyms-group {
  box-sizing: border-box;
}
.word-synonyms-scroll {
  position: relative;
  margin: 0;
}
.word-synonyms-items {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.55em 0.95em;
  align-items: flex-end;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 0.1em 0;
  scroll-behavior: smooth;
}
.word-synonyms-items::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}
.word-synonyms-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.08em;
  white-space: nowrap;
  flex: 0 0 auto;
  color: inherit;
  cursor: pointer;
}
.word-synonyms-item:hover .word-synonyms-word {
  text-decoration: underline;
  text-underline-offset: 0.12em;
}
.word-synonyms-pinyin {
  font-size: var(--ws-pinyin-size, 0.62em);
  font-weight: 400;
  opacity: 0.65;
  line-height: 1.15;
}
.word-synonyms-word {
  font-weight: 400;
  font-size: var(--ws-word-size, 0.82em);
  line-height: 1.2;
}
.word-synonyms-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.35em;
  height: 1.35em;
  padding: 0;
  margin: 0;
  border: 1px solid var(--ws-border, #b0b0b0);
  border-radius: 999px;
  background: var(--ws-bg, #e4ecf6);
  color: inherit;
  font-size: 0.95em;
  line-height: 0;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  box-shadow: var(--ws-shadow, 0 2px 6px rgba(40, 35, 30, 0.08));
  -webkit-appearance: none;
  appearance: none;
}
.word-synonyms-arrow::before {
  content: "";
  display: block;
  width: 0.36em;
  height: 0.36em;
  box-sizing: border-box;
  border: solid currentColor;
  border-width: 0 0 0.13em 0.13em;
}
.word-synonyms-arrow-left::before {
  transform: rotate(45deg);
}
.word-synonyms-arrow-right::before {
  border-width: 0.13em 0.13em 0 0;
  transform: rotate(45deg);
}
.word-synonyms-arrow-left { left: 0; }
.word-synonyms-arrow-right { right: 0; }
.word-synonyms-group:hover .word-synonyms-scroll.is-scrollable .word-synonyms-arrow {
  opacity: 0.85;
  pointer-events: auto;
}
.word-synonyms-group:hover .word-synonyms-scroll.is-scrollable .word-synonyms-arrow:hover {
  opacity: 1;
}
.word-synonyms-item.is-mature,
.word-synonyms-item.is-mature .word-synonyms-pinyin,
.word-synonyms-item.is-mature .word-synonyms-word {
  color: var(--ws-mature, #2e7d32);
}
.word-synonyms-item.is-mature .word-synonyms-pinyin {
  opacity: 0.85;
}
.word-synonyms-item.is-suspended,
.word-synonyms-item.is-suspended .word-synonyms-pinyin,
.word-synonyms-item.is-suspended .word-synonyms-word {
  color: var(--ws-suspended, #c62828);
}
.word-synonyms-item.is-suspended .word-synonyms-pinyin {
  opacity: 0.85;
}

.nightMode .word-synonyms,
.night-mode .word-synonyms {
  border-color: var(--ws-border-dark, #5a5a5a);
  background: var(--ws-bg-dark, #2a303a);
  box-shadow: var(--ws-shadow-dark, 0 4px 10px rgba(0, 0, 0, 0.28));
}
.nightMode .word-synonyms-title,
.night-mode .word-synonyms-title {
  color: var(--ws-title-dark, #b8dcff);
}
.nightMode .word-synonyms-pinyin,
.night-mode .word-synonyms-pinyin {
  opacity: 0.65;
}
.nightMode .word-synonyms-arrow,
.night-mode .word-synonyms-arrow {
  border-color: var(--ws-border-dark, #5a5a5a);
  background: var(--ws-bg-dark, #2a303a);
  color: #e8e8e8;
  box-shadow: var(--ws-shadow-dark, 0 2px 8px rgba(0, 0, 0, 0.3));
}
.nightMode .word-synonyms-item.is-mature,
.nightMode .word-synonyms-item.is-mature .word-synonyms-pinyin,
.nightMode .word-synonyms-item.is-mature .word-synonyms-word,
.night-mode .word-synonyms-item.is-mature,
.night-mode .word-synonyms-item.is-mature .word-synonyms-pinyin,
.night-mode .word-synonyms-item.is-mature .word-synonyms-word {
  color: var(--ws-mature-dark, #81c784);
}
.nightMode .word-synonyms-item.is-suspended,
.nightMode .word-synonyms-item.is-suspended .word-synonyms-pinyin,
.nightMode .word-synonyms-item.is-suspended .word-synonyms-word,
.night-mode .word-synonyms-item.is-suspended,
.night-mode .word-synonyms-item.is-suspended .word-synonyms-pinyin,
.night-mode .word-synonyms-item.is-suspended .word-synonyms-word {
  color: var(--ws-suspended-dark, #ef9a9a);
}
"""

PANEL_JS = """
(function () {
  function refresh(wrap) {
    var track = wrap.querySelector(".word-synonyms-items");
    if (!track) return;
    var can = track.scrollWidth > track.clientWidth + 2;
    wrap.classList.toggle("is-scrollable", can);
  }
  function bindScroll(wrap) {
    if (wrap.getAttribute("data-ws-bound") === "1") {
      refresh(wrap);
      return;
    }
    wrap.setAttribute("data-ws-bound", "1");
    var track = wrap.querySelector(".word-synonyms-items");
    var left = wrap.querySelector(".word-synonyms-arrow-left");
    var right = wrap.querySelector(".word-synonyms-arrow-right");
    if (!track || !left || !right) return;
    left.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      track.scrollBy({ left: -160, behavior: "smooth" });
    });
    right.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      track.scrollBy({ left: 160, behavior: "smooth" });
    });
    track.addEventListener("scroll", function () { refresh(wrap); });
    if (window.ResizeObserver) {
      new ResizeObserver(function () { refresh(wrap); }).observe(track);
    }
    refresh(wrap);
  }
  function bindClicks() {
    document.querySelectorAll(".word-synonyms-item[data-nid]").forEach(function (el) {
      if (el.getAttribute("data-ws-click") === "1") return;
      el.setAttribute("data-ws-click", "1");
      el.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var nid = el.getAttribute("data-nid");
        if (!nid) return;
        if (typeof pycmd === "function") {
          pycmd("word_synonyms_browse:" + nid);
        }
      });
    });
  }
  document.querySelectorAll(".word-synonyms-scroll").forEach(bindScroll);
  bindClicks();
})();
"""


def _item_class(entry: SynonymEntry) -> str:
    if entry.suspended:
        return "word-synonyms-item is-suspended"
    if entry.mature:
        return "word-synonyms-item is-mature"
    return "word-synonyms-item"


def _css_var_block(ui: dict[str, Any]) -> str:
    """Inline style attribute setting CSS variables from ui config."""
    shadow_on = bool(ui.get("show_shadow", True))
    shadow = "0 3px 8px rgba(40, 35, 30, 0.07)" if shadow_on else "none"
    shadow_dark = "0 4px 10px rgba(0, 0, 0, 0.28)" if shadow_on else "none"
    pairs = {
        "--ws-max-width": str(ui.get("max_width") or "100%"),
        "--ws-gap": f"{float(ui.get('gap_em', 0.65))}em",
        "--ws-radius": f"{int(ui.get('border_radius_px', 12))}px",
        "--ws-char-size": f"{float(ui.get('char_size_em', 1.05))}em",
        "--ws-word-size": f"{float(ui.get('word_size_em', 0.82))}em",
        "--ws-pinyin-size": f"{float(ui.get('pinyin_size_em', 0.62))}em",
        "--ws-bg": str(ui.get("bg_light") or "#e4ecf6"),
        "--ws-bg-dark": str(ui.get("bg_dark") or "#2a303a"),
        "--ws-border": str(ui.get("border_light") or "#b0b0b0"),
        "--ws-border-dark": str(ui.get("border_dark") or "#5a5a5a"),
        "--ws-mature": str(ui.get("mature_light") or "#2e7d32"),
        "--ws-mature-dark": str(ui.get("mature_dark") or "#81c784"),
        "--ws-suspended": str(ui.get("suspended_light") or "#c62828"),
        "--ws-suspended-dark": str(ui.get("suspended_dark") or "#ef9a9a"),
        "--ws-shadow": shadow,
        "--ws-shadow-dark": shadow_dark,
    }
    return "; ".join(f"{k}: {escape(v, quote=True)}" for k, v in pairs.items())


def _safe_custom_css(css: str) -> str:
    """Prevent breaking out of the style tag."""
    return (css or "").replace("</", "<\\/")


def render_panel(
    entries: list[SynonymEntry],
    ui: Optional[dict[str, Any]] = None,
) -> str:
    """
    Build the Synonyms panel HTML, or "" if there is nothing to show.

    *ui* comes from config["ui"] (Appearance tab). Defaults applied if omitted.
    MVP: one horizontal group under the title “Synonyms”.
    """
    if not entries:
        return ""

    ui = merge_ui(ui)
    custom = _safe_custom_css(str(ui.get("custom_css") or "")).strip()
    custom_block = f"<style id=\"word-synonyms-custom\">{custom}</style>" if custom else ""

    parts: list[str] = [
        f"<style id=\"word-synonyms-style\">{PANEL_CSS}</style>",
        custom_block,
        f'<div class="word-synonyms" id="word-synonyms-panel" style="{_css_var_block(ui)}">',
        '<div class="word-synonyms-group">',
        '<div class="word-synonyms-heading">',
        '<div class="word-synonyms-title">Synonyms</div>',
        "</div>",
        '<div class="word-synonyms-scroll">',
        '<button type="button" class="word-synonyms-arrow word-synonyms-arrow-left" '
        'aria-label="Scroll left"></button>',
        '<div class="word-synonyms-items">',
    ]

    for entry in entries:
        word = escape(entry.word)
        pinyin = escape(entry.pinyin) if entry.pinyin else ""
        nid = int(entry.note_id)
        parts.append(
            f'<span class="{_item_class(entry)}" data-nid="{nid}" '
            f'role="button" title="Open in Browser" tabindex="0">'
        )
        if pinyin:
            parts.append(f'<span class="word-synonyms-pinyin">{pinyin}</span>')
        parts.append(f'<span class="word-synonyms-word">{word}</span>')
        parts.append("</span>")

    parts.extend(
        [
            "</div>",
            '<button type="button" class="word-synonyms-arrow word-synonyms-arrow-right" '
            'aria-label="Scroll right"></button>',
            "</div>",
            "</div>",
            "</div>",
            f"<script>{PANEL_JS}</script>",
        ]
    )
    return "".join(parts)
