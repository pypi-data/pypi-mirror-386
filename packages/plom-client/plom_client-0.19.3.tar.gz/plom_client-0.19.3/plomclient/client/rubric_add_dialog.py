# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2021 Andrew Rechnitzer
# Copyright (C) 2018 Elvis Cai
# Copyright (C) 2019-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2020 Vala Vakilian
# Copyright (C) 2021 Forest Kobayashi
# Copyright (C) 2024 Bryan Tanady
# Copyright (C) 2024 Aidan Murphy

from __future__ import annotations

import re
import sys
from textwrap import shorten
from typing import Any

import arrow
from spellchecker import SpellChecker

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6 import QtGui
from PyQt6.QtGui import (
    QColor,
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QRegularExpressionValidator,
    QTextCursor,
    QMouseEvent,
)

from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QInputDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QToolButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QSplitter,
)

from plomclient.plom_exceptions import PlomNoServerSupportException
from plomclient.misc_utils import next_in_longest_subsequence
from . import icons
from .useful_classes import InfoMsg, WarnMsg, SimpleQuestion


# TODO this object only allows int inputs, replace to allow float scores
class SignedSB(QSpinBox):
    # add an explicit sign to spinbox and no 0
    # range is from -N,..,-1,1,...N
    # note - to fix #1561 include +/- N in this range.
    # else 1 point questions become very problematic
    # TODO: its possible to manually enter zero (Issue #3446) we currently
    # deal with that in the parent
    def __init__(self, maxMark: int) -> None:
        super().__init__()
        self.setRange(-maxMark, maxMark)
        self.setValue(1)

    def stepBy(self, steps):
        self.setValue(self.value() + steps)
        # to skip 0.
        if self.value() == 0:
            self.setValue(self.value() + steps)

    def textFromValue(self, v) -> str:
        t = QSpinBox().textFromValue(v)
        if v > 0:
            return "+" + t
        else:
            return t


class SubstitutionsHighlighter(QSyntaxHighlighter):
    """Highlight tex prefix, parametric substitutions, and spelling mistakes."""

    def __init__(self, *args, **kwargs):
        # TODO: initial value of subs?
        self.subs = []
        super().__init__(*args, **kwargs)
        # TODO: see dynamic spellchecker, future work
        # self.wordRegEx = re.compile(r"\b([A-Za-z]{2,})\b")
        self.speller = SpellChecker(distance=1)

    def highlightBlock(self, text: str | None) -> None:
        self._highlight_prefix(text)
        # TODO: new MR for dynamic spellchecker
        # self._highlight_spelling(text)

    def _highlight_prefix(self, text: str | None):
        """Highlight tex prefix and matches in our substitution list.

        Args:
            text: the text to be highlighted.

        TODO: use colours from the palette?
        """
        if text is None:
            return
        # TODO: can we set a popup: "v2 value: 'x'"
        # reset format
        self.setFormat(0, len(text), QTextCharFormat())
        # highlight tex: at beginning
        if text.casefold().startswith("tex:"):
            self.setFormat(0, len("tex:"), QColor("grey"))
        # highlight parametric substitutions
        for s in self.subs:
            for match in re.finditer(s, text):
                # print(f"matched on {s} at {match.start()} to {match.end()}!")
                frmt = QTextCharFormat()
                frmt.setForeground(QColor("teal"))
                # TODO: not sure why this doesn't work?
                # frmt.setToolTip('v2 subs: "TODO"')
                self.setFormat(match.start(), match.end() - match.start(), frmt)

    # def _highlight_spelling(self, text: str | None):
    #     """Highlight spelling mistakes with red squiggle line.
    #
    #     TODO: Currently unused, pending testing and review in new MR.
    #
    #     Args:
    #         text: the text to be highlighted.
    #     """
    #     if text is None:
    #         return
    #
    #     self.misspelledFormat = QTextCharFormat()
    #     self.misspelledFormat.setUnderlineStyle(
    #         QTextCharFormat.UnderlineStyle.SpellCheckUnderline
    #     )  # Platform and theme dependent
    #     self.misspelledFormat.setUnderlineColor(QColor("red"))
    #
    #     for word_object in self.wordRegEx.finditer(text):
    #         if word_object.group() != "tex" and word_object.group().isalpha():
    #             most_likely_word = self.speller.correction(word_object.group())
    #
    #             if most_likely_word and most_likely_word != word_object.group():
    #                 self.setFormat(
    #                     word_object.start(),
    #                     word_object.end() - word_object.start(),
    #                     self.misspelledFormat,
    #                 )

    def setSubs(self, subs):
        self.subs = subs
        self.rehighlight()


