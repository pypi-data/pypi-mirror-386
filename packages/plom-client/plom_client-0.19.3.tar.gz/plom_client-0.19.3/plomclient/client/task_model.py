# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2024 Andrew Rechnitzer
# Copyright (C) 2018 Elvis Cai
# Copyright (C) 2019-2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2022 Edith Coates
# Copyright (C) 2022 Lior Silberman
# Copyright (C) 2024 Bryan Tanady
# Copyright (C) 2024 Aidan Murphy

"""Client-side model for tasks, implementation details for MVC stuff."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from plomclient.misc_utils import pprint_score

from .useful_classes import _json_path_to_str

log = logging.getLogger("marker")


def _marking_time_as_str(m):
    if m < 10:
        # show 2 sigfigs if less than 10
        return f"{m:.2g}"
    else:
        # otherwise show integer
        return f"{m:.0f}"


# yuck numbers, but at least in one place
_idx_task_id = 0  # here called "prefix"
_idx_status = 1
_idx_mark = 2
_idx_marking_time = 3
_idx_tags = 4
_idx_user = 5
_idx_annotated_file = 6
_idx_plom_file = 7
_idx_paper_dir = 8
_idx_src_img_data = 9
_idx_integrity = 10

# the possible status that we make locally
# TODO: "reassigned"?
local_possible_statuses = (
    "untouched",
    "marked",  # deprecated, legacy still uses
    "complete",
    "uploading...",
    "failed upload",
    "deferred",
)

# there is some overlap with the servers's status strings
# note: we don't casefold these ones
server_possible_statuses = ("Complete", "To Do", "Out")


class MarkerExamModel(QStandardItemModel):
    """A tablemodel for handling the group image marking data."""

    columns_to_hide = [
        _idx_annotated_file,
        _idx_plom_file,
        _idx_paper_dir,
        _idx_integrity,
        _idx_src_img_data,
    ]

    def __init__(self, parent=None):
        """Initializes a new MarkerExamModel.

        Args:
            parent (QStandardItemModel): MarkerExamModel's Parent.
        """
        super().__init__(parent)
        self.setHorizontalHeaderLabels(
            [
                "Task",
                "Status",
                "Mark",
                "Time (s)",
                "Tag",
                "User",
                "AnnotatedFile",
                "PlomFile",
                "PaperDir",
                "src_img_data",
                "integrity_check",
            ]
        )

    def add_task(
        self,
        task_id_str: str,
        *,
        src_img_data: list[dict[str, Any]] = [],
        status: str = "untouched",
        mark: int | float | None = -1,
        marking_time: float = 0.0,
        tags: list[str] = [],
        integrity_check: str = "",
        username: str = "",
    ) -> int:
        """Add a new row to the task table.

        Args:
            task_id_str: the Task ID for the page being uploaded. Takes the form
                "1234g9" for paper 1234 question 9.

        Keyword Args:
            status: test status string.
            mark: the mark awarded to the question, can be None.
            marking_time (float/int): marking time spent on that page in seconds.
            tags: Tags corresponding to the exam.  We will flatten to a
                space-separated string.  TODO: maybe we should do that for display
                but store as repr/json.
            integrity_check: something from the server, especially legacy
                servers, generally a concat of md5sums of underlying images.
                The server expects us to be able to give it back to them.
            src_img_data: a list of dicts of md5sums, filenames and other
                metadata of the images for the test question.
            username: who owns this task.

        Returns:
            The integer row identifier of the added paper.

        Raises:
            KeyError: already have a task matching that task_id_str.
        """
        try:
            # raise a KeyError if we already have this task.
            r = self._findTask(task_id_str)
            raise KeyError(f"We already have task {task_id_str} in the table at r={r}.")
        except ValueError as e:
            assert "not found" in str(e), f"Oh my, unexpected stuff: {e}"
            pass

        # some processes might use -1 for unmarked papers
        if mark is not None and mark < 0:
            markstr = ""
        else:
            markstr = pprint_score(mark)

        # these *must* be strings but I don't understand why
        self.appendRow(
            [
                QStandardItem(task_id_str),
                QStandardItem(status),
                QStandardItem(markstr),
                QStandardItem(_marking_time_as_str(marking_time)),
                QStandardItem(" ".join(tags)),
                QStandardItem(username),
                QStandardItem(""),  # annotatedFile,
                QStandardItem(""),  # plomFile
                QStandardItem(""),  # paperdir
                QStandardItem(json.dumps(src_img_data, default=_json_path_to_str)),
                QStandardItem(str(integrity_check)),
            ]
        )
        return self.rowCount() - 1

    def update_task(
        self,
        task_id_str: str,
        *,
        integrity: str,
        src_img_data: list[dict[str, Any]] | None = None,
        status: str = "untouched",
        mark: int = -1,
        marking_time: float = 0.0,
        tags: list[str] = [],
        username: str = "",
    ) -> int:
        """Modify an existing row, keeping any unspecified local data if it is deemed safe to do so.

        Currently only ``src_img_data`` is carefully preserved: this
        may change in the future.

        Args:
            task_id_str: the Task ID for the page being uploaded. Takes the form
                "1234g9" for paper 1234 question 9.

        Keywords Args:
            integrity: mandatory input, used to determine if we can keep things.
            src_img_data: a list of dicts of md5sums, filenames and other
                metadata of the images for the test question.  If this is omitted
                (None) and the integrity matches, we'll keep the current data.
            status: task status string.
            mark: the mark of the question.
            marking_time: marking time spent on that page in seconds.
            tags: Tags corresponding to the exam.  We will flatten to a
                space-separated string.  TODO: maybe we should do that for display
                but store as repr/json.
            username: who owns this task.

        Returns:
            The integer row identifier of the added/modified paper.

        Raises:
            ValueError: cannot find task.
        """
        r = self._findTask(task_id_str)
        log.debug(f"Found task {task_id_str} in the table at r={r}, updating...")

        # its only typed as string, but Nones are getting in...
        if integrity is None:
            integrity = ""
        integrity = str(integrity)

        current_integrity = self.getIntegrityCheck(task_id_str)
        msg = f"Task {task_id_str} integrity"
        if src_img_data is None:
            if current_integrity == integrity:
                # TODO: this includes the blank integrity case
                log.debug(msg + " up-to-date: keep local src_img_data")
            else:
                log.debug(msg + " out-of-date: dropping local src_img_data")
                self.set_source_image_data(task_id_str, [])
        else:
            if current_integrity == integrity:
                log.debug(msg + " up-to-date, but new data forced")
            else:
                log.debug(msg + " out-of-date, and new src_img_data provided")
            self.set_source_image_data(task_id_str, src_img_data)
        self.set_integrity_by_task(task_id_str, integrity)
        self._setStatus(r, status)
        self._set_mark(r, mark)
        self._set_marking_time(r, marking_time)
        self.setTagsByTask(task_id_str, tags)
        self.set_username_by_task(task_id_str, username)
        return r

    def _getPrefix(self, r: int) -> str:
        """Returns the task code of a specified row of the table."""
        return self.data(self.index(r, _idx_task_id))

    def _getStatus(self, r: int) -> str:
        """Returns the status of the image.

        Args:
            r: the row identifier of the paper.

        Returns:
            The status of the image
        """
        return self.data(self.index(r, _idx_status))

    def _setStatus(self, r: int, status: str) -> None:
        """Sets the status of the image.

        Args:
            r: the row identifier of the paper.
            status: the new status string of the image.

        Returns:
            None
        """
        assert (
            status.casefold() in local_possible_statuses
            or status in server_possible_statuses
        ), f'Task status "{status}" is not in the allow lists'
        self.setData(self.index(r, _idx_status), status)

    def _setAnnotatedFile(self, r: int, aname: Path | str, pname: Path | str) -> None:
        self.setData(self.index(r, _idx_annotated_file), str(aname))
        self.setData(self.index(r, _idx_plom_file), str(pname))

    def _setPaperDir(self, r: int, tdir: Path | str | None) -> None:
        """Sets the paper directory for the given paper.

        Args:
            r: the row identifier of the paper.
            tdir: None or the name of a temporary directory for this paper.

        Returns:
            None
        """
        if tdir is not None:
            tdir = str(tdir)
        self.setData(self.index(r, _idx_paper_dir), tdir)

    def _clearPaperDir(self, r: int) -> None:
        """Clears the paper directory for the given paper.

        Args:
            r: the row identifier of the paper.

        Returns:
            None
        """
        self._setPaperDir(r, None)

    def _getPaperDir(self, r: int) -> str:
        """Returns the paper directory for the given paper.

        Args:
            r: the row identifier of the paper.

        Returns:
            Name of a temporary directory for this paper.
        """
        return self.data(self.index(r, _idx_paper_dir))

    def _set_mark(self, r: int, mark: int) -> None:
        # hide -1 which something might be using for "not yet marked"
        try:
            markstr = str(mark) if int(mark) >= 0 else ""
        except ValueError:
            markstr = ""
        self.setData(self.index(r, _idx_mark), markstr)

    def _get_marking_time(self, r):
        column_idx = _idx_marking_time
        # TODO: instead of packing/unpacking a string, there should be a model
        return float(self.data(self.index(r, column_idx)))

    def _set_marking_time(self, r, marking_time):
        column_idx = _idx_marking_time
        self.setData(self.index(r, column_idx), _marking_time_as_str(marking_time))

    def get_all_tasks(self) -> list[str]:
        """Return the task id strings of all the tasks in the full list.

        Result is a list but no particular order is implied: for example
        if the user has sorted the tasks this may or may not reflect that
        ordering.
        """
        return [self._getPrefix(n) for n in range(self.rowCount())]

    def has_task(self, task: str) -> bool:
        try:
            self._findTask(task)
        except ValueError:
            return False
        return True

    def _findTask(self, task: str) -> int:
        """Return the row index of this task.

        Args:
            task (str): the task for the image files to be loaded from.
                Takes the form "1234g9" = test 1234 question index 9.

        Returns:
            The row index of the task.

        Raises:
            ValueError: if task not found.
        """
        r0 = []
        for r in range(self.rowCount()):
            if self._getPrefix(r) == task:
                r0.append(r)

        if len(r0) == 0:
            raise ValueError("task {} not found!".format(task))
        elif not len(r0) == 1:
            raise ValueError(
                "Repeated task {} in rows {}  This should not happen!".format(task, r0)
            )
        return r0[0]

    def _setDataByTask(self, task, n, stuff):
        """Find the row identifier with `task` and sets `n`th column to `stuff`.

        Args:
            task (str): the task for the image files to be loaded from.
            n (int): the column to be loaded into.
            stuff: whatever is being added.

        Returns:
            None
        """
        r = self._findTask(task)
        self.setData(self.index(r, n), stuff)

    def _getDataByTask(self, task, n):
        """Returns contents of task in `n`th column.

        Args:
            task (str): the task for the image files to be loaded from.
            n (int): the column to return from.

        Returns:
            Contents of task in `n`th column.

        Raises:
            ValueError: if task not found.
        """
        r = self._findTask(task)
        return self.data(self.index(r, n))

    def getStatusByTask(self, task: str) -> str:
        """Return status for task."""
        return self._getDataByTask(task, _idx_status)

    def setStatusByTask(self, task: str, st: str) -> None:
        """Set status for task."""
        self._setDataByTask(task, _idx_status, st)

    def getTagsByTask(self, task: str) -> list[str]:
        """Return a list of tags for task.

        TODO: can we draw flat, but use list for storing?
        """
        return self._getDataByTask(task, _idx_tags).split()

    def setTagsByTask(self, task: str, tags: list[str]) -> None:
        """Set a list of tags for task.

        Note: internally stored as flattened string.
        """
        self._setDataByTask(task, _idx_tags, " ".join(tags))

    def get_marking_time_by_task(self, task: str) -> float:
        """Return total marking time (s) for task (str), return float."""
        r = self._findTask(task)
        return self._get_marking_time(r)

    def getAnnotatedFileByTask(self, task: str) -> Path:
        """Returns the filename of the annotated image."""
        return Path(self._getDataByTask(task, _idx_annotated_file))

    def getPlomFileByTask(self, task: str) -> Path:
        """Returns the filename of the plom json data."""
        return Path(self._getDataByTask(task, _idx_plom_file))

    def getPaperDirByTask(self, task: str) -> str:
        """Return temporary directory for this task."""
        return self._getDataByTask(task, _idx_paper_dir)

    def setPaperDirByTask(self, task: str, tdir: Path | str) -> None:
        """Set temporary directory for this grading.

        Args:
            task: the task for the image files to be loaded from.
            tdir: the temporary directory for task to be set to.

        Returns:
            None
        """
        self._setDataByTask(task, _idx_paper_dir, str(tdir))

    def get_source_image_data(self, task):
        """Return the image data (as a list of dicts) for task.

        Raises:
            ValueError: if task not found.
        """
        column_idx = _idx_src_img_data
        r = json.loads(self._getDataByTask(task, column_idx))
        return r

    def set_source_image_data(
        self, task: str, src_img_data: list[dict[str, Any]]
    ) -> None:
        """Set the original un-annotated image filenames and other metadata.

        Note, the data is stored in JSON and Path objects will become plain
        'ol strings.
        """
        log.debug("Setting src img data to {}".format(src_img_data))
        column_idx = _idx_src_img_data
        self._setDataByTask(
            task, column_idx, json.dumps(src_img_data, default=_json_path_to_str)
        )

    def setAnnotatedFile(self, task: str, aname: Path | str, pname: Path | str) -> None:
        """Set the annotated image and .plom file names as strings.

        Args:
            task: the task ID string.
            aname: the name for the annotated file.
            pname: the name for the .plom file

        Returns:
            None
        """
        self._setDataByTask(task, _idx_annotated_file, str(aname))
        self._setDataByTask(task, _idx_plom_file, str(pname))

    def set_username_by_task(self, task: str, user: str) -> None:
        """Set the username of a task."""
        self._setDataByTask(task, _idx_user, user)

    def get_username_by_task(self, task: str) -> str:
        """Get the username of a task."""
        return self._getDataByTask(task, _idx_user)

    def _get_username(self, r: int) -> str:
        return self.data(self.index(r, _idx_user))

    def is_our_task(self, task: str, username) -> bool:
        """Does this task belong to a particular user.

        TODO: includes some asserts about status, which may need
        relaxing/adjusting in the future.
        """
        task_username = self._getDataByTask(task, _idx_user)
        status = self._getDataByTask(task, _idx_status)
        if task_username == username:
            assert (
                status.casefold() in local_possible_statuses
            ), f'Unexpected status "{status}" seen in one of our tasks'
            return True
        assert (
            status in server_possible_statuses
        ), f'Unexpected server task status "{status}"'
        return False

    def set_integrity_by_task(self, task: str, integrity: str) -> None:
        """Set the integrity check for a task."""
        self._setDataByTask(task, _idx_integrity, integrity)

    def getIntegrityCheck(self, task: str) -> str:
        """Return the integrity check string for a task.

        Raises:
            ValueError: if task not found.
        """
        # not sure why we need str() here but it was returning int
        return str(self._getDataByTask(task, _idx_integrity))

    def markPaperByTask(self, task, mark, aname, pname, marking_time, tdir) -> None:
        """Add marking data for the given task.

        Args:
            task (str): the task for the image files to be loaded from.
            mark (int): the mark for this paper.
            aname (str): the annotated file name.
            pname (str): the .plom file name.
            marking_time (int/float): total marking time in seconds.
            tdir (dir): the temporary directory for task to be set to.

        Returns:
            None
        """
        # There should be exactly one row with this Task
        r = self._findTask(task)
        # When marked, set the annotated filename, the plomfile, the mark,
        # and the total marking time (in case it was annotated earlier)
        t = self._get_marking_time(r)
        self._set_marking_time(r, marking_time + t)
        self._setStatus(r, "uploading...")
        self.setData(self.index(r, _idx_mark), pprint_score(mark))
        self._setAnnotatedFile(r, aname, pname)
        self._setPaperDir(r, tdir)

    def deferPaper(self, task):
        """Sets the status for the task's paper to deferred."""
        self.setStatusByTask(task, "deferred")

    def remove_task(self, task: str) -> None:
        """Removes the task from the list."""
        r = self._findTask(task)
        self.removeRow(r)

    def countReadyToMark(self):
        """Returns the number of untouched Papers."""
        count = 0
        for r in range(self.rowCount()):
            if self._getStatus(r) == "untouched":
                count += 1
        return count


