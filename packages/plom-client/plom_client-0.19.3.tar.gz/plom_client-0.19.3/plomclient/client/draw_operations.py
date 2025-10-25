# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Andrew Rechnitzer
# Copyright (C) 2020-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2022 Joey Shi
# Copyright (C) 2024 Aden Chan
# Copyright (C) 2024 Aidan Murphy
# Copyright (C) 2024-2025 Bryan Tanady
# Copyright (C) 2025 Deep Shah

"""Handles drawing operations for the Plom client Annotator.

This module defines the logic for all the drawing tools available in the client,
including creating, modifying, and deleting annotations on a page.
"""

# a different kind of annotations... this is about code typing
from __future__ import annotations

from PyQt6.QtCore import QLineF, QPointF, Qt, QRectF
from PyQt6.QtGui import QGuiApplication, QPainterPath, QTransform, QPen, QColor
from PyQt6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsSceneDragDropEvent,
    QGraphicsSceneMouseEvent,
)

from .tools import (
    CommandArrow,
    CommandArrowDouble,
    CommandLine,
    CommandTiltedBox,
    CommandBox,
    CommandEllipse,
    CommandRubric,
    CommandPen,
    DefaultTickRadius,
    CommandTick,
    CommandCross,
    CommandQMark,
    CommandText,
    TextItem,
    CommandDelete,
    CommandPenArrow,
    CommandHighlight,
)

from .pageview import PageView


class MultiStageDrawer:
    """An abstract base class for a multi-stage drawing operation.

    Each specific tool that requires a sequence of mouse events (press, move,
    release) will have its own concrete Drawer class that inherits from this one.
    """

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the drawer with a reference to the main scene and the initial mouse event.

        Args:
            scene (PageScene): A reference to the main scene where drawing occurs.
                This is a `QGraphicsScene` but probably it needs to be the
                subclass PageScene (from Plom Client).
            event: The initial mouse press or drag event.
        """
        self.scene = scene
        self.origin_pos = event.scenePos()
        self.is_finished = False

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Abstract method to handle a mouse move event."""
        pass

    def mouse_release(self, event: QGraphicsSceneMouseEvent) -> None:
        """Abstract method to handle a mouse release event."""
        pass

    def mouse_press(self, event: QGraphicsSceneMouseEvent) -> None:
        """Abstract method to handle a mouse press event."""
        pass

    def cleanup(self):
        """Abstract method to do any cleanup."""
        pass

    def cancel(self):
        """Cancel the operation and clean up temporary items."""
        self.cleanup()
        self.is_finished = True

    def finish(self):
        """Complete the operation and clean up temporary items."""
        self.cleanup()
        self.is_finished = True


