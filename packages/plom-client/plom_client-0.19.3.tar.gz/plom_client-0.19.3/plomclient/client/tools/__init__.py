# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2019 Andrew Rechnitzer
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2022, 2025 Colin B. Macdonald
# Copyright (C) 2024 Aden Chan

import logging

log = logging.getLogger("tools")

from PyQt6.QtGui import QBrush, QColor, QPen

OutOfBoundsPenColour = QColor(255, 165, 0)
OutOfBoundsFillColour = QColor(255, 165, 0, 128)
OutOfBoundsPen = QPen(OutOfBoundsPenColour, 8)
OutOfBoundsFill = QBrush(OutOfBoundsFillColour)

DefaultTickRadius = 20
DefaultPenWidth = 2
# I don't know what units this is, especially after Issue #1071.
# see also, ScenePixelHeight
AnnFontSizePts = 34.0

from .move import CommandMoveItem, UndoStackMoveMixin
from .tool import CommandTool
from .delete import CommandDelete
from .crop import CommandCrop
from .rotate_page import CommandRotatePage
from .shift_page import CommandShiftPage
from .remove_page import CommandRemovePage

from .box import CommandBox
from .rubric import CommandRubric, RubricItem, GhostComment
from .cross import CommandCross, CrossItem
from .delta import GhostDelta, DeltaItem
from .ellipse import CommandEllipse, EllipseItem
from .highlight import CommandHighlight, HighlightItem
from .image import CommandImage, ImageItem
from .line import CommandLine, LineItem
from .arrow import CommandArrow, CommandArrowDouble, ArrowItem, ArrowDoubleItem
from .pen import CommandPen, PenItem
from .penArrow import CommandPenArrow, PenArrowItem
from .questionMark import CommandQMark, QMarkItem
from .text import CommandText, TextItem, GhostText
from .tick import CommandTick, TickItem

from .tilted_box import CommandTiltedBox, TiltedBoxItem
