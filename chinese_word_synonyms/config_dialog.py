# -*- coding: utf-8 -*-
"""GUI settings dialog — General, Appearance, and About tabs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from aqt import mw
from aqt.qt import (
    QAbstractButton,
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPainter,
    QPalette,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSize,
    QSizePolicy,
    QSpinBox,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)
from aqt.utils import askUser, openLink, showInfo, tooltip

from . import about_meta, indexer
from .defaults import DEFAULT_CONFIG, DEFAULT_UI, merge_config
from .meaning import (
    DEFAULT_SPLIT_DELIMITERS,
    KNOWN_SPLIT_DELIMITERS,
    KNOWN_SPLIT_TOOLTIPS,
    delimiters_to_spec,
    spec_to_ui,
)

ADDON_PACKAGE = __name__.split(".")[0]

_GROUP_STYLE = """
QGroupBox {
  font-weight: 600;
  font-size: 13px;
  margin-top: 0.4em;
  margin-bottom: 0.55em;
  padding-top: 0.85em;
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 8px;
  padding: 0 4px;
}
"""

_CONTROL_FIELD_HEIGHT = 28
_CONTROL_LABEL_STYLE = "font-size: 11px;"


def _normalize_control_field(widget: QWidget) -> None:
    widget.setMinimumWidth(0)
    widget.setMinimumHeight(_CONTROL_FIELD_HEIGHT)
    widget.setMaximumHeight(_CONTROL_FIELD_HEIGHT)
    widget.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    _clamp_field_width(widget)


def _is_dark(widget: QWidget) -> bool:
    return widget.palette().color(QPalette.ColorRole.Window).value() < 128


def _style_group(box: QGroupBox) -> QGroupBox:
    box.setStyleSheet(_GROUP_STYLE)
    box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    return box


class ToggleSwitch(QAbstractButton):
    """Painted on/off switch — QCheckBox stylesheets look like solid pills in Anki."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(44, 24)

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(44, 24)

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark = _is_dark(self)
        on = self.isChecked()

        track = self.rect().adjusted(1, 3, -1, -3)
        if on:
            track_color = QColor("#2d6cdf")
        elif dark:
            track_color = QColor("#5a5a5a")
        else:
            track_color = QColor("#c0c0c0")

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track, track.height() / 2, track.height() / 2)

        knob_d = track.height() - 2
        margin = 1
        if on:
            kx = track.right() - knob_d - margin
        else:
            kx = track.left() + margin
        ky = track.top() + (track.height() - knob_d) / 2
        knob = QColor("#ffffff")
        p.setBrush(knob)
        p.drawEllipse(int(kx), int(ky), knob_d, knob_d)