##########################
class ProxyModel(QSortFilterProxyModel):
    """A proxymodel wrapper to handle filtering and sorting of table model."""

    def __init__(self, parent=None):
        """Initializes a new ProxyModel object.

        Args:
            parent (QObject): self's parent.
        """
        super().__init__(parent)
        self.setFilterKeyColumn(_idx_tags)
        self.tag_search_terms = []
        self.invert_tag_search = False
        self.show_only_this_user = ""

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """Sees if left data is less than right data.

        Args:
            left (QModelIndex): comparing inequality between left and right.
            right (QModelIndex): as above.

        Returns:
            bool: if both can be converted to int, compare as ints.
            Otherwise, convert to strings and compare.
        """
        # try to compare as integers
        try:
            return int(left.data()) < int(right.data())
        except (ValueError, TypeError):
            pass
        # else compare as strings
        return str(left.data()) < str(right.data())

    def set_show_only_this_user(self, user: str) -> None:
        """Show only the tasks that belong to a particular user."""
        self.show_only_this_user = user
        self._trigger_filter_change()

    def set_filter_tags(self, filter_str: str, *, invert: bool = False) -> None:
        """Filter the visible tasks based on a string.

        Args:
            filter_str: which terms to search for.

        Keyword Args:
            invert: True if looking for tasks that do not have given
                filter string, false otherwise.

        Returns:
            None
        """
        self.invert_tag_search = invert
        self.tag_search_terms = filter_str.casefold().split()
        self._trigger_filter_change()

    def _trigger_filter_change(self) -> None:
        # trigger update (but filterAcceptsRow will be used)
        self.setFilterFixedString("")

    def filterAcceptsRow(self, pos, index):
        """Checks if a row matches the current filter.

        Notes:
            Overrides base method.

        Args:
            pos (int): row being checked.
            index (any): unused.

        Returns:
            bool: True if filter accepts the row, False otherwise.

        The filter string is first broken into words.  All of those words
        must be in the tags of the row, in any order.  The `invert` flag
        inverts that logic: at least one of the words must not be in the
        tags.
        """
        if self.show_only_this_user:
            user = self.sourceModel().data(self.sourceModel().index(pos, _idx_user))
            if user != self.show_only_this_user:
                return False

        tags = (
            self.sourceModel().data(self.sourceModel().index(pos, _idx_tags)).casefold()
        )
        all_search_terms_in_tags = all(x in tags for x in self.tag_search_terms)
        if self.invert_tag_search:
            return not all_search_terms_in_tags
        return all_search_terms_in_tags

    def getPrefix(self, r: int) -> str:
        """Returns the task code of a given row index."""
        return self.data(self.index(r, _idx_task_id))

    def getStatus(self, r: int) -> str:
        """Returns the status of inputted row index.

        Args:
            r: the row identifier of the paper.

        Returns:
            The status of the paper indicated by r.
        """
        return self.data(self.index(r, _idx_status))

    def getAnnotatedFile(self, r: int) -> Path:
        """Returns the file names of an annotated image.

        Args:
            r: the row identifier of the paper.

        Returns:
            The file name of the annotated image of the paper in r.
        """
        return Path(self.data(self.index(r, _idx_annotated_file)))

    def rowFromTask(self, task):
        """Return the row index (int) of this task (str) or None if absent."""
        r0 = []
        for r in range(self.rowCount()):
            if self.getPrefix(r) == task:
                r0.append(r)

        if len(r0) == 0:
            return None
        elif not len(r0) == 1:
            raise ValueError(
                "Repeated task {} in rows {}  This should not happen!".format(task, r0)
            )
        return r0[0]
