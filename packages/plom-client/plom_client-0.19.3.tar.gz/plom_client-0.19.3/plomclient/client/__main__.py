#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2020 Andrew Rechnitzer
# Copyright (C) 2018 Elvis Cai
# Copyright (C) 2019-2025 Colin B. Macdonald
# Copyright (C) 2021 Elizabeth Xiao
# Copyright (C) 2022 Edith Coates

"""Start the Plom client."""

__copyright__ = "Copyright (C) 2018-2025 Andrew Rechnitzer, Colin B. Macdonald, et al"
__credits__ = "The Plom Project Developers"
__license__ = "AGPL-3.0-or-later"

import argparse
import os
import platform
import signal
import sys
import traceback as tblib
from multiprocessing import freeze_support
from textwrap import shorten

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox, QStyleFactory

from plomclient.common import Default_Port
from plomclient.misc_utils import utc_now_to_string
from plomclient.client import __version__
from plomclient.client import Chooser
from plomclient.client.useful_classes import ErrorMsg, WarningQuestion


def add_popup_to_toplevel_exception_handler() -> None:
    """Muck around with sys's excepthook to popup dialogs on exception and force exit."""
    # monkey-patch in a reference to the original hook
    sys._excepthook = sys.excepthook  # type: ignore[attr-defined]

    def exception_hook(exctype, value, traceback):
        rawlines = tblib.format_exception(exctype, value, traceback)
        # docs say some of the lines may contain newlines so join and split again
        lines = "".join(rawlines).splitlines()
        # only last few lines
        if len(lines) >= 9:
            lines = ["\N{VERTICAL ELLIPSIS}", *lines[-7:]]
        # no line too long
        lines = [shorten(x, 88, placeholder="\N{HORIZONTAL ELLIPSIS}") for x in lines]
        abbrev = "\n".join(lines)

        rawlines.insert(0, f"Timestamp: {utc_now_to_string()}\n\n")
        details = "".join(rawlines)

        txt = f"""<p><b>Something unexpected has happened!</b>
        A partial error message follows.</p>
        <p>(You could consider filing an issue; if you do, please copy-paste
        the text under &ldquo;Details&rdquo;.)</p>
        <p>Plom v{__version__}<br />
        PyQt {PYQT_VERSION_STR} (Qt {QT_VERSION_STR})<br />
        Python {platform.python_version()},
        {platform.platform()}<br />
        Timestamp: {utc_now_to_string()}</p>
        """
        msg = ErrorMsg(None, txt, info=abbrev, details=details)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
        # call the original hook after our dialog closes
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook


def sigint_handler(*args) -> None:
    """Handler for the SIGINT signal.

    This is in order to have a somewhat graceful exit on control-c [1]

    [1] https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co?noredirect=1&lq=1
    """
    sys.stderr.write("\r")
    msg = WarningQuestion(
        None, "Caught interrupt signal!", "Do you want to force-quit?"
    )
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    if msg.exec() == QMessageBox.StandardButton.Yes:
        QApplication.exit(42)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Plom client. No arguments = run as normal."
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "user",
        type=str,
        nargs="?",
        help="Also checks the environment variable PLOM_USER.",
    )
    parser.add_argument(
        "password",
        type=str,
        nargs="?",
        help="Also checks the environment variable PLOM_PASSWORD.",
    )
    parser.add_argument(
        "-s",
        "--server",
        metavar="SERVER[:PORT]",
        action="store",
        help=f"""
            Which server to contact, port defaults to {Default_Port}.
            Also checks the environment variable PLOM_SERVER if omitted.
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i", "--identifier", action="store_true", help="Run the identifier"
    )
    group.add_argument(
        "-m",
        "--marker",
        const="json",
        nargs="?",
        type=str,
        help="""
            Run the marker. Pass either -m n:k (to run on pagegroup n, version k)
            or -m (to run on whatever was used last time).
        """,
    )
    return parser


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    args.server = args.server or os.environ.get("PLOM_SERVER")
    args.password = args.password or os.environ.get("PLOM_PASSWORD")
    args.user = args.user or os.environ.get("PLOM_USER")

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("PlomClient")
    app.setApplicationVersion(__version__)

    signal.signal(signal.SIGINT, sigint_handler)
    add_popup_to_toplevel_exception_handler()

    # create a small timer here, so that we can
    # kill the app with ctrl-c.
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(1000)
    # got this solution from
    # https://machinekoder.com/how-to-not-shoot-yourself-in-the-foot-using-python-qt/

    window = Chooser(app)
    window.show()

    if args.user:
        window.ui.userLE.setText(args.user)
    window.ui.passwordLE.setText(args.password)
    if args.server:
        window.setServer(args.server)

    if args.identifier:
        window.ui.identifyButton.animateClick()
    if args.marker:
        if args.marker != "json":
            pg, v = args.marker.split(":")
            try:
                window.ui.pgSB.setValue(int(pg))
                window.ui.vSB.setValue(int(v))
            except ValueError:
                print(
                    "When you use -m, there should either be no argument, or "
                    " an argument of the form n:k where n,k are integers."
                )
                sys.exit(43)

        window.ui.markButton.animateClick()
    sys.exit(app.exec())


if __name__ == "__main__":
    # See Issue #2172: needed for Windows + PyInstaller
    freeze_support()
    main()