class CorrectionWidget(QFrame):
    def __init__(self):
        """Constructor of the QFrame showing spelling correction suggestions."""
        super().__init__()
        self.speller = SpellChecker(distance=1)
        self.list_widget = QListWidget()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.list_widget.doubleClicked.connect(self.replace_word_from_correction_list)

        self.init_ui()

        # Only show the widget when it's not empty
        self.hide()

    def init_ui(self):
        self.label = QLabel("Suggestions:")
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.replace_word_from_correction_list
        )
        buttons.rejected.connect(self.close)

        # Layouts
        v_layout = QVBoxLayout()
        v_layout.addWidget(self.label)
        v_layout.addWidget(self.list_widget)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)

        h_layout.addWidget(buttons)

    def set_selected_word(self, selected_word: str, cursor: QTextCursor):
        """Request spelling correction for the selected word.

        Args:
            selected_word: the word that will be requested for
            spelling corrections.

            cursor: the text cursor location in WideTextEdit text box.
        """
        self.selected_word = selected_word
        self.cursor_position = cursor
        self.update_suggestions()

    def update_suggestions(self):
        """Update the spelling correction suggestion list."""
        self.list_widget.clear()
        suggestions = self.speller.candidates(self.selected_word)
        capitalized = self.selected_word.istitle()

        # Most probable candidate is set as the first item.
        if suggestions:
            most_probable_candidate = self.speller.correction(self.selected_word)
            if capitalized:
                self.list_widget.addItem(most_probable_candidate.capitalize())
            else:
                self.list_widget.addItem(most_probable_candidate)

            for suggestion in suggestions:
                if suggestion != most_probable_candidate:
                    if capitalized:
                        self.list_widget.addItem(suggestion.capitalize())
                    else:
                        self.list_widget.addItem(suggestion)

        # the first item in the list is the default chosen correction.
        self.list_widget.setCurrentRow(0)
        if self.list_widget.count() > 0:
            self.show()
        else:
            self.hide()

    def replace_word_from_correction_list(self):
        """Replace the selected text with the chosen correction option."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "No Selection", "Please select an option for correction."
            )
            return
        selected_correction = selected_items[0].text()
        cursor = self.cursor_position
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(selected_correction)
        cursor.endEditBlock()
        self.close()


class ShortTextEdit(QTextEdit):
    """Just like QTextEdit but doesn't want to be tall."""

    def sizeHint(self):
        sz = super().sizeHint()
        sz.setHeight(sz.height() // 3)
        return sz


class WideTextEdit(QTextEdit):
    """Just like QTextEdit but with hacked sizeHint() to be wider.

    Also, hacked to ignore shift-enter.
    """

    def __init__(self):
        super().__init__()
        self.speller = SpellChecker(distance=1)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        """Handle double left-click event.

        Only pops up the spelling corrections if the most likely
        replacement word is different from the selected text, and the
        selected text is not empty.

        Note: Ignore the word "tex" and non alphabetical.

        Raises:
            RunTimeError if the AddRubricDialog is uninitialized.
        """
        if not event:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)
            selected_text = self.textCursor().selectedText()
            best_correction = self.speller.correction(selected_text)
            if (
                selected_text.isalpha()
                and selected_text != "tex"
                and len(selected_text)
                and best_correction
                and best_correction != selected_text
            ):
                # The first parent is QSplitter
                splitter = self.parentWidget()
                if splitter:
                    rubric_dialog = splitter.parentWidget()
                else:
                    raise RuntimeError(
                        "Rubric Box Dialog is unexpectedly uninitialized"
                    )

                if isinstance(rubric_dialog, AddRubricDialog):
                    rubric_dialog.correction_widget.set_selected_word(
                        selected_text, self.textCursor()
                    )

    def sizeHint(self):
        sz = super().sizeHint()
        sz.setWidth(sz.width() * 2)
        # 2/3 height of default
        sz.setHeight((sz.height() * 2) // 3)
        return sz

    def keyPressEvent(self, e: QtGui.QKeyEvent | None) -> None:
        if e is not None:
            if e.modifiers() == Qt.KeyboardModifier.ShiftModifier and (
                e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter
            ):
                e.ignore()
                return

            # Reset formatting, otherwise it can unexpectedly adopt the
            # red squiggle line while backspacing.
            # TODO: Decide whether reset format for any key or only backspace
            # What should happen when text is inputted in the middle of
            # the highlighted text?.
            elif e.key() == Qt.Key.Key_Backspace:
                super().keyPressEvent(e)
                self.setCurrentCharFormat(QTextCharFormat())
                return

        super().keyPressEvent(e)

    def highlight_text(self) -> None:
        """Underline the texts that are suspected for spelling mistake.

        The text is underlined with red squiggle line when the most likely
        replacement word is not an empty text and is different from the
        selected text.

        Note: Ignore "tex" and non alphabetical.
        """
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.beginEditBlock()

        # Create a QTextCharFormat for formatting
        format = QTextCharFormat()
        format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        format.setUnderlineColor(QColor("red"))

        start_position = 0
        cursor.setPosition(start_position)
        selected_text = " "
        while not cursor.atEnd():
            cursor.movePosition(
                QTextCursor.MoveOperation.EndOfWord,
                QTextCursor.MoveMode.KeepAnchor,
            )
            selected_text = cursor.selectedText()
            best_correction = self.speller.correction(selected_text)
            if (
                selected_text.isalpha()
                and selected_text != "tex"
                and best_correction
                and best_correction != selected_text
            ):
                cursor.mergeCharFormat(format)
            cursor.movePosition(
                QTextCursor.MoveOperation.NextWord, QTextCursor.MoveMode.MoveAnchor
            )

        cursor.endEditBlock()
        self.setCurrentCharFormat(QTextCharFormat())


class AddRubricDialog(QDialog):
    def __init__(
        self,
        parent,
        username,
        maxMark,
        question_idx,
        question_label,
        version,
        maxver,
        com=None,
        *,
        groups=[],
        reapable=[],
        experimental=False,
        add_to_group=None,
        num_uses=0,
    ):
        """Initialize a new dialog to edit/create a comment.

        Args:
            parent (QWidget): the parent window.
            username (str): who is creating this rubric or who is
                modifying this rubric.
            maxMark (int): the maximum score for this question.
            question_idx (int): which question?
            question_label (str): human-readable label for the question.
            version (int): which version is currently being marked?
            maxver (int): the largest version: versions range from 1
                to this value.
            com (dict/None): if None, we're creating a new rubric.
                Otherwise, this has the current comment data.

        Keyword Args:
            groups (list): optional list of existing/recommended group
                names that the rubric could be added to.
            add_to_group (str/None): preselect this group in the scope
                settings when creating a new rubric.  This must be one
                of the `groups` list above.
            reapable (list): these are used to "harvest" plain 'ol text
                annotations and morph them into comments.
            experimental (bool): whether to enable experimental or advanced
                features.
            num_uses (int/None): how many annotations use this rubric.
                Might also be `None` if the server doesn't support this.

        Raises:
            none expected!
        """
        super().__init__(parent)

        self.use_experimental_features = experimental
        self.question_idx = question_idx
        self.version = version
        self.maxver = maxver
        self._username = username

        self._is_edit = False
        if com:
            self._is_edit = True

        if self.is_edit():
            self.setWindowTitle("Modify rubric")
        else:
            self.setWindowTitle("Add new rubric")

        self.reapable_CB = QComboBox()
        self.TE = WideTextEdit()
        self.correction_widget = CorrectionWidget()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.TE)
        self.splitter.addWidget(self.correction_widget)

        self.hiliter = SubstitutionsHighlighter(self.TE)
        self.relative_value_SB = SignedSB(maxMark)  # QSpinBox allows only int
        self.TEtag = QLineEdit()
        self.TEmeta = ShortTextEdit()
        # cannot edit these
        self.label_rubric_id = QLabel("Will be auto-assigned")
        self.last_modified_label = QLabel()

        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy.setVerticalStretch(3)
        self.splitter.setSizePolicy(sizePolicy)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy.setVerticalStretch(1)
        self.TEmeta.setSizePolicy(sizePolicy)

        flay = QFormLayout()
        flay.addRow("Text", self.splitter)
        lay = QHBoxLayout()
        lay.addItem(
            QSpacerItem(
                32, 10, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
            )
        )
        lay.addWidget(self.reapable_CB)
        if self.use_experimental_features:
            __ = QPushButton("Check Spelling")
            __.clicked.connect(self.TE.highlight_text)
            lay.addWidget(__)
        flay.addRow("", lay)

        frame = QFrame()
        vlay = QVBoxLayout(frame)
        vlay.setContentsMargins(0, 0, 0, 0)
        b = QRadioButton("neutral")
        b.setToolTip("more of a comment, this rubric does not change the mark")
        b.setChecked(True)
        vlay.addWidget(b)
        self.typeRB_neutral = b
        lay = QHBoxLayout()
        b = QRadioButton("relative")
        b.setToolTip("changes the mark up or down by some number of points")
        lay.addWidget(b)
        self.typeRB_relative = b
        # lay.addWidget(self.DE)
        lay.addWidget(self.relative_value_SB)
        self.relative_value_SB.valueChanged.connect(b.click)
        # self.relative_value_SB.clicked.connect(b.click)
        lay.addItem(
            QSpacerItem(16, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        lay.addItem(
            QSpacerItem(
                48, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )
        vlay.addLayout(lay)

        hlay = QHBoxLayout()
        b = QRadioButton("absolute")
        abs_tooltip = "Indicates a score as a part of a maximum possible amount"
        b.setToolTip(abs_tooltip)
        hlay.addWidget(b)
        self.typeRB_absolute = b
        __ = QSpinBox()
        __.setRange(0, maxMark)
        __.setValue(0)
        __.valueChanged.connect(b.click)
        # __.clicked.connect(b.click)
        hlay.addWidget(__)
        self.abs_value_SB = __
        __ = QLabel("out of")
        __.setToolTip(abs_tooltip)
        # _.clicked.connect(b.click)
        hlay.addWidget(__)
        __ = QSpinBox()
        __.setRange(0, maxMark)
        __.setValue(maxMark)
        __.valueChanged.connect(b.click)
        # _.clicked.connect(b.click)
        hlay.addWidget(__)
        self.abs_out_of_SB = __
        hlay.addItem(
            QSpacerItem(
                48, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )
        vlay.addLayout(hlay)
        flay.addRow("Marks", frame)

        # scope
        self.scopeButton = QToolButton()
        self.scopeButton.setCheckable(True)
        self.scopeButton.setChecked(False)
        self.scopeButton.setAutoRaise(True)
        self.scopeButton.setText("Scope")
        self.scopeButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.scopeButton.clicked.connect(self.toggle_scope_elements)
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.scope_frame = frame
        flay.addRow(self.scopeButton, frame)
        vlay = QVBoxLayout(frame)
        cb = QCheckBox(
            f'specific to question "{question_label}" (index {question_idx})'
        )
        cb.setEnabled(False)
        cb.setChecked(True)
        vlay.addWidget(cb)
        # For the future, once implemented:
        # label = QLabel("Specify a list of question indices to share this rubric.")
        # label.setWordWrap(True)
        # vlay.addWidget(label)
        vlay.addWidget(QLabel("<hr>"))
        lay = QHBoxLayout()
        cb = QCheckBox("specific to version(s)")
        cb.stateChanged.connect(self.toggle_version_specific)
        lay.addWidget(cb)
        self.version_specific_cb = cb
        le = QLineEdit()

        # Regular expression for validating version list
        #
        #   whitespace only or...
        #       ╭─┴─╮
        re = r"(^\s*$|^\s*(\d+\s*,\s*)*(\d+)\s*$)"
        #             │   ╰──┬───────╯│╰─┬─╯└ trailing whitespace
        #             │      │        │  └ final number
        #             │      │        └ can repeat
        #             │      └ number and comma
        #             └ leading whitespace
        #
        # "1, 2,3" acceptable; "1,2, " intermediate; ",2" unacceptable
        le.setValidator(QRegularExpressionValidator(QRegularExpression(re), self))
        lay.addWidget(le)
        self.version_specific_le = le
        space = QSpacerItem(
            48, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.version_specific_space = space
        lay.addItem(space)
        vlay.addLayout(lay)
        if maxver > 1:
            s = "<p>By default, rubrics are shared between versions of a question.<br />"
            s += "You can also parameterize using version-specific substitutions.</p>"
        else:
            s = "<p>By default, rubrics are shared between versions of a question.</p>"
        vlay.addWidget(QLabel(s))
        self._param_grid = QGridLayout()  # placeholder
        vlay.addLayout(self._param_grid)
        vlay.addWidget(QLabel("<hr>"))
        hlay = QHBoxLayout()
        self.group_checkbox = QCheckBox("Associate with the group ")
        hlay.addWidget(self.group_checkbox)
        b = QComboBox()
        # b.setEditable(True)
        # b.setDuplicatesEnabled(False)
        b.addItems(groups)
        b.setMinimumContentsLength(5)
        # changing the group ticks the group checkbox
        b.activated.connect(lambda: self.group_checkbox.setChecked(True))
        hlay.addWidget(b)
        self.group_combobox = b
        b = QToolButton(text="\N{HEAVY PLUS SIGN}")
        b.setToolTip("Add new group")
        b.setAutoRaise(True)
        b.clicked.connect(self.add_new_group)
        self.group_add_btn = b
        hlay.addWidget(b)
        # b = QToolButton(text="\N{HEAVY MINUS SIGN}")
        # b.setToolTip("Delete currently-selected group")
        # b.setAutoRaise(True)
        # hlay.addWidget(b)
        hlay.addItem(
            QSpacerItem(
                48, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )
        b = QToolButton(text="What are groups?")
        b.setAutoRaise(True)
        msg = """<p>Groups are intended for multi-part questions.
              For example, you could make groups &ldquo;(a)&rdquo;,
              &ldquo;(b)&rdquo; and &ldquo;(c)&rdquo;.
              Some tips:</p>
            <ul>
            <li><b>This is a new feature:</b> you may want to discuss
              with your team before using groups.</li>
            <li>Groups create automatic tabs, shared with other users.
              <b>Other users may need to click the &ldquo;sync&rdquo; button.</b>
            </li>
            <li>Making a rubric <em>exclusive</em> means it cannot be used alongside
              others from the same exclusion group.</li>
            <li>Groups will disappear automatically if there are no
              rubrics in them.</li>
            <ul>
        """
        b.clicked.connect(lambda: InfoMsg(self, msg).exec())
        hlay.addWidget(b)
        vlay.addLayout(hlay)
        hlay = QHBoxLayout()
        hlay.addSpacing(24)
        # TODO: note default for absolute rubrics?  (once it is the default)
        c = QCheckBox("Exclusive in this group (at most one such rubric can be placed)")
        hlay.addWidget(c)
        self.group_excl = c
        self.group_checkbox.toggled.connect(lambda x: self.group_excl.setEnabled(x))
        self.group_checkbox.toggled.connect(lambda x: self.group_combobox.setEnabled(x))
        self.group_checkbox.toggled.connect(lambda x: self.group_add_btn.setEnabled(x))
        # TODO: connect self.typeRB_neutral etc change to check/uncheck the exclusive button
        self.group_excl.setChecked(False)
        self.group_excl.setEnabled(False)
        self.group_combobox.setEnabled(False)
        self.group_add_btn.setEnabled(False)
        self.group_checkbox.setChecked(False)
        vlay.addLayout(hlay)
        self.toggle_version_specific()
        self.toggle_scope_elements()

        # TODO: in the future?
        hlay = QHBoxLayout()
        hlay.addWidget(self.TEtag)
        self.label_pedagogy_tags = QLabel("")
        self.label_pedagogy_tags.setVisible(False)
        hlay.addWidget(self.label_pedagogy_tags)
        flay.addRow("Tags", hlay)
        self.TEtag.setEnabled(False)
        flay.addRow("Meta", self.TEmeta)

        flay.addRow("Rubric ID", self.label_rubric_id)
        flay.addRow("", self.last_modified_label)

        # Usage info and major/minor change
        self.usage_button = QToolButton()
        self.usage_button.setCheckable(True)
        self.usage_button.setChecked(False)
        if num_uses:
            self.usage_button.setChecked(True)
        self.usage_button.setAutoRaise(True)
        self.update_usage_button(num_uses)
        self.usage_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.usage_button.clicked.connect(self.toggle_usage_panel)
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        vlay = QVBoxLayout(frame)
        self._major_minor_frame = frame
        flay.addRow(self.usage_button, frame)
        # vlay.setContentsMargins(0, 0, 0, 0)

        b = QRadioButton(
            "This is a major edit; all tasks using this rubric should be revisited."
        )
        b.setToolTip('The "revision" number will increase; "track changes" enabled')
        self.majorRB = b
        b.setChecked(True)
        vlay.addWidget(b)
        # QCheckBox does not itself do html
        cb = QCheckBox('Also tag all tasks with "rubric_changed"')
        cb.setChecked(True)
        self.tagtasksCB = cb

        def _on_major_checkbox_change(checked):
            if checked:
                cb.setEnabled(True)
                cb.setChecked(True)
            else:
                cb.setEnabled(False)
                cb.setChecked(False)

        self.majorRB.toggled.connect(_on_major_checkbox_change)
        hlay = QHBoxLayout()
        hlay.addSpacing(24)
        hlay.addWidget(cb)
        vlay.addLayout(hlay)
        b = QRadioButton(
            "This is minor edit; I don't want to update any existing tasks."
        )
        b.setToolTip('The "revision" number will stay the same; no "track changes"')
        self.minorRB = b
        vlay.addWidget(b)
        b = QRadioButton("Server default / let server autodetect.")
        # b.setToolTip("Roughly: major changes for student-visible edits")
        b.setToolTip(
            "Currently (0.19.x) the server defaults to major edits, subject to change."
        )
        vlay.addWidget(b)
        self.toggle_usage_panel()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # if self.is_edit():
        #     # TODO: this would need to fresh everything, not just count
        #     __ = QPushButton("\N{ANTICLOCKWISE OPEN CIRCLE ARROW} Refresh")
        #     __.clicked.connect(self.refresh_usage)
        #     buttons.addButton(__, QDialogButtonBox.ButtonRole.ActionRole)

        vlay = QVBoxLayout()
        vlay.addLayout(flay)
        vlay.addWidget(buttons)
        self.setLayout(vlay)

        self._formlayout = flay

        # set up widgets
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if reapable:
            self.reapable_CB.addItem("")
            reaplabels = [shorten(x.strip(), 42, placeholder="...") for x in reapable]
            self.reapable_CB.addItems(reaplabels)
            self._list_of_reapables = reapable
            self.reapable_CB.setToolTip("Take from text annotations")
        else:
            self.reapable_CB.setEnabled(False)
            self.reapable_CB.setToolTip("Take from text annotations (none available)")
            self.reapable_CB.setVisible(False)
        # Set up TE and CB so that when CB changed, text is updated
        self.reapable_CB.currentIndexChanged.connect(self.changedReapableCB)

        # the rubric may have fields we don't modify: keep a copy around
        self._old_rubric = {} if not com else com.copy()
        params = []
        # If supplied with current text/delta then set them
        if com:
            if com["text"]:
                self.TE.clear()
                self.TE.insertPlainText(com["text"])
            self.TEmeta.insertPlainText(com.get("meta", ""))
            if com["kind"]:
                if com["kind"] == "neutral":
                    self.typeRB_neutral.setChecked(True)
                elif com["kind"] == "relative":
                    self.relative_value_SB.setValue(int(com["value"]))  # int rubrics
                    self.typeRB_relative.setChecked(True)
                elif com["kind"] == "absolute":
                    self.abs_value_SB.setValue(int(com["value"]))  # int rubrics
                    self.abs_out_of_SB.setValue(int(com["out_of"]))  # int rubrics
                    self.typeRB_absolute.setChecked(True)
                else:
                    raise RuntimeError(f"unexpected kind in {com}")
            if com.get("rid"):
                self.label_rubric_id.setText(str(com["rid"]))
            s = ""
            lastmod = com.get("last_modified", "unknown")
            # Note sure it would be None but seems harmless (or no more harmful
            # than "unknown" sentinel from legacy anyway)
            if lastmod is not None and lastmod != "unknown":
                rev = com.get("revision", 0)
                s += f"revision {rev}"
                if rev > 0:
                    s += f", last modified {arrow.get(lastmod).humanize()}"
                    s += f' by {com["modified_by_username"]}'
                s += ", "
            s += f'created by {com.get("username", "unknown")}'
            self.last_modified_label.setText(s)
            self.last_modified_label.setWordWrap(True)
            if com.get("versions"):
                self.version_specific_cb.setChecked(True)
                self.version_specific_le.setText(com.get("versions"))
            params = com.get("parameters", [])
            if not params:
                # in case it was empty string or None or ...
                params = []
            tags = com.get("tags", "").split()
            # TODO: Python >= 3.9: t.removeprefix("exclusive:")
            exclusive_tags = [
                t[len("exclusive:") :] for t in tags if t.startswith("exclusive:")
            ]
            group_tags = [t[len("group:") :] for t in tags if t.startswith("group:")]

            if len(group_tags) == 0:
                self.group_checkbox.setChecked(False)
            elif len(group_tags) == 1:
                self.group_checkbox.setChecked(True)
                (g,) = group_tags
                if g not in groups:
                    self.group_combobox.insertItem(-1, g)
                self.group_combobox.setCurrentText(g)
            else:
                self.group_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
                self.group_combobox.setEnabled(False)

            if len(exclusive_tags) == 0:
                self.group_excl.setChecked(False)
            elif len(exclusive_tags) == 1:
                self.group_excl.setChecked(True)
            else:
                self.group_excl.setCheckState(Qt.CheckState.PartiallyChecked)

            if not group_tags and not exclusive_tags:
                pass
            elif len(group_tags) == 1 and not exclusive_tags:
                (g,) = group_tags
                tags.remove(f"group:{g}")
            elif len(group_tags) == 1 and group_tags == exclusive_tags:
                (g,) = group_tags
                (excl,) = exclusive_tags
                tags.remove(f"exclusive:{excl}")
                tags.remove(f"group:{g}")
            else:
                # not UI representable: disable UI controls
                self.group_checkbox.setEnabled(False)
                self.group_combobox.setEnabled(False)
                self.group_excl.setEnabled(False)
                self.TEtag.setEnabled(True)
            # repack the tags
            self.TEtag.setText(" ".join(tags))

            if com.get("pedagogy_tags"):
                self.label_pedagogy_tags.setText(
                    "Pedagogy tags: " + ", ".join(com["pedagogy_tags"])
                )
                self.label_pedagogy_tags.setVisible(True)

        else:
            self.TE.setPlaceholderText(
                "Your rubric must contain some text.\n\n"
                'Prepend with "tex:" to use latex.\n\n'
                "You can harvest existing text from the page.\n\n"
                'Change "Marks" below to associate a point-change.'
            )
            self.TEtag.setPlaceholderText(
                "Currently not user-editable, used for grouping."
            )
            self.TEmeta.setPlaceholderText(
                "Notes about this rubric such as hints on when to use it.\n\n"
                "Not shown to student!"
            )
            self.last_modified_label.setText(
                f"You ({self._username}) are creating a new rubric"
            )
            self._formlayout.setRowVisible(self._major_minor_frame, False)

            if add_to_group:
                assert add_to_group in groups, f"{add_to_group} not in groups={groups}"
                self.group_checkbox.setChecked(True)
                self.group_combobox.setCurrentText(add_to_group)
                # show the user we did this by opening the scope panel
                self.scopeButton.animateClick()
        self.subsRemakeGridUI(params)
        self.hiliter.setSubs([x for x, __ in params])

    def is_edit(self):
        """Answer true if we are editing a rubric (rather than making a new one)."""
        return self._is_edit

    def subsMakeGridUI(self, params):
        maxver = self.maxver
        grid = QGridLayout()
        nr = 0
        if params:
            for v in range(maxver):
                grid.addWidget(QLabel(f"ver {v + 1}"), nr, v + 1)
            nr += 1

        def _func_factory(zelf, i):
            def f():
                zelf.subsRemoveRow(i)

            return f

        for i, (param, values) in enumerate(params):
            w = QLineEdit(param)
            # w.connect...  # TODO: redo syntax highlighting?
            grid.addWidget(w, nr, 0)
            for v in range(maxver):
                w = QLineEdit(values[v])
                w.setPlaceholderText(f"<value for ver{v + 1}>")
                grid.addWidget(w, nr, v + 1)
            b = QToolButton(text="\N{HEAVY MINUS SIGN}")
            b.setToolTip("remove this parameter and values")
            b.setAutoRaise(True)
            f = _func_factory(self, i)
            b.pressed.connect(f)
            grid.addWidget(b, nr, maxver + 1)
            nr += 1

        if params:
            b = QToolButton(text="\N{HEAVY PLUS SIGN} add another")
        else:
            b = QToolButton(text="\N{HEAVY PLUS SIGN} add a parameterized substitution")
        b.setAutoRaise(True)
        b.pressed.connect(self.subsAddRow)
        b.setToolTip("Inserted at cursor point; highlighted text as initial value")
        self.addParameterButton = b
        grid.addWidget(b, nr, 0)
        nr += 1
        return grid

    def subsAddRow(self):
        params = self.get_parameters()
        current_param_names = [p for p, __ in params]
        # find a new parameter name not yet used
        n = 1
        while True:
            new_param = "{param" + str(n) + "}"
            new_param_alt = f"<param{n}>"
            if (
                new_param not in current_param_names
                and new_param_alt not in current_param_names
            ):
                break
            n += 1
        if self.TE.toPlainText().casefold().startswith("tex:"):
            new_param = new_param_alt

        # we insert the new parameter at the cursor/selection
        tc = self.TE.textCursor()
        # save the selection as the new parameter value for this version
        values = ["" for __ in range(self.maxver)]
        if tc.hasSelection():
            values[self.version - 1] = tc.selectedText()
        params.append([new_param, values])
        self.hiliter.setSubs([x for x, __ in params])
        self.TE.textCursor().insertText(new_param)
        self.subsRemakeGridUI(params)

    def subsRemoveRow(self, i=0):
        params = self.get_parameters()
        params.pop(i)
        self.hiliter.setSubs([x for x, __ in params])
        self.subsRemakeGridUI(params)

    def subsRemakeGridUI(self, params):
        # discard the old grid and sub in a new one
        idx = self.scope_frame.layout().indexOf(self._param_grid)
        # print(f"discarding old grid at layout index {idx} to build new one")
        layout = self.scope_frame.layout().takeAt(idx)
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()
        layout.deleteLater()
        grid = self.subsMakeGridUI(params)
        # self.scope_frame.layout().addLayout(grid)
        self.scope_frame.layout().insertLayout(idx, grid)
        self._param_grid = grid

    def get_parameters(self) -> list[tuple[str, list[str]]]:
        """Extract the current parametric values from the UI."""
        idx = self.scope_frame.layout().indexOf(self._param_grid)
        # print(f"extracting parameters from grid at layout index {idx}")
        layout = self.scope_frame.layout().itemAt(idx)
        N = layout.rowCount()
        params = []
        for r in range(1, N - 1):
            param = layout.itemAtPosition(r, 0).widget().text()
            values = []
            for c in range(1, self.maxver + 1):
                values.append(layout.itemAtPosition(r, c).widget().text())
            params.append((param, values))
        return params

    def add_new_group(self):
        groups = []
        for n in range(self.group_combobox.count()):
            groups.append(self.group_combobox.itemText(n))
        suggested_name = next_in_longest_subsequence(groups)
        s, ok = QInputDialog.getText(
            self,
            "New group for rubric",
            "<p>New group for rubric.</p><p>(Currently no spaces allowed.)</p>",
            QLineEdit.EchoMode.Normal,
            suggested_name,
        )
        if not ok:
            return
        s = s.strip()
        if not s:
            return
        if " " in s:
            return
        n = self.group_combobox.count()
        self.group_combobox.insertItem(n, s)
        self.group_combobox.setCurrentIndex(n)

    def changedReapableCB(self, idx: int) -> None:
        if idx <= 0:
            # -1 for newly-empted combobox
            # 0 for selecting the first empty placeholder
            # In either case, user might be surprised by clearing the text
            return
        self.TE.clear()
        self.TE.insertPlainText(self._list_of_reapables[idx - 1])

    def toggle_version_specific(self):
        if self.version_specific_cb.isChecked():
            self.version_specific_le.setText(str(self.version))
            self.version_specific_le.setPlaceholderText("")
            self.version_specific_le.setEnabled(True)
        else:
            self.version_specific_le.setText("")
            self.version_specific_le.setPlaceholderText(
                ", ".join(str(x + 1) for x in range(self.maxver))
            )
            self.version_specific_le.setEnabled(False)

    def toggle_scope_elements(self):
        """Show or hide the panel of "scoping" options for rubrics."""
        if self.scopeButton.isChecked():
            self.scopeButton.setArrowType(Qt.ArrowType.DownArrow)
            # QFormLayout.setRowVisible but only in Qt 6.4!
            # instead we are using a QFrame
            self.scope_frame.setVisible(True)
            # self._formlayout.setRowVisible(self.scope_frame, False)
        else:
            self.scopeButton.setArrowType(Qt.ArrowType.RightArrow)
            self.scope_frame.setVisible(False)
            # self._formlayout.setRowVisible(self.scope_frame, True)

    def toggle_usage_panel(self):
        """Show or hide the panel of "usage" options for rubrics."""
        if self.usage_button.isChecked():
            self.usage_button.setArrowType(Qt.ArrowType.DownArrow)
            self._major_minor_frame.setVisible(True)
        else:
            self.usage_button.setArrowType(Qt.ArrowType.RightArrow)
            self._major_minor_frame.setVisible(False)

    def update_usage_button(self, n: int | None) -> None:
        """Update a button in the interface."""
        if n is None:
            self.usage_button.setText("Used: ??")
            self.usage_button.setToolTip(
                "Unknown how many annotations use this rubric "
                "[perhaps no server support?]\n"
                "Click to expand for options"
            )
        elif n:
            self.usage_button.setText(f"Used: {n}")
            self.usage_button.setToolTip(
                f"Currently, {n} saved annotations use this rubric.\n"
                "Click to expand for options"
            )
        else:
            self.usage_button.setText("Unused")
            self.usage_button.setToolTip(
                "Currently, this rubric isn't used in any saved annotations.\n"
                "Click to expand for options"
            )

    def refresh_usage(self):
        """Ask Annotator to call the server the find out how many tasks use this rubric.

        Currently unused.
        """
        if not self.is_edit():
            return
        # TODO: No no use signals slots or something, not like this
        annotr = self.parent()._parent
        rid = self.label_rubric_id.text()
        try:
            N = len(annotr.getOtherRubricUsagesFromServer(rid))
        except PlomNoServerSupportException as e:
            InfoMsg(self, str(e)).exec()
            return
        self.update_usage_button(N)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier and (
            event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter
        ):
            # print("Dialog: Shift-Enter event")
            event.accept()
            self.accept()
            return
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and (
            event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter
        ):
            # print("Dialog: Ctrl-Enter event")
            event.accept()
            txt = self.TE.toPlainText().strip()
            if not txt.casefold().startswith("tex:"):
                self.TE.setText("tex: " + self.TE.toPlainText())
            self.accept()
            return
        return super().keyPressEvent(event)

    def accept(self):
        """Make sure rubric is valid before accepting."""
        if self.relative_value_SB.value() == 0:
            # Issue #3446: could also try to fix in the spinbox code
            WarnMsg(self, "Relative rubric cannot be zero.").exec()
            return
        if not self.version_specific_le.hasAcceptableInput():
            WarnMsg(
                self, '"Versions" must be a comma-separated list of positive integers.'
            ).exec()
            return

        txt = self.TE.toPlainText().strip()
        if len(txt) <= 0 or txt.casefold() == "tex:":
            WarnMsg(
                self,
                "Your rubric must contain some text.",
                info="No whitespace only rubrics.",
                info_pre=False,
            ).exec()
            return
        if txt == ".":
            WarnMsg(
                self,
                f"Invalid text &ldquo;<tt>{txt}</tt>&rdquo; for rubric",
                info="""
                   <p>A single full-stop has meaning internally (as a sentinel),
                   so we cannot let you make one.  See
                   <a href="https://gitlab.com/plom/plom/-/issues/2421">Issue #2421</a>
                   for details.</p>
                """,
                info_pre=False,
            ).exec()
            return
        if not txt.casefold().startswith("tex:") and txt.count("$") >= 2:
            # Image by krzysiu, CC-PDDC, https://openclipart.org/detail/213508/crazy-paperclip
            res = resources.files(icons) / "crazy_paperclip.svg"
            pix = QPixmap()
            pix.loadFromData(res.read_bytes())
            pix = pix.scaledToHeight(150, Qt.TransformationMode.SmoothTransformation)
            if (
                SimpleQuestion.ask(
                    self,
                    "<p>It looks like you might be writing some mathematics!</p",
                    """
                        <p>I noticed more than one dollar sign in your text:
                        do you want to render this rubric with LaTeX?</p>
                        <p>(You can avoid seeing this dialog by prepending your
                        rubric with &ldquo;<tt>tex:</tt>&rdquo;)</p>
                    """,
                    icon_pixmap=pix,
                )
                == QMessageBox.StandardButton.Yes
            ):
                self.TE.setText("tex: " + txt)
        super().accept()

    def _gimme_rubric_tags(self):
        tags = self.TEtag.text().strip()
        if not self.group_checkbox.isEnabled():
            # non-handled cases (such as multiple groups) disable these widgets
            return tags
        if self.group_checkbox.isChecked():
            group = self.group_combobox.currentText()
            if not group:
                return tags
            if " " in group:
                # quote spaces in future?
                group = '"' + group + '"'
                raise NotImplementedError("groups with spaces not implemented")
            if self.group_excl.isChecked():
                tag = f"group:{group} exclusive:{group}"
            else:
                tag = f"group:{group}"
            if tags:
                tags = tag + " " + tags
            else:
                tags = tag
        return tags

    def gimme_rubric_data(self) -> dict[str, Any]:
        txt = self.TE.toPlainText().strip()  # we know this has non-zero length.
        tags = self._gimme_rubric_tags()

        meta = self.TEmeta.toPlainText().strip()
        if self.typeRB_neutral.isChecked():
            kind = "neutral"
            value = 0
            out_of = 0
            display_delta = "."
        elif self.typeRB_relative.isChecked():
            kind = "relative"
            value = self.relative_value_SB.value()
            out_of = 0
            display_delta = str(value) if value < 0 else f"+{value}"
        elif self.typeRB_absolute.isChecked():
            kind = "absolute"
            value = self.abs_value_SB.value()
            out_of = self.abs_out_of_SB.value()
            display_delta = f"{value} of {out_of}"
        else:
            raise RuntimeError("no radio was checked")

        if not self.version_specific_cb.isChecked():
            vers = ""
        else:
            vers = self.version_specific_le.text()

        params = self.get_parameters()

        rubric = self._old_rubric
        rubric.update(
            {
                "kind": kind,
                "display_delta": display_delta,
                "value": value,
                "out_of": out_of,
                "text": txt,
                "tags": tags,
                "meta": meta,
                "question": self.question_idx,
                "versions": vers,
                "parameters": params,
            }
        )
        if not self.is_edit():
            rubric.update(
                {
                    "username": self._username,
                }
            )

        return rubric

    def gimme_change_options(self) -> tuple[bool | None, bool | None]:
        """Return whether this is minor change, and whether to tag tasks."""
        if self.majorRB.isChecked():
            if self.tagtasksCB.isChecked():
                return False, True
            else:
                return False, False
        elif self.minorRB.isChecked():
            # TODO: in principle, one could tag tasks for minor edits...
            return True, None
        else:
            return None, None
