# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2021 Andrew Rechnitzer
# Copyright (C) 2020-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2024 Aden Chan
# Copyright (C) 2024 Bryan Tanady

from __future__ import annotations

from copy import deepcopy
from typing import Any

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsItem

from . import (
    CommandTool,
    OutOfBoundsFill,
    OutOfBoundsPen,
    UndoStackMoveMixin,
)
from .delta import DeltaItem, GhostDelta
from .text import GhostText, TextItem


class CommandRubric(CommandTool):
    """A group of marks and text.

    Command to do a delta and a textitem together (a "rubric" or
    "saved comment").
    """

    def __init__(self, scene, pt: QPointF, rubric: dict[str, Any]) -> None:
        """Constructor for this class.

        Args:
            scene (PageScene): Plom's annotation scene.
            pt: where to place the rubric.
            rubric: must have at least these keys:
                "rid", "kind", "value", "out_of", "display_delta", "text".
                Any other keys are probably ignored and will almost
                certainly not survive being serialized.
                We copy the data, so changes to the original will not
                automatically update this object,

        Returns:
            None
        """
        super().__init__(scene)
        self.gdt = RubricItem(pt, rubric, _scene=scene, style=scene.style)
        self.setText("Rubric")

    @classmethod
    def from_pickle(cls, X, *, scene):
        """Construct a CommandRubric from a serialized RubricItem.

        TODO: could this comandFoo.__init__() take a FooItem?
        """
        assert X[0] == "Rubric"
        if len(X) != 4:
            raise ValueError("wrong length of pickle data")
        # knows to latex it if needed.
        return cls(scene, QPointF(X[1], X[2]), X[3])

    def get_undo_redo_animation_shape(self):
        return self.gdt.shape()

    def redo(self):
        self.scene.addItem(self.gdt)
        self.redo_animation()

    def undo(self):
        self.scene.removeItem(self.gdt)
        self.undo_animation()


