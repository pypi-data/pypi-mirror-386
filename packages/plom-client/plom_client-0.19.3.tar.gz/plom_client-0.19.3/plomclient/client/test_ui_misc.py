# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2020, 2023-2025 Colin B. Macdonald

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from pytest import raises

from .chooser import Chooser
from .useful_classes import BigMessageDialog, BlankIDBox


def test_BlankIDBoxDialog(qtbot) -> None:
    d = BlankIDBox(None, 16)
    d.show()
    qtbot.addWidget(d)
    qtbot.mouseClick(d.noB, Qt.MouseButton.LeftButton)
    assert d.testNumber == 16


def test_BlankIDBoxDialog2(qtbot) -> None:
    d = BlankIDBox(None, 32)
    d.show()
    qtbot.addWidget(d)
    qtbot.mouseClick(d.blankB, Qt.MouseButton.LeftButton)
    assert d.testNumber == 32


def DISABLE_test_Chooser(qtbot) -> None:
    app = QApplication([])
    window = Chooser(app)
    window.show()
    qtbot.add_widget(window)
    # TODO: only if a local server is running, otherwise pops the dialog
    qtbot.mouseClick(window.ui.getServerInfoButton, Qt.MouseButton.LeftButton)
    assert window.ui.infoLabel.text().startswith("Server address")
    # TODO: seems to pop open the (model) dialog
    # qtbot.mouseClick(window.ui.optionsButton, Qt.MouseButton.LeftButton)
    # TODO: password too short, generates log should be so testable
    qtbot.mouseClick(window.ui.markButton, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.ui.closeButton, Qt.MouseButton.LeftButton)


def DISABLE_test_Chooser_again(qtbot) -> None:
    # TODO: disabled as we cannot open another, maybe b/c this:
    # TODO: https://pytest-qt.readthedocs.io/en/3.3.0/app_exit.html
    app = QApplication([])
    window = Chooser(app)
    window.show()
    qtbot.addWidget(window)
    qtbot.mouseClick(window.ui.closeButton, Qt.MouseButton.LeftButton)


def test_BigMessageDialog_no_details(qtbot) -> None:
    d = BigMessageDialog(None, "foo")
    d.show()
    qtbot.addWidget(d)
    assert not d.toggle_button.isVisible()


def test_BigMessageDialog_details_not_both(qtbot) -> None:
    with raises(ValueError, match="Cannot.*both.*"):
        BigMessageDialog(None, "foo", details="bar", details_html="<p>bar</p>")


def test_BigMessageDialog_gets_big_then_small(qtbot) -> None:
    d = BigMessageDialog(None, "foo", details="bar")
    d.show()
    qtbot.addWidget(d)
    w = d.geometry().width()
    h = d.geometry().height()
    qtbot.mouseClick(d.toggle_button, Qt.MouseButton.LeftButton)
    w2 = d.geometry().width()
    h2 = d.geometry().height()
    # width is maintained
    assert w2 == w
    assert h2 > h
    qtbot.mouseClick(d.toggle_button, Qt.MouseButton.LeftButton)
    w3 = d.geometry().width()
    h3 = d.geometry().height()
    assert w3 == w
    assert h3 == h
    d.accept()


def test_BigMessageDialog_starts_big_then_small(qtbot) -> None:
    d = BigMessageDialog(None, "foo", details="bar", show=True)
    d.show()
    qtbot.addWidget(d)
    w = d.geometry().width()
    h = d.geometry().height()
    qtbot.mouseClick(d.toggle_button, Qt.MouseButton.LeftButton)
    w2 = d.geometry().width()
    h2 = d.geometry().height()
    # width is maintained
    assert w2 == w
    assert h2 < h
    qtbot.mouseClick(d.toggle_button, Qt.MouseButton.LeftButton)
    w3 = d.geometry().width()
    h3 = d.geometry().height()
    assert w3 == w
    assert h3 == h
    d.accept()
