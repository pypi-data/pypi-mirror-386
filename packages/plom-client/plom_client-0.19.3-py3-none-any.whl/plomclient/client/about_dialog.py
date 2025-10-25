# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2021-2025 Colin B. Macdonald

import platform
from textwrap import dedent

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt6.QtWidgets import QMessageBox
from requests import __version__ as requests_version

from . import __version__

# TODO: use resources to important contributors list?


def show_about_dialog(parent):
    QMessageBox.about(
        parent,
        "Plom Client",
        dedent(
            f"""
            <h2>Plom Client {__version__}</h2>

            <p><a href="https://plomgrading.org">https://plomgrading.org</a></p>

            <p>Copyright &copy; 2018-2025 Andrew Rechnitzer,
            Colin B. Macdonald, and other contributors.</p>

            <p>Plom is Free Software, available under the GNU Affero
            General Public License version 3, or at your option, any
            later version.</p>

            <h3>Contributors</h3>

            <p>Plom would not have been possible without the help of
            <a href="https://gitlab.com/plom/plom/-/blob/main/CONTRIBUTORS">our
            contributors</a>.</p>

            <h3>System info</h3>
            <p>
            PyQt {PYQT_VERSION_STR} (Qt {QT_VERSION_STR})<br />
            Requests {requests_version}<br />
            Python {platform.python_version()}<br />
            {platform.platform()}</p>
            """
        ),
    )