class RubricItem(UndoStackMoveMixin, QGraphicsItemGroup):
    """A group of Delta and Text presenting a rubric.

    TODO: passing in scene is a workaround so the TextItem can talk to
    someone about building LaTeX... can we refactor that somehow?
    """

    def __init__(
        self, pt: QPointF, rubric: dict[str, Any], *, _scene, style: dict[str, Any]
    ) -> None:
        """Constructor for this class.

        Args:
            pt: where to place the rubric.
            rubric: must have at least these keys:
                "rid", "kind", "value", "out_of", "display_delta", "text".
                It can optionally have "revision" and "tags".
                TODO: these two use get so will automatically become None.
                Any other keys are probably ignored and will almost
                certainly not survive being serialized.
                We copy the data, so changes to the original will not
                automatically update this object,

        Keyword Args:
            _scene (PageScene): Plom's annotation scene.
            style: various things effecting color, linewidths etc.

        Returns:
            None
        """
        super().__init__()
        self.pt = pt
        self.style = style
        self._rubric = deepcopy(rubric)
        self._attn_msg = ""
        # self._attn_button = None
        # TODO: replace each with @property?
        self.rubricID = rubric["rid"]
        self.kind = rubric["kind"]
        # centre under click
        self.di = DeltaItem(pt, rubric["value"], rubric["display_delta"], style=style)
        self.blurb = TextItem(pt, rubric["text"], style=style, _texmaker=_scene)
        # TODO: probably we "restyle" the child objects twice as each init did this too
        self.restyle(style)
        # Set the underlying delta and text to not pickle as we will handle that
        self.saveable = True
        self.di.saveable = False
        self.blurb.saveable = False

        # TODO: the blurb will do this anyway, but may defer this to "later",
        # meanwhile we have the wrong size for tweakPositions (Issue #1391).
        # TODO: can be removed once the border adjusts automatically to resize.
        self.blurb.textToPng()

        # move blurb so that its top-left corner is next to top-right corner of delta.
        self._tweakPositions(rubric["display_delta"], rubric["text"])
        # hide delta if trivial
        if rubric["display_delta"] == ".":
            self.di.setVisible(False)
        else:
            self.di.setVisible(True)
            self.addToGroup(self.di)
        # hide blurb if text is trivial
        if rubric["text"] == ".":
            self.blurb.setVisible(False)
        else:
            self.blurb.setVisible(True)
            self.addToGroup(self.blurb)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        # self.update_attn_state(attn_msg, _scene=_scene)

    def update_attn_state(self, attn_msg: str, *, _scene=None) -> None:
        """Update the "attention state" of this RubricItem.

        Args:
            attn_msg: a string indicating what the problem is, that
                will be shown as a tooltip and perhaps in other ways.
                You can pass the empty string to reset the state to
                NOT needing attention.
        """
        self.setToolTip(attn_msg)
        self._attn_msg = attn_msg
        # # TODO: this button stuff disabled for now
        # if not self._attn_button:
        #     self._create_attn_button(attn_msg, _scene)
        #     self._attn_msg = attn_msg
        #     return
        # h = self._attn_button
        # b = h.widget()
        # b.setToolTip(attn_msg)
        # rand_colour = "#" + hex(random.randint(0, 256**3 - 1))[2:]
        # b.setStyleSheet("QToolButton { background-color: " + rand_colour + "; }")
        # self._attn_msg = attn_msg

    # # WIP currently-unused code to draw action buttons near the rubric
    # def _create_attn_button(self, attn_msg: str, _scene) -> None:
    #     b = QToolButton(text="\N{Warning Sign}")  # type: ignore[call-arg]
    #     b.setStyleSheet("QToolButton { background-color: #0000ff; }")
    #     b.clicked.connect(self._dismiss_attn_button_interactively)
    #     # parenting the menu inside the scene
    #     m = QMenu(b)
    #     m.addAction(
    #         "Show me the diff", lambda: print("Update rubric: not implemented yet")
    #     )
    #     m.addSeparator()
    #     m.addAction("Dismiss", self._dismiss_attn_button)
    #     b.setMenu(m)
    #     # b.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    #     # TODO: "most common way is to pass a widget pointer to [Scene.addWidget()]"
    #     h = QGraphicsProxyWidget()
    #     h.setWidget(b)
    #     h.setOpacity(0.66)
    #     # h.setPos(self.blurb.boundingRect().bottomRight())
    #     # TODO: these magic numbers come from _tweakPositions
    #     h.setPos(self.pt)
    #     cr = self.di.boundingRect()
    #     h.moveBy(cr.width() + 5, cr.height() / 2)

    #     h.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
    #     h.setFlag(QGraphicsItem.GraphicsItemFlag.ItemDoesntPropagateOpacityToChildren)
    #     b.setToolTip(attn_msg)
    #     # TODO: both of these allow it to move but not receive mouse events
    #     # self.addToGroup(h)
    #     # h.setParentItem(self)
    #     _scene.addItem(h)
    #     self._attn_button = h

    def as_rubric(self) -> dict[str, Any]:
        """Return as a rubric dict."""
        # TODO: probably `return self._rubric`?  or is explicit is better than implicit?
        return {
            "rid": self.rubricID,
            "kind": self.kind,
            "display_delta": self.di.display_delta,
            "value": self.di.value,
            "out_of": self._rubric["out_of"],
            "text": self.blurb.toPlainText(),
            "revision": self._rubric.get("revision"),
            "tags": self._rubric["tags"],
        }

    def restyle(self, style) -> None:
        self.style = style
        self.thick = self.style["pen_width"] / 2
        # force a relatexing of the textitem in case it is a latex png
        self.blurb.restyle(style)
        self.di.restyle(style)

    def _tweakPositions(self, display_delta, text):
        pt = self.pt
        self.blurb.setPos(pt)
        self.di.setPos(pt)
        # TODO: may want some special treatment in "." case
        # cr = self.di.boundingRect()
        # self.blurb.moveBy(cr.width() + 5, 0)

        # if no display_delta, then move things accordingly
        if display_delta == ".":
            cr = self.blurb.boundingRect()
            self.blurb.moveBy(0, -cr.height() / 2)
        elif text == ".":
            cr = self.di.boundingRect()
            self.di.moveBy(0, -cr.height() / 2)
        else:  # render both
            cr = self.di.boundingRect()
            self.di.moveBy(0, -cr.height() / 2)
            self.blurb.moveBy(cr.width() + 5, -cr.height() / 2)

    def pickle(self) -> list[Any]:
        return [
            "Rubric",
            self.pt.x() + self.x(),
            self.pt.y() + self.y(),
            self.as_rubric(),
        ]

    def paint(self, painter, option, widget):
        # TODO: for now, we reuse the out-of-bounds colouring for needs attn
        if not self.scene().itemWithinBounds(self) or self._attn_msg:
            painter.setPen(OutOfBoundsPen)
            painter.setBrush(OutOfBoundsFill)
            painter.drawLine(option.rect.topLeft(), option.rect.bottomRight())
            painter.drawLine(option.rect.topRight(), option.rect.bottomLeft())
            painter.drawRoundedRect(option.rect, 10, 10)
        else:
            # paint a bounding rectangle for undo/redo highlighting
            painter.setPen(
                QPen(self.style["annot_color"], self.thick, style=Qt.PenStyle.DotLine)
            )
            painter.drawRoundedRect(option.rect, 10, 10)
        # paint the normal item with the default 'paint' method
        super().paint(painter, option, widget)

    def sign_of_delta(self) -> int:
        if int(self.di.value) == 0:
            return 0
        elif int(self.di.value) > 0:
            return 1
        else:
            return -1

    def is_delta_positive(self) -> bool:
        return int(self.di.value) > 0

    def get_delta_value(self) -> int:
        return int(self.di.value)

    # # WIP currently-unused code to draw action buttons near the rubric
    # def _dismiss_attn_button_interactively(self):
    #     if not self.scene():
    #         # nothing to do if we're not in a scene any more
    #         return
    #     parent = self.scene().views()[0].parent()
    #     # yuck, had to go way up the chain to find someone who can parent a dialog!
    #     # maybe that means this code should NOT be opening dialogs
    #     InfoMsg(
    #         parent,
    #         self._attn_msg,
    #         info="""
    #             Learn more about
    #             <a href="https://plom.readthedocs.io/en/latest/rubrics.html">rubric
    #             revisions</a>.
    #         """,
    #         info_pre=False,
    #     ).exec()
    #     self._dismiss_attn_button()

    # # WIP currently-unused code to draw action buttons near the rubric
    # def _dismiss_attn_button(self):
    #     if not self.scene():
    #         # nothing to do if we're not in a scene any more
    #         return
    #     if not self._attn_button:
    #         # nothing to do b/c no more attn button
    #         return
    #     self.scene().removeItem(self._attn_button)
    #     self._attn_button.deleteLater()
    #     self._attn_button = None
    #     self._attn_msg = ""