class LineToolDrawer(MultiStageDrawer):
    """Handles all drawing logic for the 'Line' tool.

    This includes creating simple lines and maybe in the future the
    tilted rectangles feature.  Issue #5019.
    """

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the LineToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.current_pos = self.origin_pos
        self.arrow_flag = self._get_arrow_flag(event)

        self.line_item = QGraphicsLineItem(QLineF(self.origin_pos, self.current_pos))
        self.line_item.setPen(self.scene.ink)
        self.scene.addItem(self.line_item)

    def _get_arrow_flag(self, event):
        """Determines which version of the line tool to use based on modifier keys."""
        if (event.button() == Qt.MouseButton.RightButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ShiftModifier
        ):
            return 2
        elif (event.button() == Qt.MouseButton.MiddleButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ControlModifier
        ):
            return 4
        else:
            return 1

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Updates the temporary line to follow the mouse cursor."""
        self.current_pos = event.scenePos()
        self.line_item.setLine(QLineF(self.origin_pos, self.current_pos))

    def mouse_release(self, event) -> None:
        """Finalizes the drawing operation, creating a line or perhaps other object.

        We create either a simple line or in the future maybe
        or a tilted rectangle.  Push the corresponding command
        to the undo stack.
        """
        command = None

        if (self.origin_pos - self.current_pos).manhattanLength() > 24:
            if self.arrow_flag == 1:
                command = CommandLine(self.scene, self.origin_pos, self.current_pos)
            elif self.arrow_flag == 2:
                # TODO: we might be porting to tilted boxes instead, Issue #5019
                command = CommandArrow(self.scene, self.origin_pos, self.current_pos)
                # command = self._create_tilted_box(height=80.0)
            elif self.arrow_flag == 4:
                # command = self._create_tilted_box(height=120.0)
                command = CommandArrowDouble(
                    self.scene, self.origin_pos, self.current_pos
                )

        if command:
            self.scene.undoStack.push(command)

        self.finish()

    def _create_tilted_box(self, height):
        """Helper function to perform the vector math for a tilted rectangle."""
        p1 = self.origin_pos
        p2 = self.current_pos
        v1 = p2 - p1

        # Prevent a crash if the user clicks without dragging.
        if v1.x() == 0 and v1.y() == 0:
            return None

        v_perp = QPointF(-v1.y(), v1.x())
        if v_perp.y() > 0:
            v_perp *= -1

        v2 = v_perp
        v2_length = (v2.x() ** 2 + v2.y() ** 2) ** 0.5

        if v2_length == 0:
            return None

        # Scale the perpendicular vector to the fixed height.
        v2_unit = v2 / v2_length
        v2_scaled = v2_unit * height

        # Calculate the final two points of the rectangle.
        p3 = p2 + v2_scaled
        p4 = p1 + v2_scaled

        path = QPainterPath(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.lineTo(p4)
        path.closeSubpath()

        return CommandTiltedBox(self.scene, path)

    def cleanup(self):
        """Removes the temporary line item from the scene."""
        if self.line_item and self.line_item.scene():
            self.scene.removeItem(self.line_item)
        self.line_item = None


class BoxToolDrawer(MultiStageDrawer):
    """Handles all drawing logic for the 'Box' tool (both rectangles and ellipses)."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the BoxToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.current_pos = self.origin_pos
        self.box_flag = self._get_box_flag(event)
        # TODO: probably this can be lots of things
        self.temp_item: None | QGraphicsRectItem | QGraphicsEllipseItem = None
        self.minimum_side_length = 24

        if self.box_flag == 1:  # Rectangle
            self.temp_item = QGraphicsRectItem(
                QRectF(self.origin_pos, self.current_pos).normalized()
            )
        elif self.box_flag == 2:  # Ellipse
            self.temp_item = QGraphicsEllipseItem(
                QRectF(self.origin_pos.x(), self.origin_pos.y(), 0, 0)
            )

        if self.temp_item:
            self.temp_item.setPen(self.scene.ink)
            self.temp_item.setBrush(self.scene.lightBrush)
            self.scene.addItem(self.temp_item)

    def _get_box_flag(self, event):
        """Determines whether to draw a box or an ellipse."""
        if (event.button() == Qt.MouseButton.RightButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ShiftModifier
        ):
            return 2  # Ellipse
        else:
            return 1  # Box

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Updates the size of the temporary shape as the user drags the mouse."""
        if not self.temp_item:
            return

        self.current_pos = event.scenePos()

        if self.box_flag == 1:
            rect = QRectF(self.origin_pos, self.current_pos).normalized()
            self.temp_item.setRect(rect)
        elif self.box_flag == 2:
            rx = abs(self.origin_pos.x() - self.current_pos.x())
            ry = abs(self.origin_pos.y() - self.current_pos.y())
            rect = QRectF(
                self.origin_pos.x() - rx, self.origin_pos.y() - ry, 2 * rx, 2 * ry
            )
            self.temp_item.setRect(rect)

    def mouse_release(self, event):
        """Finalizes the shape and pushes the correct command to the undo stack."""
        command = None

        if self.temp_item:
            final_rect = self.temp_item.rect().normalized()

            if (
                final_rect.width() > self.minimum_side_length
                and final_rect.height() > self.minimum_side_length
            ):
                if self.box_flag == 1:
                    command = CommandBox(self.scene, final_rect)
                elif self.box_flag == 2:
                    command = CommandEllipse(self.scene, final_rect)

        if command:
            self.scene.undoStack.push(command)

        self.finish()

    def cleanup(self):
        """Removes the temporary shape from the scene."""
        if self.temp_item and self.temp_item.scene():
            self.scene.removeItem(self.temp_item)
        self.temp_item = None


class RubricToolDrawer(MultiStageDrawer):
    """Handles the both the simple placement and complex click-or-drag logic for the Rubric tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the RubricToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.state = 0  # 0=idle, 1=drawing box, 2=drawing line
        self.temp_box_item: None | QGraphicsRectItem = None
        self.path_item = None
        self.permanent_box_item = None
        self.minimum_side_length = 24

        self.scene._updateGhost(self.scene.current_rubric)
        self.scene._exposeGhost()
        self.scene.ghostItem.setPos(event.scenePos())

        if isinstance(event, QGraphicsSceneDragDropEvent):
            # special handing of the drag-drop event from rubric list
            self._stamp_rubric()
            self.finish()
        else:
            self.mouse_press(event)

    def _stamp_rubric(self) -> bool:
        """Helper to place a rubric annotation at the ghost item's position."""
        pt = self.scene.ghostItem.pos()
        if not self.scene.isLegalRubric(
            self.scene.current_rubric
        ) or self.scene.textUnderneathPoint(pt):
            return False
        command = CommandRubric(self.scene, pt, self.scene.current_rubric)
        self.scene.undoStack.push(command)
        return True

    def mouse_press(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse press events for the rubric tool."""
        if self.state == 0:
            if not self.scene.isLegalRubric(self.scene.current_rubric):
                self.cancel()
                return

            if self.scene.textUnderneathGhost():
                self.cancel()
                return

            self.state = 1
            self.origin_pos = event.scenePos()
            self.temp_box_item = QGraphicsRectItem(
                QRectF(self.origin_pos, self.origin_pos)
            )
            self.temp_box_item.setPen(self.scene.ink)
            self.temp_box_item.setBrush(self.scene.lightBrush)
            self.scene.addItem(self.temp_box_item)

        elif self.state == 2:
            if not self._stamp_rubric():
                return

            assert self.path_item is not None
            final_path = self.path_item.path()
            self.scene.removeItem(self.path_item)
            self.path_item = None

            if not final_path.isEmpty():
                line_command = CommandPen(self.scene, final_path)
                self.scene.undoStack.push(line_command)

            self.scene.undoStack.endMacro()
            self.state = 3
            self.finish()

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the rubric tool."""
        self.scene.ghostItem.setPos(event.scenePos())

        if self.state == 1:
            if self.temp_box_item:
                self.current_pos = event.scenePos()
                self.temp_box_item.setRect(
                    QRectF(self.origin_pos, self.current_pos).normalized()
                )
        elif self.state == 2:
            if self.path_item and self.permanent_box_item:
                self.current_pos = event.scenePos()
                ghost_rect = self.scene.ghostItem.mapRectToScene(
                    self.scene.ghostItem.boundingRect()
                )
                box_rect = self.permanent_box_item.mapRectToScene(
                    self.permanent_box_item.boundingRect()
                )
                self.path_item.setPath(self.scene.whichLineToDraw(ghost_rect, box_rect))

    def mouse_release(self, event):
        """Handles mouse release events for the rubric tool."""
        if self.state == 1:
            final_rect = self.temp_box_item.rect()
            self.scene.removeItem(self.temp_box_item)
            self.temp_box_item = None

            if (
                final_rect.width() < self.minimum_side_length
                or final_rect.height() < self.minimum_side_length
            ):
                self._stamp_rubric()
                self.finish()
            else:
                # The box is large enough, so transition to the next state.
                self.state = 2
                self.scene.undoStack.beginMacro("Click-Drag Rubric")

                command = CommandBox(self.scene, final_rect)
                self.scene.undoStack.push(command)
                self.permanent_box_item = command.obj

                self.path_item = QGraphicsPathItem()
                self.path_item.setPen(self.scene.ink)
                self.scene.addItem(self.path_item)
                self.mouse_move(event)

    def cleanup(self):
        """Clean up and remaining temporary objects, possibly ending the macro and undoing."""
        # if state 2 (elastic line) was in-progress, we need to undo the box draw
        if self.state == 2:
            self.scene.undoStack.endMacro()
            self.scene.undo()

        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)
        if self.path_item and self.path_item.scene():
            self.scene.removeItem(self.path_item)


