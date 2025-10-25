# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2021 Andrew Rechnitzer
# Copyright (C) 2018 Elvis Cai
# Copyright (C) 2019-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2022 Edith Coates
# Copyright (C) 2022 Lior Silberman
# Copyright (C) 2024 Bryan Tanady
# Copyright (C) 2025 Brody Sanderson

"""The Plom Marker client."""

from __future__ import annotations

from collections import defaultdict
import html
import json
import logging
from math import ceil
from pathlib import Path
import platform
import sys
import tempfile
from textwrap import shorten
import time
import threading
from typing import Any

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from packaging.version import Version
from PyQt6 import QtGui, uic
from PyQt6.QtCore import (
    Qt,
    QItemSelection,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtWidgets import (
    QDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QToolButton,
    QWidget,
    #
    QFrame,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QVBoxLayout,
)
from PyQt6.QtGui import QKeySequence, QShortcut

from . import __version__
from plomclient.misc_utils import unpack_task_code
from plomclient.plom_exceptions import (
    PlomAuthenticationException,
    PlomBadTagError,
    PlomBenignException,
    PlomConnectionError,
    PlomForceLogoutException,
    PlomRangeException,
    PlomVersionMismatchException,
    PlomSeriousException,
    PlomTakenException,
    PlomTaskChangedError,
    PlomTaskDeletedError,
    PlomConflict,
    PlomNoPaper,
    PlomNoPermission,
    PlomNoServerSupportException,
    PlomNoSolutionException,
)
from plomclient.messenger import Messenger
from plomclient.feedback_rules import feedback_rules as static_feedback_rules_data
from .question_labels import (
    check_for_shared_pages,
    get_question_label,
    verbose_question_label,
)
from .about_dialog import show_about_dialog
from .annotator import Annotator
from .image_view_widget import ImageViewWidget
from .key_wrangler import get_key_bindings
from .viewers import QuestionViewDialog, SelectPaperQuestion, SolutionViewer
from .tagging import AddRemoveTagDialog
from .useful_classes import ErrorMsg, WarnMsg, InfoMsg, SimpleQuestion
from .useful_classes import _json_path_to_str
from .tagging_range_dialog import TaggingAndRangeOptions
from .quota_dialogs import ExplainQuotaDialog, ReachedQuotaLimitDialog
from .task_model import MarkerExamModel, ProxyModel
from .uploader import BackgroundUploader, synchronous_upload
from . import ui_files


if platform.system() == "Darwin":
    # apparently needed for shortcuts under macOS
    from PyQt6.QtGui import qt_set_sequence_auto_mnemonic

    qt_set_sequence_auto_mnemonic(True)


log = logging.getLogger("marker")


def paper_question_index_to_task_id_str(papernum: int, question_idx: int) -> str:
    """Helper function to convert between paper/question and task string."""
    return f"{papernum:04}g{question_idx}"


class MarkerClient(QWidget):
    """Setup for marking client and annotator.

    Notes:
        TODO: should be a QMainWindow but at any rate not a Dialog
        TODO: should this be parented by the QApplication?

    Signals:
        my_shutdown_signal: called when TODO
        tags_changed_signal: emitted when tags might have changed, such
            as after an explicit server refresh or some other event. The
            arguments are the task code (e.g., "0123g2") and a list,
            possibly empty, of the current tags.
    """

    my_shutdown_signal = pyqtSignal(int, list)
    tags_changed_signal = pyqtSignal(str, list)

    def __init__(self, Qapp, *, tmpdir=None):
        """Initialize a new MarkerClient.

        Args:
            Qapp (QApplication): Main client application

        Keyword Args:
            tmpdir (pathlib.Path/None): a temporary directory for
                storing image files and other data.  In principle can
                be shared with Identifier although this may not be
                implemented.  If `None`, we will make our own.
                TODO: we don't clean up this directory at all, which
                is reasonable enough if the caller *made* it, but a
                bit strange in the `None` case...
        """
        super().__init__()
        self.Qapp = Qapp

        uic.loadUi(resources.files(ui_files) / "marker.ui", self)
        # TODO: temporary workaround
        self.ui = self

        self._annotator = None

        self.solutionView = None

        # Save the local temp directory for image files and the class list.
        if not tmpdir:
            # TODO: in this case, *we* should be responsible for cleaning up
            tmpdir = tempfile.mkdtemp(prefix="plom_")
        self.workingDirectory = Path(tmpdir)
        log.debug("Working directory set to %s", self.workingDirectory)

        self.tags_changed_signal.connect(self._update_tags_in_examModel)

        self.maxMark = -1  # temp value
        self.downloader = self.Qapp.downloader
        if self.downloader:
            # for unit tests, we might mockup Qapp.downloader as None
            # (Marker will not be functional without a downloader)
            self.downloader.download_finished.connect(self.background_download_finished)
            self.downloader.download_failed.connect(self.background_download_failed)
            self.downloader.download_queue_changed.connect(self.update_technical_stats)

        self.examModel = (
            MarkerExamModel()
        )  # Exam model for the table of groupimages - connect to table
        self.prxM = ProxyModel()  # set proxy for filtering and sorting
        # A view window for the papers so user can zoom in as needed.
        self.testImg = ImageViewWidget(self, has_rotate_controls=False)
        # A view window for the papers so user can zoom in as needed.
        self.ui.paperBoxLayout.addWidget(self.testImg, 10)

        # settings variable for annotator settings (initially None)
        self.annotatorSettings = defaultdict(lambda: None)
        self.commentCache = {}  # cache for Latex Comments
        self.backgroundUploader = None

        self.allowBackgroundOps = True

        # instance vars that get initialized later
        self.question_idx = None
        self.version = None
        self.exam_spec = None
        self.max_papernum = None
        self._user_reached_quota_limit = False

        self.msgr = None
        # history contains all the tgv in order of being marked except the current one.
        self.marking_history = []

        self._hack_prevent_shutdown = False

    def setup(
        self,
        messenger: Messenger,
        question_idx: int,
        version: int,
        lastTime: dict[str, Any],
    ) -> None:
        """Performs setup procedure for MarkerClient.

        TODO: move all this into init?

        TODO: verify all lastTime Params, there are almost certainly some missing

        Args:
            messenger: handle communication with server.
            question_idx: question index number, one based.
            version: question version number
            lastTime: dict of settings.
                Containing::

                   {
                     "FOREGROUND"
                     "KeyBinding"
                   }

                and potentially others

        Returns:
            None
        """
        self.msgr = messenger
        self.question_idx = question_idx
        self.version = version

        # Get the number of Tests, Pages, Questions and Versions
        # Note: if this fails UI is not yet in a usable state
        self.exam_spec = self.msgr.get_spec()

        self.UIInitialization()
        self.applyLastTimeOptions(lastTime)
        self._connectGuiButtons()

        # self.maxMark = self.exam_spec["question"][str(question_idx)]["mark"]
        try:
            self.maxMark = self.msgr.getMaxMark(self.question_idx)
        except PlomRangeException as err:
            ErrorMsg(self, str(err)).exec()
            return

        if not self.msgr.is_legacy_server():
            assert self.msgr.username
            self.annotatorSettings["nextTaskPreferTagged"] = "@" + self.msgr.username
        self.update_get_next_button()

        # Get list of papers already marked and add to table.
        if self.msgr.is_legacy_server():
            self.loadMarkedList()
        self.refresh_server_data()

        # Connect the view **after** list updated.
        # Connect the table-model's selection change to Marker functions
        self.ui.tableView.selectionModel().selectionChanged.connect(
            self.updatePreviewImage
        )
        self.ui.tableView.selectionModel().selectionChanged.connect(
            self.update_annotator
        )
        self.ui.tableView.selectionModel().selectionChanged.connect(
            self.ensureAllDownloaded
        )
        self.ui.tableView.selectionModel().selectionChanged.connect(
            self.update_window_title
        )

        # Get a question to mark from the server
        self._requestNext(enter_annotate_mode_if_possible=True)
        # reset the view so whole exam shown.
        self.testImg.resetView()
        # resize the table too.
        QTimer.singleShot(100, self.ui.tableView.resizeRowsToContents)
        log.debug("Marker main thread: " + str(threading.get_ident()))

        if self.allowBackgroundOps:
            self.backgroundUploader = BackgroundUploader(self.msgr)
            self.backgroundUploader.uploadSuccess.connect(self.backgroundUploadFinished)
            self.backgroundUploader.uploadFail.connect(self.backgroundUploadFailed)
            self.backgroundUploader.queue_status_changed.connect(
                self.update_technical_stats_upload
            )
            self.backgroundUploader.start()
        self.cacheLatexComments()  # Now cache latex for comments:
        s = check_for_shared_pages(self.exam_spec, self.question_idx)
        if s:
            InfoMsg(self, s).exec()

    def applyLastTimeOptions(self, lastTime: dict[str, Any]) -> None:
        """Applies all settings from previous client.

        Args:
            lastTime (dict): information about settings, often from a
            config file such as from the last time the client was run.

        Returns:
            None
        """
        # TODO: some error handling here for users who hack their config?
        self.annotatorSettings["keybinding_name"] = lastTime.get("KeyBinding")
        self.annotatorSettings["keybinding_custom_overlay"] = lastTime.get("CustomKeys")

        if lastTime.get("FOREGROUND", False):
            self.allowBackgroundOps = False

    def is_experimental(self):
        return self.annotatorSettings["experimental"]

    def set_experimental(self, x):
        # TODO: maybe signals/slots should be used to watch for changes
        if x:
            log.info("Experimental/advanced mode enabled")
            self.annotatorSettings["experimental"] = True
        else:
            log.info("Experimental/advanced mode disabled")
            self.annotatorSettings["experimental"] = False

    # TODO: does it matter if we connect to selectionChanged that sends new/old?
    @pyqtSlot()
    def update_window_title(self) -> None:
        try:
            question_label = get_question_label(self.exam_spec, self.question_idx)
        except (ValueError, KeyError):
            question_label = ""
        if self.exam_spec:
            assessment_name = self.exam_spec["name"]
        else:
            assessment_name = ""

        task = self.get_current_task_id_or_none()
        if not ((task or question_label) and assessment_name):
            window_title = "Plom"
        else:
            window_title = "{what} of {assessment_name} \N{EM DASH} Plom".format(
                what=(task if task else question_label),
                assessment_name=assessment_name,
            )
        # note this [*] is used by Qt to know here to put an * to indicate unsaved results
        self.setWindowTitle("[*]" + window_title)

    def UIInitialization(self) -> None:
        """Startup procedure for the user interface.

        Returns:
            None: Modifies self.ui
        """
        try:
            question_label = get_question_label(self.exam_spec, self.question_idx)
        except (ValueError, KeyError):
            question_label = "???"
        self.ui.labelTasks.setText(
            "{question_label} (ver. {question_version})\n{assessment_name}".format(
                question_label=question_label,
                question_version=self.version,
                assessment_name=self.exam_spec["name"],
            )
        )
        self.ui.labelTasks.setWordWrap(True)
        self.update_window_title()

        self.prxM.setSourceModel(self.examModel)
        self.ui.tableView.setModel(self.prxM)

        # when to open annotator: for now, needs double-click first time
        # TODO: could always open annotator but may want background
        # downloader placeholder support first (?)
        # Note: clicked events occur AFTER the selection has already changed
        # self.ui.tableView.clicked.connect(self.annotate_task)
        # TODO: currently not firing?  Proabbly b/c of mouseEvent hackery
        self.ui.tableView.doubleClicked.connect(self.annotate_task)
        self.ui.tableView.annotateSignal.connect(self.annotate_task)
        self.ui.tableView.tagSignal.connect(self.manage_tags)
        self.ui.tableView.claimSignal.connect(self.claim_task)
        self.ui.tableView.deferSignal.connect(self.defer_task)
        self.ui.tableView.reassignSignal.connect(self.reassign_task)
        self.ui.tableView.reassignToMeSignal.connect(self.reassign_task_to_me)
        self.ui.tableView.resetSignal.connect(self.reset_task)
        self.ui.tableView.want_to_change_task.connect(self.switch_task)
        self.ui.tableView.want_to_annotate_task.connect(self.annotate_task)
        self.ui.tableView.refresh_task_list.connect(self.refresh_server_data)

        # A view window for the papers so user can zoom in as needed.
        # Paste into appropriate location in gui.
        self.ui.paperBoxLayout.addWidget(self.testImg, 10)

        # mess around with the splitter
        self.ui.splitter.setCollapsible(0, False)
        self.ui.splitter.setCollapsible(1, True)
        self.ui.splitter.setHandleWidth(30)
        # some labels to stick on the grab bar
        label0 = QLabel("")
        label1 = QLabel("")
        # "dark" too light and "shadow" too dark ;-(
        # label0.setStyleSheet("QLabel { color: palette(dark); }")
        # label1.setStyleSheet("QLabel { color: palette(shadow); }")

        @pyqtSlot()
        def _check_split_width():
            # if the right-widget (ie marker task list) is narrow, then
            # set the labels to indicate 'expansion'
            if self.ui.splitter.sizes()[1] < 8:
                # TRANSLATOR: decorative, no meaning
                label0.setText("<\n<\n<")
                label1.setText("<\n<\n<")
            else:
                label0.setText("")
                label1.setText("")

        self.ui.splitter.splitterMoved.connect(_check_split_width)
        handy = self.ui.splitter.handle(1)
        vb = QVBoxLayout()
        for n in range(3):
            hb = QHBoxLayout()
            hb.setSpacing(3)  # little gap between each line
            for i in range(3):
                f = QFrame()
                f.setFrameShape(QFrame.Shape.VLine)
                f.setFrameShadow(QFrame.Shadow.Raised)
                hb.addWidget(f)
            vb.addItem(
                QSpacerItem(
                    1,
                    64,
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Minimum,
                )
            )
            vb.addLayout(hb)
            if n == 0:
                vb.addItem(
                    QSpacerItem(
                        1,
                        64,
                        QSizePolicy.Policy.Preferred,
                        QSizePolicy.Policy.Minimum,
                    )
                )
                vb.addWidget(label0)
            if n == 1:
                vb.addItem(
                    QSpacerItem(
                        1,
                        64,
                        QSizePolicy.Policy.Preferred,
                        QSizePolicy.Policy.Minimum,
                    )
                )
                vb.addWidget(label1)
        vb.addItem(
            QSpacerItem(
                1,
                64,
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Minimum,
            )
        )
        handy.setLayout(vb)

        # Note: for some reason the RHS panel isn't as small as it could be
        # This call should make it smaller
        # TODO: yuck yuck yuck, dislike this Qtimer things
        QTimer.singleShot(100, lambda: self.ui.splitter.setSizes([4096, 100]))

        if Version(__version__).is_devrelease:
            # self.ui.technicalButton.setChecked(True)
            # TODO: trigger the action instead?
            self.ui.failmodeCB.setEnabled(True)
        else:
            # self.ui.technicalButton.setChecked(False)
            self.ui.failmodeCB.setEnabled(False)
        self.show_hide_technical()
        # self.force_update_technical_stats()
        self.update_technical_stats_upload(0, 0, 0, 0)

    def _connectGuiButtons(self) -> None:
        """Connect gui buttons to appropriate functions.

        Notes:
            TODO: remove the total-radiobutton

        Returns:
            None but modifies self.ui
        """
        self.ui.getMoreButton.clicked.connect(self.request_one_more)
        # TODO: we're considering hiding this, so its only in the menu
        # (a good idea when space is tight; less clear when panel is large)
        # self.ui.getMoreButton.setVisible(False)
        self.ui.annButton.clicked.connect(self.annotate_task)
        m = QMenu(self)
        m.addAction("&Defer selected task", self.defer_task)
        m.addSeparator()
        m.addAction("Claim selected task for me", self.claim_task)
        m.addAction("Claim more tasks for me", self.request_one_more)
        m.addAction("Claim by paper number...", self.claim_task_interactive)
        m.addAction("Preferences for claiming tasks...", self.change_tag_range_options)
        m.addSeparator()
        m.addAction("Reset selected task", self.reset_task)
        m.addAction("Reassign selected task to me", self.reassign_task_to_me)
        m.addAction("Reassign selected task...", self.reassign_task)
        # self.ui.task_overflow_button.setText("\N{VERTICAL ELLIPSIS}")
        self.ui.task_overflow_button.setMenu(m)
        self.ui.task_overflow_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.ui.deferButton.clicked.connect(self.defer_task)
        # self.ui.deferButton.setVisible(False)
        self.ui.tasksComboBox.activated.connect(self.change_task_view)
        self.ui.refreshTaskListButton.clicked.connect(self.refresh_server_data)
        self.ui.refreshTaskListButton.setText("\N{CLOCKWISE OPEN CIRCLE ARROW}")
        self.ui.refreshTaskListButton.setToolTip("Refresh task list")
        self.ui.tagButton.clicked.connect(self.manage_tags)
        self.ui.filterLE.returnPressed.connect(self.setFilter)
        self.ui.filterLE.textEdited.connect(self.setFilter)
        self.ui.filterInvCB.stateChanged.connect(self.setFilter)
        self.ui.viewButton.clicked.connect(self.choose_and_view_other)
        self.ui.viewButton.setVisible(False)
        self.ui.failmodeCB.stateChanged.connect(self.toggle_fail_mode)
        self.ui.explainQuotaButton.clicked.connect(ExplainQuotaDialog(self).exec)

        self.ui.hamMenuButton.setMenu(self.build_hamburger())
        self.ui.hamMenuButton.setText("\N{TRIGRAM FOR HEAVEN}")
        # self.ui.hamMenuButton.setToolTip("Menu (F10)")
        self.ui.hamMenuButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        m = QMenu()
        m.addAction("Where did the marking tools go?", self.pop_up_explain_view_edit)
        self.ui.viewModeMenuButton.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.ui.viewModeMenuButton.setText("\N{TRIGRAM FOR HEAVEN}")
        self.ui.viewModeMenuButton.setMenu(m)

    def build_hamburger(self):
        # TODO: no customizable keys are needed outside of Annotator
        # TODO: but later we should store the keybinding here no in Ann
        keydata = get_key_bindings("default")

        self._store_QShortcuts = []

        m = QMenu()

        # TODO: use \N{CLOCKWISE OPEN CIRCLE ARROW} as the icon
        m.addAction("Refresh task list", self.refresh_server_data)
        m.addAction("View another paper...", self.choose_and_view_other)

        (key,) = keydata["show-solutions"]["keys"]
        cmd = self.view_solutions
        sc = QShortcut(QKeySequence(key), self)
        sc.activated.connect(cmd)
        self._store_QShortcuts.append(sc)
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"View solutions\t{key}", cmd)

        (key,) = keydata["tag-paper"]["keys"]
        cmd = self.manage_tags
        sc = QShortcut(QKeySequence(key), self)
        sc.activated.connect(cmd)
        self._store_QShortcuts.append(sc)
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Tag paper...\t{key}", cmd)

        m.addSeparator()

        x = m.addAction("Show technical debugging info")
        x.setCheckable(True)
        x.triggered.connect(self.show_hide_technical)
        self._show_hide_technical_action = x
        m.addSeparator()

        m.addAction("Help", self.show_help)
        m.addAction("About Plom", lambda: show_about_dialog(self))

        m.addSeparator()

        key = "ctrl+w"
        command = self._close_but_dont_quit
        sc = QShortcut(QKeySequence(key), self)
        sc.activated.connect(command)
        self._store_QShortcuts.append(sc)
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Change question or server\t{key}", command)

        key = "ctrl+q"
        command = self.close
        sc = QShortcut(QKeySequence(key), self)
        sc.activated.connect(command)
        self._store_QShortcuts.append(sc)
        key = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        m.addAction(f"Quit\t{key}", command)

        return m

    def _close_but_dont_quit(self):
        # unpleasant hackery but gets job done
        self._hack_prevent_shutdown = True
        self.close()

    def show_help(self):
        # TODO: it should know if its in view or edit mode and say so.
        # TODO: may need adjusted as the mechanisms for moving between the
        # two modes mature.
        s = """
            <h2>Welcome to Plom \N{EM DASH} brief help</h2>
            <p>
              This software is Plom Client: it talks to a server to coordinate
              marking.
            </p>
            <p>
              Plom Client has two modes.  You'll spend most of your time in the
              default &ldquo;edit mode&rdquo; where you mark papers using the
              annotation tools on the left.
            </p>
            <p>
              In &ldquo;view mode&rdquo; you can
              look at tasks, including annotated tasks, but you cannot edit
              them. To return to &ldquo;edit mode&rdquo;, click on the
              &ldquo;Mark&rdquo; button, or double-click on a task from the
              list on the right.
           </p>
           <p>
              General information about Plom can be found at
              <a href="https://plomgrading.org">plomgrading.org</a>
              and documentation can be found at
              <a href="https://plom.readthedocs.io">plom.readthedocs.io</a>.
           </p>
        """
        InfoMsg(self, s).exec()

    def pop_up_explain_view_edit(self):
        s = """
            <p>
              You are currently in &ldquo;view mode&rdquo; where you can
              look at tasks, including annotated tasks, but you cannot edit
              them.
            </p>
            <p>
              To return to &ldquo;edit mode&rdquo;, click on the
              &ldquo;Mark&rdquo; button, or double-click on a task.
           </p>
        """
        InfoMsg(self, s).exec()

    def _exit_annotate_mode(self):
        # Careful with this: its currently more "in reaction to annotr closing"
        # rather than "tell/force the annotator to close".
        self._annotator = None
        self.testImg.setVisible(True)
        self.ui.viewModeFrame.setVisible(True)
        self.ui.tableView.clicked.disconnect()

    def change_tag_range_options(self):
        all_tags = [tag for key, tag in self.msgr.get_all_tags()]
        r = (
            self.annotatorSettings["nextTaskMinPaperNum"],
            self.annotatorSettings["nextTaskMaxPaperNum"],
        )
        tag = self.annotatorSettings["nextTaskPreferTagged"]
        mytag = "@" + self.msgr.username
        if tag == mytag:
            prefer_tagged_for_me = True
            tag = ""
        else:
            prefer_tagged_for_me = False
        d = TaggingAndRangeOptions(self, prefer_tagged_for_me, tag, all_tags, *r)
        if not d.exec():
            return
        r = d.get_papernum_range()
        tag = d.get_preferred_tag(self.msgr.username)
        self.annotatorSettings["nextTaskMinPaperNum"] = r[0]
        self.annotatorSettings["nextTaskMaxPaperNum"] = r[1]
        self.annotatorSettings["nextTaskPreferTagged"] = tag
        self.update_get_next_button()

    def update_get_next_button(self):
        tag = self.annotatorSettings["nextTaskPreferTagged"]
        mn = self.annotatorSettings["nextTaskMinPaperNum"]
        mx = self.annotatorSettings["nextTaskMaxPaperNum"]
        exclaim = False
        tips = []
        if mn is not None or mx is not None:
            exclaim = True
            s = "Restricted paper number "
            if mx is None:
                s += f"\N{GREATER-THAN OR EQUAL TO} {mn}"
            elif mn is None:
                s += f"\N{LESS-THAN OR EQUAL TO} {mx}"
            else:
                s += f"in [{mn}, {mx}]"
            tips.append(s)
        if tag:
            tips.append(f'prefer tagged "{tag}"')

        button_text = "&Get more"
        if exclaim:
            button_text += " (!)"
        self.getMoreButton.setText(button_text)
        self.getMoreButton.setToolTip("\n".join(tips))

    def loadMarkedList(self):
        """Loads the list of previously marked papers into self.examModel.

        Returns:
            None

        Deprecated: only called on legacy servers.

        Note: this tries to update the history between sessions; we don't
        try to do that on the new server, partially b/c the ordering seems
        fragile and I'm not sure its necessary.
        """
        # Ask server for list of previously marked papers
        markedList = self.msgr.MrequestDoneTasks(self.question_idx, self.version)
        self.marking_history = []
        for x in markedList:
            # TODO: might not the "markedList" have some other statuses?
            self.examModel.add_task(
                x[0],
                src_img_data=[],
                status="marked",
                mark=x[1],
                marking_time=x[2],
                tags=x[3],
                integrity_check=x[4],
                username=self.msgr.username,
            )
            self.marking_history.append(x[0])

    def get_files_for_previously_annotated(self, task: str) -> bool:
        """Loads the annotated image, the plom file, and the original source images.

        TODO: maybe it could not aggressively download the src images: sometimes
        people just want to look at the annotated image.

        Note that the local source image data will be replaced by data
        extracted from the Plom file.

        Args:
            task: the task for the image files to be loaded from.
                Takes the form "q1234g9" = test 1234 question 9

        Returns:
            True if the src_img_data, and the annotation files exist,
            False if not.  User will have seen an error message if
            False is returned.

        Raises:
            Uses error dialogs; not currently expected to throw exceptions
        """
        # First, check if we have the three things: if so we're done.
        # TODO: special hack as empty "" comes back as Path which is "."
        try:
            if (
                self.examModel.get_source_image_data(task)
                and self.examModel.getPaperDirByTask(task)
                and str(self.examModel.getAnnotatedFileByTask(task)) != "."
            ):
                return True
        except ValueError:
            # Asking examModel about non-existent task is a ValueError.
            # This can happen using Ctrl-left after resetting a task; just
            # bail with False for now...  Issue #5078.
            return False

        num, question_idx = unpack_task_code(task)
        assert question_idx == self.question_idx, f"wrong qidx={question_idx}"

        # TODO: this integrity is almost certainly not important unless I want
        # to modify.  If just looking...?  Anyway, non-legacy doesn't enforce it
        try:
            integrity = self.examModel.getIntegrityCheck(task)
        except ValueError:
            return False

        try:
            plomdata = self.msgr.get_annotations(
                num, question_idx, edition=None, integrity=integrity
            )
            annot_img_info, annot_img_bytes = self.msgr.get_annotations_image(
                num, question_idx, edition=plomdata["annotation_edition"]
            )
        except PlomNoPaper as e:
            ErrorMsg(None, f"no annotations for task {task}: {e}").exec()
            return False
        except (PlomTaskChangedError, PlomTaskDeletedError) as ex:
            # TODO: better action we can take here?
            # TODO: the real problem here is that the full_pagedata is potentially out of date!
            # TODO: we also need (and maybe already have) a mechanism to invalidate existing annotations
            # TODO: Issue #2146, parent=self will cause Marker to popup on top of Annotator
            ErrorMsg(
                None,
                '<p>The task "{}" has changed in some way by the manager; it '
                "may need to be remarked.</p>\n\n"
                '<p>Specifically, the server says: "{}"</p>\n\n'
                "<p>This is a rare situation; just in case, we'll now force a "
                "shutdown of your client.  Sorry.</p>"
                "<p>Please log back in and continue marking.</p>".format(task, str(ex)),
            ).exec()
            # Log out the user and then raise an exception
            try:
                self.msgr.closeUser()
            except PlomAuthenticationException:
                log.warning("We tried to logout user but they were already logged out.")
                pass
            # exit with code that is not 0 or 1
            self.Qapp.exit(57)
            log.critical("Qapp.exit() may not exit immediately; force quitting...")
            raise PlomForceLogoutException("Manager changed task") from ex

        log.info("importing source image data (orientations etc) from .plom file")
        # filenames likely stale: could have restarted client in meantime
        src_img_data = plomdata["base_images"]
        for row in src_img_data:
            # remove legacy "local_filename" if present
            f = row.pop("local_filename", None) or row.get("filename")
            if not row.get("server_path"):
                # E.g., Reannotator used to lose "server_path", keep workaround
                # just in case, by using previous session's filename
                row["server_path"] = f
        self.get_downloads_for_src_img_data(src_img_data)

        self.examModel.set_source_image_data(task, src_img_data)

        assert not task.startswith("q")
        paperdir = Path(tempfile.mkdtemp(prefix=task + "_", dir=self.workingDirectory))
        log.debug("create paperdir %s for already-graded download", paperdir)
        self.examModel.setPaperDirByTask(task, paperdir)
        aname = paperdir / f"G{task}.{annot_img_info['extension']}"
        pname = paperdir / f"G{task}.plom"
        with open(aname, "wb") as fh:
            fh.write(annot_img_bytes)
        with open(pname, "w") as f:
            json.dump(plomdata, f, indent="  ", default=_json_path_to_str)
            f.write("\n")
        self.examModel.setAnnotatedFile(task, aname, pname)
        return True

    def _updateImage(self, pr: int) -> None:
        """Updates the preview image for a particular row of the table.

        Try various things to get an appropriate image to display.
        Lots of side effects as we update the table as needed.

        .. note::
           This function is a workaround used to keep the preview
           up-to-date as the table of papers changes.  Ideally
           the two widgets would be linked with some slots/signals
           so that they were automatically in-sync and updates to
           the table would automatically reload the preview.  Perhaps
           some future Qt expert will help us...

        Args:
            pr: which row is highlighted, via row index.

        Returns:
            None
        """
        # simplest first: if we have the annotated image then display that
        ann_img_file = self.prxM.getAnnotatedFile(pr)
        # TODO: special hack as empty "" comes back as Path which is "."
        if str(ann_img_file) == ".":
            ann_img_file = ""
        if ann_img_file:
            self.testImg.updateImage(ann_img_file)
            return

        task = self.prxM.getPrefix(pr)
        status = self.prxM.getStatus(pr)

        # next we try to download annotated image for certain hardcoded states
        if status.casefold() in ("complete", "marked"):
            # Note: "marked" is only on legacy servers
            r = self.get_files_for_previously_annotated(task)
            if not r:
                return
            self._updateImage(pr)  # recurse
            return

        # try the raw page images instead from the cached src_img_data
        src_img_data = self.examModel.get_source_image_data(task)
        if src_img_data:
            self.get_downloads_for_src_img_data(src_img_data)
            self.testImg.updateImage(src_img_data)
            return

        # but if the src_img_data isn't present, get and trigger background downloads
        src_img_data = self.get_src_img_data(task, cache=True)
        if src_img_data:
            self.get_downloads_for_src_img_data(src_img_data)
            self.testImg.updateImage(src_img_data)
            return

        # All else fails, just wipe the display (e.g., pages removed from server)
        self.testImg.updateImage(None)

    def get_src_img_data(
        self, task: str, *, cache: bool = False
    ) -> list[dict[str, Any]]:
        """Download the pagedate/src_img_data for a particular task.

        Note this does not trigger downloads of the page images.  For
        that, see :method:`get_downloads_for_src_img_data`.

        Args:
            task: which task to download the page data for.

        Keyword Args:
            cache: if this is one of the questions that we're marking,
                also fill-in or update the client-side cache of pagedata.
                Caution: page-arranger might mess with the local copy,
                so for now be careful using this option.  Default: False.

        Returns:
            The source image data.

        Raises:
            PlomConflict: no paper.
        """
        papernum, qidx = unpack_task_code(task)
        pagedata = self.msgr.get_pagedata_context_question(papernum, qidx)

        # TODO: is this the main difference between pagedata and src_img_data?
        pagedata = [x for x in pagedata if x["included"]]

        if cache and self.question_idx == qidx:
            try:
                self.examModel.set_source_image_data(task, pagedata)
            except KeyError:
                pass
        return pagedata

    def _updateCurrentlySelectedRow(self) -> None:
        """Updates the preview image for the currently selected row of the table.

        Returns:
            None
        """
        prIndex = self.ui.tableView.selectedIndexes()
        if len(prIndex) == 0:
            return
        # Note: a single selection should have length 11: could assert
        pr = prIndex[0].row()
        self._updateImage(pr)

    def updateProgress(self, *, info: dict[str, Any] | None = None) -> None:
        """Updates the progress bar and related display of progress information.

        Keyword Args:
            info: key-value pairs with information about progress overall,
                and for this user, including information about quota.
                If omitted, we'll contact the server synchronously to get
                this info.

        Returns:
            None

        May open dialogs in some circumstances.
        """
        if info is None:
            # ask server for progress update
            try:
                info = self.msgr.get_marking_progress(self.question_idx, self.version)
            except PlomRangeException as e:
                ErrorMsg(self, str(e)).exec()
                return

        if info["total_tasks"] == 0:
            self.ui.labelProgress.setText("Progress: no papers to mark")
            self.ui.mProgressBar.setVisible(False)
            self.ui.explainQuotaButton.setVisible(False)
            try:
                qlabel = get_question_label(self.exam_spec, self.question_idx)
                verbose_qlabel = verbose_question_label(
                    self.exam_spec, self.question_idx
                )
            except (ValueError, KeyError):
                qlabel = "???"
                verbose_qlabel = qlabel
            msg = f"<p>Currently there is nothing to mark for version {self.version}"
            msg += f" of {verbose_qlabel}.</p>"
            infostr = f"""<p>There are several ways this can happen:</p>
                <ul>
                <li>Perhaps the relevant papers have not yet been scanned.</li>
                <li>This assessment may not have instances of version
                    {self.version} of {qlabel}.</li>
                </ul>
            """
            InfoMsg(self, msg, info=infostr, info_pre=False).exec()
            return

        if not self.ui.mProgressBar.isVisible():
            self.ui.mProgressBar.setVisible(True)

        self.ui.explainQuotaButton.setVisible(False)
        if info["user_quota_limit"] is not None:
            s = f"Marking limit: {info['user_quota_limit']} papers"
            self.ui.labelProgress.setText(s)
            self.ui.explainQuotaButton.setVisible(True)
            self.ui.mProgressBar.setMaximum(info["user_quota_limit"])
            self.ui.mProgressBar.setValue(info["user_tasks_marked"])

            self._user_reached_quota_limit = False
            if info["user_tasks_marked"] >= info["user_quota_limit"]:
                self._user_reached_quota_limit = True
                ReachedQuotaLimitDialog(self, limit=info["user_quota_limit"]).exec()
            return

        self.ui.labelProgress.setText("")
        self.ui.mProgressBar.setMaximum(info["total_tasks"])
        self.ui.mProgressBar.setValue(info["total_tasks_marked"])

    def claim_task_interactive(self) -> None:
        """Ask user for paper number and then ask server for that paper.

        If available, download stuff, add to list, update view.
        """
        verbose_qlabel = verbose_question_label(self.exam_spec, self.question_idx)
        s = "<p>Which paper number would you like to get?</p>"
        s += f"<p>Note: you are marking version {self.version}"
        s += f" of {verbose_qlabel}.</p>"
        n, ok = QInputDialog.getInt(
            self, "Which paper to get", s, 1, 1, self.max_papernum
        )
        if not ok:
            return
        task = paper_question_index_to_task_id_str(n, self.question_idx)
        self._claim_task(task)

    def request_one_more(self) -> None:
        """Ask server for an unmarked paper, get file, add to list, update view, but don't automatically select."""
        self._requestNext(update_select=False)

    def _requestNext(
        self,
        *,
        update_select: bool = True,
        enter_annotate_mode_if_possible: bool = False,
    ) -> None:
        """Ask server for an unmarked paper, get file, add to list, update view.

        Retry a few times in case two clients are asking for same.

        Keyword Args:
            update_select (bool): default True, send False if you don't
                want to adjust the visual selection.
            enter_annotate_mode_if_possible: if true, then if there is a
                task to be me marked, try to enter annotate mode to mark
                it.  False by default, b/c if user is in view mode they
                may not want to aggressively enter annotate mode, except
                on marker init.
        """
        attempts = 0
        tag = self.annotatorSettings["nextTaskPreferTagged"]
        paper_range = (
            self.annotatorSettings["nextTaskMinPaperNum"],
            self.annotatorSettings["nextTaskMaxPaperNum"],
        )
        if tag and (paper_range[0] or paper_range[1]):
            log.info('Next available?  Range %s, prefer tagged "%s"', paper_range, tag)
        elif tag:
            log.info('Next available?  Prefer tagged "%s"', tag)
        elif paper_range[0] or paper_range[1]:
            log.info("Next available?  Range %s", paper_range)
        if tag:
            tags = [tag]
        else:
            tags = []
        while True:
            attempts += 1
            # little sanity check - shouldn't be needed.
            # TODO remove.
            if attempts > 5:
                return
            try:
                task = self.msgr.MaskNextTask(
                    self.question_idx,
                    self.version,
                    tags=tags,
                    min_paper_num=paper_range[0],
                    max_paper_num=paper_range[1],
                )
                if not task:
                    return
            except PlomSeriousException as err:
                log.exception("Unexpected error getting next task: %s", err)
                ErrorMsg(
                    self,
                    "Unexpected error getting next task. Client will now crash!",
                    info=str(err),
                ).exec()
                raise
            try:
                self.claim_task_and_trigger_downloads(task)
                break
            except PlomTakenException as err:
                log.info("will keep trying as task already taken: {}".format(err))
                continue
        if update_select:
            self.moveSelectionToTask(task)
        if enter_annotate_mode_if_possible:
            self.annotate_task()

    def get_downloads_for_src_img_data(
        self, src_img_data: list[dict[str, Any]], trigger: bool = True
    ) -> bool:
        """Make sure the images for some source image data are downloaded.

        If an image is not yet downloaded, trigger the download again.

        Args:
            src_img_data (list): list of dicts.  Note we may modify this
                so pass a copy if you don't want this!  Specifically,
                the ``"filename"`` key is inserted or replaced with the
                path to the downloaded image or the placeholder image.

        Keyword Args:
            trigger (bool): if True we trigger background jobs for any
                that have not been downloaded.

        Returns:
            bool: True if all images have already been downloaded, False
            if at least one was not.  In the False case, downloads have
            been triggered; wait; process events; then call back if you
            want.
        """
        all_present = True
        PC = self.downloader.pagecache
        for row in src_img_data:
            if PC.has_page_image(row["id"]):
                row["filename"] = PC.page_image_path(row["id"])
                continue
            all_present = False
            log.info("triggering download for image id %d", row["id"])
            try:
                self.downloader.download_in_background_thread(row)
            except PlomConnectionError as e:
                # Issue #3427: it seems some kind of race can happen, presumably
                # when we call downloader.detach_messenger, but somehow one of
                # the various ways of refreshing the image is still triggered.
                # In this happens, don't crash, log that it happened.  Worst case
                # we're left staring at the placeholder.
                log.error(f"{e}")
            row["filename"] = self.downloader.get_placeholder_path()
        return all_present

    def claim_task_and_trigger_downloads(self, task: str) -> None:
        """Claim a particular task for the current user and start image downloads.

        Notes:
            Side effects: on success, updates the table of tasks by adding
            a new row (or modifying an existing one).  But the new row is
            *not* automatically selected.

        Returns:
            None

        Raises:
            PlomTakenException
            PlomVersionMismatchException
        """
        __, qidx = unpack_task_code(task)
        assert qidx == self.question_idx, f"wrong question: question_idx={qidx}"
        src_img_data, tags, integrity_check = self.msgr.claim_task(
            task, version=self.version
        )

        self.get_downloads_for_src_img_data(src_img_data)

        # TODO: do we really want to just hardcode "untouched" here?
        if self.examModel.has_task(task):
            self.examModel.update_task(
                task,
                src_img_data=src_img_data,
                status="untouched",
                mark=-1,
                marking_time=0.0,
                tags=tags,
                integrity=integrity_check,
                username=self.msgr.username,
            )
        else:
            self.examModel.add_task(
                task,
                src_img_data=src_img_data,
                status="untouched",
                mark=-1,
                marking_time=0.0,
                tags=tags,
                integrity_check=integrity_check,
                username=self.msgr.username,
            )

    def moveSelectionToTask(self, task: str) -> None:
        """Update the selection in the list of papers.

        Args:
            task: a string such as "0123g13".
        """
        assert not task.startswith("q")
        pr = self.prxM.rowFromTask(task)
        if pr is None:
            return
        self.ui.tableView.selectRow(pr)
        # this might redraw it twice: oh well this is not common operation
        # TODO: not sure, it may be more common now...
        self._updateCurrentlySelectedRow()
        # Clean up the table
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.resizeRowsToContents()

    def background_download_finished(self, img_id, md5, filename):
        log.debug(f"PageCache has finished downloading {img_id} to {filename}")
        self.ui.labelTech2.setText(f"last msg: downloaded img id={img_id}")
        self.ui.labelTech2.setToolTip(f"{filename}")
        # TODO: not all downloads require redrawing the current row...
        # if any("placeholder" in x for x in testImg.imagenames):
        # force a redraw
        self._updateCurrentlySelectedRow()

    def background_download_failed(self, img_id):
        """Callback when a background download has failed."""
        self.ui.labelTech2.setText(f"<p>last msg: failed download img id={img_id}</p>")
        log.info(f"failed download img id={img_id}")
        self.ui.labelTech2.setToolTip("")

    def force_update_technical_stats(self):
        stats = self.downloader.get_stats()
        self.update_technical_stats(stats)

    def update_technical_stats(self, d):
        self.ui.labelTech1.setText(
            "<p>"
            f"d/l: {d['queued']} queued, {d['cache_size']} cached,"
            f" {d['retries']} retried, {d['fails']} failed"
            "</p>"
        )

    def update_technical_stats_upload(self, n, m, numup, failed):
        if n == 0 and m == 0:
            txt = "u/l: idle"
        else:
            txt = f"u/l: {n} queued, {m} inprogress"
        txt += f", {numup} done, {failed} failed"
        self.ui.labelTech3.setText(txt)

    def show_hide_technical(self):
        """Toggle the technical panel in response to checking a button."""
        if not self.ui.frameTechnical.isVisible():
            self.ui.frameTechnical.setVisible(True)
            ptsz = self.ui.hamMenuButton.fontInfo().pointSizeF()
            self.ui.frameTechnical.setStyleSheet(
                f"QWidget {{ font-size: {0.7 * ptsz}pt; }}"
            )
            # toggle various columns without end-user useful info
            for i in self.ui.examModel.columns_to_hide:
                self.ui.tableView.showColumn(i)
                # Limit the widths of the debugging columns, otherwise ridiculous
                # TODO: no initial effect (before view setModel, does self.setHorizontalHeaderLabels)

                self.ui.tableView.setColumnWidth(i, 128)
        else:
            self.ui.frameTechnical.setVisible(False)
            for i in self.ui.examModel.columns_to_hide:
                self.ui.tableView.hideColumn(i)

    def toggle_fail_mode(self):
        """Toggle artificial failures simulatiing flaky networking in response to ticking a button."""
        if self.ui.failmodeCB.isChecked():
            self.Qapp.downloader.enable_fail_mode()
            r = self.Qapp.downloader._simulate_failure_rate
            a, b = self.Qapp.downloader._simulate_slow_net
            tip = f"download: delay ∈ [{a}s, {b}s], {r:0g}% retry"
            if self.allowBackgroundOps:
                self.backgroundUploader.enable_fail_mode()
                r = self.backgroundUploader._simulate_failure_rate
                a, b = self.backgroundUploader._simulate_slow_net
                tip += f"\nupload delay ∈ [{a}s, {b}s], {r:0g}% fail"
            self.ui.failmodeCB.setToolTip(tip)
        else:
            self.ui.failmodeCB.setToolTip("")
            self.Qapp.downloader.disable_fail_mode()
            if self.allowBackgroundOps:
                self.backgroundUploader.disable_fail_mode()

    def moveToNextUnmarkedTask(self, start_from_task: str | None = None) -> bool:
        """Move the task list selection to the next unmarked test, if possible.

        Updating this selection should be enough for the rest of the UI
        to react to the changes.

        Args:
            start_from_task: the task number to start searching from.
                If this task is untouched, you'll get that one.  If
                omitted, we start searching at the top of the table.

        Returns:
            True if move was successful, False if not, for any reason.
        """
        # Move to the next unmarked test in the table.
        # Be careful not to get stuck in a loop if all marked
        prt = self.prxM.rowCount()
        if prt == 0:  # no tasks
            return False

        prstart = None
        if start_from_task:
            prstart = self.prxM.rowFromTask(start_from_task)
        if not prstart:
            # it might be hidden by filters
            prstart = 0  # put 'start' at row=0
        pr = prstart
        while self.prxM.getStatus(pr).casefold() != "untouched":
            pr = (pr + 1) % prt
            if pr == prstart:  # don't get stuck in a loop
                break
        if pr == prstart:
            return False  # have looped over all rows and not found anything.
        self.ui.tableView.selectRow(pr)

        # Might need to wait for a background downloader.  Important to
        # processEvents() so we can receive the downloader-finished signal.
        task = self.prxM.getPrefix(pr)
        count = 0
        # placeholder = self.downloader.get_placeholder_path()
        while True:
            src_img_data = self.examModel.get_source_image_data(task)
            if self.get_downloads_for_src_img_data(src_img_data):
                break
            time.sleep(0.05)
            self.Qapp.processEvents()
            count += 1
            if (count % 10) == 0:
                log.info("waiting for downloader to fill table...")
            if count >= 100:
                msg = SimpleQuestion(
                    self,
                    "Still waiting for downloader to get the next image.  "
                    "Do you want to wait a few more seconds?\n\n"
                    "(It is safe to choose 'no': the Annotator will simply close)",
                )
                if msg.exec() == QMessageBox.StandardButton.No:
                    return False
                count = 0
                self.Qapp.processEvents()

        return True

    def change_task_view(self, cbidx: int) -> None:
        """Update task list in response to combobox activation.

        In some cases we reject the change and change the index ourselves.
        """
        if cbidx == 0:
            self._show_only_my_tasks()
            return
        if cbidx != 1:
            raise NotImplementedError(f"Unexpected cbidx={cbidx}")
        if not self.annotatorSettings["user_can_view_all_tasks"]:
            InfoMsg(self, "You don't have permission to view all tasks").exec()
            self.ui.tasksComboBox.setCurrentIndex(0)
            self._show_only_my_tasks()
            return
        self._show_all_tasks()
        if not self.download_task_list():
            # could not update (maybe legacy server) so go back to only mine
            self.ui.tasksComboBox.setCurrentIndex(0)
            self._show_only_my_tasks()

    def refresh_server_data(self):
        """Refresh various server data including the current task last from the server."""
        info = self.msgr.get_exam_info()
        self.max_papernum = info["current_largest_paper_num"]
        # legacy won't provide this; fallback to a static value
        self.annotatorSettings["feedback_rules"] = info.get(
            "feedback_rules", static_feedback_rules_data
        )
        if not self.msgr.is_legacy_server():
            # TODO: in future, I think I prefer a rules-based framework
            # Not "you are lead marker" but "you can view all tasks".
            # To my mind, "lead_marker" etc is some server detail that
            # could stay on the server.
            if self.msgr.get_user_role() == "lead_marker":
                self.annotatorSettings["user_can_view_all_tasks"] = True
            else:
                self.annotatorSettings["user_can_view_all_tasks"] = False
        else:
            self.annotatorSettings["user_can_view_all_tasks"] = False
        if not self.annotatorSettings["user_can_view_all_tasks"]:
            # it might've changed, so reset combobox selection
            self.ui.tasksComboBox.setCurrentIndex(0)
            self._show_only_my_tasks()

        # legacy does it own thing earlier in the workflow
        if not self.msgr.is_legacy_server():
            if self.ui.tasksComboBox.currentIndex() == 0:
                assert self.msgr.username is not None
                self.download_task_list(username=self.msgr.username)
            else:
                self.download_task_list()

        # TODO: re-queue any failed uploads, Issue #3497

        self.updateProgress()

    def download_task_list(self, *, username: str = "") -> bool:
        """Download and fill/update the task list.

        Danger: there is quite a bit of subtly here about how to update
        tasks when we already have local cached data or when the local
        state might be mid-upload.

        Keyword Args:
            username: find tasks assigned to this user, or all tasks if
                omitted.

        Returns:
            True if the donload was successful, False if the server
            does not support this.
        """
        try:
            tasks = self.msgr.get_tasks(
                self.question_idx, self.version, username=username
            )
        except PlomNoServerSupportException as e:
            WarnMsg(self, str(e)).exec()
            return False
        our_username = self.msgr.username
        task_ids_seen = []
        for t in tasks:
            task_id_str = paper_question_index_to_task_id_str(
                t["paper_number"], t["question"]
            )
            task_ids_seen.append(task_id_str)
            username = t.get("username", "")
            integrity = t.get("integrity", "")
            # TODO: maybe task_model can support None for mark too...?
            mark = t.get("score", -1)  # not keen on this -1 sentinel
            status = t["status"]
            # mismatch b/w server status and how we represent claimed tasks locally
            if status.casefold() == "out" and username == our_username:
                status = "untouched"

            # Issue #3706: sometimes server sends attn_tags...
            tags = t["tags"]
            tags.extend(t.get("attn_tags", []))
            try:
                self.examModel.add_task(
                    task_id_str,
                    src_img_data=[],
                    mark=mark,
                    marking_time=t.get("marking_time", 0.0),
                    status=status,
                    tags=tags,
                    username=username,
                    integrity_check=integrity,
                )
            except KeyError:
                # Be careful b/c we don't want to stomp local state during
                # in-progress uploads or situations we might want to retry
                local_status = self.examModel.getStatusByTask(task_id_str)
                if local_status.casefold() in ("uploading...", "failed upload"):
                    log.info(
                        'Refreshing but task %s has status "%s": not touching local data',
                        task_id_str,
                        local_status,
                    )
                    # even for those, we should update the tags
                    self.tags_changed_signal.emit(task_id_str, tags)
                    continue

                # In future, could try to keep existing src_img_data by *not* including
                # it here: examModel will preserve it if possible.  This could decrease
                # metadata transfer from server (but note page images are already cached).
                self.examModel.update_task(
                    task_id_str,
                    src_img_data=t.get("src_img_data"),
                    integrity=t.get("integrity"),
                    mark=mark,
                    marking_time=t.get("marking_time", 0.0),
                    status=status,
                    tags=tags,
                    username=username,
                )

                # TODO: in the future, the `t` data could have information about the
                # latest annotation but for now we just clear, unless the task is ours.
                # This will cause images to be downloaded again after refreshes.
                # Issue #3630 proposes improvements.
                if username != our_username:
                    self.examModel.setAnnotatedFile(task_id_str, "", "")
                    self.examModel.setPaperDirByTask(task_id_str, "")
                else:
                    # for now, also force redownloads of our own annotation images, else
                    # we would need to fix Issue #3631: wrong annot image in corner cases
                    self.examModel.setAnnotatedFile(task_id_str, "", "")
                    self.examModel.setPaperDirByTask(task_id_str, "")

        # Prune stale tasks that the server no longer lists as ours, carefully keep
        # any that might not be saved yet (even if not seen in previous loop).
        for task_id_str in self.examModel.get_all_tasks():
            local_status = self.examModel.getStatusByTask(task_id_str)
            if local_status.casefold() in ("uploading...", "failed upload"):
                continue
            if task_id_str in task_ids_seen:
                continue
            log.info("Removing row %s: server no longer says its ours", task_id_str)
            self.examModel.remove_task(task_id_str)

        self._updateCurrentlySelectedRow()
        return True

    def reassign_task_to_me(self, task: str | None = None) -> None:
        """Reassign a task to the current user."""
        self.reassign_task(task, assign_to=self.msgr.username)

    def reassign_task(
        self, task: str | None = None, *, assign_to: str | None = None
    ) -> None:
        """Reassign a task (by default the currently-selected task) to ourselves or another user.

        Args:
            task: a task code like `"0123g5"`, or None to use the
                currently-selected task.

        Keyword Args:
            assign_to: if present, try to reassign to this user directly.
                If omitted, we'll ask using a popup dialog.
        """
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return
        papernum, qidx = unpack_task_code(task)

        if assign_to is None:
            # TODO: combobox or similar to choose users
            assign_to, ok = QInputDialog.getText(
                self,
                "Reassign to",
                f"Who would you like to reassign {task} to?",
                text=self.msgr.username,
            )
            if not ok:
                return

        try:
            # TODO: consider augmenting with a reason, e.g., reason="help" kwarg
            self.msgr.reassign_task(papernum, qidx, assign_to)
        except (
            PlomNoServerSupportException,
            PlomRangeException,
            PlomNoPermission,
        ) as e:
            InfoMsg(self, f"{e}").exec()
            return
        # The simplest thing is simply to refresh/rebuild the task list
        self.refresh_server_data()

    def claim_task(self, task: str | None = None) -> None:
        """Try to claim a certain task for this user.

        Args:
            task: a task string like `0123g13`.  If None then query
                the selection for the currently selected task.
        """
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return
        # TODO: if its "To Do" we can just claim it
        # TODO: in fact, I'd expect double-click to do that.
        user = self.examModel.get_username_by_task(task)
        if user == self.msgr.username:
            InfoMsg(
                self,
                f"Note: task {task} appears to already belong to you,"
                " trying to claim anyway...",
            ).exec()
        elif self.examModel.getStatusByTask(task).casefold() != "to do":
            WarnMsg(
                self, f'Not implemented yet: cannot claim {task} from user "{user}"'
            ).exec()
            return
        self._claim_task(task)

    def _claim_task(self, task: str) -> None:
        log.info("claiming task %s", task)
        try:
            self.claim_task_and_trigger_downloads(task)
        except (
            PlomTakenException,
            PlomRangeException,
            PlomVersionMismatchException,
        ) as err:
            WarnMsg(self, f"Cannot get task {task}.", info=err).exec()
            return

    def defer_task(self, *, advance_to_next: bool = True) -> None:
        """Mark task as "defer" - to be skipped until later.

        You'll still have to do it.

        Keyword Args:
            advance_to_next: whether to also advance to the next task
                (default).
        """
        task = self.get_current_task_id_or_none()
        if not task:
            return
        if self.examModel.getStatusByTask(task) == "deferred":
            return
        if not self.examModel.is_our_task(task, self.msgr.username):
            s = f"Cannot defer task {task} b/c it isn't yours"
            user = self.examModel.get_username_by_task(task)
            if user:
                s += f': {task} belongs to "{user}"'
            InfoMsg(self, s).exec()
            return
        if self.examModel.getStatusByTask(task).casefold() in (
            "complete",
            "marked",
            "uploading...",
            "failed upload",
        ):
            InfoMsg(self, "Cannot defer a marked test.").exec()
            return

        if self._annotator:
            # currently always true but maybe in future you can defer others
            if task == self._annotator.task:
                if self._annotator.is_dirty():
                    msg = SimpleQuestion(
                        self, "Discard any annotations and defer this task?"
                    )
                    if msg.exec() != QMessageBox.StandardButton.Yes:
                        return
                    # TODO: maybe Ann needs a "revert" option?
                    self._annotator.close_current_task()
        self.examModel.deferPaper(task)
        if advance_to_next:
            # TODO: maybe we really need request_one_more_if_necessary
            # TODO: or that someone would just notice we're not far enough ahead
            # TODO: problem with current approach is if you "get more" til you
            # TODO: have 4 untouched, each defer will get one more untouhed.
            # TODO: IMHO, I'd rather this only happen when there is less than 2 untouched
            self.request_one_more()
            self.moveToNextUnmarkedTask()
            # alternatively or if we want to search "forward" of current:
            # self.moveToNextUnmarkedTask(task)

    def reset_task(self, task: str | None = None) -> None:
        """Reset this task, outdating all annotations and putting it back into the pool.

        Args:
            task: a string such as `"0123g5"` or if None / omitted, then
                try to get from the current selection.

        Note: if you reset the current task that is being annotated, its not
        entirely (currently) well specified which task will be selected, but
        currently it stays in edit mode.
        """
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return
        papernum, qidx = unpack_task_code(task)
        question_label = get_question_label(self.exam_spec, qidx)

        msg = SimpleQuestion(
            self,
            f"This will reset task {task}; any annotations will be discarded."
            f" Someone will have to mark paper {papernum:04}"
            f" question {question_label} again!",
            "Are you sure you wish to proceed?",
        )
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return

        if self._annotator:
            if task == self._annotator.task:
                # Note even if _annotator.is_dirty(), user has already confirmed
                log.debug("We are resetting the very task we are annotating...")
                self._annotator.close_current_task()

        try:
            self.msgr.reset_task(papernum, qidx)
        except (
            PlomNoServerSupportException,
            PlomRangeException,
            PlomNoPermission,
        ) as e:
            InfoMsg(self, f"{e}").exec()
            return
        self.refresh_server_data()

    def startTheAnnotator(self, initialData) -> None:
        """This fires up the annotation widget for user annotation + marking.

        Args:
            initialData (list): containing things documented elsewhere
                in :method:`getDataForAnnotator`
                and :func:`plom.client.annotator.Annotator.__init__`.

        Returns:
            None
        """
        annotator = Annotator(
            self.msgr.username,
            parentMarkerUI=self,
            initialData=initialData,
        )
        # run the annotator
        annotator.annotator_upload.connect(self.callbackAnnWantsUsToUpload)
        annotator.annotator_done_closing.connect(self.callbackAnnDoneClosing)
        annotator.annotator_done_reject.connect(self.callbackAnnDoneCancel)
        # manages the "*" in the titlebar when the pagescene is dirty
        annotator.cleanChanged.connect(self.clean_changed)

        # Do a bunch of (temporary) hacking to embed Annotator
        self._annotator = annotator
        self.ui.paperBoxLayout.addWidget(self._annotator, 24)
        self.testImg.setVisible(False)
        self.ui.viewModeFrame.setVisible(False)
        self.ui.tableView.clicked.connect(self.annotate_task)
        # not sure why this needs a typing exception...
        annotator.ui.verticalLayout.setContentsMargins(0, 0, 6, 0)  # type: ignore[attr-defined]
        # TODO: doesn't help, why not?  Not worth worrying about if we remove
        # self.testImg.resetView()

    @pyqtSlot(bool)
    def clean_changed(self, clean: bool) -> None:
        """React to changes in the cleanliness of annotator, indicating that changes need to be saved."""
        super().setWindowModified(not clean)

    def switch_task(self, task: str) -> None:
        """Try to switch to marking/viewing a particular task, possibly checking with user.

        Args:
            task: a string like `0123g7`.

        This code might fail to the switch the task, for example, if the
        user has unsaved work and doesn't watch to discard it.
        If it does succeed in switching, it will also update the task
        table selection indicator.
        """
        if self._annotator:
            if self._annotator.task == task:
                log.debug("Annotator already on %s; no change required", task)
                return
            if self._annotator.is_dirty():
                msg = SimpleQuestion(self, "Discard any annotations and switch papers?")
                if msg.exec() != QMessageBox.StandardButton.Yes:
                    return
            if self.examModel.getStatusByTask(task) == "To Do":
                InfoMsg(
                    self,
                    f"Task {task} may not be assigned to you. "
                    "If you want to look at it, close the annotator "
                    'and change to read-only "view-mode".  '
                    "If you want to mark this paper, you can try to claim it.",
                ).exec()
                # TODO: QoL says put a "claim" button in the dialog
                # TODO: or easier yes/no: "Do you want to claim it?"
                return
            if self.examModel.getStatusByTask(task) == "Complete":
                if not self.examModel.is_our_task(task, self.msgr.username):
                    InfoMsg(
                        self,
                        # TODO: useful to say what username here
                        f"Task {task} is not our task. "
                        "If you want to look at it, close the annotator "
                        'and change to read-only "view-mode".  '
                        "(If you want to edit this task, you'll need to "
                        "reassign the task to yourself).",
                    ).exec()
                    return
            self._annotator.close_current_task()
        self.moveSelectionToTask(task)

    def annotate_task(self, task: str | None = None) -> None:
        """Annotate a particular task, or currently-selected task, starting Annotator if necessary."""
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return

        if self._annotator:
            assert not task.startswith("q")
            if self._annotator.task == task:
                log.debug("Annotator already on %s; no change required", task)
                return

            if self._annotator.is_dirty():
                msg = SimpleQuestion(self, "Discard any annotations and switch papers?")
                if not msg.exec() == QMessageBox.StandardButton.Yes:
                    # TODO: hacking to change the selection *back* to what is was in the
                    # task list.  A lot to dislike here; lots of signals are going to happen
                    # for example.  And its yet another piece of spaghetti...
                    old_task = self._annotator.task
                    self.moveSelectionToTask(old_task)
                    return
            self._annotator.close_current_task()

        self._annotate_task(task)

    def _annotate_task(self, task: str | None = None) -> None:
        """Lower-level non-interactive start/switch Annotator."""
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return

        if self.examModel.getStatusByTask(task) == "To Do":
            log.warn("Ignored attempt to annotate 'To Do' task %s", task)
            return
        if self.examModel.getStatusByTask(task) == "Complete":
            if not self.examModel.is_our_task(task, self.msgr.username):
                log.warn(
                    "Ignored attempt to annotate 'Complete' task %s, not our's", task
                )
                return

        inidata = self.getDataForAnnotator(task)
        if inidata is None:
            return

        # If we're at quota, don't start marking as server will reject them
        # (but its ok to modify papers we've already marked).
        task_status = self.examModel.getStatusByTask(task)
        if task_status == "untouched" and self.marker_has_reached_task_limit():
            ReachedQuotaLimitDialog(self).exec()
            return

        if self.allowBackgroundOps:
            # If just one in the queue (which we are grading) then ask for more
            if self.examModel.countReadyToMark() <= 1:
                self.request_one_more()

        if self._annotator:
            self._annotator.load_new_question(*inidata)
        else:
            self.startTheAnnotator(inidata)

    def marker_has_reached_task_limit(self, *, use_cached: bool = True) -> bool:
        """Check whether a marker has reached their task limit if applicable.

        Keyword Args:
            use_cached: by default we use a cached value rather than connecting
                to the server to check.

        Returns:
            True if marker is in quota and they have reached their
            limit, otherwise False.
        """
        if not use_cached:
            self.updateProgress()
        return self._user_reached_quota_limit

    def getDataForAnnotator(self, task: str) -> tuple | None:
        """Get the data the Annotator will need for a particular task.

        Args:
            task: the task id.  If original XXXXgYY, then annotated
                filenames are GXXXXgYY (G=graded).

        Returns:
            A tuple of data or None.  In the case of None, the user has already
            been shown a dialog, or parhaps choose a course of action already.
        """
        if not self.examModel.is_our_task(task, self.msgr.username):
            InfoMsg(
                self,
                f"Cannot annotate {task}: it is not assigned to you.",
                info=(
                    "Perhaps it was originally assigned to you and"
                    " has recently changed ownership. Or if you recently "
                    " re-assigned it yourself, try refreshing your task "
                    " list as a server change may not yet have propagated."
                ),
                info_pre=False,
            ).exec()
            return None

        status = self.examModel.getStatusByTask(task)

        # Create annotated filename.
        assert not task.startswith("q")
        paperdir = Path(tempfile.mkdtemp(prefix=task + "_", dir=self.workingDirectory))
        log.debug("create paperdir %s for annotating", paperdir)
        Gtask = "G" + task
        # note no extension yet
        aname = paperdir / Gtask
        pdict = None

        # TODO: prevent reannotating when its still uploading?
        if status.casefold() in ("uploading...", "failed upload"):
            msg = SimpleQuestion(
                self,
                "Uploading is in-progress or has failed.",
                question="Do you want to try to continue marking paper?",
            )
            if not msg.exec() == QMessageBox.StandardButton.Yes:
                return None
        if status.casefold() in ("complete", "marked", "uploading...", "failed upload"):
            oldpname = self.examModel.getPlomFileByTask(task)
            with open(oldpname, "r") as fh:
                pdict = json.load(fh)

        # Yes do this even for a regrade!  We will recreate the annotations
        # (using the plom file) on top of the original file.
        count = 0
        while True:
            if pdict:
                log.info("Taking src_img_data from previous plom data")
                src_img_data = pdict["base_images"]
            else:
                src_img_data = self.examModel.get_source_image_data(task)
            if self.get_downloads_for_src_img_data(src_img_data):
                break
            time.sleep(0.1)
            self.Qapp.processEvents()
            count += 1
            if (count % 10) == 0:
                log.info("waiting for downloader: {}".format(src_img_data))
            if count >= 40:
                msg = SimpleQuestion(
                    self,
                    "Still waiting for download.  Do you want to wait a bit longer?",
                )
                if msg.exec() == QMessageBox.StandardButton.No:
                    return None
                count = 0
                self.Qapp.processEvents()

        # maybe the downloader failed for some (rare) reason
        for data in src_img_data:
            if not Path(data["filename"]).exists():
                WarnMsg(
                    self,
                    f"Cannot annotate {task} because a file we expected "
                    "to find does not exist. Some kind of downloader fail?"
                    " While unnexpected, this is probably harmless.",
                ).exec()
                return None

        # we used to set status to indicate annotation-in-progress; removed as
        # it doesn't seem necessary (it was tricky to set it back afterwards)

        exam_name = self.exam_spec["name"]

        __, question_idx = unpack_task_code(task)
        question_label = get_question_label(self.exam_spec, question_idx)
        integrity_check = self.examModel.getIntegrityCheck(task)
        return (
            task,
            question_label,
            self.version,
            self.exam_spec["numberOfVersions"],
            exam_name,
            paperdir,
            aname,
            self.maxMark,
            pdict,
            integrity_check,
            src_img_data,
            self.examModel.getTagsByTask(task),
        )

    def getRubricsFromServer(self, question: int | None = None) -> list[dict[str, Any]]:
        """Get list of rubrics from server.

        Args:
            question: pertaining to which question or ``None`` for all
                rubrics.

        Returns:
            A list of the dictionary objects.
        """
        return self.msgr.MgetRubrics(question)

    def getOneRubricFromServer(self, key: int) -> dict[str, Any]:
        """Get one rubric from server.

        Args:
            key: which rubric.

        Returns:
            Dictionary representation of the rubric..

        Raises:
            PlomNoRubric
        """
        return self.msgr.get_one_rubric(key)

    def getOtherRubricUsagesFromServer(self, key: str) -> list[int]:
        """Get list of paper numbers using the given rubric.

        Args:
            key: the identifier of the rubric.

        Returns:
            List of paper numbers using the rubric.

        Raises:
            PlomNoServerSupportException
        """
        return self.msgr.get_other_rubric_usages(key)

    def sendNewRubricToServer(self, new_rubric) -> dict[str, Any]:
        return self.msgr.McreateRubric(new_rubric)

    def modifyRubricOnServer(
        self,
        rid: int,
        updated_rubric: dict[str, Any],
        *,
        minor_change: bool | None = None,
        tag_tasks: bool | None = None,
    ) -> dict[str, Any]:
        """Ask server to modify a rubric and get back new rubric.

        See the messenger method for detailed docs.
        """
        return self.msgr.MmodifyRubric(
            rid, updated_rubric, minor_change=minor_change, tag_tasks=tag_tasks
        )

    def _getSolutionImage(self) -> Path | None:
        """Get the file from disc if it exists, else grab from server."""
        f = self.workingDirectory / f"solution.{self.question_idx}.{self.version}.png"
        if f.is_file():
            return f
        return self.refreshSolutionImage()

    def refreshSolutionImage(self) -> Path | None:
        """Get solution image and save it to working dir."""
        f = self.workingDirectory / f"solution.{self.question_idx}.{self.version}.png"
        try:
            im_bytes = self.msgr.getSolutionImage(self.question_idx, self.version)
            with open(f, "wb") as fh:
                fh.write(im_bytes)
            return f
        except PlomNoSolutionException as e:
            log.warning(f"no solution image: {e}")
            # if a residual file is there, try to delete it
            try:
                f.unlink()
            except FileNotFoundError:
                pass
            return None

    def view_solutions(self):
        solutionFile = self._getSolutionImage()
        if solutionFile is None:
            InfoMsg(self, "No solution has been uploaded").exec()
            return

        if self.solutionView is None:
            self.solutionView = SolutionViewer(self, solutionFile)
        self.solutionView.show()
        # Issue #5090: get it back it back to the top
        # On Gnome, `activateWindow` works with shortcut key but
        # clicking with the mouse requires `raise` as well, except
        # TODO: it doesn't work, perhaps b/c they do not share a parent
        self.solutionView.activateWindow()
        self.solutionView.raise_()
        # TODO: test on other desktops and OSes

    def saveTabStateToServer(self, tab_state):
        """Upload a tab state to the server."""
        log.info("Saving user's rubric tab configuration to server")
        self.msgr.MsaveUserRubricTabs(self.question_idx, tab_state)

    def getTabStateFromServer(self):
        """Download the state from the server."""
        log.info("Pulling user's rubric tab configuration from server")
        return self.msgr.MgetUserRubricTabs(self.question_idx)

    # when Annotator done, we come back to one of these callbackAnnDone* fcns
    @pyqtSlot(str)
    def callbackAnnDoneCancel(self, task: str) -> None:
        """Called when annotator is done grading.

        Args:
            task: task name without the leading "q".

        Returns:
            None
        """
        # update image view b/c its image might have changed
        self._updateCurrentlySelectedRow()
        self._exit_annotate_mode()

    @pyqtSlot(str)
    def callbackAnnDoneClosing(self, task: str) -> None:
        """Called when annotator is done grading and is closing.

        Args:
            task: the task ID of the current test with no leading "q".

        Returns:
            None
        """
        # update image view b/c its image might have changed
        self._updateCurrentlySelectedRow()
        self._annotator = None
        self.testImg.setVisible(True)
        self.ui.viewModeFrame.setVisible(True)
        self.ui.tableView.clicked.disconnect()

    @pyqtSlot(str, list)
    def callbackAnnWantsUsToUpload(self, task: str, stuff: list) -> None:
        """Called when annotator wants to upload.

        Args:
            task: the task ID of the current test, "0123g13".
            stuff (list): a list containing
                grade(int): grade given by marker.
                markingTime(int): total time spent marking.
                paperDir(dir): Working directory for the current task
                aname(str): annotated file name
                plomFileName(str): the name of the .plom file
                rubric(list[str]): the keys of the rubrics used
                integrity_check(str): the integrity_check string of the task.

        Returns:
            None
        """
        (
            grade,
            markingTime,
            paperDir,
            aname,
            plomFileName,
            rubrics,
            integrity_check,
        ) = stuff
        if not isinstance(grade, (int, float)):
            raise RuntimeError(f"Mark {grade} type {type(grade)} is not a number")
        if not (0 <= grade and grade <= self.maxMark):
            raise RuntimeError(
                f"Mark {grade} outside allowed range [0, {self.maxMark}]. Please file a bug!"
            )
        assert not task.startswith("q")

        # TODO: this was unused?  comment out for now...
        # stat = self.examModel.getStatusByTask(task)

        # Copy the mark, annotated filename and the markingtime into the table
        # TODO: this is probably the right time to insert the modified src_img_data
        # TODO: but it may not matter as now the plomFileName has it internally
        self.examModel.markPaperByTask(
            task, grade, aname, plomFileName, markingTime, paperDir
        )
        # update the markingTime to be the total marking time
        totmtime = self.examModel.get_marking_time_by_task(task)

        _data = (
            task,
            grade,
            aname,
            plomFileName,
            totmtime,  # total marking time (seconds)
            self.question_idx,
            self.version,
            rubrics,
            integrity_check,
        )
        if self.allowBackgroundOps:
            # the actual upload will happen in another thread
            self.backgroundUploader.enqueueNewUpload(*_data)
        else:
            synchronous_upload(
                self.msgr,
                *_data,
                failCallback=self.backgroundUploadFailed,
                successCallback=self.backgroundUploadFinished,
            )
        # successfully marked and put on the upload list.
        # now update the marking history with the task.
        self.marking_history.append(task)

    def getMorePapers(self, old_task: str) -> tuple | None:
        """Loads more tests.

        Args:
            old_task: the task code with no leading "q" for the previous
                thing marked.

        Returns:
            The data for the annotator or None as described in
            :method:`getDataForAnnotator`.
        """
        log.debug("Annotator wants more (w/o closing)")
        if not self.allowBackgroundOps:
            self.request_one_more()
        if not self.moveToNextUnmarkedTask(old_task if old_task else None):
            return None
        task_id_str = self.get_current_task_id_or_none()
        if not task_id_str:
            return None
        data = self.getDataForAnnotator(task_id_str)
        if data is None:
            return None

        assert task_id_str == data[0]
        pdict = data[8]  # eww, hardcoded numbers
        assert pdict is None, "Annotator should not pull a regrade"

        if self.allowBackgroundOps:
            # If just one in the queue (which we are grading) then ask for more
            if self.examModel.countReadyToMark() <= 1:
                self.request_one_more()

        return data

    def backgroundUploadFinished(
        self, task: str, progress_info: dict[str, Any]
    ) -> None:
        """An upload has finished, do appropriate UI updates.

        Args:
            task: the task ID of the upload.
            progress_info: information about progress.

        Returns:
            None
        """
        stat = self.examModel.getStatusByTask(task)
        # maybe it changed while we waited for the upload
        if stat == "uploading...":
            if self.msgr.is_legacy_server():
                self.examModel.setStatusByTask(task, "marked")
            else:
                self.examModel.setStatusByTask(task, "Complete")
        self.updateProgress(info=progress_info)

    def backgroundUploadFailed(
        self, task: str, errmsg: str, server_changed: bool, unexpected: bool
    ) -> None:
        """An upload has failed, LOUDLY tell the user.

        Args:
            task: the task ID of the current test.
            errmsg: the error message.
            server_changed: True if this was something that changed server-side
                outside of our control.
            unexpected: True if this wasn't expected.

        Returns:
            None
        """
        self.examModel.setStatusByTask(task, "failed upload")

        msg = f"The server did not accept our marking for task {task}."

        if server_changed:
            msg += "\nSomeone has changed something on the server."
            # "This is a rare situation; no data corruption has occurred but "
            # "your annotations have been discarded just in case."

        if unexpected:
            msg += (
                "\nYour internet connection may be unstable or something"
                " unexpected has gone wrong."
                " Please consider logging out and restarting your client."
            )

        if not unexpected:
            WarnMsg(self, msg, info=errmsg).exec()
        else:
            ErrorMsg(self, msg, info=errmsg).exec()

    def updatePreviewImage(self, new: QItemSelection, old: QItemSelection) -> None:
        """Updates the displayed image when the selection changes.

        Args:
            new: the newly selected cells.
            old: the previously selected cells.

        Returns:
            None
        """
        idx = new.indexes()
        if len(idx) == 0:
            # Remove preview when user unselects row (e.g., ctrl-click)
            log.debug("User managed to unselect current row")
            self.testImg.updateImage(None)
            return
        # Note: a single selection should have length 11 all with same row: could assert
        self._updateImage(idx[0].row())

    def update_annotator(self, new: QItemSelection, old: QItemSelection) -> None:
        """If the annotator is active, make sure it is showing the correct task.

        Args:
            new: the newly selected cells.
            old: the previously selected cells.

        This is not the time for asking questions: we're well past the point of
        user interactivity: so if the scene is modified ("dirty") then too bad:
        discard and move!

        TODO: perhaps some unpleasant duplication between this and :method:`switch_task`.
        One difference is that code it allowed to be interactive and this is not.
        """
        if not self._annotator:
            return
        idx = new.indexes()
        idx2 = old.indexes()
        if len(idx) == 0:
            log.debug(f"UPDATE ANNOTR FROM SELECTION: new idx={idx}, old idx={idx2}")
            # TODO: we're getting here with empties after "refresh_server_data"
            # TODO: perhaps need to pause signals during that call?
            # Remove preview when user unselects row (e.g., ctrl-click)
            log.debug("User managed to unselect current row... or???")
            # TODO: we probably want close_current_task but annoying with above bug
            # self._annotator.close_current_task()
            # self._annotator._close_without_saving()
            # return

        self._annotator.close_current_task()
        self._annotate_task()

    def ensureAllDownloaded(self, new, old):
        """Whenever the selection changes, ensure downloaders are either finished or running for each image.

        We might need to restart downloaders if they have repeatedly failed.
        Even if we are still waiting, we can signal to the download the we
        have renewed interest in this particular download.
        TODO: for example. maybe we should send a higher priority?  No: currently
        this also happens "in the background" b/c Marker selects the new row.

        Args:
            new (QItemSelection): the newly selected cells.
            old (QItemSelection): the previously selected cells.

        Returns:
            None
        """
        idx = new.indexes()
        if len(idx) == 0:
            return
        # Note: a single selection should have length 11 all with same row: could assert
        pr = idx[0].row()
        task = self.prxM.getPrefix(pr)
        src_img_data = self.examModel.get_source_image_data(task)
        self.get_downloads_for_src_img_data(src_img_data)

    def get_upload_queue_length(self):
        """How long is the upload queue?

        An overly long queue might be a sign of network troubles.

        Returns:
            int: The number of papers waiting to upload, possibly but
            not certainly including the current upload-in-progress.
            Value might also be approximate.
        """
        if not self.backgroundUploader:
            return 0
        return self.backgroundUploader.queue_size()

    def wait_for_bguploader(self, timeout=0):
        """Wait for the uploader queue to empty.

        Args:
            timeout (int): return early after approximately `timeout`
                seconds.  If 0 then wait forever.

        Returns:
            bool: True if it shutdown.  False if we timed out.
        """
        dt = 0.1  # timestep
        if timeout != 0:
            N = ceil(float(timeout) / dt)
        else:
            N = 0  # zero/infinity: pretty much same
        M = ceil(2.0 / dt)  # warn every M seconds
        if self.backgroundUploader:
            count = 0
            while self.backgroundUploader.isRunning():
                if self.backgroundUploader.isEmpty():
                    # don't try to quit until the queue is empty
                    self.backgroundUploader.quit()
                time.sleep(dt)
                count += 1
                if N > 0 and count >= N:
                    log.warning(
                        "Timed out after {} seconds waiting for uploader to finish".format(
                            timeout
                        )
                    )
                    return False
                if count % M == 0:
                    log.warning("Still waiting for uploader to finish...")
            self.backgroundUploader.wait()
        return True

    def closeEvent(self, event: None | QtGui.QCloseEvent) -> None:
        log.debug("Something has triggered a shutdown event")

        if self._annotator:
            if self._annotator.is_dirty():
                msg0 = SimpleQuestion(self, "Discard unsaved annotations and quit?")
                if msg0.exec() != QMessageBox.StandardButton.Yes:
                    if event:
                        event.ignore()
                    return
            self._annotator.close()

        log.debug("Clean up any lingering solution-views etc")
        if self.solutionView:
            log.debug("Cleaning a solution-view")
            self.solutionView.close()
            self.solutionView = None

        while not self.Qapp.downloader.stop(500):
            if (
                SimpleQuestion(
                    self,
                    "Download threads are still in progress.",
                    question="Do you want to wait a little longer?",
                ).exec()
                == QMessageBox.StandardButton.No
            ):
                # TODO: do we have a force quit?
                break
        N = self.get_upload_queue_length()
        if N > 0:
            msg = QMessageBox()
            s = "<p>There is 1 paper" if N == 1 else f"<p>There are {N} papers"
            s += " uploading or queued for upload.</p>"
            msg.setText(s)
            s = "<p>You may want to cancel and wait a few seconds.</p>\n"
            s += "<p>If you&apos;ve already tried that, then the upload "
            s += "may have failed: you can quit, losing any non-uploaded "
            s += "annotations.</p>"
            msg.setInformativeText(s)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Discard
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            button = msg.button(QMessageBox.StandardButton.Cancel)
            assert button
            button.setText("Wait (cancel close)")
            msg.setIcon(QMessageBox.Icon.Warning)
            if msg.exec() == QMessageBox.StandardButton.Cancel:
                if event:
                    event.ignore()
                return
        if self.backgroundUploader is not None:
            # politely ask one more time
            if self.backgroundUploader.isRunning():
                self.backgroundUploader.quit()
            if not self.backgroundUploader.wait(50):
                log.info("Background downloader did stop cleanly in 50ms, terminating")
            # then nuke it from orbit
            if self.backgroundUploader.isRunning():
                self.backgroundUploader.terminate()

        log.debug("Revoking login token")
        # after revoking, Downloader's msgr will be invalid
        self.Qapp.downloader.detach_messenger()
        try:
            self.msgr.closeUser(revoke_token=True)
        except PlomAuthenticationException:
            log.warning("User tried to logout but was already logged out.")
            pass
        log.debug("Emitting Marker shutdown signal")
        retval = 2 if self._hack_prevent_shutdown else 1
        self.my_shutdown_signal.emit(
            retval,
            [
                self.annotatorSettings["keybinding_name"],
                self.annotatorSettings["keybinding_custom_overlay"],
            ],
        )
        if event:
            event.accept()
        log.debug("Marker: goodbye!")

    def cacheLatexComments(self):
        """Caches Latexed comments."""
        if True:
            log.debug("TODO: currently skipping LaTeX pre-rendering, see Issue #1491")
            return

        clist = []
        # sort list in order of longest comment to shortest comment
        clist.sort(key=lambda C: -len(C["text"]))

        # Build a progress dialog to warn user
        pd = QProgressDialog("Caching latex comments", None, 0, 3 * len(clist), self)
        pd.setWindowModality(Qt.WindowModality.WindowModal)
        pd.setMinimumDuration(0)
        # Start caching.
        c = 0
        pd.setValue(c)

        for X in clist:
            if X["text"][:4].upper() == "TEX:":
                txt = X["text"][4:].strip()
                pd.setLabelText("Caching:\n{}".format(txt[:64]))
                # latex the red version
                self.latexAFragment(txt, quiet=True)
                c += 1
                pd.setValue(c)
                # and latex the previews (legal and illegal versions)
                txtp = (
                    "\\color{blue}" + txt
                )  # make color blue for ghost rendering (legal)
                self.latexAFragment(txtp, quiet=True)
                c += 1
                pd.setValue(c)
                txtp = (
                    "\\color{gray}" + txt
                )  # make color gray for ghost rendering (illegal)
                self.latexAFragment(txtp, quiet=True)
                c += 1
                pd.setValue(c)
            else:
                c += 3
                pd.setLabelText("Caching:\nno tex")
                pd.setValue(c)
        pd.close()

    def latexAFragment(
        self, txt, *, quiet=False, cache_invalid=True, cache_invalid_tryagain=False
    ):
        """Run LaTeX on a fragment of text and return the file name of a PNG.

        The files are cached for reuse if the same text is passed again.

        Args:
            txt (str): the text to be Latexed.

        Keyword Args:
            quiet (bool): if True, don't popup dialogs on errors.
                Caution: this can result in a lot of API calls because
                users can keep requesting the same (bad) TeX from the
                server, e.g., by having bad TeX in a rubric.
            cache_invalid (bool): whether to cache invalid TeX.  Useful
                to prevent repeated calls to render bad TeX but might
                prevent users from seeing (again) an error dialog that
            cache_invalid_tryagain (bool): if True then when we get
                a cache hit of `None` (corresponding to bad TeX) then we
                try to to render again.

        Returns:
            pathlib.Path/str/None: a path and filename to a ``.png`` of
            the rendered TeX.  Or None if there was an error: callers
            will need to decide how to handle that, typically by
            displaying the raw code instead.
        """
        txt = txt.strip()
        # If we already latex'd this text, return the cached image
        try:
            r = self.commentCache[txt]
        except KeyError:
            # logic is convoluted: this is cache-miss...
            r = None
        else:
            # ..and this is cache-hit of None
            if r is None and not cache_invalid_tryagain:
                log.debug(
                    "tex: cache hit None, tryagain NOT set: %s",
                    shorten(txt, 60, placeholder="..."),
                )
                return None
        if r:
            return r
        log.debug("tex: request image for: %s", shorten(txt, 80, placeholder="..."))
        r, fragment = self.msgr.MlatexFragment(txt)
        if not r:
            if not quiet:
                # Heuristics to highlight error: latex errors seem to start with "! "
                lines = fragment.split("\n")
                idx = [i for i, line in enumerate(lines) if line.startswith("! ")]
                if any(idx):
                    n = idx[0]  # could be fancier if more than one match
                    info = '<font size="-3"><pre style="white-space: pre-wrap;">\n'
                    info += "\n".join(lines[max(0, n - 5) : n + 5])
                    info += "\n</pre></font>"
                    # TODO: Issue #2146, parent=self will cause Marker to popup on top of Annotator
                    InfoMsg(
                        None,
                        """
                        <p>The server was unable to process your TeX fragment.</p>
                        <p>Partial error message:</p>
                        """,
                        details=fragment,
                        info=info,
                        info_pre=False,
                    ).exec()
                else:
                    InfoMsg(
                        None,
                        "<p>The server was unable to process your TeX fragment.</p>",
                        details=fragment,
                    ).exec()
            if cache_invalid:
                self.commentCache[txt] = None
            return None
        with tempfile.NamedTemporaryFile(
            "wb", dir=self.workingDirectory, suffix=".png", delete=False
        ) as f:
            f.write(fragment)
            fragFile = f.name
        # add it to the cache
        self.commentCache[txt] = fragFile
        return fragFile

    def get_current_task_id_or_none(self) -> str | None:
        """Give back the task id string of the currently highlighted row or None.

        Returns:
            The task code, such as "0123g13".
        """
        prIndex = self.ui.tableView.selectedIndexes()
        if len(prIndex) == 0:
            return None
        # Note: a single selection should have length 11 (see ExamModel): could assert
        pr = prIndex[0].row()
        task_id_str = self.prxM.getPrefix(pr)
        return task_id_str

    def manage_tags(
        self, task: str | None = None, *, parent: QWidget | None = None
    ) -> None:
        """Manage the tags of a task, or the currently selected task.

        Args:
            task: A string like `"0003g2"` for paper 3 question 2 or try
                to use the current selection if None or omitted.

        Keyword Args:
            parent: Which window should be dialog's parent?
                If None, then use `self` (which is Marker) but if other
                windows (such as Annotator or PageRearranger) are calling
                this and if so they should pass themselves: that way they
                would be the visual parents of this dialog.

        Returns:
            None
        """
        if not task:
            task = self.get_current_task_id_or_none()
        if not task:
            return

        if not parent:
            parent = self

        all_tags = [tag for key, tag in self.msgr.get_all_tags()]
        try:
            current_tags = self.msgr.get_tags(task)
        except PlomNoPaper as e:
            WarnMsg(parent, f"Could not get tags from {task}", info=str(e)).exec()
            return

        tag_choices = [X for X in all_tags if X not in current_tags]

        artd = AddRemoveTagDialog(parent, current_tags, tag_choices, label=task)
        if artd.exec() == QDialog.DialogCode.Accepted:
            cmd, new_tag = artd.return_values
            if cmd == "add":
                if new_tag:
                    try:
                        self.msgr.add_single_tag(task, new_tag)
                        log.debug('tagging paper "%s" with "%s"', task, new_tag)
                    except PlomBadTagError as e:
                        errmsg = html.escape(str(e))
                        WarnMsg(parent, "Tag not acceptable", info=errmsg).exec()
            elif cmd == "remove":
                try:
                    self.msgr.remove_single_tag(task, new_tag)
                except PlomConflict as e:
                    InfoMsg(
                        parent,
                        "Tag was not present, perhaps someone else removed it?",
                        info=html.escape(str(e)),
                    ).exec()
            else:
                log.error("do nothing - but we shouldn't arrive here.")
                pass

            # refresh the tags
            try:
                current_tags = self.msgr.get_tags(task)
            except PlomNoPaper as e:
                WarnMsg(parent, f"Could not get tags from {task}", info=str(e)).exec()
                return

            assert not task.casefold().startswith("q")
            self.tags_changed_signal.emit(task, current_tags)

    def _update_tags_in_examModel(self, task: str, tags: list[str]):
        assert not task.startswith("q")
        try:
            self.examModel.setTagsByTask(task, tags)
        except ValueError:
            # we might not own the task for which we've have been managing tags
            pass
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.resizeRowsToContents()

    def setFilter(self):
        """Sets a filter tag."""
        search_terms = self.ui.filterLE.text().strip()
        if self.ui.filterInvCB.isChecked():
            self.prxM.set_filter_tags(search_terms, invert=True)
        else:
            self.prxM.set_filter_tags(search_terms)

    def _show_only_my_tasks(self) -> None:
        self.prxM.set_show_only_this_user(self.msgr.username)

    def _show_all_tasks(self) -> None:
        self.prxM.set_show_only_this_user("")

    def choose_and_view_other(self) -> None:
        """Ask user to choose a paper number and question, then show images."""
        max_question_idx = self.exam_spec["numberOfQuestions"]
        qlabels = [
            get_question_label(self.exam_spec, i + 1)
            for i in range(0, max_question_idx)
        ]
        tgs = SelectPaperQuestion(
            self,
            qlabels,
            max_papernum=self.max_papernum,
            initial_idx=self.question_idx,
        )
        if tgs.exec() != QDialog.DialogCode.Accepted:
            return
        paper_number, question_idx, get_annotated = tgs.get_results()
        self.view_other(
            paper_number, question_idx, _parent=self, get_annotated=get_annotated
        )

    def view_other(
        self,
        paper_number: int,
        question_idx: int,
        *,
        _parent: QWidget | None = None,
        get_annotated: bool = True,
    ) -> None:
        """Shows a particular paper number and question.

        Args:
            paper_number: the paper number to be viewed.
            question_idx: which question to be viewed.

        Keyword Args:
            get_annotated: whether to try to get the latest annotated
                image before falling back on the original scanned images.
                True by default.

        Returns:
            None
        """
        tn = paper_number
        q = question_idx

        stuff = None

        if _parent is None:
            _parent = self

        if get_annotated:
            try:
                annot_img_info, annot_img_bytes = self.msgr.get_annotations_image(tn, q)
            except PlomNoPaper:
                pass
            except PlomBenignException as e:
                s = f"Could not get annotation image: {e}"
                s += "\nWill try to get the original images next..."
                WarnMsg(self, s).exec()
            else:
                # TODO: nonunique if we ask again: no caching here
                im_type = annot_img_info["extension"]
                aname = self.workingDirectory / f"annot_{tn}_{q}.{im_type}"
                with open(aname, "wb") as fh:
                    fh.write(annot_img_bytes)
                stuff = [aname]
                s = f"Annotations for paper {tn:04} question index {q}"

        if stuff is None:
            try:
                # TODO: later we might be able to cache here
                # ("q" might not be our question number)
                pagedata = self.get_src_img_data(
                    paper_question_index_to_task_id_str(tn, q)
                )
            except PlomBenignException as e:
                WarnMsg(self, f"Could not get page data: {e}").exec()
                return
            if not pagedata:
                WarnMsg(
                    self,
                    f"No page images for paper {tn:04} question index {q}:"
                    " perhaps it was not written, not yet scanned,"
                    " or possibly that question is not yet scanned"
                    " or has been discarded.",
                ).exec()
                return
            # (even if pagedata not cached, the images will be here)
            pagedata = self.downloader.sync_downloads(pagedata)
            stuff = pagedata
            s = f"Original ungraded images for paper {tn:04} question index {q}"

        # TODO: Restore appending version to the title by fixing Issue #2695
        # qvmap = self.msgr.getQuestionVersionMap(tn)
        # ver = qvmap[q]
        # s += f" (ver {ver})"

        d = QuestionViewDialog(_parent, stuff, tn, q, marker=self, title=s)
        # TODO: future-proofing this a bit for live download updates
        # PC.download_finished.connect(d.shake_things_up)
        d.exec()
        d.deleteLater()  # disconnects slots and signals

    def get_file_for_previous_viewer(self, task: str) -> str | Path | None:
        """Get the annotation file for the given task.

        Check to see if the
        local system already has the files for that task and if not grab them
        from the server. Then pass the annotation-image-file back to the
        caller.
        """
        if not self.get_files_for_previously_annotated(task):
            return None
        # now grab the actual annotated-image filename
        return self.examModel.getAnnotatedFileByTask(task)