class GhostComment(QGraphicsItemGroup):
    def __init__(self, annot_scale: float, display_delta: str, txt: str, fontsize: int):
        super().__init__()
        self.legal = False
        self.annot_scale = annot_scale
        self.di = GhostDelta(display_delta, fontsize, legal=self.legal)
        self.blurb = GhostText(txt, annot_scale, fontsize, legal=self.legal)
        self.changeComment(display_delta, txt)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def _tweakPositions(self, display_delta, txt):
        """Adjust the positions of the delta and text depending on their size and content.

        Note: does not fix up the size of the boxes, see changeComment which does.
        """
        pt = self.pos()
        # Offset is physical unit which will cause the gap gets bigger when zoomed in.
        offset = 0
        shifted_pt = QPointF(pt.x() + offset, pt.y())
        self.blurb.setPos(shifted_pt)
        self.di.setPos(shifted_pt)

        # if no delta, then move things accordingly
        if display_delta == ".":
            cr = self.blurb.boundingRect()
            self.blurb.moveBy(0, -cr.height() / 2)
        elif txt == ".":
            cr = self.di.boundingRect()
            self.di.moveBy(0, -cr.height() / 2)
        else:  # render both
            cr = self.di.boundingRect()
            self.di.moveBy(0, -cr.height() / 2)
            self.blurb.moveBy(cr.width() + 5, -cr.height() / 2)

    def changeComment(self, display_delta, txt, legal=True):
        # need to force a bounding-rect update by removing an item and adding it back
        self.removeFromGroup(self.di)
        self.removeFromGroup(self.blurb)
        # change things
        self.legal = legal
        self.di.changeDelta(display_delta, legal)
        self.blurb.update_annot_scale(self.annot_scale)
        self.blurb.changeText(txt, legal)
        # move to correct positions
        self._tweakPositions(display_delta, txt)
        if display_delta == ".":  # hide the delta
            self.di.setVisible(False)
        else:
            self.di.setVisible(True)
            self.addToGroup(self.di)
        # hide blurb if text trivial
        if txt == ".":  # hide the text
            self.blurb.setVisible(False)
        else:
            self.blurb.setVisible(True)
            self.addToGroup(self.blurb)

    def change_rubric_size(self, fontsize: int | None, annot_scale: float) -> None:
        """Change comment size.

        Args:
            fontsize: the fontsize that will be applied in the comment.
            annot_scale: the scene's global scale.
        """
        if not fontsize:
            fontsize = 10

        font = QFont("Helvetica")
        font.setPixelSize(round(fontsize))
        self.blurb.setFont(font)
        font = QFont("Helvetica")
        font.setPixelSize(round(1.25 * fontsize))
        self.di.setFont(font)
        self.annot_scale = annot_scale
        self.changeComment(
            self.di.display_delta, self.blurb.toPlainText(), legal=self.legal
        )

    def paint(self, painter, option, widget):
        # paint a bounding rectangle for undo/redo highlighting
        # TODO: pen width hardcoded
        painter.setPen(QPen(QColor("blue"), 0.5, style=Qt.PenStyle.DotLine))
        painter.drawRoundedRect(option.rect, 10, 10)
        # paint the normal item with the default 'paint' method
        super().paint(painter, option, widget)
