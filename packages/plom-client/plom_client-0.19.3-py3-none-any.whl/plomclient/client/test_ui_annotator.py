# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023-2025 Colin B. Macdonald

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget

from .annotator import Annotator
from .marker import MarkerClient


class MockMarker(QWidget):
    """Just enough Marker to open Annotator."""

    annotatorSettings = {
        "keybinding_name": None,
        "zoomState": None,
        "compact": None,
        "keybinding_custom_overlay": None,
    }

    tags_changed_signal = pyqtSignal(str, list)

    def getRubricsFromServer(self, q):
        return []

    def getTabStateFromServer(self):
        return []

    def is_experimental(self):
        return True

    def saveTabStateToServer(self, foo):
        pass

    def view_solutions(self):
        pass


def test_annotr_open(qtbot) -> None:
    a = Annotator("some_user", MockMarker())
    a.show()
    qtbot.addWidget(a)
    # wait before closing: annotator has some buggy QTimer stuff...
    qtbot.wait(100)
    qtbot.wait(100)

    # mash some buttons
    for b in (
        a.ui.boxButton,
        a.ui.crossButton,
        a.ui.deleteButton,
        a.ui.lineButton,
        a.ui.moveButton,
        a.ui.panButton,
        a.ui.penButton,
        a.ui.textButton,
        a.ui.tickButton,
        a.ui.zoomButton,
    ):
        qtbot.mouseClick(b, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(a.ui.undoButton, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(a.ui.redoButton, Qt.MouseButton.LeftButton)

    # narrow mode, then reopen with UI button
    qtbot.keyClick(a, Qt.Key.Key_Home)
    # TODO: no more direct button to do this, try to replace with menu clicking?
    # qtbot.mouseClick(a.ui.wideButton, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    # path = qtbot.screenshot(a)
    # assert False, path

    # clicking would do "next-paper": not prepared to test that yet
    # qtbot.mouseClick(a.saveNextButton, Qt.MouseButton.LeftButton)
    qtbot.keyClick(a, Qt.Key.Key_C, modifier=Qt.KeyboardModifier.ControlModifier)


class MockQApp:
    downloader = None


def test_marker_open(qtbot) -> None:
    w = MarkerClient(MockQApp())
    qtbot.mouseClick(w.ui.hamMenuButton, Qt.MouseButton.LeftButton)
    # path = qtbot.screenshot(w)
    # assert False, path
    qtbot.keyClick(w, Qt.Key.Key_Q, modifier=Qt.KeyboardModifier.ControlModifier)