class TickToolDrawer(MultiStageDrawer):
    """Handles the click-or-drag logic for the Tick tool.

    This class follows the same complex logic as the RubricToolDrawer,
    but stamps a Tick/Cross/QMark instead of a rubric.
    """

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the TickToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.state = 0
        self.temp_box_item: QGraphicsRectItem | None = None
        self.path_item = None
        self.permanent_box_item = None
        self.minimum_side_length = 24

        self.mouse_press(event)

    @property
    def _default_tool(self):
        return CommandTick

    @property
    def _alt_tool(self):
        return CommandCross

    @property
    def _ctrl_tool(self):
        return CommandQMark

    def _stamp(self, event: QGraphicsSceneMouseEvent) -> None:
        """Places a Tick, Cross, or Question Mark based on the mouse/key event."""
        pt = event.scenePos()
        command: CommandCross | CommandQMark | CommandTick
        if (event.button() == Qt.MouseButton.RightButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ShiftModifier
        ):
            command = self._alt_tool(self.scene, pt)
        elif (event.button() == Qt.MouseButton.MiddleButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ControlModifier
        ):
            command = self._ctrl_tool(self.scene, pt)
        else:
            command = self._default_tool(self.scene, pt)
        self.scene.undoStack.push(command)

    def mouse_press(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse press events for the tick tool."""
        if self.state == 0:
            self.state = 1
            self.origin_pos = event.scenePos()
            self.temp_box_item = QGraphicsRectItem(
                QRectF(self.origin_pos, self.origin_pos)
            )
            assert self.temp_box_item is not None
            self.temp_box_item.setPen(self.scene.ink)
            self.temp_box_item.setBrush(self.scene.lightBrush)
            self.scene.addItem(self.temp_box_item)
        elif self.state == 2:
            assert self.path_item is not None
            final_path = self.path_item.path()
            self.scene.removeItem(self.path_item)
            self.path_item = None

            if not final_path.isEmpty():
                line_command = CommandPen(self.scene, final_path)
                self.scene.undoStack.push(line_command)

            self._stamp(event)
            self.scene.undoStack.endMacro()
            self.state = 3
            self.finish()

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the tick tool."""
        if self.state == 1:
            if self.temp_box_item:
                self.current_pos = event.scenePos()
                self.temp_box_item.setRect(
                    QRectF(self.origin_pos, self.current_pos).normalized()
                )
        elif self.state == 2:
            if self.path_item and self.permanent_box_item:
                self.current_pos = event.scenePos()

                # Create a small, invisible rectangle around the cursor to use the "smart" line logic.
                tick_rad = self.scene._scale * DefaultTickRadius
                padding = tick_rad // 2
                side = round(2 * padding + 7 * tick_rad / 4)
                g_rect_top_left = QPointF(
                    self.current_pos.x() - 3 * tick_rad // 4 - padding,
                    self.current_pos.y() - tick_rad - padding,
                )
                ghost_rect = QRectF(
                    g_rect_top_left.x(), g_rect_top_left.y(), side, side
                )
                box_rect = self.permanent_box_item.mapRectToScene(
                    self.permanent_box_item.boundingRect()
                )
                self.path_item.setPath(self.scene.whichLineToDraw(ghost_rect, box_rect))

    def mouse_release(self, event):
        """Handles mouse release events for the tick tool."""
        if self.state == 1:
            final_rect = self.temp_box_item.rect()
            self.scene.removeItem(self.temp_box_item)
            self.temp_box_item = None

            if (
                final_rect.width() < self.minimum_side_length
                or final_rect.height() < self.minimum_side_length
            ):
                self._stamp(event)
                self.finish()
            else:
                self.state = 2
                self.scene.undoStack.beginMacro("Click-Drag Stamp")

                command = CommandBox(self.scene, final_rect)
                self.scene.undoStack.push(command)
                self.permanent_box_item = command.obj

                self.path_item = QGraphicsPathItem()
                self.path_item.setPen(self.scene.ink)
                self.scene.addItem(self.path_item)
                self.mouse_move(event)

    def cleanup(self):
        """Cleanup the tick/cross/question mark drawing."""
        if self.state == 2:
            self.scene.undoStack.endMacro()
            self.scene.undo()
        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)
        if self.path_item and self.path_item.scene():
            self.scene.removeItem(self.path_item)


