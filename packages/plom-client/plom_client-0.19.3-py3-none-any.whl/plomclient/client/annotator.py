# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Andrew Rechnitzer
# Copyright (C) 2018 Elvis Cai
# Copyright (C) 2019-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2022 Joey Shi
# Copyright (C) 2022 Natalia Accomazzo Scotti
# Copyright (C) 2024 Bryan Tanady
# Copyright (C) 2025 Brody Sanderson
# Copyright (C) 2025 Deep Shah

from __future__ import annotations

import html
import json
import logging
import os
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from PyQt6 import QtGui, uic
from PyQt6.QtCore import (
    QElapsedTimer,
    Qt,
    QSize,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QCursor,
    QIcon,
    QKeySequence,
    QPixmap,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QBoxLayout,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsRectItem,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from plomclient.misc_utils import pprint_score, unpack_task_code
from plomclient.rubric_utils import check_for_illadvised
from . import cursors, icons, ui_files
from .rubric_list import RubricWidget
from .key_wrangler import get_key_bindings
from .key_help import KeyHelp

from .pagerearranger import RearrangementViewer
from .viewers import WholeTestView, PreviousPaperViewer
from .pagescene import PageScene
from .pageview import PageView
from .useful_classes import ErrorMsg, WarnMsg, InfoMsg
from .useful_classes import SimpleQuestion, SimpleQuestionCheckBox
from .useful_classes import _json_path_to_str


log = logging.getLogger("annotr")

# Short descriptions of each tool to display to user.
tipText = {
    "box": "Box: L = highlighted box, R/Shift = highlighted ellipse.",
    "rubric": "Rubric: L = paste rubric, R/Shift = labelled box",
    "cross": "Cross: L = cross, M/Ctrl = ?-mark, R/Shift = checkmark.",
    "delete": "Delete: L = Delete object, L-drag = delete area.",
    "line": "Line: L = straight line, M/Ctrl = double-arrow, R/Shift = arrow.",
    "move": "Move object.",
    "pan": "Pan view.",
    "pen": (
        "Pen: L = freehand pen, M/Ctrl = pen with arrows, "
        + "R/Shift = freehand highlighter."
    ),
    "redo": "Redo last action",
    "text": "Text: Enter = newline, Shift-Enter/ESC = finish.",
    "tick": "Tick: L = checkmark, M/Ctrl = ?-mark, R/Shift = cross.",
    "undo": "Undo last action",
    "zoom": "Zoom: L = Zoom in, R = zoom out.",
}


class Annotator(QWidget):
    """The main annotation widget for annotating groups of images."""

    annotator_upload = pyqtSignal(str, list)
    annotator_done_closing = pyqtSignal(str)
    annotator_done_reject = pyqtSignal(str)
    cleanChanged = pyqtSignal(bool)

    def __init__(self, username: str, parentMarkerUI=None, initialData=None) -> None:
        """Initializes a new annotator widget.

        Args:
            username (str): username of Marker
            parentMarkerUI (MarkerClient): the parent of annotator UI.
            initialData (dict): as documented by the arguments to "load_new_question"
        """
        super().__init__()

        parentMarkerUI.tags_changed_signal.connect(self.tags_changed)

        self.username = username
        self.parentMarkerUI = parentMarkerUI

        # these three should probably be kept consistent
        self.task: str | None = None
        self.papernum: int | None = None
        self.question_idx: int | None = None

        # a key-value store for local config, including "don't ask me again"
        self._config: Dict[str, Any] = {}

        self.testName = None
        self.paperDir = None
        self.saveName: Path | None = None
        self.maxMark = 0

        # help mypy understand stuff coming from uic
        self.splitter: QSplitter
        self.hideableBox: QFrame
        self.hamMenuButton: QToolButton
        self.saveNextButton: QToolButton
        self.arrangePagesButton: QToolButton
        self.toolsLayout: QBoxLayout
        self.zoomCB: QComboBox
        self.helpButton: QToolButton
        self.boxButton: QToolButton
        self.tickButton: QToolButton
        self.crossButton: QToolButton
        self.deleteButton: QToolButton
        self.lineButton: QToolButton
        self.moveButton: QToolButton
        self.panButton: QToolButton
        self.penButton: QToolButton
        self.textButton: QToolButton
        self.zoomButton: QToolButton
        self.undoButton: QToolButton
        self.redoButton: QToolButton
        self.pageFrame: QFrame
        self.container_rubricwidget: QBoxLayout
        self.markLabel: QLabel
        self.attnFrame: QFrame
        self.attnLeftLabel: QLabel
        self.attnRightLabel: QLabel
        self.attnClearButton: QPushButton
        self.attnTagsButton: QPushButton
        self.attnDismissButton: QPushButton
        uic.loadUi(resources.files(ui_files) / "annotator.ui", self)
        # TODO: temporary workaround
        self.ui = self

        self.ui.attnDismissButton.clicked.connect(self.dismiss_attn_bar)
        self.ui.attnTagsButton.clicked.connect(self.tag_paper)

        # ordered list of minor mode tools, must match the UI order
        self._list_of_minor_modes = ["tick", "cross", "text", "line", "box", "pen"]
        # current or last used tool, tracked so we can switch back
        self._which_tool = self._list_of_minor_modes[0]

        self.wideLayout()

        self.update_attn_bar()

        # Set up the graphicsview and graphicsscene of the group-image
        # loads in the image etc
        self.view = PageView(self)
        l = self.ui.pageFrame.layout()
        assert l is not None
        assert isinstance(l, QVBoxLayout)
        l.addWidget(self.view)
        # add in another save/next button bottom-right
        self._bottom_toolbar = QFrame()
        snb_l = QHBoxLayout()
        self.another_save_next_button = QPushButton("Save && Next")
        snb_l.addStretch()
        snb_l.addWidget(self.another_save_next_button)
        self._bottom_toolbar.setLayout(snb_l)
        self._bottom_toolbar.setContentsMargins(0, 0, 0, 0)
        snb_l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(self._bottom_toolbar)
        self._bottom_toolbar.setVisible(False)
        # initially not visible

        # Create the rubric list widget and put into gui.
        self.rubric_widget = RubricWidget(self)
        self.ui.container_rubricwidget.addWidget(self.rubric_widget, 2)

        # pass the marking style to the rubric-widget
        # also when we set this up we have to connect various
        # mark set, mark change functions
        self.scene = None  # TODO?

        # set the zoom combobox
        self.setZoomComboBox()
        # Set the tool icons
        self.setAllIcons()
        # Set up cursors
        self.loadCursors()
        # set up held_crop_rectangle - if none, then not holding.
        self.held_crop_rectangle_data = None

        # Connect all the buttons to relevant functions
        self.setButtons()

        self.timer = QElapsedTimer()

        self.modeInformation = ["move"]

        # unit tests might pass None to avoid mocking support code
        if initialData:
            self.load_new_question(*initialData)
            self.rubric_widget.setInitialRubrics()

        self._load_window_settings_early()

        # no initial keybindings - get from the marker if non-default
        self.keybinding_name = self.parentMarkerUI.annotatorSettings["keybinding_name"]
        if self.keybinding_name is None:
            self.keybinding_name = "default"
            log.info('starting with default keybinding "%s"', self.keybinding_name)
        else:
            log.info('loaded previous keybinding "%s"', self.keybinding_name)
        # TODO: store this in annotatorSettings too
        self.keybinding_custom_overlay = self.parentMarkerUI.annotatorSettings[
            "keybinding_custom_overlay"
        ]
        if self.keybinding_custom_overlay is None:
            self.keybinding_custom_overlay = {}
            log.info("starting new (empty) custom overlay")
        else:
            log.info("loaded custom overlay: %s", self.keybinding_custom_overlay)

        # Note: this isn't a real user-interactive splitter right now, so
        # why have it at all?  It helps me resize dynamically with setSizes()
        self.ui.splitter.setChildrenCollapsible(False)
        # self.ui.splitter.setCollapsible(0, False)
        # self.ui.splitter.setCollapsible(1, False)
        h = self.ui.splitter.handle(1)
        assert h is not None
        h.setEnabled(False)

        self.ui.hamMenuButton.setMenu(self.build_hamburger())
        # heaven == hamburger? works for me!
        self.ui.hamMenuButton.setText("\N{TRIGRAM FOR HEAVEN}")
        self.ui.hamMenuButton.setToolTip("Menu (F10)")
        self.ui.hamMenuButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolShortCuts()
        self.setMinorShortCuts()
        self._load_window_settings_late()

    def update_attn_bar(
        self, *, tags: list[str] = [], msg: str = "", show: bool = False
    ) -> None:
        """Update the attention bar to show notifications to the user.

        Note: calling this twice will hide the previous message, so you
        cannot currently call attention to multiple situations automatically.
        Perhaps a future revision would create new bars on each call, and
        destroy them on dismiss.

        Keyword Args:
            show: force showing the notification (default: False).
            tags: a list of tags: if non-empty we'll generate appropriate
                text and show the notification bar.
            msg: a text message to show.  Can include html (so you may
                need to html-escape it first).
        """
        # TODO: share with Identifier?
        warning_yellow_style = "background-color: #FFD700; color: #000"
        self.ui.attnFrame.setStyleSheet(warning_yellow_style)
        notification_str = ""
        secondary_explanation = ""
        if tags:
            tagstr = ", ".join(f"&ldquo;{html.escape(t)}&rdquo;" for t in tags)
            notification_str += f"<p>This task is tagged {tagstr}</p>"
        if msg:
            notification_str += f"<p>{msg}</p>"
        self.ui.attnLeftLabel.setText(notification_str)
        self.ui.attnRightLabel.setText(secondary_explanation)
        # self.ui.attnRightLabel.setVisible(False)  # not yet used
        self.ui.attnClearButton.setVisible(False)  # not yet used
        if show or notification_str:
            self.ui.attnFrame.setVisible(True)
        else:
            self.ui.attnFrame.setVisible(False)

    def dismiss_attn_bar(self) -> None:
        self.ui.attnFrame.setVisible(False)

    def getScore(self):
        return self.scene.getScore()

    def toggle_hold_crop(self, checked):
        if checked:
            if not self.scene:
                # unfort. backref instance var: if no scene, prevent checking
                self._hold_crop_checkbox.setChecked(False)
                return
            self.held_crop_rectangle_data = (
                self.scene.current_crop_rectangle_as_proportions()
            )
            log.debug(f"Hold crop for upcoming pages = {self.held_crop_rectangle_data}")
        else:
            log.debug("Released crop")
            self.held_crop_rectangle_data = None

    def toggle_experimental(self, checked):
        if not checked:
            self.parentMarkerUI.set_experimental(False)
            # TODO: some kind of signal/slot, ontoggle...
            self._hold_crop_checkbox.setVisible(False)
            if self.scene:
                self.scene.remove_page_action_buttons()
            return

        txt = """<p>Enable experimental and/or advanced options?</p>
            <p>If you are part of a large marking team, you should
            probably discuss with your manager before enabling.</p>
        """
        # features = (
        #     'None, but you can help us break stuff at <a href="https://gitlab.com/plom/plom">gitlab.com/plom/plom</a>',
        # )
        features = (
            "Spelling checking in rubric creation.",
            "Persistent held region between papers.",
        )
        info = f"""
            <h4>Current experimental features</h4>
            <ul>
              {" ".join("<li>" + x + "</li>" for x in features)}
            </ul>
        """
        # Image by liftarn, public domain, https://freesvg.org/put-your-fingers-in-the-gears
        res = resources.files(icons) / "fingers_in_gears.svg"
        pix = QPixmap()
        pix.loadFromData(res.read_bytes())
        pix = pix.scaledToHeight(256, Qt.TransformationMode.SmoothTransformation)
        msg = SimpleQuestion(self, txt, question=info)
        msg.setIconPixmap(pix)
        if msg.exec() == QMessageBox.StandardButton.No:
            self._experimental_mode_checkbox.setChecked(False)
            return
        self.parentMarkerUI.set_experimental(True)
        # TODO: some kind of signal/slot, ontoggle...
        self._hold_crop_checkbox.setVisible(True)

    def is_experimental(self) -> bool:
        return self.parentMarkerUI.is_experimental()

    def pause_to_process_events(self):
        """Allow Qt's event loop to process events.

        Typically we call this if we're in a loop of our own waiting
        for something to happen which can only occur if we
        """
        self.parentMarkerUI.Qapp.processEvents()

    def build_hamburger(self):
        # TODO: use QAction, share with other UI?
        keydata = self.get_key_bindings()

        m = QMenu()
        key = keydata["next-paper"]["keys"][0]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Save && next paper\t{key}", self.saveAndGetNext)

        # TRANSLATOR: this option discards every back to the latest save
        # m.addAction("Revert changes", self.revert_changes)

        # TODO: possible this should be in the RHS task list not here?
        # TRANSLATOR: this option resets a task completely
        # m.addAction("Remove all annotations", self.todo_somemethod)

        (key,) = keydata["cancel"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Exit annotate mode\t{key}", self.close)
        m.addSeparator()
        (key,) = keydata["quick-show-prev-paper"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Show previous paper(s)\t{key}", self.show_previous)
        m.addSeparator()
        (key,) = keydata["show-solutions"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        # shortcut key handled in Marker, but keep this menu entry for now?
        m.addAction(f"View solutions\t{key}", self.parentMarkerUI.view_solutions)
        (key,) = keydata["tag-paper"]["keys"]
        # shortcut key handled in Marker, but keep this menu entry for now?
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Tag paper...\t{key}", self.tag_paper)
        m.addSeparator()
        (key,) = keydata["rearrange-pages"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Adjust pages\t{key}", self.arrangePages)
        (key,) = keydata["crop-in"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Crop to region\t{key}", self.to_crop_mode)
        (key,) = keydata["crop-out"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Uncrop\t{key}", self.uncrop_region)
        hold_crop = m.addAction("Hold crop between papers")
        hold_crop.setCheckable(True)
        hold_crop.triggered.connect(self.toggle_hold_crop)
        self._hold_crop_checkbox = hold_crop
        if not self.is_experimental():
            self._hold_crop_checkbox.setVisible(False)
        m.addSeparator()
        subm = m.addMenu("Tools")
        # to make these actions checkable, they need to belong to self.
        # submg = QActionGroup(m)
        # km.addAction(getattr(self, "kb_{}_act".format(name)))
        # TODO: add selection indicator
        # TDDO: and keyboard shortcuts: how to update them?
        subm.addAction("Box", self.ui.boxButton.animateClick)
        subm.addAction("Tick", self.ui.tickButton.animateClick)
        subm.addAction("Cross", self.ui.crossButton.animateClick)
        subm.addAction("Text", self.ui.textButton.animateClick)
        subm.addAction("Line", self.ui.lineButton.animateClick)
        subm.addAction("Pen", self.ui.penButton.animateClick)
        subm.addSeparator()
        subm.addAction("Insert image", self.addImageMode)
        subm.addSeparator()
        subm.addAction("Move", self.ui.moveButton.animateClick)
        subm.addAction("Pan", self.ui.panButton.animateClick)
        subm.addAction("Delete", self.ui.deleteButton.animateClick)
        subm.addAction("Zoom", self.ui.zoomButton.animateClick)
        m.addSeparator()
        (key,) = keydata["increase-annotation-scale"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(
            f"Increase annotation scale\t{key}",
            lambda: self.change_annot_scale(1.1),
        )
        # Keep a reference to this one so we can update the text
        self._reset_scale_menu_text = "Reset annotation scale"
        self._reset_scale_QAction = m.addAction(
            self._reset_scale_menu_text, self.change_annot_scale
        )
        self.update_annot_scale_menu_label()

        (key,) = keydata["decrease-annotation-scale"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(
            f"Decrease annotation scale\t{key}",
            lambda: self.change_annot_scale(1.0 / 1.1),
        )
        # Issue #1350: temporarily?
        m.addAction(
            "Temporarily change annot. colour",
            self.change_annotation_colour,
        )
        m.addSeparator()
        x = m.addAction("Experimental features")
        x.setCheckable(True)
        if self.is_experimental():
            x.setChecked(True)
        x.triggered.connect(self.toggle_experimental)
        self._experimental_mode_checkbox = x
        m.addAction("Synchronise rubrics", self.refreshRubrics)
        (key,) = keydata["toggle-wide-narrow"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)

        y = m.addAction("Toggle extra save button")
        y.setCheckable(True)
        y.setChecked(False)
        y.triggered.connect(self._toggle_extra_save_visibility)

        x = m.addAction(f"Compact UI\t{key}")
        x.setCheckable(True)
        if self.is_ui_compact():
            x.setChecked(True)
        x.triggered.connect(self._toggle_compact)
        self._compact_ui_toggle_action = x

        m.addSeparator()
        m.addAction("Help", lambda: self.keyPopUp(tab_idx=0))
        (key,) = keydata["help"]["keys"]
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Show shortcut keys...\t{key}", self.keyPopUp)
        return m

    def close_current_scene(self) -> None:
        """Removes the current scene, saving some info in case we want to open a new one.

        Returns:
            None: Modifies self.
        """
        # TODO: self.view.disconnectFrom(self.scene)
        # self.view = None
        # TODO: how to reset the scene?
        # This may be heavy handed, but for now we delete the old scene

        if not self.scene:
            # it was already closed
            return

        # Attempt at keeping mode information.
        self.modeInformation = [self.scene.mode]
        if self.scene.mode == "rubric":
            rid, tab = self.rubric_widget.getCurrentRubricIdAndTab()
            if rid is None:
                # Maybe row hidden (illegal) but scene knows it in the blue
                # ghost.  Fixes #1599.  Still None if scene didn't know.
                rid = self.scene.get_current_rubric_id()
            self.modeInformation.append((rid, tab))

        # after grabbed mode information, reset rubric_widget
        self.rubric_widget.setEnabled(False)

        del self.scene
        self.scene = None

    def close_current_task(self):
        """Closes the current question, closes scene and clears instance vars.

        As of 2025-Aug, this is something users of the the class can and do call.
        Its non-interactive: if you user-interactivity such as confirming via
        dialog, call something else.

        Notes:
            As a result of this method, many instance variables will be `None`.
            Be cautious of how these variables will be handled in cases where they are None.

        Returns:
            None: Modifies self.
        """
        self.close_current_scene()
        self.task = None
        self.papernum = None
        self.question_idx = None
        self.testName = None
        self.paperDir = None
        self.saveName = None
        # feels like a bit of a kludge
        self.view.setHidden(True)

    def load_new_question(
        self,
        task: str,
        question_label: str,
        version,
        max_version,
        testName,
        paperdir,
        saveName,
        maxMark,
        plomDict,
        integrity_check,
        src_img_data,
        tags: list[str],
    ):
        """Loads new data into the window for marking.

        Args:
            task: A string like "0027g13" indicating paper 0027 and
                question index 13.
            question_label: The name of the question we are
                marking.  This is generally used for display only as
                there is an integer for precise usage.
            version (int): which version are we working on?
            max_version (int): what is the largest version in this assessment?
            testName (str): Test Name
            paperdir (dir): Working directory for the current task
            saveName (str/pathlib.Path): file name (and dir, optionally)
                of the basename to save things (no .png/.jpg extension)
                If it does have an extension, it will be *ignored*.
            maxMark (int): maximum possible score for that test question
            plomDict (dict): a dictionary of annotation information.
                Contains sufficient information to recreate the annotation
                objects on the page if you go back to continue annotating a
                question.
            integrity_check (str): integrity check string
            src_img_data (list[dict]): image md5sums, filenames etc.
            tags: currently has these tags.  TODO: generally annotator
                doesn't "do" tags itself, relying on Marker to know such
                things, but we need it to set attention for now.  Maybe
                this could be refactored out to Marker later, after the
                wedding.

        Returns:
            None: Modifies many instance vars.
        """
        self.task = task
        self.papernum, self.question_idx = unpack_task_code(task)
        self.version = version
        self.max_version = max_version
        self.question_label = question_label
        self.testName = testName
        s = "{} of {}: {}".format(self.question_label, testName, task)
        log.info("Annotating {}".format(s))
        self.paperDir = paperdir
        self.saveName = Path(saveName)
        self.integrity_check = integrity_check
        self.maxMark = maxMark
        del maxMark

        if plomDict:
            assert plomDict["maxMark"] == self.maxMark, "mismatch between maxMarks"

        self.load_new_scene(src_img_data, plomDict=plomDict)

        # reset the timer (its not needed to make a new one)
        self.timer.start()

        self.update_attn_bar(tags=tags)

        # Emit signal that we are now in a clean state.  Not sure *we* should
        # *have* to do this, but somehow the undostack isn't doing it.
        self.cleanChanged.emit(True)

    def load_new_scene(self, src_img_data, *, plomDict=None):
        # Set up the graphicsview and graphicsscene of the group-image
        # loads in the image etc
        self.view.setHidden(False)  # or try not hiding it...
        self.setViewAndScene(src_img_data)
        # TODO: see above, can we maintain our zoom b/w images?  Would anyone want that?
        # TODO: see above, don't click a different button: want to keep same tool

        # update displayed score
        self.refreshDisplayedMark(self.getScore())
        # update rubrics
        self.rubric_widget.setQuestion(
            self.question_idx, self.question_label, self.maxMark
        )
        self.rubric_widget.setVersion(self.version, self.max_version)
        self.rubric_widget.setEnabled(True)

        log.debug("Restore mode info = {}".format(self.modeInformation))
        which_mode = self.modeInformation[0]
        cdr = self.modeInformation[1:]
        if which_mode == "rubric":
            # the remaining part of list should be a tuple in this case
            (extra,) = cdr
            if not self.rubric_widget.setCurrentRubricIdAndTab(*extra):
                # if no such rubric or no such tab, select move instead
                self.toMoveMode()
        else:
            # ensure we get an error on unexpected extra info
            assert not cdr
            self.setToolMode(which_mode)
        # redo this after all the other rubric stuff initialised
        self.rubric_widget.updateLegalityOfRubrics()

        # Very last thing = unpickle scene from plomDict if there is one
        if plomDict is not None:
            self.unpickleIt(plomDict)
            # restoring the scene would've marked it dirty
            self.scene.reset_dirty()
        else:
            # if there is a held crop rectangle, then use it.
            if self.held_crop_rectangle_data:
                self.scene.crop_from_plomfile(self.held_crop_rectangle_data)

    def change_annot_scale(self, scale=None):
        """Change the scale of the annotations.

        Args:
            scale (float/None): if None reset the scale to the default.
                If any floating point number, multiple the scale by that
                value.
        """
        if scale is None:
            log.info("resetting annotation scale to default")
            if self.scene:
                self.scene.reset_scale_factor()
            self.update_annot_scale_menu_label()

            return
        log.info("multiplying annotation scale by {}".format(scale))
        if self.scene:
            self.scene.increase_scale_factor(scale)
        self.update_annot_scale_menu_label()

    def update_annot_scale_menu_label(self):
        """Update the menu which shows the current annotation scale."""
        if not self.scene:
            return
        self._reset_scale_QAction.setText(
            self._reset_scale_menu_text
            + "\t{:.0%}".format(self.scene.get_scale_factor())
        )

    def change_annotation_colour(self):
        """Ask user for a new colour for the annotations."""
        if not self.scene:
            return
        c = self.scene.ink.color()
        c = QColorDialog.getColor(c)
        if c.isValid():
            self.scene.set_annotation_color(c)
        # TODO: save to settings

    def refreshDisplayedMark(self, score):
        """Update the marklabel (and narrow one) with the current score - triggered by pagescene.

        Returns:
            None
        """
        # TODO: some duplication of code b/w here and pagescene.ScoreBox
        s = ""
        if self.question_label:
            s += self.question_label + ": "
        if score is None:
            s += "Unmarked"
        else:
            s += f"{pprint_score(score)} out of {self.maxMark}"
        self.ui.markLabel.setText(s)

    def loadCursors(self):
        """Load custom cursors and set their hotspots.

        Returns:
            None
        """

        def _pixmap_from(f):
            pm = QPixmap()
            res = resources.files(cursors) / f
            pm.loadFromData(res.read_bytes())
            return pm

        # The keys here are magic values that connect to tools
        cursor = {}
        cursor["box"] = QCursor(_pixmap_from("box.png"), 4, 4)
        cursor["ellipse"] = QCursor(_pixmap_from("ellipse.png"), 4, 4)
        cursor["cross"] = QCursor(_pixmap_from("cross.png"), 4, 4)
        cursor["crop"] = QCursor(_pixmap_from("crop.png"), 4, 4)
        cursor["delete"] = QCursor(_pixmap_from("delete.png"), 4, 4)
        cursor["line"] = QCursor(_pixmap_from("line.png"), 4, 4)
        cursor["pen"] = QCursor(_pixmap_from("pen.png"), 4, 4)
        cursor["tick"] = QCursor(_pixmap_from("tick.png"), 4, 4)
        cursor["QMark"] = QCursor(_pixmap_from("question_mark.png"), 4, 4)
        cursor["Highlight"] = QCursor(_pixmap_from("highlighter.png"), 4, 4)
        cursor["arrow"] = QCursor(_pixmap_from("arrow.png"), 4, 4)
        cursor["DoubleArrow"] = QCursor(_pixmap_from("double_arrow.png"), 4, 4)
        cursor["text"] = Qt.CursorShape.IBeamCursor
        cursor["rubric"] = Qt.CursorShape.ArrowCursor
        cursor["image"] = Qt.CursorShape.CrossCursor
        cursor["zoom"] = Qt.CursorShape.SizeFDiagCursor
        # note ClosedHandCursor and OpenHandCursor also hardcoded in pagescene
        cursor["pan"] = Qt.CursorShape.OpenHandCursor
        cursor["move"] = Qt.CursorShape.OpenHandCursor

        self.cursor = cursor

    def set_tool_icon_size(self, s: int) -> None:
        for b in (
            self.ui.tickButton,
            self.ui.crossButton,
            self.ui.textButton,
            self.ui.lineButton,
            self.ui.boxButton,
            self.ui.penButton,
        ):
            b.setIconSize(QSize(s, s))
        if s <= 24:
            self.ui.toolsLayout.setSpacing(0)
        else:
            self.ui.toolsLayout.setSpacing(6)

    def is_ui_compact(self) -> bool:
        """Is the UI currently in compact mode?"""
        # TODO: fragile hack, e.g., translation
        return not self.ui.saveNextButton.text().startswith("Save")

    def toggle_compact(self) -> None:
        """Shows/Hides tools making more space to view the group-image."""
        self._compact_ui_toggle_action.trigger()

    def _toggle_compact(self) -> None:
        if self.is_ui_compact():
            self.wideLayout()
        else:
            self.compact_layout()

    def _toggle_extra_save_visibility(self) -> None:
        self._bottom_toolbar.setVisible(not self._bottom_toolbar.isVisible())

    def compact_layout(self) -> None:
        """Changes view to use a more narrow layout style."""
        self.ui.markLabel.setStyleSheet("color: #ff0000")
        # TODO: condensed font
        # QFont.setStretch(50)
        self.set_tool_icon_size(24)
        if hasattr(self, "rubric_widget"):
            self.rubric_widget.hideB.setVisible(False)
            # self.rubric_widget.syncB.setVisible(False)
        # self.ui.frameTools.setVisible(False)
        self.ui.helpButton.setText("?")
        self.ui.saveNextButton.setText("Next")
        # self.ui.arrangePagesButton.setText("\N{PAGES}")
        self.ui.arrangePagesButton.setText("")
        self.setIcon(self.ui.arrangePagesButton, "Rearrange pages", "extra_page.svg")

        # magic value :(
        self.ui.hideableBox.setMinimumWidth(120)
        self.ui.splitter.setSizes([120, 4096])

    def wideLayout(self) -> None:
        """Changes view to Wide Layout style."""
        # self.ui.markLabel.setStyleSheet("color: #ff0000; font: bold;")
        # Note: I think it looks better non-bold
        self.ui.markLabel.setStyleSheet("color: #ff0000;")
        self.set_tool_icon_size(40)
        if hasattr(self, "rubric_widget"):
            self.rubric_widget.hideB.setVisible(True)
            self.rubric_widget.syncB.setVisible(True)
        # self.ui.frameTools.setVisible(True)
        self.ui.helpButton.setText("Key help")
        self.ui.saveNextButton.setText("Save && Next")
        self.ui.arrangePagesButton.setText("Adjust pages")
        self.ui.arrangePagesButton.setIcon(QIcon())

        self.ui.hideableBox.setMinimumWidth(0)

    def next_rubric_or_reselect_rubric_tool(self):
        """Changes the tool to rubric or pick the next rubric.

        This allows the same key to switch back to rubrics (from say tick
        or delete tool) as is used to select the next rubric.
        """
        if not self.scene:
            self.rubric_widget.nextRubric()
            return
        if self.scene.mode == "rubric":
            self.rubric_widget.nextRubric()
        else:
            self.rubric_widget.reselectCurrentRubric()

    # currently no key bound to this; above used instead
    def next_rubric(self):
        self.rubric_widget.nextRubric()

    def prev_rubric(self):
        self.rubric_widget.previousRubric()

    def next_tab(self):
        self.rubric_widget.next_tab()

    def prev_tab(self):
        self.rubric_widget.prev_tab()

    def next_minor_tool(self, dir: int = 1, *, always_move: bool = False) -> None:
        """Switch to current minor tool or advance to next minor tool.

        Args:
            dir: +1 for next (default), -1 for previous.

        Keyword Args:
            always_move: the minor tools keep track of the
                last-used tool.  Often, but not always, we want to
                switch back to the last-used tool.  False by default.
        """
        if not self.scene:
            return
        L = self._list_of_minor_modes
        # if always-move then select the next/previous tool according to dir
        # elif in a tool-mode then select next/prev tool according to dir
        # elif - non-tool mode, so keep the last tool
        if always_move:  # set index to the last tool we used
            self._which_tool = L[(L.index(self._which_tool) + dir) % len(L)]
        elif self.scene.mode in L:
            self._which_tool = L[(L.index(self.scene.mode) + dir) % len(L)]
        else:
            pass  # keep the current tool
        getattr(self.ui, "{}Button".format(self._which_tool)).animateClick()

    def prev_minor_tool(self):
        """Switch backward to the previous minor tool."""
        self.next_minor_tool(dir=-1, always_move=True)

    def viewWholePaper(self) -> None:
        """Popup a dialog showing the entire paper.

        TODO: this has significant duplication with RearrangePages.
        """
        if not self.task:
            return
        log.debug("wholePage: downloading files for papernum %s", self.papernum)
        dl = self.parentMarkerUI.Qapp.downloader
        pagedata = dl.msgr.get_pagedata_context_question(
            self.papernum, self.question_idx
        )
        # Issue #1553: we filter ID page out, somewhat crudely (Issue #2707)
        pagedata = [
            x for x in pagedata if not x["pagename"].casefold().startswith("id")
        ]
        pagedata = dl.sync_downloads(pagedata)
        labels = [x["pagename"] for x in pagedata]
        WholeTestView(self.papernum, pagedata, labels, parent=self).exec()

    def arrangePages(self) -> None:
        """Arrange or rearrange pages in UI."""
        if not self.task or not self.scene:
            return
        self.parentMarkerUI.Qapp.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # disable ui before calling process events
        self.setEnabled(False)
        self.pause_to_process_events()
        src_img_data = self.scene.get_src_img_data()
        image_md5_list = [x["md5"] for x in src_img_data]
        # Look for duplicates by first inverting the dict
        repeats = {}
        for i, md5 in enumerate(image_md5_list):
            repeats.setdefault(md5, []).append(i)
        repeats = {k: v for k, v in repeats.items() if len(v) > 1}
        if repeats:
            log.warning("Repeated pages in md5sum data: %s", repeats)
            info = dedent(
                """
                <p>This can happen with self-submitted work if a student
                submits multiple copies of the same page.
                Its probably harmless in that case, but if you see this
                with scanned work, it might indicate a bug.</p>
                <p>The repeated pages are:</p>
                <ul>
                """
            )
            for md5, pages in repeats.items():
                info += f"<li>pages {pages} @ md5: {md5}</li>"
            info += "</ul>"
            ErrorMsg(
                self,
                "Warning: duplicate pages detected!",
                info=info,
                info_pre=False,
                details=(
                    f"Annotator's image_md5_list is\n  {image_md5_list}\n"
                    f"The src_img_data is\n  {src_img_data}\n"
                    "Include this info if you think this is a bug!"
                ),
            ).exec()
        log.debug("adjustpgs: downloading files for papernum %s", self.papernum)

        dl = self.parentMarkerUI.Qapp.downloader
        pagedata = dl.msgr.get_pagedata_context_question(
            self.papernum, self.question_idx
        )
        # Issue #1553: we filter ID page out, somewhat crudely (Issue #2707)
        pagedata = [
            x for x in pagedata if not x["pagename"].casefold().startswith("id")
        ]
        # TODO: eventually want dialog to open during loading, Issue #2355
        N = len(pagedata)
        pd = QProgressDialog(
            "Downloading additional images\nStarting up...", None, 0, N, self
        )
        pd.setWindowModality(Qt.WindowModality.WindowModal)
        pd.setMinimumDuration(500)
        pd.setValue(0)
        self.pause_to_process_events()
        for i, row in enumerate(pagedata):
            # TODO: would be nice to show the size in MiB here!
            pd.setLabelText(
                f"Downloading additional images\nFile {i + 1} of {N}: "
                f"img id {row['id']}"
            )
            pd.setValue(i + 1)
            self.pause_to_process_events()
            row = dl.sync_download(row)
        pd.close()

        #
        for x in image_md5_list:
            if x not in [p["md5"] for p in pagedata]:
                s = dedent(
                    f"""
                    Unexpectedly situation!\n
                    There is an image being annotated that is not present in
                    the server's page data.  Probably that is not allowed(?)
                    How did it happen?\n
                    Annotator's src img data is:
                      {src_img_data}\n
                    Server pagedata is:
                      {pagedata}\n
                    Consider filing a bug with this info!
                    """
                ).strip()
                log.error(s)
                ErrorMsg(self, s).exec()

        has_annotations = self.scene.hasAnnotations()
        log.debug("pagedata is\n  {}".format("\n  ".join([str(x) for x in pagedata])))
        rearrangeView = RearrangementViewer(
            self, self.papernum, src_img_data, pagedata, has_annotations
        )
        # TODO: have rearrange react to new downloads
        # PC.download_finished.connect(rearrangeView.shake_things_up)
        perm = []
        self.parentMarkerUI.Qapp.restoreOverrideCursor()
        if rearrangeView.exec() == QDialog.DialogCode.Accepted:
            perm = rearrangeView.permute
            log.debug("adjust pages permutation output is: %s", perm)
        # Workaround for memory leak Issue #1322, TODO better fix
        rearrangeView.listA.clear()
        rearrangeView.listB.clear()
        rearrangeView.deleteLater()  # disconnects slots and signals
        del rearrangeView
        if perm:
            # Sanity check for dupes in the permutation
            # pylint: disable=unsubscriptable-object
            md5 = [x["md5"] for x in perm]
            # But if the input already had dupes than its not our problem
            md5_in = [x["md5"] for x in src_img_data]
            if len(set(md5)) != len(md5) and len(set(md5_in)) == len(md5_in):
                s = dedent(
                    """
                    Unexpectedly repeated md5sums: did Adjust Pages somehow
                    dupe a page?  This should not happen!\n
                    Please file an issue with this info!\n
                    perm = {}\n
                    annotr src_img_data = {}\n
                    pagedata = {}
                    """.format(
                        perm, src_img_data, pagedata
                    )
                ).strip()
                log.error(s)
                ErrorMsg(self, s).exec()
            self.new_or_permuted_image_data(perm)
        self.setEnabled(True)

    def new_or_permuted_image_data(self, src_img_data):
        """We have permuted/added/removed underlying source images, tear done and build up again."""
        self.close_current_scene()
        self.load_new_scene(src_img_data)

    def experimental_cycle(self):
        self.scene.whichLineToDraw_next()

    def keyPopUp(self, *, tab_idx: int | None = None) -> None:
        """View help and keyboard shortcuts, eventually edit them.

        Keyword Arg:
            tab_idx: which tab to open in the help.  If None
                then we try to re-open on the same tab from last run.
        """
        if tab_idx is None:
            _tab_idx = getattr(self, "_keyhelp_tab_idx", 0)
        else:
            _tab_idx = tab_idx
        diag = KeyHelp(
            self,
            self.keybinding_name,
            custom_overlay=self.keybinding_custom_overlay,
            initial_tab=_tab_idx,
        )
        if diag.exec() != QDialog.DialogCode.Accepted:
            return
        self.keybinding_name = diag.get_selected_keybinding_name()
        if self.keybinding_name == "custom":
            # note: if dialog modified custom, but then selected another
            # such as "ijkl", then we should *not* overwrite custom.
            self.keybinding_custom_overlay = diag.get_custom_overlay()
        if tab_idx is None:
            # keep the open tab for next time we re-open KeyHelp
            self._keyhelp_tab_idx = diag.tabs.currentIndex()
        self.parentMarkerUI.annotatorSettings["keybinding_name"] = self.keybinding_name
        self.parentMarkerUI.annotatorSettings["keybinding_custom_overlay"] = (
            self.keybinding_custom_overlay
        )
        self.setToolShortCuts()

    def setViewAndScene(self, src_img_data):
        """Makes a new scene (pagescene object) and connects it to the view (pageview object).

        The pageview (which is a qgraphicsview) which is (mostly) a layer
        between the annotation widget and the graphics scene which
        actually stores all the graphics objects (the image, lines, boxes,
        text etc etc). The view allows us to zoom pan etc over image and
        its annotations.

        Returns:
            None: modifies self.scene from None to a pagescene object and connects it to a pageview object.
        """
        self.scene = PageScene(
            self,
            src_img_data,
            self.maxMark,
            self.question_label,
        )
        # connect view to scene
        self.view.connectScene(self.scene)
        self.scene.undoStack.cleanChanged.connect(self._gunk)
        # scene knows which views are connected via self.views()
        log.debug("Scene has this list of views: {}".format(self.scene.views()))

    # I get crashes when I try to hack with lambdas, "just" want to forward
    # the undoStack's cleanChanged onward as if it came from Annotator
    @pyqtSlot(bool)
    def _gunk(self, clean: bool) -> None:
        self.cleanChanged.emit(clean)

    def keyToChangeRubric(self, keyNumber) -> None:
        """Translates a the numerical key into a selection of that visible row of the current rubric tab.

        Returns:
            None: modifies self.rubric_widget
        """
        # row is one less than key
        self.rubric_widget.selectRubricByVisibleRow(keyNumber - 1)

    def setToolMode(self, newMode, *, cursor=None, imagePath=None, rubric=None):
        """Changes the current tool mode and cursor.

        Args:
            newMode (str): ``"move"``, ``"rubric"`` etc.

        Keyword Args:
            imagePath (?): an argument for the "image" tool, used
                used only by the image tool.
            rubric (dict[str, Any] | None): if we're changing to rubric,
                use this include the rubric.
            cursor (str): if None or omitted default cursors are used
               for each tool.  If needed you could override this.
               (currently unused, semi-deprecated).

        Notes:
            TODO: this does various other mucking around for legacy
            reasons: could probably still use some refactoring.

        Returns:
            None but modifies self.
        """
        if cursor is None:
            cursor = self.cursor[newMode]

        if newMode == "rubric":
            self._uncheck_exclusive_group()

        # ensure`_which_tool` is updated via mouse click too, see next_minor_tool()
        if newMode in self._list_of_minor_modes:
            self._which_tool = newMode

        if self.scene and imagePath is not None:
            self.scene.tempImagePath = imagePath

        # pass the new mode to the graphicsview, and set the cursor in view
        if self.scene:
            if rubric:
                self.scene.setCurrentRubric(rubric)
            self.scene.setToolMode(newMode)
            self.view.setCursor(cursor)
        self._setModeLabels(newMode)
        # refresh everything.
        self.repaint()

    def _setModeLabels(self, mode):
        if mode == "rubric":
            self.ui.modeLabel.setText(
                " rubric {} ".format(self.rubric_widget.getCurrentTabName())
            )
        else:
            self.ui.modeLabel.setText(" {} ".format(mode))

    def setIcon(self, toolButton, name, iconfile: str) -> None:
        """Sets a name and svg icon for a given QToolButton.

        Args:
            toolButton (QToolButton): the ui Tool Button for a name and icon to be added to.
            name (str): a name defining toolButton.
            iconfile: filename of .svg, local to the resource `icons`.

        Returns:
            None but alters toolButton.
        """
        toolButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolButton.setToolTip("{}".format(tipText.get(name, name)))
        pm = QPixmap()
        res = resources.files(icons) / iconfile
        pm.loadFromData(res.read_bytes())
        toolButton.setIcon(QIcon(pm))
        # toolButton.setIconSize(QSize(40, 40))

    def setAllIcons(self) -> None:
        """Sets all icons for the ui Tool Buttons.

        Returns:
            None but modifies ui Tool Buttons.
        """
        self.setIcon(self.ui.boxButton, "box", "rectangle_highlight.svg")
        self.setIcon(self.ui.crossButton, "cross", "cross.svg")
        self.setIcon(self.ui.deleteButton, "delete", "delete.svg")
        self.setIcon(self.ui.lineButton, "line", "line.svg")
        self.setIcon(self.ui.moveButton, "move", "move.svg")
        self.setIcon(self.ui.panButton, "pan", "pan.svg")
        self.setIcon(self.ui.penButton, "pen", "pen.svg")
        self.setIcon(self.ui.redoButton, "redo", "redo.svg")
        self.setIcon(self.ui.textButton, "text", "text.svg")
        self.setIcon(self.ui.tickButton, "tick", "tick.svg")
        self.setIcon(self.ui.undoButton, "undo", "undo.svg")
        self.setIcon(self.ui.zoomButton, "zoom", "zoom.svg")

    @pyqtSlot()
    def saveAndGetNext(self) -> None:
        """Saves the current annotations, and moves on to the next paper."""
        if self.scene:
            if not self.saveAnnotations():
                return
            log.debug("We have surrendered task %s", self.task)
            tmp_task = self.task
            self.close_current_task()
        else:
            tmp_task = None

        # Workaround getting too far ahead of Marker's upload queue
        # TODO: surely this can move to Marker... pop open the side panel if hidden
        queue_len = self.parentMarkerUI.get_upload_queue_length()
        if queue_len >= 3:
            WarnMsg(
                self,
                f"<p>Plom is waiting to upload {queue_len} papers.</p>"
                + "<p>This might indicate network trouble: unfortunately Plom "
                + "does not yet deal with this gracefully and there is a risk "
                + "we might lose your non-uploaded work!</p>"
                + "<p>You should consider closing the Annotator, and waiting "
                + "a moment to see if the queue of &ldquo;uploading...&rdquo; "
                + "papers clear.</p>",
            ).exec()

        # TODO: close_current_task should emit(tmp_task)
        # TODO: self.caller_give_us_more.emit(tmp_task)
        stuff = self.parentMarkerUI.getMorePapers(tmp_task)
        if not stuff:
            self.update_attn_bar(tags=[], msg="", show=False)
            InfoMsg(self, "No more to grade?").exec()
            # Not really safe to give it back? (at least we did the view...)
            return

        log.debug("saveAndGetNext: new stuff is {}".format(stuff))
        self.load_new_question(*stuff)

    # TODO: @pyqtSlot()?
    # def revert_changes(self) -> None:
    #     InfoMsg(self, "Not implemented yet").exec()
    #     print("TODO")

    @pyqtSlot()
    def saveAndClose(self) -> None:
        """Save the current annotations, and then close.

        Returns:
            None: alters self.scene
        """
        if self.scene and not self.saveAnnotations():
            return
        self._priv_force_close = True
        self.close()

    def get_key_bindings(self):
        return get_key_bindings(self.keybinding_name, self.keybinding_custom_overlay)

    def setToolShortCuts(self):
        """Set or change the shortcuts for the basic tool keys.

        These are the shortcuts that are user-editable.
        """
        keydata = self.get_key_bindings()
        actions_and_methods = (
            ("undo", self.toUndo),
            ("redo", self.toRedo),
            ("next-rubric", self.next_rubric_or_reselect_rubric_tool),
            ("prev-rubric", self.prev_rubric),
            ("next-tab", self.next_tab),
            ("prev-tab", self.prev_tab),
            ("next-tool", self.next_minor_tool),
            ("prev-tool", self.prev_minor_tool),
            ("delete", self.toDeleteMode),
            ("move", self.toMoveMode),
            ("zoom", self.toZoomMode),
        )
        # wipe any existing shortcuts
        shortcuts = getattr(self, "_store_QShortcuts", [])
        for sc in shortcuts:
            sc.deleteLater()
            del sc

        # store the shortcuts to prevent GC
        self._store_QShortcuts = []
        for action, command in actions_and_methods:
            (key,) = keydata[action]["keys"]  # enforce single item
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(command)
            self._store_QShortcuts.append(sc)

    def setMinorShortCuts(self):
        """Setup non-editable shortcuts.

        Each of these actions can be associated with multiple shortcut
        keys.
        """
        keydata = self.get_key_bindings()
        actions_and_methods = (
            ("toggle-wide-narrow", self.toggle_compact),
            ("help", self.keyPopUp),
            ("show-whole-paper", self.viewWholePaper),
            ("main-menu", self.ui.hamMenuButton.animateClick),
            ("zoom-in", self.view.zoomIn),
            ("zoom-out", self.view.zoomOut),
            ("next-paper", self.saveAndGetNext),
            ("cancel", self.close),
            ("toggle-zoom", self.view.zoomToggle),
            ("pan-through", self.view.panThrough),
            ("pan-back", self.view.depanThrough),
            ("pan-through-slowly", lambda: self.view.panThrough(0.02)),
            ("pan-back-slowly", lambda: self.view.depanThrough(0.02)),
            ("undo-2", self.toUndo),
            ("redo-2", self.toRedo),
            ("rearrange-pages", self.arrangePages),
            ("quick-show-prev-paper", self.show_previous),
            ("increase-annotation-scale", lambda: self.change_annot_scale(1.1)),
            ("decrease-annotation-scale", lambda: self.change_annot_scale(1 / 1.1)),
            ("crop-in", self.to_crop_mode),
            ("crop-out", self.uncrop_region),
        )
        self._store_QShortcuts_minor = []
        for action, command in actions_and_methods:
            for key in keydata[action]["keys"]:
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(command)
            self._store_QShortcuts_minor.append(sc)

        def lambda_factory(n):
            return lambda: self.keyToChangeRubric(n)

        # rubric shortcuts
        self._store_QShortcuts_rubrics = []
        for n in range(1, 11):
            # keys 1, 2, 3, 4, 5, 6, 7, 8, 9, 0
            key = f"{n % 10}"
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda_factory(n))
            self._store_QShortcuts_rubrics.append(sc)

        # TODO: hardcoded, do we want shift-undo to be redo? Issue #2246
        self.redoShortCut2 = QShortcut(QKeySequence("Shift+g"), self)
        self.redoShortCut2.activated.connect(self.ui.redoButton.animateClick)

        self.sekritShortCut = QShortcut(QKeySequence("Ctrl+Shift+o"), self)
        self.sekritShortCut.activated.connect(self.experimental_cycle)

    def to_crop_mode(self):
        # can't re-crop if the crop is being held
        if self.held_crop_rectangle_data:
            WarnMsg(
                self,
                "You cannot re-crop while a crop is being held.",
                info="Unselect 'hold crop' from the menu and then try again.",
            ).exec()
        else:
            self.setToolMode("crop")

    def uncrop_region(self):
        if self.held_crop_rectangle_data:
            WarnMsg(
                self,
                "You cannot un-crop while a crop is being held.",
                info="Unselect 'hold crop' from the menu and then try again.",
            ).exec()
            return
        if not self.scene:
            return
        self.scene.uncrop_underlying_images()

    def toUndo(self):
        self.ui.undoButton.animateClick()

    def undo(self):
        """Undoes the last action in the UI."""
        if not self.scene:
            return
        if self.scene.isDrawing():
            self.scene.stopMidDraw()
        else:
            self.scene.undo()

    def toRedo(self):
        self.ui.redoButton.animateClick()

    def redo(self):
        """Redoes the last action in the UI."""
        if not self.scene:
            return
        self.scene.redo()

    def toDeleteMode(self):
        self.ui.deleteButton.animateClick()

    def toMoveMode(self):
        self.ui.moveButton.animateClick()

    def toZoomMode(self):
        self.ui.zoomButton.animateClick()

    def addImageMode(self):
        """Opens a file dialog to choose an image.

        Shows a message box if the image is too large, otherwise continues to image mode.

        Notes:
            If the Image is greater than 200kb, will return an error.

        Returns:
            None
        """
        fileName, __ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image files (*.jpg *.gif *.png *.xpm)",
        )
        if not os.path.isfile(fileName):
            return
        if os.path.getsize(fileName) > 200000:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Image Too large.")
            msg.setText(
                "Max image size (200kB) reached. Please try again with a smaller image."
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            self.setToolMode("image", imagePath=fileName)

    def setButtons(self):
        """Connects buttons to their corresponding functions."""
        # Connect the key-help button
        self.ui.helpButton.clicked.connect(self.keyPopUp)

        # tool buttons change the mode
        self.ui.boxButton.clicked.connect(lambda: self.setToolMode("box"))
        self.ui.crossButton.clicked.connect(lambda: self.setToolMode("cross"))
        self.ui.deleteButton.clicked.connect(lambda: self.setToolMode("delete"))
        self.ui.lineButton.clicked.connect(lambda: self.setToolMode("line"))
        self.ui.moveButton.clicked.connect(lambda: self.setToolMode("move"))
        self.ui.panButton.clicked.connect(lambda: self.setToolMode("pan"))
        self.ui.penButton.clicked.connect(lambda: self.setToolMode("pen"))
        self.ui.textButton.clicked.connect(lambda: self.setToolMode("text"))
        self.ui.tickButton.clicked.connect(lambda: self.setToolMode("tick"))
        self.ui.zoomButton.clicked.connect(lambda: self.setToolMode("zoom"))

        # Pass the undo/redo button clicks on to the view
        self.ui.undoButton.clicked.connect(self.undo)
        self.ui.redoButton.clicked.connect(self.redo)

        # Connect the rubric buttons to the rubric list
        # They select the item and trigger its handleClick which fires
        # off a rubricSignal which will be picked up by the annotator
        # First up connect the rubric list's signal to the annotator's
        # handle rubric function.
        self.rubric_widget.rubricSignal.connect(self.handleRubric)
        self.ui.arrangePagesButton.clicked.connect(self.arrangePages)
        self.ui.saveNextButton.clicked.connect(self.saveAndGetNext)
        self.another_save_next_button.clicked.connect(self.saveAndGetNext)

    def _uncheck_exclusive_group(self):
        # Stupid hackery to uncheck an autoexclusive button.
        # For example, when we switch focus to the rubric_list, we want to
        # unselect all the tools.  An alternative would be somehow hacking
        # the autoexclusive property into rubric_list (its normally for
        # buttons).  Or to revert managing the button state ourselves.
        for X in (
            self.ui.boxButton,
            self.ui.crossButton,
            self.ui.deleteButton,
            self.ui.lineButton,
            self.ui.moveButton,
            self.ui.panButton,
            self.ui.penButton,
            self.ui.textButton,
            self.ui.tickButton,
            self.ui.zoomButton,
        ):
            if X.isChecked():
                X.setAutoExclusive(False)
                X.setChecked(False)
                X.setAutoExclusive(True)

    def handleRubric(self, rubric):
        """Pass a rubric dict onward to the scene, if we have a scene.

        Args:
            rubric (dict): we don't care what's in it: that's for the scene
                and the rubric widget to agree on!

        Returns:
            None: Modifies self.scene
        """
        self.setToolMode("rubric", rubric=rubric)

    def _load_window_settings_early(self):
        """Load the window settings, early stuff."""
        # remember the "don't ask me again" checks
        # but note that Marker is not supposed to be saving these globally to disc
        if self.parentMarkerUI.annotatorSettings.get("_config"):
            self._config = self.parentMarkerUI.annotatorSettings["_config"].copy()

        # TODO: feels flaky, and despite QTimer, doesn't work if moved to _late fcn
        # if zoom-state is none, set it to index 1 (fit page) - but delay.
        if self.parentMarkerUI.annotatorSettings["zoomState"] is None:
            QTimer.singleShot(100, lambda: self.ui.zoomCB.setCurrentIndex(1))
        elif self.parentMarkerUI.annotatorSettings["zoomState"] == 0:
            # is set to "user", so set the view-rectangle
            if self.parentMarkerUI.annotatorSettings["viewRectangle"] is not None:
                QTimer.singleShot(100, lambda: self.ui.zoomCB.setCurrentIndex(0))
                QTimer.singleShot(
                    200,
                    lambda: self.view.initializeZoom(
                        self.parentMarkerUI.annotatorSettings["viewRectangle"]
                    ),
                )
            else:
                # no view-rectangle, so set to "fit-page"
                QTimer.singleShot(100, lambda: self.ui.zoomCB.setCurrentIndex(1))
        else:
            QTimer.singleShot(
                100,
                lambda: self.ui.zoomCB.setCurrentIndex(
                    self.parentMarkerUI.annotatorSettings["zoomState"]
                ),
            )

    def _load_window_settings_late(self):
        """Load the window settings, later stuff."""
        # wide vs compact
        if self.parentMarkerUI.annotatorSettings["compact"] is True:
            log.debug("compacting UI (b/c of last use setting)")
            self.toggle_compact()

    def saveWindowSettings(self):
        """Saves current window settings and other state into the parent.

        Returns:
            None: modifies self.parentMarkerUI and self.scene
        """
        self.parentMarkerUI.annotatorSettings["viewRectangle"] = (
            self.view.getCurrentViewRect()
        )
        self.parentMarkerUI.annotatorSettings["_config"] = self._config.copy()
        self.parentMarkerUI.annotatorSettings["zoomState"] = (
            self.ui.zoomCB.currentIndex()
        )
        if self.is_ui_compact():
            self.parentMarkerUI.annotatorSettings["compact"] = True
        else:
            self.parentMarkerUI.annotatorSettings["compact"] = False

    def saveAnnotations(self) -> bool:
        """Try to save the annotations and signal Marker to upload them.

        There are various checks and user interaction to be done.

        Be careful of a score of 0 - when mark total or mark up.
        Be careful of max-score when marking down.
        In either case - get user to confirm the score before closing.
        Also confirm various "not enough feedback" cases.

        Returns:
            Return `False` if user cancels.  Return `True` if we
            should move on (for example, to close the Annotator).
        """
        assert self.scene
        # do some checks before accepting things
        if not self.scene.hasAnnotations():
            InfoMsg(
                self, "Please make an annotation, even if there is no answer."
            ).exec()
            return False

        unhappy_objs = self.scene.check_all_saveable_objects_are_happy()
        if unhappy_objs:
            msg = f"{len(unhappy_objs)} annotations are unhappy."
            msg += " Probably these are rubrics that have been updated on"
            msg += " the server.."
            info = "<p>The unhappy objects should be highlighted in orange."
            info += " Please sync your rubrics and manually edit.  A future"
            info += " update to Plom may make this process easier.</p>"
            details = "## Unhappy objects\n\n  "
            details += "\n".join(str(x) for x in unhappy_objs)
            details += "\n\n## All objects\n\n  "
            details += "\n".join(str(x) for x in self.scene.items())
            details += "\n\n## Object serialization\n\n  "
            details += "\n".join(str(x) for x in self.scene.pickleSceneItems())
            WarnMsg(self, msg, info=info, info_pre=False, details=details).exec()
            # Note: we could ask a question here and let the user "submit anyway"
            # and that might be a good idea if we find any bugs in this code...
            return False

        # check annotations are inside the margins
        out_objs = self.scene.check_all_saveable_objects_inside()
        if out_objs:
            msg = f"{len(out_objs)} annotations are outside the margins."
            msg += " Please move or delete them before saving."
            info = "<p>Out-of-bounds objects are highlighted in orange.</p>"
            info += "<p><em>Note:</em> if you cannot see any such objects "
            info += "(even after zooming out) then you may be experiencing "
            info += '<a href="https://gitlab.com/plom/plom/-/issues/1792">Issue '
            info += "#1792</a>; please help us by copy-pasting the details below, "
            info += "along with any details about how to make this happen!</p>"
            details = "## Out of bounds objects\n\n  "
            details += "\n".join(str(x) for x in out_objs)
            details += "\n\n## All objects\n\n  "
            details += "\n".join(str(x) for x in self.scene.items())
            details += "\n\n## More detail on rect objects\n\n  "
            details += "Previous instances have involved QGraphicsRectItem so\n"
            details += "here are details about all those:\n\n"
            for x in self.scene.items():
                if isinstance(x, QGraphicsRectItem):
                    details += f"\n{x}"
                    details += f"\n  - {x.rect()}"
                    details += f"\n  - {x.pen()}"
                    c = x.pen().color()
                    details += "\n     - rgba: "
                    details += f"{(c.red(), c.green(), c.blue(), c.alpha())}"
                    details += f"\n     - width: {x.pen().width()}"
                    details += f"\n  - {x.brush()}"
                    details += f"\n     - style: {x.brush().style()}"
            details += "\n\n## Object serialization\n\n  "
            details += "\n".join(str(x) for x in self.scene.pickleSceneItems())
            WarnMsg(self, msg, info=info, info_pre=False, details=details).exec()
            return False

        if self.scene.is_neutral_state():
            InfoMsg(self, "You have not yet set a score.").exec()
            return False

        assert self.getScore() is not None

        # do some checks when score is zero or full
        if not self._zeroMarksWarn():
            return False
        if not self._fullMarksWarn():
            return False

        # warn if points where lost but insufficient annotations
        # note spatial annotations (drag-box) is enough to sneak past this
        if (
            0 < self.getScore() < self.maxMark
        ) and self.scene.hasOnlyTicksCrossesDeltas():
            code = "lost-marks-but-insufficient-feedback"
            if not self._continue_after_warning(code):
                return False

        # some combinations of rubrics may seem ambiguous or potentially confusing
        rubrics = self.scene.get_rubrics()
        ok, _code, _msg = check_for_illadvised(rubrics, self.maxMark)
        if not ok:
            assert isinstance(_code, str)
            assert isinstance(_msg, str)
            if not self._continue_after_warning(_code, _msg):
                return False

        if not self._check_all_pages_touched():
            return False

        aname, plomfile = self.pickleIt()
        rubric_ids = self.scene.get_rubric_ids()

        log.debug("emitting accept signal")
        tim = self.timer.elapsed() / 1000

        # some things here hardcoded elsewhere too, and up in marker
        stuff = [
            self.getScore(),
            tim,
            self.paperDir,
            aname,
            plomfile,
            rubric_ids,
            self.integrity_check,
        ]
        self.annotator_upload.emit(self.task, stuff)
        return True

    @property
    def _feedback_rules(self) -> dict[str, Any]:
        return self.parentMarkerUI.annotatorSettings.get("feedback_rules")

    def _continue_after_warning(self, code: str, msg: str | None = None) -> bool:
        """Notify user about warnings/errors in their annotations.

        Handle "don't ask me again" and associated settings.

        Args:
            code: a string code that identified the situation.
            msg: an optional description of the situation.  If omitted
                or ``None``, we'll load one from a central config.
                You might need this if you need to fill in a templated
                explanation, which we don't (yet) do for you.

        Returns:
            True if we should continue or False if either settings or
            user choose to edit further.
        """
        situation = self._feedback_rules[code]

        if msg is None:
            # str() to shutup MyPy: we unit test that is a string
            msg = str(situation["explanation"])

        # The msg might already be phrased as a question such as "will this
        # be understandable?" but we end with a concrete question
        msg += "\n<p>Do you wish to submit?</p>"

        if not situation["allowed"]:
            InfoMsg(self, msg).exec()
            return False

        if not situation["warn"]:
            return True

        dama = False
        if situation["dama_allowed"]:
            dama = self._config.get("dama-" + code, False)
        if dama:
            return True

        if not situation["dama_allowed"]:
            if SimpleQuestion(self, msg).exec() == QMessageBox.StandardButton.No:
                return False
            return True
        d = SimpleQuestionCheckBox(self, msg, "Don't ask me again this session.")
        if d.exec() == QMessageBox.StandardButton.No:
            return False
        if d.cb.isChecked():
            self._config["dama-" + code] = True
        return True

    def _will_we_warn(self, code: str) -> bool:
        """Would we notify user about warnings/errors in their annotations?

        Determines if the closely-related :method:`_continue_after_warning`
        will popup a dialog asking and/or notifying the user of a situation.
        Its intended use it to check if a dialog *might* appear so that we
        can potentially save computation in the case it will not.

        Args:
            code: a string code that identified the situation.

        Returns:
            True if we might ask/notify the user (possibly depending on
            further maybe expensive calculations).  False if we wouldn't
            either because of global settings or b/c they have chosen
            "don't-ask-me-again".
        """
        situation = self._feedback_rules[code]
        if not situation["allowed"]:
            return True
        if situation["warn"]:
            return True
        dama = False
        if situation["dama_allowed"]:
            dama = self._config.get("dama-" + code, False)
        if dama:
            return False
        return True

    def _zeroMarksWarn(self) -> bool:
        """A helper method for saveAnnotations.

        Controls warnings for when paper has 0 marks.  If there are
        only ticks or some ticks then warns user.

        Returns:
            False if user cancels, True otherwise.
        """
        assert self.scene
        if self.getScore() != 0:
            return True
        code = None
        if self.scene.hasOnlyTicks():
            code = "zero-marks-but-has-only-ticks"
        elif self.scene.hasAnyTicks():
            code = "zero-marks-but-has-ticks"
        if code:
            msg = self._feedback_rules[code]["explanation"]
            assert isinstance(msg, str)
            msg = msg.format(max_mark=self.maxMark)
            if not self._continue_after_warning(code, msg):
                return False
        return True

    def _fullMarksWarn(self) -> bool:
        """A helper method for saveAnnotations.

        Controls warnings for when paper has full marks.  If there are
        some crosses or only crosses then warns user.

        Returns:
            False if user cancels, True otherwise.
        """
        if self.getScore() != self.maxMark:
            return True
        assert self.scene
        code = None
        if self.scene.hasOnlyCrosses():
            code = "full-marks-but-has-only-crosses"
        elif self.scene.hasAnyCrosses():
            code = "full-marks-but-has-crosses"
        elif self.scene.hasAnyComments():
            pass
        else:
            code = "full-marks-but-other-annotations-contradictory"
        if code:
            msg = self._feedback_rules[code]["explanation"]
            assert isinstance(msg, str)
            msg = msg.format(max_mark=self.maxMark)
            if not self._continue_after_warning(code, msg):
                return False
        return True

    def _check_all_pages_touched(self) -> bool:
        """A helper method for saveAnnotations.

        Are all pages touched by the hand of the annotator?

        Returns:
            False if user cancels, True otherwise.
        """
        assert self.scene
        code = "each-page-should-be-annotated"
        # save computing cost if user won't be warned
        if not self._will_we_warn(code):
            return True
        indices = self.scene.get_list_of_non_annotated_underimages()
        if not indices:
            return True

        # the try behaves like "with highlighted_pages(indices):"
        self.scene.highlight_pages(indices)
        try:
            msg = self._feedback_rules[code]["explanation"]
            msg = msg.format(which_pages=", ".join([str(p + 1) for p in indices]))
            return self._continue_after_warning(code, msg)
        finally:
            self.scene.highlight_pages_reset()

    def _close_without_saving(self) -> None:
        """Bit of a hack so we can tell Annotator to go away without popping up to ask the user stuff."""
        self._priv_force_close = True
        self.close()

    def closeEvent(self, event: None | QtGui.QCloseEvent) -> None:
        """Overrides the usual QWidget close event.

        Deal with various cases of window trying to close.

        Notes: These include:

          * User closes window via titlebar close icon (or alt-f4 or...)
          * User clicks "Cancel"
          * User clicks "Done"

        Window close or Cancel are currently treated the same way:
        discard all annotations.

        Args:
            event: the event of the window closing.

        Returns:
            None: modifies many instance vars.
        """
        log.debug("========CLOSE EVENT======: {}".format(self))

        self.saveTabStateToServer(self.rubric_widget.get_tab_rubric_lists())

        # Save the current window settings for next time annotator is launched
        self.saveWindowSettings()

        # weird hack to force close if we came from saving (or explicitly not saving)
        # Appropriate signals have already been sent so just close
        force = getattr(self, "_priv_force_close", False)
        if force:
            log.debug("emitting the closing signal")
            self.annotator_done_closing.emit(self.task)
            if event:
                event.accept()
            return

        # We are here b/c of cancel button, titlebar close, or related
        if self.is_dirty():
            msg = SimpleQuestion(
                self,
                "<p>There are unsaved changes to the annotations.</p>\n"
                "<p>Do you want to discard changes and close the annotator?</p>",
            )
            if msg.exec() == QMessageBox.StandardButton.No:
                if event:
                    event.ignore()
                return

        log.debug("emitting reject/cancel signal, discarding, and closing")
        self.annotator_done_reject.emit(self.task)
        if event:
            event.accept()

    def is_dirty(self) -> bool:
        """Is the scene dirty?

        Has the scene been annotated or changed this session? Re-opening
        a previous annotated scene does not dirty it, until changes are
        made. Changes could be made and then undone back to the clean state.
        The concept should be familiar to "file saved" in a text editor.
        """
        if not self.scene:
            return False
        return self.scene.is_dirty()

    def get_nonrubric_text_from_page(self) -> list[str]:
        """Retrieves text (not in rubrics) from the scene.

        Returns:
            List of strings for text annotations not in a rubric.
        """
        if not self.scene:
            return []
        return self.scene.get_nonrubric_text_from_page()

    def latexAFragment(self, *args, **kwargs):
        """Latex a fragment of text."""
        return self.parentMarkerUI.latexAFragment(*args, **kwargs)

    def pickleIt(self) -> tuple[Path, Path]:
        """Capture the annotated pages as a bitmap and a .plom file.

        1. Renders the current scene as a static bitmap.
        2. Retrieves current annotations in reverse chronological order.
        3. Adds various other metadata.
        4. Writes JSON into the ``.plom`` file.

        Note: called "pickle" for historical reasons: it is neither a
        Python pickle nor a real-life pickle.

        Returns:
            tuple: two `pathlib.Path`, one for the rendered image and
            one for the ``.plom`` file.
        """
        assert self.scene
        aname = self.scene.save(self.saveName)
        lst = self.scene.pickleSceneItems()  # newest items first
        lst.reverse()  # so newest items last
        # get the crop-rect as proportions of underlying image
        # is 4-tuple (x,y,w,h) scaled by image width / height
        crop_rect_data = self.scene.current_crop_rectangle_as_proportions()
        # TODO: consider saving colour only if not red?
        plomData = {
            "base_images": self.scene.get_src_img_data(only_visible=True),
            "saveName": str(aname),
            "maxMark": self.maxMark,
            "currentMark": self.getScore(),
            "sceneScale": self.scene.get_scale_factor(),
            "annotationColor": self.scene.ink.color().getRgb()[:3],
            "crop_rectangle_data": crop_rect_data,
            "sceneItems": lst,
        }
        plomfile = self.saveName.with_suffix(".plom")

        with open(plomfile, "w") as fh:
            json.dump(plomData, fh, indent="  ", default=_json_path_to_str)
            fh.write("\n")
        return aname, plomfile

    def unpickleIt(self, plomData: dict[str, Any]) -> None:
        """Unpickles the page by calling scene.unpickleSceneItems and sets the page's mark.

        Args:
            plomData: a dictionary containing the data for the
                pickled ``.plom`` file.

        Returns:
            None
        """
        self.view.setHidden(True)
        assert self.scene
        if plomData.get("sceneScale", None):
            self.scene.set_scale_factor(plomData["sceneScale"])
        if plomData.get("annotationColor", None):
            self.scene.set_annotation_color(plomData["annotationColor"])
        # Put the scene items back
        self.scene.unpickleSceneItems(plomData["sceneItems"])
        # set crop rectangle from plom file contains if present
        # else, if use held-crop rectangle if present
        if plomData.get("crop_rectangle_data", None):
            self.scene.crop_from_plomfile(plomData["crop_rectangle_data"])
        else:
            if self.held_crop_rectangle_data:  # if a crop is being held, use it.
                self.scene.crop_from_plomfile(self.held_crop_rectangle_data)
        self.view.setHidden(False)

    def setZoomComboBox(self) -> None:
        """Sets the combo box for the zoom method.

        Returns:
            None but modifies self.ui
        """
        self.ui.zoomCB.addItem("User")
        self.ui.zoomCB.addItem("Fit page")
        self.ui.zoomCB.addItem("Fit width")
        self.ui.zoomCB.addItem("Fit height")
        self.ui.zoomCB.addItem("200%")
        self.ui.zoomCB.addItem("150%")
        self.ui.zoomCB.addItem("100%")
        self.ui.zoomCB.addItem("50%")
        self.ui.zoomCB.addItem("33%")
        self.ui.zoomCB.currentIndexChanged.connect(self.zoomCBChanged)

    def isZoomFitWidth(self) -> bool:
        """Has the user selected "Fit Width"?"""
        return self.ui.zoomCB.currentText() == "Fit width"

    def isZoomFitHeight(self) -> bool:
        """Has the user selected "Fit Height"?"""
        return self.ui.zoomCB.currentText() == "Fit height"

    def changeCBZoom(self, CBIndex: int) -> None:
        """Keeps zoom combo box at selected index.

        Args:
            CBIndex: the current zoom Combo Box Index

        Returns:
            None but modifies self.ui
        """
        old = self.ui.zoomCB.blockSignals(True)
        self.ui.zoomCB.setCurrentIndex(CBIndex)
        self.ui.zoomCB.blockSignals(old)

    def zoomCBChanged(self) -> None:
        """Modifies the page view based on the selected zoom option.

        Returns:
            None but modifies self.ui
        """
        if not self.scene:
            return
        if self.ui.zoomCB.currentText() == "Fit page":
            self.view.zoomFitPage()
        elif self.ui.zoomCB.currentText() == "Fit width":
            self.view.zoomFitWidth()
        elif self.ui.zoomCB.currentText() == "Fit height":
            self.view.zoomFitHeight()
        elif self.ui.zoomCB.currentText() == "100%":
            self.view.zoomToScale(1)
        elif self.ui.zoomCB.currentText() == "150%":
            self.view.zoomToScale(1.5)
        elif self.ui.zoomCB.currentText() == "200%":
            self.view.zoomToScale(2)
        elif self.ui.zoomCB.currentText() == "50%":
            self.view.zoomToScale(0.5)
        elif self.ui.zoomCB.currentText() == "33%":
            self.view.zoomToScale(0.33)
        else:
            pass
        self.view.setFocus()

    def getRubricsFromServer(self) -> list[dict[str, Any]]:
        """Request a latest rubric list for current question."""
        return self.parentMarkerUI.getRubricsFromServer(self.question_idx)

    def getOneRubricFromServer(self, rid: int) -> dict[str, Any]:
        """Request a latest rubric list for current question."""
        return self.parentMarkerUI.getOneRubricFromServer(rid)

    def getOtherRubricUsagesFromServer(self, rid: int) -> list[int]:
        """Request a list of paper numbers using the given rubric.

        Args:
            rid: the identifier of the rubric.

        Returns:
            List of paper numbers using the rubric, excluding the paper
            the annotator currently at.
        """
        assert self.task
        curr_paper_number = self.papernum
        result = self.parentMarkerUI.getOtherRubricUsagesFromServer(rid)
        if curr_paper_number in result:
            result.remove(curr_paper_number)
        return result

    def view_other_paper(
        self, paper_number: int, *, _parent: QWidget | None = None
    ) -> None:
        """Opens another dialog to view a paper.

        Args:
            paper_number: the paper number of the paper to be viewed.

        Keyword:
            _parent: override the default parent which is ourselves.

        Returns:
            None
        """
        if _parent is None:
            _parent = self
        self.parentMarkerUI.view_other(
            paper_number=paper_number, question_idx=self.question_idx, _parent=_parent
        )

    def saveTabStateToServer(self, tab_state):
        """Have Marker upload this tab state to the server."""
        self.parentMarkerUI.saveTabStateToServer(tab_state)

    def getTabStateFromServer(self):
        """Have Marker download the tab state from the server."""
        return self.parentMarkerUI.getTabStateFromServer()

    def refreshRubrics(self):
        """Ask the rubric widget to refresh rubrics."""
        self.rubric_widget.refreshRubrics()

    def createNewRubric(self, new_rubric) -> dict[str, Any]:
        """Ask server to create a new rubric with data supplied."""
        return self.parentMarkerUI.sendNewRubricToServer(new_rubric)

    def modifyRubric(
        self,
        rid: int,
        updated_rubric: dict[str, Any],
        *,
        minor_change: bool | None = None,
        tag_tasks: bool | None = None,
    ) -> dict[str, Any]:
        """Ask server to modify an existing rubric with the new data supplied."""
        return self.parentMarkerUI.modifyRubricOnServer(
            rid, updated_rubric, minor_change=minor_change, tag_tasks=tag_tasks
        )

    def tags_changed(self, task: str, tags: list[str]) -> None:
        """React to possible tag change signals."""
        if task == self.task:
            self.update_attn_bar(tags=tags)

    def tag_paper(
        self, task: str | None = None, dialog_parent: QWidget | None = None
    ) -> None:
        """Open the tagging dialog on this task."""
        if not self.scene:
            return
        if not task:
            if not self.task:
                return
            task = self.task
        if not dialog_parent:
            dialog_parent = self
        self.parentMarkerUI.manage_tags(task, parent=dialog_parent)

    def show_previous(self):
        log.debug(
            f"Show previous called: debug history = {self.parentMarkerUI.marking_history}"
        )

        if not self.parentMarkerUI.marking_history:
            WarnMsg(
                self,
                "The client cannot determine the previous paper. "
                "Please select from the task list instead.",
            ).exec()
            return
        keydata = self.get_key_bindings()
        PreviousPaperViewer(self, self.parentMarkerUI.marking_history, keydata).exec()

    def _get_annotation_by_task(self, task):
        return self.parentMarkerUI.get_file_for_previous_viewer(task)