def _add_toggle_row(layout: QVBoxLayout, label: str, toggle: ToggleSwitch) -> None:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 6, 0, 6)
    lay.setSpacing(12)
    text = QLabel(label)
    text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    lay.addWidget(text, 1, Qt.AlignmentFlag.AlignVCenter)
    lay.addWidget(toggle, 0, Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(row)


class _DeckDropdown(QFrame):
    """Clickable field with centered chevron; opens a checkbox menu."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("wsDeckDropdown")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(_CONTROL_FIELD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet(
            "#wsDeckDropdown {"
            "  border: 1px solid palette(mid);"
            "  border-radius: 4px;"
            "  background: palette(base);"
            "}"
            "#wsDeckDropdown:hover {"
            "  border-color: palette(highlight);"
            "}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(6)

        self._summary = QLabel("All decks")
        self._summary.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self._summary.setMinimumWidth(0)
        self._summary.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self._full_summary = "All decks"

        self._chevron = QLabel("▾")
        self._chevron.setFixedWidth(18)
        self._chevron.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chevron.setStyleSheet("font-size: 12px; opacity: 0.75;")

        lay.addWidget(self._summary, 1)
        lay.addWidget(self._chevron, 0, Qt.AlignmentFlag.AlignVCenter)

        self._menu = QMenu(self)
        panel = QWidget()
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(8, 8, 8, 8)
        panel_lay.setSpacing(6)

        self._all_cb = QCheckBox("All decks")
        self._all_cb.toggled.connect(self._on_all_toggled)
        panel_lay.addWidget(self._all_cb)

        self._list = QListWidget()
        self._list.setMinimumWidth(240)
        self._list.setMaximumHeight(180)
        panel_lay.addWidget(self._list)

        btn_row = QHBoxLayout()
        select_all = QPushButton("Select all")
        select_none = QPushButton("Select none")
        select_all.clicked.connect(self._select_all)
        select_none.clicked.connect(self._select_none)
        btn_row.addWidget(select_all)
        btn_row.addWidget(select_none)
        btn_row.addStretch(1)
        panel_lay.addLayout(btn_row)

        action = QWidgetAction(self._menu)
        action.setDefaultWidget(panel)
        self._menu.addAction(action)

        self._list.itemChanged.connect(lambda *_: self._sync_summary())
        self._sync_summary()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_menu()
            event.accept()
            return
        super().mousePressEvent(event)

    def _open_menu(self) -> None:
        self._menu.setMinimumWidth(max(self.width(), 280))
        self._menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def set_deck_names(self, names: list[str]) -> None:
        self._list.clear()
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list.addItem(item)
        self._sync_summary()

    def set_selection(self, deck_names: list[str]) -> None:
        """Empty list means all decks."""
        all_decks = len(deck_names) == 0
        self._all_cb.blockSignals(True)
        self._all_cb.setChecked(all_decks)
        self._all_cb.blockSignals(False)
        selected = set(deck_names)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if all_decks:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(
                    Qt.CheckState.Checked
                    if item.text() in selected
                    else Qt.CheckState.Unchecked
                )
        self._on_all_toggled(all_decks)

    def has_deck_list(self) -> bool:
        return self._list.count() > 0

    def all_decks_selected(self) -> bool:
        return self._all_cb.isChecked()

    def selected_decks(self) -> list[str]:
        if self._all_cb.isChecked():
            return []
        decks: list[str] = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                decks.append(item.text())
        return decks

    def _on_all_toggled(self, checked: bool) -> None:
        self._list.setEnabled(not checked)
        if checked:
            for i in range(self._list.count()):
                self._list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._sync_summary()

    def _select_all(self) -> None:
        self._all_cb.setChecked(False)
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(Qt.CheckState.Checked)
        self._sync_summary()

    def _select_none(self) -> None:
        self._all_cb.setChecked(False)
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._sync_summary()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_summary_text()

    def _sync_summary(self) -> None:
        if self._all_cb.isChecked():
            self._full_summary = "All decks"
        else:
            names = self.selected_decks()
            if not names:
                self._full_summary = "No decks selected"
            elif len(names) == 1:
                self._full_summary = names[0]
            else:
                self._full_summary = f"{len(names)} decks selected"
        self._apply_summary_text()

    def _apply_summary_text(self) -> None:
        text = getattr(self, "_full_summary", "All decks")
        self._summary.setToolTip(text)
        width = max(40, self.width() - 40)
        elided = self._summary.fontMetrics().elidedText(
            text, Qt.TextElideMode.ElideMiddle, width
        )
        self._summary.setText(elided)


def _load_config() -> dict[str, Any]:
    return merge_config(mw.addonManager.getConfig(ADDON_PACKAGE))


def _save_config(conf: dict[str, Any]) -> None:
    mw.addonManager.writeConfig(ADDON_PACKAGE, conf)


def _deck_names() -> list[str]:
    if mw.col is None:
        return []
    try:
        return sorted(d.name for d in mw.col.decks.all_names_and_ids())
    except Exception:
        try:
            return sorted(mw.col.decks.allNames())
        except Exception:
            return []


def _field_names() -> list[str]:
    if mw.col is None:
        return []
    names: set[str] = set()
    try:
        for model in mw.col.models.all():
            for fld in model.get("flds", []):
                name = fld.get("name")
                if name:
                    names.add(name)
    except Exception:
        pass
    return sorted(names, key=lambda s: s.lower())


class _ColorButton(QPushButton):
    """Swatch + hex; click to edit hex or open the system color picker."""

    def __init__(self, color: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._hex = "#ffffff"
        self.setMinimumWidth(88)
        self.setMinimumHeight(_CONTROL_FIELD_HEIGHT)
        self.setMaximumHeight(_CONTROL_FIELD_HEIGHT)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.set_color(color)
        self.clicked.connect(self._pick)

    def set_color(self, color: str) -> None:
        c = QColor(color)
        if not c.isValid():
            c = QColor("#ffffff")
        self._hex = c.name()
        self.setText(self._hex)
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._hex}; color: "
            f"{'#111' if c.lightness() > 140 else '#eee'}; "
            f"border: 1px solid #888; padding: 4px 8px; text-align: left; }}"
        )

    def color(self) -> str:
        return self._hex

    def _pick(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Pick color")
        root = QVBoxLayout(dlg)
        hex_edit = QLineEdit(self._hex)
        hex_edit.setPlaceholderText("#rrggbb")
        form = QFormLayout()
        form.addRow("Hex", hex_edit)
        root.addLayout(form)

        pick_btn = QPushButton("Open color picker…")

        def _from_wheel() -> None:
            start = QColor(hex_edit.text().strip() or self._hex)
            chosen = QColorDialog.getColor(start, dlg, "Pick color")
            if chosen.isValid():
                hex_edit.setText(chosen.name())

        pick_btn.clicked.connect(_from_wheel)
        root.addWidget(pick_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        root.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        raw = hex_edit.text().strip()
        if raw and not raw.startswith("#"):
            raw = f"#{raw}"
        chosen = QColor(raw)
        if chosen.isValid():
            self.set_color(chosen.name())


def _wrap_scroll(inner: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    inner.setMinimumWidth(0)
    inner.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    scroll.setWidget(inner)
    return scroll


def _clamp_field_width(widget: QWidget) -> None:
    """Stop Qt size-hints (esp. QComboBox) from forcing a horizontal scrollbar."""
    widget.setMinimumWidth(0)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    if isinstance(widget, QComboBox):
        widget.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        widget.setMinimumContentsLength(6)


def _link_button(label: str, url: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.clicked.connect(lambda _checked=False, u=url: openLink(u))
    return btn


def _meta_row(form: QFormLayout, label: str, value: str) -> None:
    val = QLabel(value)
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    # Do not wrap — scroll-area Ignored width can clip the second line
    # (e.g. "Chinese Word Synonyms" → only "Chinese Word" visible).
    val.setWordWrap(False)
    val.setToolTip(value)
    val.setMinimumWidth(0)
    val.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred,
    )
    val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    form.addRow(label, val)


def _about_form() -> QFormLayout:
    """Left-aligned key/value rows (macOS QFormLayout defaults to centered)."""
    form = QFormLayout()
    form.setSpacing(6)
    form.setFormAlignment(
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
    )
    form.setLabelAlignment(
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    )
    form.setFieldGrowthPolicy(
        QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
    )
    return form


class ConfigDialog(QDialog):
    """Settings dialog with General, Appearance, and About tabs."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle(about_meta.ADDON_NAME)
        self.setMinimumWidth(520)
        self.resize(560, 620)
        self.setMinimumHeight(520)
        self._conf = _load_config()
        self._build_ui()
        self._load_into_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        self.tabs.addTab(_wrap_scroll(self._build_general_tab()), "General")
        self.tabs.addTab(_wrap_scroll(self._build_appearance_tab()), "Appearance")
        self.tabs.addTab(_wrap_scroll(self._build_about_tab()), "About")
        root.addWidget(self.tabs)

        actions = QHBoxLayout()
        self.restore_btn = QPushButton("Restore defaults")
        self.restore_btn.clicked.connect(self._restore_defaults)
        actions.addWidget(self.restore_btn)
        actions.addStretch(1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        actions.addWidget(buttons)
        root.addLayout(actions)

    def _build_general_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(28)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        intro = QLabel(
            "Choose which decks and fields to use for synonym Chinese words "
            "shown on the answer side during review."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addWidget(self._build_decks_group())
        layout.addWidget(self._build_fields_group())
        layout.addWidget(self._build_delimiters_group())
        layout.addWidget(self._build_display_group())
        layout.addWidget(self._build_index_group())
        layout.addStretch(1)
        return page

    def _build_appearance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(28)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        intro = QLabel(
            "Customize how the Synonyms panel looks on the card. "
            "Changes apply on the next answer flip (no rebuild needed). "
            "Use max width like 100%, 36em, or 650px to match your card template."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addWidget(self._build_layout_group())
        layout.addWidget(self._build_type_group())
        layout.addWidget(self._build_colors_group())
        layout.addWidget(self._build_custom_css_group())
        layout.addStretch(1)
        return page

    def _build_about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(28)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        intro = QLabel(
            "Add-on info, support links, and recent changes. "
            "Nothing on this tab is saved with your settings."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addWidget(self._build_about_addon_group())
        layout.addWidget(self._build_about_author_group())
        layout.addWidget(self._build_about_changelog_group())
        layout.addStretch(1)
        return page

    def _build_about_addon_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Add-on"))
        layout = QVBoxLayout(box)
        layout.setSpacing(8)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        form = _about_form()
        _meta_row(form, "Name", about_meta.ADDON_NAME)
        _meta_row(form, "Version", about_meta.ADDON_VERSION)
        _meta_row(form, "Requires Anki", about_meta.MIN_ANKI)
        _meta_row(form, "License", about_meta.LICENSE)
        layout.addLayout(form)

        tip = QLabel(
            "After deck or field changes, rebuild the index on the General tab."
        )
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)

        links = QHBoxLayout()
        links.setSpacing(8)
        links.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ankiweb = (about_meta.URL_ANKIWEB or "").strip()
        if ankiweb:
            links.addWidget(_link_button("Anki page", ankiweb))
            links.addWidget(_link_button("Rate", ankiweb))
        else:
            soon = QLabel("AnkiWeb listing coming soon")
            soon.setAlignment(Qt.AlignmentFlag.AlignLeft)
            soon.setStyleSheet("opacity: 0.7; font-size: 11px;")
            links.addWidget(soon)
        links.addStretch(1)
        layout.addLayout(links)
        return box

    def _build_about_author_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Author & support"))
        layout = QVBoxLayout(box)
        layout.setSpacing(8)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        form = _about_form()
        _meta_row(form, "Author", about_meta.AUTHOR)
        layout.addLayout(form)

        links = QHBoxLayout()
        links.setSpacing(8)
        links.setAlignment(Qt.AlignmentFlag.AlignLeft)
        links.addWidget(_link_button("Report a bug", about_meta.URL_ISSUES))
        links.addWidget(_link_button("GitHub", about_meta.URL_GITHUB))
        links.addWidget(_link_button("X", about_meta.URL_X))
        links.addStretch(1)
        layout.addLayout(links)

        tip = QLabel(
            "Please file bugs on GitHub so they don’t get lost. "
            "Short questions welcome on X."
        )
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)
        return box

    def _build_about_changelog_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Changelog"))
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        entries = about_meta.CHANGELOG
        if not entries:
            empty = QLabel("No changelog entries yet.")
            empty.setStyleSheet("opacity: 0.7; font-size: 11px;")
            layout.addWidget(empty)
            return box

        latest_ver, latest_notes = entries[0]
        latest_title = QLabel(f"v{latest_ver}")
        latest_title.setStyleSheet("font-weight: 600;")
        layout.addWidget(latest_title)

        for note in latest_notes[:5]:
            bullet = QLabel(f"• {note}")
            bullet.setWordWrap(True)
            layout.addWidget(bullet)

        for ver, notes in entries[1:]:
            summary = notes[0] if notes else ""
            line = f"v{ver}"
            if summary:
                line = f"{line} — {summary}"
            older = QLabel(line)
            older.setWordWrap(True)
            older.setStyleSheet("opacity: 0.7; font-size: 11px;")
            layout.addWidget(older)

        return box

    def _build_decks_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Decks to scan"))
        layout = QVBoxLayout(box)
        layout.setSpacing(4)

        lbl = QLabel("Decks")
        lbl.setStyleSheet(_CONTROL_LABEL_STYLE)
        layout.addWidget(lbl)

        self.deck_picker = _DeckDropdown()
        self.deck_picker.set_deck_names(_deck_names())
        layout.addWidget(self.deck_picker)

        tip = QLabel("Open the menu to choose decks. Leave on All decks to scan everything.")
        tip.setWordWrap(True)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)
        return box

    def _build_fields_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Note fields"))
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        field_names = _field_names()
        common = [
            "Word", "Hanzi", "Expression", "Chinese", "Front", "Pinyin",
            "Reading", "Meaning", "Definition", "English", "Gloss",
            "Translation", "含义", "释义", "Back",
        ]
        suggestions = list(dict.fromkeys(field_names + common))

        self.word_combo = self._make_field_combo(suggestions)
        self.pinyin_combo = self._make_field_combo(suggestions)
        self.meaning_combo = self._make_field_combo(suggestions)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        self._add_control_cell(grid, 0, 0, "Word / Hanzi", self.word_combo)
        self._add_control_cell(grid, 0, 1, "Pinyin", self.pinyin_combo)
        self._add_control_cell(grid, 1, 0, "Meaning", self.meaning_combo)
        for col in range(2):
            grid.setColumnStretch(col, 1)
        layout.addLayout(grid)

        tip = QLabel(
            "Meaning is required for synonym matching. "
            "Pick from your note types, or type a custom field name."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)
        return box

    def _build_delimiters_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Meaning delimiters"))
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        tip = QLabel(
            "Characters that separate senses in your Meaning field "
            "(e.g. happy, glad or happy; glad)."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        self.delim_checks: dict[str, QCheckBox] = {}
        for i, delim in enumerate(KNOWN_SPLIT_DELIMITERS):
            cb = QCheckBox(delim)
            cb.setToolTip(KNOWN_SPLIT_TOOLTIPS.get(delim, delim))
            self.delim_checks[delim] = cb
            grid.addWidget(cb, i // 3, i % 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        layout.addLayout(grid)

        extra_row = QHBoxLayout()
        extra_row.setSpacing(8)
        extra_lbl = QLabel("Extra")
        extra_lbl.setStyleSheet(_CONTROL_LABEL_STYLE)
        self.delim_extra_edit = QLineEdit()
        self.delim_extra_edit.setPlaceholderText("optional · : …")
        self.delim_extra_edit.setToolTip(
            "Any extra single-character delimiters not listed above."
        )
        _normalize_control_field(self.delim_extra_edit)
        extra_row.addWidget(extra_lbl, 0)
        extra_row.addWidget(self.delim_extra_edit, 1)
        layout.addLayout(extra_row)

        rebuild_tip = QLabel("Rebuild the index after changing delimiters.")
        rebuild_tip.setWordWrap(True)
        rebuild_tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(rebuild_tip)
        return box

    def _build_display_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Display options"))
        layout = QVBoxLayout(box)
        layout.setSpacing(4)

        caps = QGridLayout()
        caps.setHorizontalSpacing(10)
        caps.setVerticalSpacing(4)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 50)
        self.min_len_spin = QSpinBox()
        self.min_len_spin.setRange(1, 10)
        self._add_control_cell(caps, 0, 0, "Max synonyms", self.max_spin)
        self._add_control_cell(caps, 0, 1, "Min word length", self.min_len_spin)
        for col in range(2):
            caps.setColumnStretch(col, 1)
        layout.addLayout(caps)

        self.include_suspended_toggle = ToggleSwitch()
        self.include_suspended_toggle.setToolTip(
            "When off, fully suspended notes are hidden from synonyms."
        )
        _add_toggle_row(layout, "Include suspended notes", self.include_suspended_toggle)

        self.back_only_toggle = ToggleSwitch()
        self.back_only_toggle.setToolTip(
            "On: full Synonyms panel on the card back only. "
            "Off: show the full panel on front and back."
        )
        _add_toggle_row(layout, "Show only on back", self.back_only_toggle)

        self.show_synonym_counts_toggle = ToggleSwitch()
        self.show_synonym_counts_toggle.setToolTip(
            "On: show a small front card with Known (unsuspended) and Total synonym "
            "counts (when Show only on back is on). Off: no front summary."
        )
        _add_toggle_row(layout, "Show synonym counts", self.show_synonym_counts_toggle)
        return box

    def _build_index_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Index"))
        layout = QVBoxLayout(box)
        tip = QLabel(
            "Rebuild after changing decks, fields, or meaning delimiters, "
            "or when new notes should appear in Synonyms. "
            "Appearance changes do not need a rebuild."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)

        row = QHBoxLayout()
        self.rebuild_btn = QPushButton("Rebuild Index")
        self.rebuild_btn.setToolTip("Scan decks and refresh the meaning → notes index.")
        self.rebuild_btn.clicked.connect(self._on_rebuild_index)
        row.addWidget(self.rebuild_btn)
        row.addStretch(1)
        layout.addLayout(row)
        return box

    def _on_rebuild_index(self) -> None:
        if mw.col is None:
            showInfo("Open a profile before rebuilding the index.")
            return
        # Persist current form values first so rebuild uses what the user sees.
        conf = self._collect()
        if conf is None:
            return
        _save_config(conf)
        self._conf = conf
        indexer.rebuild_index(show_progress=True, notify=True)

    def _build_layout_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Layout"))
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(8, 8, 8, 8)

        self.max_width_edit = QLineEdit()
        self.max_width_edit.setPlaceholderText("100%  ·  36em  ·  650px")
        self.max_width_edit.setToolTip(
            "CSS max-width for the Synonyms panel. Use 100% to fill the card container."
        )

        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 40)

        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0.2, 2.0)
        self.gap_spin.setSingleStep(0.05)
        self.gap_spin.setDecimals(2)

        self._add_control_cell(grid, 0, 0, "Max width", self.max_width_edit)
        self._add_control_cell(grid, 0, 1, "Corner radius (px)", self.radius_spin)
        self._add_control_cell(grid, 0, 2, "Card gaps (em)", self.gap_spin)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        return box

    def _build_type_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Type size"))
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(8, 8, 8, 8)

        self.char_size_spin = self._em_spin()
        self.word_size_spin = self._em_spin()
        self.pinyin_size_spin = self._em_spin()
        for spin in (self.char_size_spin, self.word_size_spin, self.pinyin_size_spin):
            spin.setSuffix("")

        self._add_control_cell(grid, 0, 0, "Title (em)", self.char_size_spin)
        self._add_control_cell(grid, 0, 1, "Synonym word (em)", self.word_size_spin)
        self._add_control_cell(grid, 0, 2, "Pinyin (em)", self.pinyin_size_spin)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        return box

    @staticmethod
    def _add_control_cell(
        grid: QGridLayout, row: int, col: int, label: str, widget: QWidget
    ) -> None:
        cell = QWidget()
        cell.setMinimumWidth(0)
        cell.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
        cell_lay = QVBoxLayout(cell)
        cell_lay.setContentsMargins(0, 0, 0, 0)
        cell_lay.setSpacing(2)
        cell_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl = QLabel(label)
        lbl.setStyleSheet(_CONTROL_LABEL_STYLE)
        lbl.setWordWrap(True)
        lbl.setMinimumWidth(0)
        lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        cell_lay.addWidget(lbl)
        cell_lay.addWidget(widget)
        _normalize_control_field(widget)
        grid.addWidget(cell, row, col)
        grid.setColumnMinimumWidth(col, 0)

    @staticmethod
    def _add_color_cell(
        grid: QGridLayout, row: int, col: int, label: str, button: _ColorButton
    ) -> None:
        ConfigDialog._add_control_cell(grid, row, col, label, button)

    def _build_colors_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Colors"))
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(8, 8, 8, 8)

        self.bg_light_btn = _ColorButton("#e4ecf6")
        self.bg_dark_btn = _ColorButton("#2a303a")
        self.border_light_btn = _ColorButton("#b0b0b0")
        self.border_dark_btn = _ColorButton("#5a5a5a")
        self.mature_light_btn = _ColorButton("#2e7d32")
        self.mature_dark_btn = _ColorButton("#81c784")
        self.suspended_light_btn = _ColorButton("#c62828")
        self.suspended_dark_btn = _ColorButton("#ef9a9a")

        self._add_color_cell(grid, 0, 0, "Background (light)", self.bg_light_btn)
        self._add_color_cell(grid, 0, 1, "Background (dark)", self.bg_dark_btn)
        self._add_color_cell(grid, 0, 2, "Border (light)", self.border_light_btn)
        self._add_color_cell(grid, 0, 3, "Border (dark)", self.border_dark_btn)
        self._add_color_cell(grid, 1, 0, "Mature (light)", self.mature_light_btn)
        self._add_color_cell(grid, 1, 1, "Mature (dark)", self.mature_dark_btn)
        self._add_color_cell(grid, 1, 2, "Suspended (light)", self.suspended_light_btn)
        self._add_color_cell(grid, 1, 3, "Suspended (dark)", self.suspended_dark_btn)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        return box

    def _build_custom_css_group(self) -> QGroupBox:
        box = _style_group(QGroupBox("Custom CSS (advanced)"))
        layout = QVBoxLayout(box)
        tip = QLabel(
            "Optional extra CSS appended after the built-in panel styles. "
            "Target .word-synonyms, .word-synonyms-group, etc."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("opacity: 0.7; font-size: 11px;")
        layout.addWidget(tip)
        self.custom_css_edit = QPlainTextEdit()
        self.custom_css_edit.setPlaceholderText(
            ".word-synonyms-group {\n  /* your rules */\n}"
        )
        self.custom_css_edit.setMinimumHeight(100)
        layout.addWidget(self.custom_css_edit)
        return box

    @staticmethod
    def _em_spin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.4, 2.5)
        spin.setSingleStep(0.01)
        spin.setDecimals(2)
        spin.setSuffix(" em")
        return spin

    @staticmethod
    def _make_field_combo(suggestions: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.addItems(suggestions)
        combo.setMinimumWidth(0)
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        combo.setMinimumContentsLength(6)
        _normalize_control_field(combo)
        return combo

    def _load_into_ui(self) -> None:
        conf = self._conf
        decks = list(conf.get("decks") or [])
        self.deck_picker.set_deck_names(_deck_names())
        self.deck_picker.set_selection(decks)

        fields = conf.get("fields") or {}
        self._set_combo(self.word_combo, fields.get("word", "Word"))
        self._set_combo(self.pinyin_combo, fields.get("pinyin", "Pinyin"))
        self._set_combo(self.meaning_combo, fields.get("meaning", "Meaning"))

        self.max_spin.setValue(int(conf.get("max_synonyms", 12)))
        self.min_len_spin.setValue(int(conf.get("candidate_min_length", 1)))
        self.include_suspended_toggle.setChecked(
            bool(conf.get("include_suspended", True))
        )
        back_only = conf.get("show_only_on_back")
        if back_only is None:
            back_only = conf.get("show_on_answer_only", True)
        self.back_only_toggle.setChecked(bool(back_only))
        self.show_synonym_counts_toggle.setChecked(
            bool(conf.get("show_synonym_counts", True))
        )

        known, extra = spec_to_ui(
            str(conf.get("meaning_split_delimiters") or DEFAULT_SPLIT_DELIMITERS)
        )
        known_set = set(known)
        for delim, cb in self.delim_checks.items():
            cb.setChecked(delim in known_set)
        self.delim_extra_edit.setText(extra)

        ui = conf.get("ui") or deepcopy(DEFAULT_UI)
        self.max_width_edit.setText(str(ui.get("max_width", "100%")))
        self.radius_spin.setValue(int(ui.get("border_radius_px", 12)))
        self.gap_spin.setValue(float(ui.get("gap_em", 0.65)))
        self.char_size_spin.setValue(float(ui.get("char_size_em", 1.05)))
        self.word_size_spin.setValue(float(ui.get("word_size_em", 0.82)))
        self.pinyin_size_spin.setValue(float(ui.get("pinyin_size_em", 0.62)))
        self.bg_light_btn.set_color(str(ui.get("bg_light", "#e4ecf6")))
        self.bg_dark_btn.set_color(str(ui.get("bg_dark", "#2a303a")))
        self.border_light_btn.set_color(str(ui.get("border_light", "#b0b0b0")))
        self.border_dark_btn.set_color(str(ui.get("border_dark", "#5a5a5a")))
        self.mature_light_btn.set_color(str(ui.get("mature_light", "#2e7d32")))
        self.mature_dark_btn.set_color(str(ui.get("mature_dark", "#81c784")))
        self.suspended_light_btn.set_color(str(ui.get("suspended_light", "#c62828")))
        self.suspended_dark_btn.set_color(str(ui.get("suspended_dark", "#ef9a9a")))
        self.custom_css_edit.setPlainText(str(ui.get("custom_css") or ""))

    @staticmethod
    def _set_combo(combo: QComboBox, value: str) -> None:
        idx = combo.findText(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(value)

    def _restore_defaults(self) -> None:
        if not askUser("Reset all settings (General + Appearance) to defaults?"):
            return
        self._conf = deepcopy(DEFAULT_CONFIG)
        self._load_into_ui()

    def _collect_ui(self) -> dict[str, Any]:
        max_width = self.max_width_edit.text().strip() or "100%"
        return {
            "max_width": max_width,
            "border_radius_px": self.radius_spin.value(),
            "gap_em": round(self.gap_spin.value(), 2),
            "char_size_em": round(self.char_size_spin.value(), 2),
            "word_size_em": round(self.word_size_spin.value(), 2),
            "pinyin_size_em": round(self.pinyin_size_spin.value(), 2),
            "bg_light": self.bg_light_btn.color(),
            "bg_dark": self.bg_dark_btn.color(),
            "border_light": self.border_light_btn.color(),
            "border_dark": self.border_dark_btn.color(),
            "mature_light": self.mature_light_btn.color(),
            "mature_dark": self.mature_dark_btn.color(),
            "suspended_light": self.suspended_light_btn.color(),
            "suspended_dark": self.suspended_dark_btn.color(),
            "show_shadow": True,
            "custom_css": self.custom_css_edit.toPlainText(),
        }

    def _collect(self) -> Optional[dict[str, Any]]:
        word = self.word_combo.currentText().strip()
        if not word:
            showInfo("Please set a Word / Hanzi field name.")
            return None
        meaning = self.meaning_combo.currentText().strip()
        if not meaning:
            showInfo("Please set a Meaning field name.")
            return None

        decks = self.deck_picker.selected_decks()
        if (
            self.deck_picker.has_deck_list()
            and not decks
            and not self.deck_picker.all_decks_selected()
        ):
            showInfo(
                "No decks selected. Choose All decks, or select at least one deck."
            )
            return None

        prev = self._conf
        selected = [d for d, cb in self.delim_checks.items() if cb.isChecked()]
        delim_spec = delimiters_to_spec(selected, self.delim_extra_edit.text())
        if not selected and not (self.delim_extra_edit.text() or "").strip():
            showInfo("Select at least one meaning delimiter.")
            return None

        return {
            "decks": decks,
            "fields": {
                "word": word,
                "pinyin": self.pinyin_combo.currentText().strip() or "Pinyin",
                "meaning": meaning,
            },
            "max_synonyms": self.max_spin.value(),
            "include_suspended": self.include_suspended_toggle.isChecked(),
            "candidate_min_length": self.min_len_spin.value(),
            "show_only_on_back": self.back_only_toggle.isChecked(),
            "show_synonym_counts": self.show_synonym_counts_toggle.isChecked(),
            "meaning_split_delimiters": delim_spec,
            "min_key_length": int(prev.get("min_key_length", 2) or 2),
            "strip_leading_to": bool(prev.get("strip_leading_to", True)),
            "ignore_keys": list(prev.get("ignore_keys") or []),
            "ui": self._collect_ui(),
        }

    def _on_save(self) -> None:
        conf = self._collect()
        if conf is None:
            return
        prev = self._conf
        _save_config(conf)
        self.accept()

        needs_rebuild = (
            conf.get("decks") != prev.get("decks")
            or conf.get("fields") != prev.get("fields")
            or conf.get("meaning_split_delimiters")
            != prev.get("meaning_split_delimiters")
        )

        if needs_rebuild:
            rebuild = askUser(
                "Settings saved.\n\nRebuild the synonym index now?\n"
                "(Recommended after changing decks, fields, or meaning delimiters.)"
            )
            if rebuild:
                if mw.col is None:
                    tooltip("Open a profile first, then rebuild from Settings → General.")
                else:
                    indexer.rebuild_index(show_progress=True, notify=True)
            else:
                tooltip("Settings saved. Rebuild from General → Rebuild Index when ready.")
        else:
            tooltip("Settings saved. Flip a card to see UI changes.")


def open_config() -> bool:
    """
    Entry point for Tools menu and Anki's Config button.

    Returning True (or None) prevents the raw JSON editor from opening.
    """
    if mw.col is None:
        showInfo("Open a profile before changing settings.")
        return True
    dlg = ConfigDialog(mw)
    dlg.exec()
    return True