class CrossToolDrawer(TickToolDrawer):
    """Handles the click-or-drag logic for the Cross tool."""

    @property
    def _default_tool(self):
        return CommandCross

    @property
    def _alt_tool(self):
        return CommandTick


class TextToolDrawer(MultiStageDrawer):
    """Handles the logic for the Text tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the TextToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.state = 0
        self.temp_box_item: QGraphicsRectItem | None = None
        self.path_item = None
        self.permanent_box_item = None
        self.minimum_side_length = 24

        under = self.scene.itemAt(event.scenePos() + QPointF(2, 0), QTransform())
        if self._handle_existing_text(under):
            self.finish()
            return

        self.mouse_press(event)

    def _handle_existing_text(self, item):
        """If the item under the cursor is an editable TextItem, give it focus."""
        if item is not None and isinstance(item, TextItem):
            if item.group() is None:
                item.enable_interactive()
                item.setFocus()
                return True
        return False

    def _stamp(self, event: QGraphicsSceneMouseEvent) -> None:
        """Places a new, empty text item and gives it focus for typing."""
        pt = event.scenePos()
        command = CommandText(self.scene, pt, "")
        text_item = command.obj

        text_item.setPos(pt - QPointF(0, text_item.boundingRect().height() / 2))

        self.scene.undoStack.push(command)
        text_item.enable_interactive()
        text_item.setFocus()

    def mouse_press(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse press events for the text tool."""
        if self.state == 0:
            self.state = 1
            self.origin_pos = event.scenePos()
            self.temp_box_item = QGraphicsRectItem(
                QRectF(self.origin_pos, self.origin_pos)
            )
            assert self.temp_box_item is not None
            self.temp_box_item.setPen(self.scene.ink)
            self.temp_box_item.setBrush(self.scene.lightBrush)
            self.scene.addItem(self.temp_box_item)
        elif self.state == 2:
            assert self.path_item is not None
            final_path = self.path_item.path()
            self.scene.removeItem(self.path_item)
            self.path_item = None

            if not final_path.isEmpty():
                line_command = CommandPen(self.scene, final_path)
                self.scene.undoStack.push(line_command)

            self._stamp(event)
            self.scene.undoStack.endMacro()
            self.finish()

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the text tool."""
        if self.state == 1:
            if self.temp_box_item:
                self.current_pos = event.scenePos()
                self.temp_box_item.setRect(
                    QRectF(self.origin_pos, self.current_pos).normalized()
                )
        elif self.state == 2:
            if self.path_item and self.permanent_box_item:
                self.current_pos = event.scenePos()
                tick_rad = self.scene._scale * DefaultTickRadius
                padding = tick_rad // 2
                side = round(2 * padding + 7 * tick_rad / 4)
                g_rect_top_left = QPointF(
                    self.current_pos.x() - 3 * tick_rad // 4 - padding,
                    self.current_pos.y() - tick_rad - padding,
                )
                ghost_rect = QRectF(
                    g_rect_top_left.x(), g_rect_top_left.y(), side, side
                )
                box_rect = self.permanent_box_item.mapRectToScene(
                    self.permanent_box_item.boundingRect()
                )
                self.path_item.setPath(self.scene.whichLineToDraw(ghost_rect, box_rect))

    def mouse_release(self, event):
        """Handles mouse release events for the text tool."""
        if self.state == 1:
            final_rect = self.temp_box_item.rect()
            self.scene.removeItem(self.temp_box_item)
            self.temp_box_item = None

            if (
                final_rect.width() < self.minimum_side_length
                or final_rect.height() < self.minimum_side_length
            ):
                self._stamp(event)
                self.finish()
            else:
                self.state = 2
                self.scene.undoStack.beginMacro("Click-Drag Text")

                command = CommandBox(self.scene, final_rect)
                self.scene.undoStack.push(command)
                self.permanent_box_item = command.obj

                self.path_item = QGraphicsPathItem()
                self.path_item.setPen(self.scene.ink)
                self.scene.addItem(self.path_item)
                self.mouse_move(event)

    def cancel(self):
        """Cancels the current drawing operation."""
        if self.state == 2:
            self.scene.undoStack.endMacro()
            self.scene.undo()
        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)
        if self.path_item and self.path_item.scene():
            self.scene.removeItem(self.path_item)
        super().cancel()


class DeleteToolDrawer(MultiStageDrawer):
    """Handles the click-or-drag logic for the Delete tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the DeleteToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.current_pos = self.origin_pos
        self.is_dragging = False

        self.temp_box_item = QGraphicsRectItem(
            QRectF(self.origin_pos, self.current_pos).normalized()
        )
        self.temp_box_item.setPen(QPen(QColor("red"), self.scene.style["pen_width"]))
        self.temp_box_item.setBrush(self.scene.deleteBrush)
        self.scene.addItem(self.temp_box_item)

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the delete tool."""
        self.is_dragging = True
        self.current_pos = event.scenePos()
        if self.temp_box_item:
            self.temp_box_item.setRect(
                QRectF(self.origin_pos, self.current_pos).normalized()
            )

    def mouse_release(self, event):
        """Handles mouse release events for the delete tool."""
        del_list = []
        if not self.is_dragging:  # Simple click
            nearby_rect = QRectF(
                self.origin_pos.x() - 5, self.origin_pos.y() - 5, 10, 10
            )
            items_to_check = self.scene.items(
                nearby_rect, mode=Qt.ItemSelectionMode.IntersectsItemShape
            )
            if items_to_check:
                for item in items_to_check:
                    target_item = item.group() if item.group() is not None else item
                    if self.scene.deleteIfLegal(target_item, dryrun=True):
                        del_list.append(target_item)
                        break
        else:  # Drag operation
            items_to_check = self.scene.items(
                self.temp_box_item.rect(), mode=Qt.ItemSelectionMode.ContainsItemShape
            )
            for item in items_to_check:
                if self.scene.deleteIfLegal(item, dryrun=True):
                    del_list.append(item)

        if del_list:
            if len(del_list) > 1:
                self.scene.undoStack.beginMacro(f"Deleting {len(del_list)} items")

            for item in del_list:
                command = CommandDelete(self.scene, item)
                self.scene.undoStack.push(command)

            if len(del_list) > 1:
                self.scene.undoStack.endMacro()

        self.finish()

    def cleanup(self):
        """Cancels the current drawing operation."""
        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)


class ZoomToolDrawer(MultiStageDrawer):
    """Handles the click-or-drag logic for the Zoom tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the ZoomToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.temp_box_item = None
        self.is_dragging = False

        if (event.button() == Qt.MouseButton.RightButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ShiftModifier
        ):
            self.scene.views()[0].scale(0.8, 0.8)
            self.scene.views()[0].centerOn(event.scenePos())
            self._finish_and_update_selector()
        else:
            self.temp_box_item = QGraphicsRectItem(
                QRectF(self.origin_pos, self.origin_pos)
            )
            self.temp_box_item.setPen(QPen(QColor("blue")))
            self.temp_box_item.setBrush(self.scene.zoomBrush)
            self.scene.addItem(self.temp_box_item)

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the zoom tool."""
        if self.temp_box_item:
            self.is_dragging = True
            self.current_pos = event.scenePos()
            self.temp_box_item.setRect(
                QRectF(self.origin_pos, self.current_pos).normalized()
            )

    def mouse_release(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse release events for the zoom tool."""
        if not self.temp_box_item:
            return

        if not self.is_dragging or (
            self.temp_box_item.rect().height() < 8
            and self.temp_box_item.rect().width() < 8
        ):
            self.scene.views()[0].scale(1.25, 1.25)
            self.scene.views()[0].centerOn(event.scenePos())
        else:
            self.scene.views()[0].fitInView(
                self.temp_box_item, Qt.AspectRatioMode.KeepAspectRatio
            )

        self._finish_and_update_selector()

    def _finish_and_update_selector(self):
        """Finishes the zoom operation and updates the zoom selector."""
        page_view = self.scene.views()[0]
        assert isinstance(page_view, PageView)
        page_view.setZoomSelector(True)
        self.finish()

    def cleanup(self):
        """Clean up temp objects from the zoom operation."""
        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)


class CropToolDrawer(MultiStageDrawer):
    """Handles the click-or-drag logic for the Crop tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the CropToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.current_pos = self.origin_pos

        self.temp_box_item = QGraphicsRectItem(
            QRectF(self.origin_pos, self.current_pos).normalized()
        )
        self.temp_box_item.setPen(QPen(QColor("red"), self.scene.style["pen_width"]))
        self.temp_box_item.setBrush(self.scene.deleteBrush)
        self.scene.addItem(self.temp_box_item)

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the crop tool."""
        self.current_pos = event.scenePos()
        if self.temp_box_item:
            self.temp_box_item.setRect(
                QRectF(self.origin_pos, self.current_pos).normalized()
            )

    def mouse_release(self, event):
        """Handles mouse release events for the crop tool."""
        minbox = max(256, 0.2 * self.scene.underImage.min_dimension)

        if (
            self.temp_box_item.rect().height() >= minbox
            and self.temp_box_item.rect().width() >= minbox
        ):
            self.scene.trigger_crop(self.temp_box_item.rect())

        self.finish()

    def cleanup(self):
        """Cleanup temporary objects from the crop drawing operation."""
        if self.temp_box_item and self.temp_box_item.scene():
            self.scene.removeItem(self.temp_box_item)


class PenToolDrawer(MultiStageDrawer):
    """Handles the free-form drawing logic for the Pen tool."""

    def __init__(self, scene, event: QGraphicsSceneMouseEvent) -> None:
        """Initializes the PenToolDrawer.

        Args:
            scene (PageScene): The scene to draw on.
            event: The mouse event that triggered the drawer.
        """
        super().__init__(scene, event)
        self.current_pos = self.origin_pos
        self.pen_flag = self._get_pen_flag(event)

        self.path = QPainterPath()
        self.path.moveTo(self.origin_pos)
        self.path.lineTo(self.current_pos)
        self.path_item = QGraphicsPathItem(self.path)

        if self.pen_flag == 2:  # Highlighter
            self.path_item.setPen(self.scene.highlight)
        else:  # Normal Pen or Arrow Pen
            self.path_item.setPen(self.scene.ink)

        self.scene.addItem(self.path_item)

    def _get_pen_flag(self, event):
        """Determines the pen type based on the mouse event."""
        if (event.button() == Qt.MouseButton.RightButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ShiftModifier
        ):
            return 2  # Highlighter
        elif (event.button() == Qt.MouseButton.MiddleButton) or (
            QGuiApplication.queryKeyboardModifiers()
            == Qt.KeyboardModifier.ControlModifier
        ):
            return 4  # Pen with arrows
        else:
            return 1  # Normal Pen

    def mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse move events for the pen tool."""
        self.current_pos = event.scenePos()
        self.path.lineTo(self.current_pos)
        self.path_item.setPath(self.path)

    def mouse_release(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handles mouse release events for the pen tool."""
        command = None
        if self.path.length() <= 1:
            blob_size = 4 if self.pen_flag == 2 else 2
            self.path.lineTo(event.scenePos() + QPointF(blob_size, 0))
            self.path.lineTo(event.scenePos() + QPointF(blob_size, blob_size))
            self.path.lineTo(event.scenePos() + QPointF(0, blob_size))
            self.path.lineTo(event.scenePos())

        if self.pen_flag == 1:
            command = CommandPen(self.scene, self.path)
        elif self.pen_flag == 2:
            command = CommandHighlight(self.scene, self.path)
        elif self.pen_flag == 4:
            command = CommandPenArrow(self.scene, self.path)

        if command:
            self.scene.undoStack.push(command)

        self.finish()

    def cleanup(self):
        """Cleanup temporary objects from the pen drawing operation."""
        if self.path_item and self.path_item.scene():
            self.scene.removeItem(self.path_item)
